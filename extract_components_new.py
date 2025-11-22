from PIL import Image
import numpy as np
from collections import Counter
import os

def find_component_area(filepath):    
    # Load the image and convert to grayscale
    img = Image.open(filepath).convert('L')
    img_array = np.array(img)
    
    height, width = img_array.shape
    scan_y = height // 2
    
    # Define threshold for "black" pixels (adjust as needed)
    BLACK_THRESHOLD = 100
    # Minimum width for a "thicker" bar (adjust based on your data)
    MIN_BAR_WIDTH = 3
    
    # Try a few rows if we hit a horizontal line
    max_attempts = 5
    
    bar_x = None
    bar_center_x = None
    initial_y = None
    
    for attempt in range(max_attempts):
        current_y = scan_y + attempt
        if current_y >= height:
            break
            
        # Get the row of pixels
        row = img_array[current_y, :]
        
        # Find consecutive black pixels
        is_black = row < BLACK_THRESHOLD
        
        # Find runs of black pixels
        bar_start = None
        bar_width = 0
        
        for x in range(width):
            if is_black[x]:
                if bar_start is None:
                    bar_start = x
                bar_width += 1
            else:
                # End of a black region
                if bar_width >= MIN_BAR_WIDTH:
                    bar_x = bar_start
                    bar_center_x = bar_start + bar_width // 2
                    initial_y = current_y
                    break
                # Reset for next bar
                bar_start = None
                bar_width = 0
        
        # Check if we ended on a black bar
        if bar_width >= MIN_BAR_WIDTH:
            bar_x = bar_start
            bar_center_x = bar_start + bar_width // 2
            initial_y = current_y
        
        if bar_x is not None:
            break
    
    if bar_x is None:
        print("No thicker black bar found")
        return None

    GAP_TOLERANCE = 1  # Allow this many consecutive non-black pixels before stopping (adjust as needed for noise)

    # Trace upward (towards smaller y)
    bar_top = initial_y
    y = initial_y - 1
    gap_count = 0
    while y >= 0:
        if img_array[y, bar_center_x] < BLACK_THRESHOLD:
            bar_top = y
            gap_count = 0
        else:
            gap_count += 1
            if gap_count > GAP_TOLERANCE:
                break
        y -= 1

    # Trace downward (towards larger y)
    bar_bottom = initial_y
    y = initial_y + 1
    gap_count = 0
    while y < height:
        if img_array[y, bar_center_x] < BLACK_THRESHOLD:
            bar_bottom = y
            gap_count = 0
        else:
            gap_count += 1
            if gap_count > GAP_TOLERANCE:
                break
        y += 1
        
    # Now scan rightwards from the top position to find the next black line
    next_bar_x = None
    start_x = bar_center_x + 1  # Start after the current bar
    

    for x in range(start_x, width):
        if img_array[bar_top, x] < BLACK_THRESHOLD:
            next_bar_x = x
            break
    
    if next_bar_x is None:
        return {
            'x_start': bar_x,
            'x_end': None,
            'y_start': bar_top,
            'y_end': bar_bottom,
            'height': bar_bottom - bar_top + 1
        }
      
    return {
        'x_start': bar_x + 30,
        'x_end': next_bar_x - 30,
        'y_start': bar_top,
        'y_end': bar_bottom,
    }

def export_area_to_analyze(filepath, area):
    output_path = "extracted_components.jpg"

    img = Image.open(input_path)

    crop_box = (
        area['x_start'],
        area['y_start'],
        area['x_end'],
        area['y_end']
    )

    cropped = img.crop(crop_box)

    cropped.save(output_path, "JPEG", quality=95)

    print(f"Saved cropped component → {output_path}")
    print(f"Size: {cropped.width} × {cropped.height} pixels")
    
def find_non_white_at_fraction(
    image_path, x_fraction=1 / 10, intensity_threshold=250, merge_threshold=5
):
    """Find y coordinates with non-white content at a fractional x position."""
    img_array = np.array(Image.open(image_path).convert('L'))
    height, width = img_array.shape

    x = max(0, min(width - 1, int(width * x_fraction)))
    non_white_ys = np.where(img_array[:, x] < intensity_threshold)[0]

    if non_white_ys.size == 0:
        return x, np.array([], dtype=int)
    
    # Compute gaps between consecutive detections
    gaps = np.diff(non_white_ys)
    
    # Find indices where gap > merge_threshold → these mark new clusters
    split_points = np.where(gaps > merge_threshold)[0] + 1
    
    # Split the array into clusters and take the first element of each
    clusters = np.split(non_white_ys, split_points)
    selected_ys = np.array([cluster[0] for cluster in clusters], dtype=int)
    
    return x, selected_ys

# Test the function

input_path  = "pages/page_2.jpg"
area = find_component_area(input_path)
print(area)

export_area_to_analyze(input_path, area)

output_path = "extracted_components.jpg"
print(find_non_white_at_fraction(output_path))