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
x_pos, y_coords = find_non_white_at_fraction('output_page.jpg', x_fraction=1/5, intensity_threshold=250, merge_threshold=3)
print(f"Scanning at x={x_pos}")
print(f"Found {len(y_coords)} merged non-white line positions")
print(y_coords)