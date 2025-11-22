from PIL import Image
import numpy as np
from collections import Counter
import os


def _merge_positions(positions, threshold):
    """Merge nearby positions into single representative positions."""
    if len(positions) == 0:
        return []

    merged = []
    group_sum = int(positions[0])
    group_count = 1
    last_pos = positions[0]

    for pos in positions[1:]:
        if pos - last_pos <= threshold:
            group_sum += int(pos)
            group_count += 1
        else:
            merged.append(int(round(group_sum / group_count)))
            group_sum = int(pos)
            group_count = 1
        last_pos = pos

    merged.append(int(round(group_sum / group_count)))
    return merged


def find_non_white_at_fraction(
    image_path, x_fraction=1 / 5, intensity_threshold=250, merge_threshold=3
):
    """Find y coordinates with non-white content at a fractional x position."""
    img_array = np.array(Image.open(image_path).convert('L'))
    height, width = img_array.shape

    x = max(0, min(width - 1, int(width * x_fraction)))
    non_white_ys = np.where(img_array[:, x] < intensity_threshold)[0]

    if non_white_ys.size == 0:
        return x, np.array([], dtype=int)

    merged = _merge_positions(non_white_ys, merge_threshold)
    return x, np.array(merged, dtype=int)


def _is_wall(img_array, x, y, wall_height, intensity_threshold):
    """Check if position is a vertical wall."""
    height, width = img_array.shape

    if x < 0 or x >= width or y < wall_height or y >= height - wall_height:
        return False

    # Check if pixels above and below are all black
    return np.all(
        img_array[y - wall_height : y + wall_height + 1, x] < intensity_threshold
    )


def find_cell_walls(
    image_path,
    y_coords,
    x_start,
    search_range=None,
    intensity_threshold=250,
    wall_height=10,
):
    """Find left and right cell wall x-positions for each y coordinate."""
    img_array = np.array(Image.open(image_path).convert('L'))
    height, width = img_array.shape

    if search_range is None:
        search_range = (0, width - 1)

    walls = []
    for y in y_coords:
        if y < wall_height or y >= height - wall_height:
            walls.append((None, None))
            continue

        # Search left from x_start
        left_wall = next(
            (
                x
                for x in range(x_start, search_range[0] - 1, -1)
                if _is_wall(img_array, x, y, wall_height, intensity_threshold)
            ),
            None,
        )

        # Search right from x_start
        right_wall = next(
            (
                x
                for x in range(x_start, search_range[1] + 1)
                if _is_wall(img_array, x, y, wall_height, intensity_threshold)
            ),
            None,
        )

        walls.append((left_wall, right_wall))

    return walls


def filter_by_most_common_width(cell_walls, y_coords, tolerance=5):
    """Filter cell walls to keep only those matching the most common width."""
    valid_cells = [
        (y_coords[i], left, right, right - left)
        for i, (left, right) in enumerate(cell_walls)
        if left is not None and right is not None
    ]

    if not valid_cells:
        return []

    widths = [cell[3] for cell in valid_cells]
    most_common_width = Counter(widths).most_common(1)[0][0]

    return [
        cell for cell in valid_cells if abs(cell[3] - most_common_width) <= tolerance
    ]


def extract_cell_squares(filtered_cells, image_path):
    """Compute cell boundaries (left, top, right, bottom) for each filtered cell."""
    if not filtered_cells:
        return []

    img_array = np.array(Image.open(image_path).convert('L'))
    img_height, img_width = img_array.shape

    centers = [c[0] for c in filtered_cells]
    squares = []

    for i, (y, left, right, width) in enumerate(filtered_cells):
        prev_y = centers[i - 1] if i > 0 else None
        next_y = centers[i + 1] if i < len(centers) - 1 else None

        # Calculate top/bottom based on neighbors
        if prev_y and next_y:
            top, bottom = (prev_y + y) // 2, (y + next_y) // 2
        elif next_y:
            top = max(0, y - (next_y - y) // 2)
            bottom = (y + next_y) // 2
        elif prev_y:
            top = (prev_y + y) // 2
            bottom = min(img_height - 1, y + (y - prev_y) // 2)
        else:
            half_h = width // 2 or 1
            top = max(0, y - half_h)
            bottom = min(img_height - 1, y + half_h)

        # Ensure valid bounds
        top = max(0, min(img_height - 1, top))
        bottom = max(top + 1, min(img_height - 1, bottom))
        left = max(0, left)
        right = min(img_width - 1, right)

        squares.append((y, left, top, right, bottom))

    return squares


def save_squares(squares, image_path, out_dir='extracted_cells', prefix='cell'):
    """Save cropped rectangles from the image."""
    if not squares:
        return []

    os.makedirs(out_dir, exist_ok=True)
    img = Image.open(image_path).convert('RGB')
    img_w, img_h = img.size

    saved_paths = []
    for i, (y, left, top, right, bottom) in enumerate(squares):
        if None in (left, right, top, bottom):
            continue

        # Clamp coordinates (PIL crop uses exclusive upper bounds)
        left, top = max(0, int(left)), max(0, int(top))
        right, bottom = min(img_w, int(right) + 1), min(img_h, int(bottom) + 1)

        if right <= left or bottom <= top:
            continue

        crop = img.crop((left, top, right, bottom))
        filename = f'{prefix}_{i}_y{y}_l{left}_t{top}_r{right - 1}_b{bottom - 1}.png'
        out_path = os.path.join(out_dir, filename)
        crop.save(out_path)
        saved_paths.append(out_path)

    return saved_paths


def extract_cells_from_image(
    image_path,
    out_dir='extracted_cells',
    x_fraction=1 / 5,
    intensity_threshold=250,
    merge_threshold=3,
    wall_height=10,
    width_tolerance=5,
    prefix='cell',
):
    """Extract component cells from an image and save them to a directory."""
    # Find cell centers
    x_pos, y_coords = find_non_white_at_fraction(
        image_path, x_fraction, intensity_threshold, merge_threshold
    )

    if len(y_coords) == 0:
        return 0

    # Find cell boundaries
    cell_walls = find_cell_walls(
        image_path,
        y_coords,
        x_pos,
        intensity_threshold=intensity_threshold,
        wall_height=wall_height,
    )

    # Filter by most common width
    filtered_cells = filter_by_most_common_width(cell_walls, y_coords, width_tolerance)

    if not filtered_cells:
        return 0

    # Extract and save cells
    squares = extract_cell_squares(filtered_cells, image_path)
    saved = save_squares(squares, image_path, out_dir, prefix)

    return len(saved)
