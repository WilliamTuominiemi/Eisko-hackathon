from PIL import Image
import numpy as np
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
        print('Warning: Could not find right boundary of component area')
        return None

    x_start = bar_x + 30
    x_end = next_bar_x - 30

    # Validate that x_end is actually greater than x_start
    if x_end <= x_start:
        print(f'Warning: Invalid x coordinates (x_start={x_start}, x_end={x_end})')
        return None

    return {
        'x_start': x_start,
        'x_end': x_end,
        'y_start': bar_top,
        'y_end': bar_bottom,
    }


def export_area_to_analyze(filepath, area, output_path):
    img = Image.open(filepath)

    # Validate coordinates
    if area['x_end'] is None or area['x_end'] <= area['x_start']:
        raise ValueError(
            f'Invalid crop coordinates: x_start={area["x_start"]}, x_end={area["x_end"]}'
        )

    if area['y_end'] <= area['y_start']:
        raise ValueError(
            f'Invalid crop coordinates: y_start={area["y_start"]}, y_end={area["y_end"]}'
        )

    crop_box = (area['x_start'], area['y_start'], area['x_end'], area['y_end'])

    cropped = img.crop(crop_box)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cropped.save(output_path, 'JPEG', quality=95)

    print(f'Saved cropped component → {output_path}')
    print(f'Size: {cropped.width} × {cropped.height} pixels')


def find_non_white_at_fraction(
    image_path, x_fraction=1 / 10, intensity_threshold=250, merge_threshold=5
):
    """Find y coordinates with non-white content at a fractional x position."""
    img_array = np.array(Image.open(image_path).convert('L'))

    x = 5
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


def extract_components(lines, image_path):
    # Extract just the y-coordinates array from the tuple
    y_coordinates = lines[1]  # lines[1] contains the array of y-coordinates

    print(f'Detected lines at y-coordinates: {y_coordinates}')

    distances = np.diff(y_coordinates)
    average_distance = np.mean(distances)
    print(f'Distances between consecutive values: {distances}')
    print(f'Average distance: {average_distance}')

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
        print(f'Component {i + 1}: {component_area}')

    print(f'\nTotal components: {len(component_areas)}')

    return (component_areas, half_height)


def save_components_to_folder(input_path, component_areas, output_folder='components'):
    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Open the source image
    img = Image.open(input_path)

    cropped_images = []
    # Save each component
    for i, area in enumerate(component_areas, start=1):
        print(area)
        crop_box = (area['x_start'], area['y_start'], area['x_end'], area['y_end'])
        cropped = img.crop(crop_box)
        cropped_images.append(cropped)

        # Save with numbered filename
        output_path = os.path.join(output_folder, f'component_{i:02d}.jpg')
        cropped.save(output_path, 'JPEG', quality=95)
        print(
            f'Saved: {output_path} (size: {cropped.size[0]} × {cropped.size[1]} pixels)'
        )

    print(f'\nTotal components saved: {len(component_areas)}')
    print(f'Location: {output_folder}/')
    return cropped_images


def do_extraction(image_path, out_dir='extracted_cells'):
    try:
        area = find_component_area(image_path)

        if area is None:
            print(f'Warning: Could not find component area in {image_path}')
            return []

        output_path = os.path.join(out_dir, 'extracted_components.jpg')
        export_area_to_analyze(image_path, area, output_path)
        lines = find_non_white_at_fraction(output_path)
        component_areas, half_height = extract_components(lines, output_path)
        cropped_images = save_components_to_folder(output_path, component_areas)
        return cropped_images
    except (ValueError, Exception) as e:
        print(f'Warning: Failed to extract components from {image_path}: {str(e)}')
        return []
