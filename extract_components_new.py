from PIL import Image
import numpy as np
from collections import Counter
import os

def find_component_area(filepath):
    print(filepath)
    
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
                    # print(f"Found thicker bar at x={bar_start} (width={bar_width}) on row {current_y}")
                    break
                # Reset for next bar
                bar_start = None
                bar_width = 0
        
        # Check if we ended on a black bar
        if bar_width >= MIN_BAR_WIDTH:
            bar_x = bar_start
            bar_center_x = bar_start + bar_width // 2
            initial_y = current_y
            # print(f"Found thicker bar at x={bar_start} (width={bar_width}) on row {current_y}")
        
        if bar_x is not None:
            break
    
    if bar_x is None:
        print("No thicker black bar found")
        return None
    
    # Assuming img_array is a numpy array (grayscale image), BLACK_THRESHOLD is defined,
    # initial_y and bar_center_x are the starting point in the middle of the bar,
    # height = img_array.shape[0]

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
    
    # print(f"First bar vertical range: y={bar_top} to y={bar_bottom} (height={bar_bottom - bar_top + 1})")
    
    # Now scan rightwards from the top position to find the next black line
    next_bar_x = None
    start_x = bar_center_x + 1  # Start after the current bar
    

    for x in range(start_x, width):
        if img_array[bar_top, x] < BLACK_THRESHOLD:
            next_bar_x = x
            # print(f"Found next black line at x={next_bar_x}")
            break
    
    if next_bar_x is None:
        # print("No next black line found to the right")
        return {
            'x_start': bar_x,
            'x_end': None,
            'y_start': bar_top,
            'y_end': bar_bottom,
            'height': bar_bottom - bar_top + 1
        }
  
    
    # print(f"Next bar vertical range: y={next_bar_top} to y={next_bar_bottom} (height={next_bar_bottom - next_bar_top + 1})")
    
    return {
        'x_start': bar_x + 30,
        'x_end': next_bar_x - 30,
        'y_start': bar_top,
        'y_end': bar_bottom,
    }

def export_area_to_analyze(filepath):
    area = find_component_area(filepath)
    output_path = "extracted_components.jpg"

    print(area)

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
    

# Test the function
input_path  = "pages/page_2.jpg"
export_area_to_analyze(input_path)
