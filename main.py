from PIL import Image
import numpy as np

def find_non_white_at_fraction(image_path, x_fraction=1/5, threshold=250):
    """
    Find all y coordinates with non-white content at a fractional x position.
    
    Args:
        image_path: Path to the image
        x_fraction: Fraction of width (e.g., 1/5 = 0.2)
        threshold: Pixel values below this are considered non-white
    
    Returns:
        x position and array of y coordinates
    """
    img = Image.open(image_path)
    img_array = np.array(img)
    
    # Calculate x position
    height, width = img_array.shape[:2]
    x = int(width * x_fraction)
    
    # Get the column at x
    column = img_array[:, x]
    
    # Find non-white pixels
    if len(column.shape) == 2:  # RGB/RGBA
        non_white_ys = np.where(np.any(column < threshold, axis=1))[0]
    else:  # Grayscale
        non_white_ys = np.where(column < threshold)[0]
    
    return x, non_white_ys

# Usage
x_pos, y_coords = find_non_white_at_fraction('output_page.jpg', x_fraction=1/5)
print(f"Scanning at x={x_pos}")
print(f"Found {len(y_coords)} non-white pixels")
print(y_coords)