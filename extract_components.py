from PIL import Image
import numpy as np
import os
from typing import Dict
from OCR import ocr_read_area
import pytesseract


def normalize_suoja_value(suoja_value: str) -> str:
    if '/' in suoja_value:
        return suoja_value.split('/')[-1].strip()
    return suoja_value.strip()


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
        print('No thicker black bar found')
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
            'height': bar_bottom - bar_top + 1,
        }

    return {
        'x_start': bar_x + 20,
        'x_end': 1020,
        'y_start': bar_top,
        'y_end': bar_bottom,
    }


def export_area_to_analyze(filepath, area, output_path):
    img = Image.open(filepath)

    # {'x_start': 225, 'x_end': 997, 'y_start': 320, 'y_end': 2103}
    print(area)

    crop_box = (area['x_start'], area['y_start'], area['x_end'], area['y_end'])

    cropped = img.crop(crop_box)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cropped.save(output_path, 'JPEG', quality=95)

    # print(f'Saved cropped component → {output_path}')
    # print(f'Size: {cropped.width} × {cropped.height} pixels')


def find_non_white_at_fraction(
    image_path, x_fraction=1 / 10, intensity_threshold=250, merge_threshold=5
):
    """Find y coordinates with non-white content at a fractional x position."""
    img_array = np.array(Image.open(image_path).convert('L'))

    img = Image.open(image_path).convert('L')
    img_array = np.array(img)
    height, width = img_array.shape

    x = 5
    antiX = width - 5
    non_white_ys = np.where(img_array[:, x] < intensity_threshold)[0]
    non_white_ys_rev = np.where(img_array[:, antiX] < intensity_threshold)[0]

    combined_non_whites = np.unique(np.concatenate((non_white_ys, non_white_ys_rev)))
    non_white_ys = combined_non_whites  # use combined results for downstream processing

    print(non_white_ys)

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


def extract_components(lines, image_path):
    # Extract just the y-coordinates array from the tuple
    y_coordinates = lines[1]  # lines[1] contains the array of y-coordinates

    # print(f'Detected lines at y-coordinates: {y_coordinates}')

    distances = np.diff(y_coordinates)
    average_distance = np.mean(distances)
    # print(f'Distances between consecutive values: {distances}')
    # print(f'Average distance: {average_distance}')

    half_height = average_distance / 3

    img_array = np.array(Image.open(image_path).convert('L'))
    height, width = img_array.shape

    component_areas = []
    for i, y_center in enumerate(y_coordinates):
        component_area = {
            'x_start': 0,
            'x_end': width,
            'y_start': int(y_center - half_height),
            'y_end': int(y_center + half_height),
        }
        component_areas.append(component_area)
        # print(f'Component {i + 1}: {component_area}')

    # print(f'\nTotal components: {len(component_areas)}')

    return (component_areas, half_height)


def find_suoja_cell_start_and_end(crop_offset, y_pos, original_image_path):
    img = Image.open(original_image_path)

    # Search for "Suoja" in the header area (at the top of the full image)
    header_y_start = 0  # Start from the top of the image
    header_y_end = 200  # First 200 pixels should contain the header
    header_x_start = 0
    header_x_end = img.width

    # Crop just the header area where column names should be
    header_crop = img.crop((header_x_start, header_y_start, header_x_end, header_y_end))

    # Use pytesseract to get detailed word-level data with bounding boxes
    ocr_data = pytesseract.image_to_data(
        header_crop, output_type=pytesseract.Output.DICT
    )

    # Find the word "Suoja" and get its x-coordinates
    suoja_left = None
    suoja_right = None

    for i, word in enumerate(ocr_data['text']):
        if word.lower() == 'suoja':
            # Get the bounding box of this word
            x = ocr_data['left'][i]
            w = ocr_data['width'][i]
            suoja_left = x + header_x_start
            suoja_right = x + w + header_x_start
            print(f"Found 'Suoja' header at x: {suoja_left} to {suoja_right}")
            break

    # If we didn't find "Suoja", try looking for it with some fuzzy matching
    if suoja_left is None:
        for i, word in enumerate(ocr_data['text']):
            if 'suoj' in word.lower() or 'suo' in word.lower():
                x = ocr_data['left'][i]
                w = ocr_data['width'][i]
                suoja_left = x + header_x_start
                suoja_right = x + w + header_x_start
                print(
                    f"Found similar word '{word}' at x: {suoja_left} to {suoja_right}"
                )
                break

    if suoja_left is None:
        print(
            "Warning: Could not find 'Suoja' header, falling back to column detection"
        )
        # Fallback: use the old bar-counting method
        BLACK_THRESHOLD = 100
        start_x = crop_offset[0]
        start_y = crop_offset[1] + y_pos
        img_array = np.array(img.convert('L'))
        row = img_array[start_y, start_x:]
        row_width = img.width - start_x
        is_black = row < BLACK_THRESHOLD

        cursor = 0
        bars_positions = []

        for x in range(row_width):
            if is_black[x] and x - cursor > 10:
                cursor = x
                true_position = x + crop_offset[0]
                bars_positions.append(true_position)

        if len(bars_positions) >= 3:
            suoja_start = bars_positions[1]
            suoja_end = bars_positions[2]
        else:
            suoja_start = 0
            suoja_end = 0
    else:
        # Now find the vertical bars (column separators) closest to these x-coordinates
        BLACK_THRESHOLD = 100
        start_y = crop_offset[1] + y_pos
        img_array = np.array(img.convert('L'))
        row = img_array[start_y, :]
        is_black = row < BLACK_THRESHOLD

        # Find all vertical bars
        cursor = 0
        bars_positions = []
        for x in range(img.width):
            if is_black[x] and x - cursor > 10:
                cursor = x
                bars_positions.append(x)

        # Find the bars that bound the Suoja column
        # The start bar should be just before suoja_left
        # The end bar should be just after suoja_right
        suoja_start = suoja_left
        suoja_end = suoja_right

        for bar_x in bars_positions:
            if bar_x < suoja_left and (
                suoja_start == suoja_left or bar_x > suoja_start
            ):
                suoja_start = bar_x
            if bar_x > suoja_right and (suoja_end == suoja_right or bar_x < suoja_end):
                suoja_end = bar_x
                break

    return tuple((suoja_start, suoja_end))


def save_components_to_folder(
    input_path,
    component_areas,
    original_image_path,
    crop_offset,
    output_folder='components',
):
    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Open the source image
    img = Image.open(input_path)

    cropped_images = []

    # get suoja start and end boundaries
    component_center_y = component_areas[0]['y_end']
    suoja_edges = find_suoja_cell_start_and_end(
        crop_offset, component_center_y, original_image_path
    )

    component_with_suoja: Dict[Image, str] = {}

    # Save each component
    for i, area in enumerate(component_areas, start=1):
        # print(area)
        crop_box = (area['x_start'], area['y_start'], area['x_end'], area['y_end'])

        suoja_area = {
            'x_start': suoja_edges[0],
            'x_end': suoja_edges[1],
            'y_start': area['y_start'] + crop_offset[1] - 25,
            'y_end': area['y_end'] + crop_offset[1],
        }

        suoja_value = ocr_read_area(original_image_path, suoja_area)
        # Normalize suoja value to extract only the part after the slash
        suoja_value = normalize_suoja_value(suoja_value)

        cropped = img.crop(crop_box)
        cropped_images.append(cropped)

        # Save with numbered filename
        output_path = os.path.join(output_folder, f'component_{i:02d}.jpg')
        cropped.save(output_path, 'JPEG', quality=95)

        component_with_suoja[output_path] = suoja_value
        # print(
        #     f'Saved: {output_path} (size: {cropped.size[0]} × {cropped.size[1]} pixels)'
        # )

    # print(f'\nTotal components saved: {len(component_areas)}')
    # print(f'Location: {output_folder}/')

    return tuple((cropped_images, component_with_suoja))


def do_extraction(image_path, out_dir='extracted_cells'):
    area = find_component_area(image_path)
    crop_offset = tuple((area['x_start'] + area['x_end'], area['y_start']))
    output_path = os.path.join(out_dir, 'extracted_components.jpg')
    export_area_to_analyze(image_path, area, output_path)
    lines = find_non_white_at_fraction(output_path)
    component_areas, half_height = extract_components(lines, output_path)
    return save_components_to_folder(
        output_path, component_areas, image_path, crop_offset
    )
