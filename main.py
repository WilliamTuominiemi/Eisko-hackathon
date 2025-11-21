from PIL import Image
import numpy as np

def find_non_white_at_fraction(image_path, x_fraction=1/5, intensity_threshold=250, merge_threshold=3):
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
    img = Image.open(image_path).convert('L')
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

from PIL import Image
import numpy as np

def find_cell_walls(image_path, y_coords, x_start, search_range=None, 
                    intensity_threshold=250, wall_height=10):
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
    img = Image.open(image_path).convert('L')
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

# Complete usage
x_pos, y_coords = find_non_white_at_fraction(
    'output_page.jpg', 
    x_fraction=1/5, 
    intensity_threshold=250, 
    merge_threshold=3
)

print(f"Scanning at x={x_pos}")
print(f"Found {len(y_coords)} merged non-white line positions")

# Find cell walls
cell_walls = find_cell_walls(
    'output_page.jpg',
    y_coords,
    x_start=x_pos,
    intensity_threshold=250,
    wall_height=10
)

print("\nCell walls found:")
for i, (left, right) in enumerate(cell_walls):
    if left is not None and right is not None:
        width = right - left
        print(f"Row {i} (y={y_coords[i]}): Left wall at x={left}, Right wall at x={right}, Width={width}px")
    else:
        print(f"Row {i} (y={y_coords[i]}): Walls not found (left={left}, right={right})")