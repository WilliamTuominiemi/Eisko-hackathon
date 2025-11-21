from PIL import Image
import numpy as np
import os


def find_vertical_lines(image_path, intensity_threshold=200, min_height_fraction=0.3):
    """
    Find x-coordinates of vertical black lines in the image.

    Args:
        image_path: Path to the image
        intensity_threshold: Pixel values below this are considered black lines
        min_height_fraction: Minimum fraction of height that must be dark

    Returns:
        List of x-coordinates where vertical lines are found
    """
    img = Image.open(image_path).convert("L")
    img_array = np.array(img)

    height, width = img_array.shape

    # For each column, check if it's mostly dark (vertical line)
    vertical_lines = []
    for x in range(width):
        column = img_array[:, x]
        # If more than min_height_fraction of pixels are dark, consider it a vertical line
        dark_pixels = np.sum(column < intensity_threshold)
        if dark_pixels > height * min_height_fraction:
            vertical_lines.append(x)

    # Merge consecutive x values (a thick line might span multiple pixels)
    if not vertical_lines:
        return []

    merged_lines = []
    group_start = vertical_lines[0]
    last_x = vertical_lines[0]

    for x in vertical_lines[1:]:
        if x - last_x > 2:  # Gap detected, finalize previous line
            merged_lines.append((group_start + last_x) // 2)
            group_start = x
        last_x = x

    # Add final line
    merged_lines.append((group_start + last_x) // 2)

    return merged_lines


def find_horizontal_lines(image_path, intensity_threshold=200, min_width_fraction=0.3):
    """
    Find y-coordinates of horizontal black lines in the image.

    Args:
        image_path: Path to the image
        intensity_threshold: Pixel values below this are considered black lines
        min_width_fraction: Minimum fraction of width that must be dark

    Returns:
        List of y-coordinates where horizontal lines are found
    """
    img = Image.open(image_path).convert("L")
    img_array = np.array(img)

    height, width = img_array.shape

    # For each row, check if it's mostly dark (horizontal line)
    horizontal_lines = []
    for y in range(height):
        row = img_array[y, :]
        # If more than min_width_fraction of pixels are dark, consider it a horizontal line
        dark_pixels = np.sum(row < intensity_threshold)
        if dark_pixels > width * min_width_fraction:
            horizontal_lines.append(y)

    # Merge consecutive y values
    if not horizontal_lines:
        return []

    merged_lines = []
    group_start = horizontal_lines[0]
    last_y = horizontal_lines[0]

    for y in horizontal_lines[1:]:
        if y - last_y > 2:  # Gap detected
            merged_lines.append((group_start + last_y) // 2)
            group_start = y
        last_y = y

    # Add final line
    merged_lines.append((group_start + last_y) // 2)

    return merged_lines


def extract_suoja_numbers(
    image_path, debug=False, save_crops=False, output_folder="suoja_extracts"
):
    """
    Extract Suoja numbers from the electrical component table.

    Args:
        image_path: Path to the image
        debug: If True, print debug information
        save_crops: If True, save cropped regions to files
        output_folder: Folder to save cropped images

    Returns:
        List of tuples (row_index, y_position, cropped_image)
    """
    # Create output folder if saving crops
    if save_crops and not os.path.exists(output_folder):
        os.makedirs(output_folder)
    # Find vertical and horizontal lines
    vertical_lines = find_vertical_lines(image_path)
    horizontal_lines = find_horizontal_lines(image_path)

    if debug:
        print(f"Found {len(vertical_lines)} vertical lines")
        print(f"Found {len(horizontal_lines)} horizontal lines")
        print(f"\nVertical lines at x: {vertical_lines}")
        print(f"\nHorizontal lines at y: {horizontal_lines}")

    img = Image.open(image_path)
    img_gray = img.convert("L")
    img_array = np.array(img_gray)
    height, width = img_array.shape

    # The Suoja column is between specific vertical lines
    # Looking at the image structure, it's roughly at 69-73% of the width
    # Let's find the column boundaries more precisely

    # Find vertical lines that bound the Suoja column
    suoja_left = None
    suoja_right = None

    for i in range(len(vertical_lines) - 1):
        x = vertical_lines[i]
        # Suoja column left boundary is around 69-73% of width
        if width * 0.69 < x < width * 0.73:
            suoja_left = x
        # Suoja column right boundary is around 75-82% of width
        if width * 0.75 < x < width * 0.82 and suoja_left:
            suoja_right = x
            break

    if not suoja_left or not suoja_right:
        if debug:
            print("Could not find Suoja column boundaries precisely, using estimates")
        suoja_left = int(width * 0.695)
        suoja_right = int(width * 0.76)

    if debug:
        print(f"\nSuoja column boundaries: x={suoja_left} to x={suoja_right}")

    # Instead of relying on horizontal lines, scan for rows with content
    # in the Suoja column within the main table area (skip header and footer)

    # Main table typically starts after first ~10% and ends before last ~20% of height
    table_start_y = int(height * 0.05)
    table_end_y = int(height * 0.80)

    if debug:
        print(f"Scanning table area from y={table_start_y} to y={table_end_y}")

    # Get the Suoja column region
    suoja_column = img_array[table_start_y:table_end_y, suoja_left:suoja_right]

    # Find rows with content
    row_has_content = []
    for y in range(len(suoja_column)):
        row = suoja_column[y, :]
        non_white_count = np.sum(row < 250)
        if non_white_count > 5:  # Has some text
            row_has_content.append(table_start_y + y)

    if debug:
        print(f"\nFound {len(row_has_content)} rows with content in raw scan")

    # Group consecutive rows into text blocks
    if not row_has_content:
        return []

    text_blocks = []
    block_start = row_has_content[0]
    last_y = row_has_content[0]

    for y in row_has_content[1:]:
        if y - last_y > 20:  # Gap between rows
            text_blocks.append((block_start, last_y))
            block_start = y
        last_y = y

    # Add final block
    text_blocks.append((block_start, last_y))

    if debug:
        print(f"Grouped into {len(text_blocks)} text blocks")

    # Extract each text block
    results = []
    value_count = 0

    for idx, (y_start, y_end) in enumerate(text_blocks):
        y_center = (y_start + y_end) // 2

        # Add padding to capture full text, but skip the top border line
        padding_bottom = 5
        padding_top_skip = 3  # Skip the black line at top
        crop_box = (
            max(0, suoja_left + 2),
            max(0, y_start + padding_top_skip),  # Start below the border line
            min(width, suoja_right - 2),
            min(height, y_end + padding_bottom),
        )

        cropped = img.crop(crop_box)

        # Skip the first block (header) and validate the block has reasonable height
        block_height = y_end - y_start
        is_header = idx == 0
        is_too_small = block_height < 15  # Skip very small blocks (likely noise)

        if is_header:
            if debug:
                print(f"Skipping block {idx} (header): y={y_start}-{y_end}")
            continue

        if is_too_small:
            if debug:
                print(
                    f"Skipping block {idx} (too small): y={y_start}-{y_end}, height={block_height}"
                )
            continue

        # This is a valid Suoja value
        results.append((value_count, y_center, cropped))

        if save_crops:
            output_path = os.path.join(
                output_folder, f"suoja_{value_count}_y{y_center}.png"
            )
            cropped.save(output_path)
            if debug:
                print(
                    f"Saved: {output_path} ({y_start}-{y_end}, height={block_height}px)"
                )

        value_count += 1

    return results


def read_text_from_crops(regions, use_ocr=True):
    """
    Try to read text from cropped images.

    Args:
        regions: List of (index, y_position, cropped_image) tuples
        use_ocr: If True, try to use pytesseract (if available)

    Returns:
        List of (index, y_position, text) tuples
    """
    results = []

    # Check if pytesseract is available
    ocr_available = False
    if use_ocr:
        try:
            import pytesseract

            # Test if tesseract binary is available
            pytesseract.get_tesseract_version()
            ocr_available = True
        except Exception:
            pass

    for idx, y_pos, cropped_img in regions:
        text = None

        if ocr_available:
            try:
                # Use pytesseract to extract text
                text = pytesseract.image_to_string(
                    cropped_img,
                    config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
                ).strip()
                text = text.replace(" ", "").replace("\n", "")
            except Exception:
                pass

        results.append(
            (idx, y_pos, text if text else "[Image saved - manual review needed]")
        )

    return results


# Main execution
if __name__ == "__main__":
    image_path = "output_page.jpg"
    output_folder = "suoja_extracts"

    print("Extracting Suoja numbers from electrical component table...")
    print("=" * 60)

    # Extract Suoja cell regions and save them as images
    suoja_regions = extract_suoja_numbers(
        image_path, debug=True, save_crops=True, output_folder=output_folder
    )

    print("\n" + "=" * 60)
    print("READING TEXT FROM EXTRACTED REGIONS:")
    print("=" * 60)

    # Try to read text from the cropped regions
    text_results = read_text_from_crops(suoja_regions, use_ocr=True)

    print("\nExtracted Suoja Values:")
    print("-" * 40)
    for idx, y_pos, text in text_results:
        print(f"Suoja {idx + 1}: {text}")

    print("\n" + "=" * 60)
    print(f"Total: {len(text_results)} Suoja values extracted")
    print(f"Images saved in folder: {output_folder}/")
