from PIL import Image
import numpy as np
from collections import Counter
import os


def find_non_white_at_fraction(
    image_path, x_fraction=1 / 5, intensity_threshold=250, merge_threshold=3
):
    """
    Find y coordinates with non-white content at a fractional x position,
    merging nearby y positions that are within merge_threshold pixels.

    Args:
        image_path: Path to the image
        x_fraction: Fraction of width (e.g., 1/5 = 0.2)
        intensity_threshold: Pixel values below this are considered non-white (0-255)
        merge_threshold: Vertical pixel distance under which two y positions are merged

    Returns:
        x position and numpy array of merged y coordinates
    """
    # Open as grayscale for simpler thresholding
    img = Image.open(image_path).convert("L")
    img_array = np.array(img)

    # Calculate x position and clamp to valid range
    height, width = img_array.shape[:2]
    x = int(width * x_fraction)
    x = max(0, min(width - 1, x))

    # Get the column at x
    column = img_array[:, x]

    # Find non-white pixels
    non_white_ys = np.where(column < intensity_threshold)[0]

    # If none found return empty array
    if non_white_ys.size == 0:
        return x, np.array([], dtype=int)

    # Merge nearby y indices into single representative positions
    merged = []
    group_sum = int(non_white_ys[0])
    group_count = 1
    last_y = non_white_ys[0]

    for y in non_white_ys[1:]:
        if y - last_y <= merge_threshold:
            group_sum += int(y)
            group_count += 1
        else:
            # finalize group (use integer average)
            merged.append(int(round(group_sum / group_count)))
            group_sum = int(y)
            group_count = 1
        last_y = y
    # finalize final group
    merged.append(int(round(group_sum / group_count)))

    return x, np.array(merged, dtype=int)


# Usage
# x_pos, y_coords = find_non_white_at_fraction('output_page.jpg', x_fraction=1/5, intensity_threshold=250, merge_threshold=3)
# print(f"Scanning at x={x_pos}")
# print(f"Found {len(y_coords)} merged non-white line positions")
# print(y_coords)


def find_cell_walls(
    image_path,
    y_coords,
    x_start,
    search_range=None,
    intensity_threshold=250,
    wall_height=10,
):
    """
    Find left and right cell wall x-positions for each y coordinate.
    A wall is detected when there's continuous black for wall_height pixels above and below.

    Args:
        image_path: Path to the image
        y_coords: Array of y coordinates to scan from
        x_start: Starting x position (e.g., the 1/5 width position)
        search_range: (left_limit, right_limit) for x search, or None for full width
        intensity_threshold: Pixel values below this are considered black
        wall_height: Pixels above and below that must be black to confirm a wall

    Returns:
        List of tuples: [(left_x, right_x), ...] for each y coordinate
    """
    # Open as grayscale
    img = Image.open(image_path).convert("L")
    img_array = np.array(img)
    height, width = img_array.shape

    if search_range is None:
        search_range = (0, width - 1)

    walls = []

    for y in y_coords:
        # Ensure y is within valid range for checking above/below
        if y < wall_height or y >= height - wall_height:
            walls.append((None, None))
            continue

        left_wall = None
        right_wall = None

        # Search left from x_start
        for x in range(x_start, search_range[0] - 1, -1):
            if is_wall(img_array, x, y, wall_height, intensity_threshold):
                left_wall = x
                break

        # Search right from x_start
        for x in range(x_start, search_range[1] + 1):
            if is_wall(img_array, x, y, wall_height, intensity_threshold):
                right_wall = x
                break

        walls.append((left_wall, right_wall))

    return walls


def is_wall(img_array, x, y, wall_height, intensity_threshold):
    """
    Check if position (x, y) is a vertical wall by checking if pixels
    wall_height above and below are all black.
    """
    height, width = img_array.shape

    # Check bounds
    if x < 0 or x >= width or y < wall_height or y >= height - wall_height:
        return False

    # Check vertical line: wall_height pixels above and below
    for dy in range(-wall_height, wall_height + 1):
        if img_array[y + dy, x] >= intensity_threshold:  # Not black
            return False

    return True


def filter_by_most_common_width(cell_walls, y_coords, tolerance=5):
    """
    Filter cell walls to keep only those matching the most common width.

    Args:
        cell_walls: List of (left_x, right_x) tuples
        y_coords: Corresponding y coordinates
        tolerance: Allow widths within ±tolerance pixels of the most common

    Returns:
        Filtered list of (y, left_x, right_x, width) tuples
    """
    # Calculate widths for valid walls
    valid_cells = []
    for i, (left, right) in enumerate(cell_walls):
        if left is not None and right is not None:
            width = right - left
            valid_cells.append((y_coords[i], left, right, width))

    if not valid_cells:
        return []

    # Get all widths
    widths = [cell[3] for cell in valid_cells]

    # Find most common width
    width_counts = Counter(widths)
    most_common_width = width_counts.most_common(1)[0][0]

    print(
        f"Most common width: {most_common_width}px (appears {width_counts[most_common_width]} times)"
    )

    # Filter cells with width close to most common
    filtered = [
        cell for cell in valid_cells if abs(cell[3] - most_common_width) <= tolerance
    ]

    return filtered


def extract_cell_squares(filtered_cells, image_path):
    """
    From filtered_cells (list of (y, left, right, width)), compute square corners
    (left, top, right, bottom) where top is midpoint between this center y and previous center,
    and bottom is midpoint between this center y and next center. Edges use the sole neighbor
    or fallback to half the width if no neighbor exists.
    """
    if not filtered_cells:
        return []

    # Open image to get bounds
    img = Image.open(image_path).convert("L")
    img_array = np.array(img)
    img_height, img_width = img_array.shape

    centers = [c[0] for c in filtered_cells]
    squares = []

    n = len(centers)
    for i, (y, left, right, width) in enumerate(filtered_cells):
        prev_y = centers[i - 1] if i > 0 else None
        next_y = centers[i + 1] if i < n - 1 else None

        if prev_y is not None and next_y is not None:
            top = (prev_y + y) // 2
            bottom = (y + next_y) // 2
        elif prev_y is None and next_y is not None:
            # first cell: top halfway toward next
            top = max(0, y - (next_y - y) // 2)
            bottom = (y + next_y) // 2
        elif prev_y is not None and next_y is None:
            # last cell: bottom halfway from previous
            top = (prev_y + y) // 2
            bottom = min(img_height - 1, y + (y - prev_y) // 2)
        else:
            # single cell fallback: use half the width as half-height
            half_h = width // 2
            top = max(0, y - half_h)
            bottom = min(img_height - 1, y + half_h)

        # Ensure integer and within bounds
        top = int(max(0, min(img_height - 1, top)))
        bottom = int(max(0, min(img_height - 1, bottom)))

        # If top >= bottom, fallback to square centered at y using width
        if top >= bottom:
            half_h = width // 2 or 1
            top = int(max(0, y - half_h))
            bottom = int(min(img_height - 1, y + half_h))

        # Clamp left/right as well
        left = int(max(0, left)) if left is not None else None
        right = int(min(img_width - 1, right)) if right is not None else None

        squares.append((y, left, top, right, bottom))

    return squares


def save_squares(squares, image_path, out_dir="extracted_cells", prefix="cell"):
    """
    Save cropped rectangles defined by squares (list of (y, left, top, right, bottom))
    from the original image to out_dir. Returns list of saved file paths.
    """
    if not squares:
        return []

    os.makedirs(out_dir, exist_ok=True)
    img = Image.open(image_path).convert("RGB")
    img_w, img_h = img.size

    saved_paths = []
    for i, (y, left, top, right, bottom) in enumerate(squares):
        # Skip incomplete boxes
        if left is None or right is None or top is None or bottom is None:
            continue

        # Clamp coordinates
        left_coord = max(0, int(left))
        upper_coord = max(0, int(top))
        right_coord = min(img_w, int(right) + 1)  # PIL crop right is exclusive
        lower_coord = min(img_h, int(bottom) + 1)  # PIL crop lower is exclusive

        # Skip invalid boxes
        if right_coord <= left_coord or lower_coord <= upper_coord:
            continue

        crop = img.crop((left_coord, upper_coord, right_coord, lower_coord))
        filename = f"{prefix}_{i}_y{y}_l{left_coord}_t{upper_coord}_r{right_coord - 1}_b{lower_coord - 1}.png"
        out_path = os.path.join(out_dir, filename)
        crop.save(out_path)
        saved_paths.append(out_path)

    return saved_paths


def extract_cells_from_image(
    image_path,
    out_dir="extracted_cells",
    x_fraction=1 / 5,
    intensity_threshold=250,
    merge_threshold=3,
    wall_height=10,
    width_tolerance=5,
    prefix="cell",
):
    """
    Extract component cells from an image and save them to a directory.

    Args:
        image_path: Path to the input image
        out_dir: Directory to save extracted cells
        x_fraction: Fraction of width to scan for cell centers (default 1/5)
        intensity_threshold: Pixel values below this are considered non-white (0-255)
        merge_threshold: Vertical pixel distance under which two y positions are merged
        wall_height: Pixels above and below that must be black to confirm a wall
        width_tolerance: Allow widths within ±tolerance pixels of the most common
        prefix: Prefix for saved cell filenames

    Returns:
        int: Number of cells extracted
    """
    # Find non-white positions at fractional x position
    x_pos, y_coords = find_non_white_at_fraction(
        image_path,
        x_fraction=x_fraction,
        intensity_threshold=intensity_threshold,
        merge_threshold=merge_threshold,
    )

    if len(y_coords) == 0:
        print(f"No cells found in {image_path}")
        return 0

    # Find cell walls
    cell_walls = find_cell_walls(
        image_path,
        y_coords,
        x_start=x_pos,
        intensity_threshold=intensity_threshold,
        wall_height=wall_height,
    )

    # Filter by most common width
    filtered_cells = filter_by_most_common_width(
        cell_walls, y_coords, tolerance=width_tolerance
    )

    if not filtered_cells:
        print(f"No valid cells after filtering in {image_path}")
        return 0

    # Extract square corners for each filtered cell
    squares = extract_cell_squares(filtered_cells, image_path)

    # Save cropped rectangles to folder
    saved = save_squares(squares, image_path, out_dir=out_dir, prefix=prefix)

    return len(saved)
