"""
Count the occurrences of each Suoja type from extracted images.
"""

from PIL import Image
import os
from collections import Counter

def read_suoja_from_image(image_path, use_ocr=True):
    """
    Read text from a Suoja image.
    
    Args:
        image_path: Path to the image
        use_ocr: If True, try to use pytesseract
    
    Returns:
        Text string or None
    """
    if not use_ocr:
        return None
    
    try:
        import pytesseract
        
        img = Image.open(image_path)
        
        # Preprocess: Convert to grayscale and increase contrast
        img = img.convert('L')
        
        # Use tesseract with configuration for short text
        text = pytesseract.image_to_string(
            img,
            config='--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        ).strip()
        
        # Clean up the text
        text = text.replace(' ', '').replace('\n', '').replace('\r', '')
        
        if text:
            return text
        
        return None
        
    except Exception as e:
        print(f"Error reading {image_path}: {e}")
        return None


def count_suoja_types(folder_path="suoja_extracts", use_ocr=True):
    """
    Count occurrences of each Suoja type.
    
    Args:
        folder_path: Path to folder containing extracted images
        use_ocr: If True, try to use OCR
    
    Returns:
        Dictionary of {suoja_type: count}
    """
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist")
        return {}
    
    # Get all PNG files in the folder
    image_files = sorted([f for f in os.listdir(folder_path) if f.endswith('.png')])
    
    if not image_files:
        print(f"No PNG images found in '{folder_path}'")
        return {}
    
    print(f"Found {len(image_files)} images in '{folder_path}/'")
    print("=" * 60)
    
    suoja_values = []
    
    for img_file in image_files:
        img_path = os.path.join(folder_path, img_file)
        
        # Try OCR
        text = read_suoja_from_image(img_path, use_ocr=use_ocr)
        
        if text:
            print(f"{img_file}: {text}")
            suoja_values.append(text)
        else:
            print(f"{img_file}: [Could not read - manual review needed]")
    
    print("=" * 60)
    
    # Count occurrences
    if suoja_values:
        counter = Counter(suoja_values)
        return dict(counter)
    
    return {}


def main():
    folder_path = "suoja_extracts"
    
    print("Reading Suoja values from extracted images...")
    print()
    
    # Try to check if tesseract is available
    ocr_available = False
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        ocr_available = True
    except Exception:
        pass
    
    if not ocr_available:
        print("⚠️  WARNING: Tesseract OCR not available")
        print("Install it with: brew install tesseract")
        print("Then install Python package: uv pip install pytesseract")
        print()
        print("Reading images manually...")
        print()
    
    # Count Suoja types
    counts = count_suoja_types(folder_path, use_ocr=ocr_available)
    
    if counts:
        print("\n📊 SUOJA TYPE COUNTS:")
        print("=" * 60)
        
        total = sum(counts.values())
        
        for suoja_type, count in sorted(counts.items()):
            percentage = (count / total) * 100
            print(f"  {suoja_type}: {count} ({percentage:.1f}%)")
        
        print("-" * 60)
        print(f"  Total: {total} Suoja values")
    else:
        print("\n❌ Could not extract any Suoja values")
        print("Please install tesseract or review images manually")


if __name__ == "__main__":
    main()

