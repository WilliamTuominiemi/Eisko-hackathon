from PIL import Image
import numpy as np
import cv2
import os
from typing import List, Optional, Union
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


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


def extract_suoja_numbers(
    image_path, debug=False, save_crops=False, output_folder='suoja_extracts'
):
    """Extract Suoja numbers from electrical component table."""
    if save_crops:
        os.makedirs(output_folder, exist_ok=True)

    img = Image.open(image_path)
    img_array = np.array(img.convert('L'))
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

        # Use more generous margins - preprocessing will handle border removal
        crop_box = (
            max(0, suoja_left - 5),  # Include some left margin for border detection
            max(0, y_start - 2),
            min(width, suoja_right + 5),  # Include some right margin
            min(height, y_end + 8),
        )
        cropped = img.crop(crop_box)
        y_center = (y_start + y_end) // 2

        results.append((len(results), y_center, cropped))

        if save_crops:
            cropped.save(
                os.path.join(output_folder, f'suoja_{len(results) - 1}_y{y_center}.png')
            )

    return results


def _preprocess_for_ocr(cropped_img):
    """Preprocess image for better OCR accuracy."""
    # Convert PIL to numpy array
    img_array = np.array(cropped_img.convert('L'))

    # Remove left and right borders more aggressively (table lines)
    # Detect and crop out vertical lines
    h, w = img_array.shape

    # Find leftmost text pixel (skip table border)
    left_margin = 0
    for x in range(w):
        col = img_array[:, x]
        if np.sum(col < 200) > h * 0.3:  # Vertical line
            left_margin = x + 1
        else:
            break

    # Find rightmost content
    right_margin = w
    for x in range(w - 1, -1, -1):
        col = img_array[:, x]
        if np.sum(col < 200) > h * 0.3:  # Vertical line
            right_margin = x
        else:
            break

    # Crop out borders
    if left_margin < right_margin:
        img_array = img_array[:, left_margin:right_margin]

    # Apply binary threshold for cleaner text
    _, img_binary = cv2.threshold(
        img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    # Denoise
    img_denoised = cv2.fastNlMeansDenoising(img_binary, None, 10, 7, 21)

    # Convert back to PIL
    return Image.fromarray(img_denoised)


def _try_ocr(cropped_img, config: Optional[str] = None):
    """Try to extract text from image using OCR."""
    try:
        import pytesseract

        # Preprocess image for better accuracy
        processed_img = _preprocess_for_ocr(cropped_img)

        # Use default config if none provided
        if config is None:
            config = '--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

        # Use more aggressive OCR settings for single-line alphanumeric text
        text = pytesseract.image_to_string(
            processed_img,
            config=config,
        ).strip()

        # Clean up the text
        cleaned = text.replace(' ', '').replace('\n', '').replace('\r', '')

        return cleaned or None
    except Exception:
        return None


def _try_ocr_batch_worker(args):
    """Worker function for parallel OCR processing."""
    idx, y_center, cropped_img = args
    result = _try_ocr(cropped_img)
    return idx, result


def extract_suoja_values_from_image(
    image_path: Union[str, Path],
    use_ocr: bool = True,
    debug: bool = False,
    save_crops: bool = False,
    output_folder: str = 'suoja_extracts',
    parallel: bool = True,
    max_workers: Optional[int] = None,
) -> List[Optional[str]]:
    """
    Extract all Suoja values from a JPG image in order (top to bottom).

    Args:
        image_path: Path to the image file
        use_ocr: Whether to perform OCR (if False, returns list of None)
        debug: Print debug information
        save_crops: Save cropped regions to disk
        output_folder: Folder for saved crops
        parallel: Use parallel OCR processing (faster for many values)
        max_workers: Number of parallel workers (None = auto)

    Returns:
        List of strings (or None if OCR fails for that value)
    """
    regions = extract_suoja_numbers(
        image_path, save_crops=save_crops, output_folder=output_folder
    )

    if not use_ocr:
        return [None] * len(regions)

    # Sequential processing for small number of regions
    if not parallel or len(regions) <= 3:
        values = [_try_ocr(cropped_img) for _, _, cropped_img in regions]
    else:
        # Parallel OCR processing for speed
        if max_workers is None:
            max_workers = min(len(regions), os.cpu_count() or 4)

        # Use ThreadPoolExecutor (pytesseract releases GIL)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(_try_ocr_batch_worker, regions))

        # Sort by original index to maintain order
        results.sort(key=lambda x: x[0])
        values = [result for _, result in results]

    if debug:
        print(f'  Extracted {len(values)} Suoja values: {values}')

    return values


def extract_suoja_values_batch(
    image_paths: List[Union[str, Path]],
    use_ocr: bool = True,
    debug: bool = False,
    save_crops: bool = False,
    output_folder: str = 'suoja_extracts',
    parallel: bool = True,
) -> List[List[Optional[str]]]:
    """
    Extract Suoja values from multiple images in parallel.

    Args:
        image_paths: List of image file paths
        use_ocr: Whether to perform OCR
        debug: Print debug information
        save_crops: Save cropped regions
        output_folder: Folder for saved crops
        parallel: Use parallel processing

    Returns:
        List of lists, each containing Suoja values for one image
    """
    if not parallel or len(image_paths) == 1:
        return [
            extract_suoja_values_from_image(
                img_path, use_ocr, debug, save_crops, output_folder, parallel=False
            )
            for img_path in image_paths
        ]

    # Process multiple images in parallel
    with ThreadPoolExecutor(
        max_workers=min(len(image_paths), os.cpu_count() or 4)
    ) as executor:
        results = list(
            executor.map(
                lambda p: extract_suoja_values_from_image(
                    p, use_ocr, debug, save_crops, output_folder, parallel=True
                ),
                image_paths,
            )
        )

    return results
