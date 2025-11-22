from PIL import Image
import numpy as np
import os


def _merge_consecutive_positions(positions, gap_threshold=2):
    """Merge consecutive positions into single representative positions."""
    if not positions:
        return []
    
    merged = []
    group_start = positions[0]
    last_pos = positions[0]
    
    for pos in positions[1:]:
        if pos - last_pos > gap_threshold:
            merged.append((group_start + last_pos) // 2)
            group_start = pos
        last_pos = pos
    
    merged.append((group_start + last_pos) // 2)
    return merged


def _find_suoja_column_bounds(width):
    """Find the Suoja column boundaries based on image width."""
    return int(width * 0.695), int(width * 0.76)


def _group_rows_into_blocks(row_ys, gap_threshold=20):
    """Group consecutive row positions into text blocks."""
    if not row_ys:
        return []
    
    blocks = []
    block_start = row_ys[0]
    last_y = row_ys[0]
    
    for y in row_ys[1:]:
        if y - last_y > gap_threshold:
            blocks.append((block_start, last_y))
            block_start = y
        last_y = y
    
    blocks.append((block_start, last_y))
    return blocks


def extract_suoja_numbers(image_path, debug=False, save_crops=False, output_folder="suoja_extracts"):
    """Extract Suoja numbers from electrical component table."""
    if save_crops:
        os.makedirs(output_folder, exist_ok=True)
    
    img = Image.open(image_path)
    img_array = np.array(img.convert("L"))
    height, width = img_array.shape
    
    # Find Suoja column boundaries
    suoja_left, suoja_right = _find_suoja_column_bounds(width)
    
    # Scan table area (skip header/footer)
    table_start_y = int(height * 0.05)
    table_end_y = int(height * 0.80)
    suoja_column = img_array[table_start_y:table_end_y, suoja_left:suoja_right]
    
    # Find rows with content
    row_has_content = [
        table_start_y + y 
        for y in range(len(suoja_column))
        if np.sum(suoja_column[y, :] < 250) > 5
    ]
    
    # Group into text blocks
    text_blocks = _group_rows_into_blocks(row_has_content)
    
    # Extract each text block (skip first which is header)
    results = []
    for idx, (y_start, y_end) in enumerate(text_blocks[1:]):
        if y_end - y_start < 15:  # Skip tiny blocks
            continue
        
        crop_box = (
            suoja_left + 2,
            y_start + 3,  # Skip top border
            suoja_right - 2,
            y_end + 5
        )
        cropped = img.crop(crop_box)
        y_center = (y_start + y_end) // 2
        
        results.append((len(results), y_center, cropped))
        
        if save_crops:
            cropped.save(os.path.join(output_folder, f"suoja_{len(results)-1}_y{y_center}.png"))
    
    return results


def _try_ocr(cropped_img):
    """Try to extract text from image using OCR."""
    try:
        import pytesseract
        text = pytesseract.image_to_string(
            cropped_img,
            config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        ).strip()
        return text.replace(" ", "").replace("\n", "").replace("\r", "") or None
    except Exception:
        return None


def extract_suoja_values_from_image(image_path, use_ocr=True, debug=False, save_crops=False, output_folder="suoja_extracts"):
    """
    Extract all Suoja values from a JPG image in order (top to bottom).
    
    Returns:
        List of strings (or None if OCR fails for that value)
    """
    regions = extract_suoja_numbers(image_path, save_crops=save_crops, output_folder=output_folder)
    
    if not use_ocr:
        return [None] * len(regions)
    
    values = [_try_ocr(cropped_img) for _, _, cropped_img in regions]
    
    if debug:
        print(f"  Extracted {len(values)} Suoja values: {values}")
    
    return values
