from PIL import Image
import pytesseract

def ocr_read_area(file_path, area, debug=False, debug_output='debug_crop.png'):
    """
    Reads text from a specific area of an image using OCR.
    
    Args:
        file_path (str): Path to the image file
        area (dict): Dictionary with keys 'x_start', 'x_end', 'y_start', 'y_end'
                    defining the rectangular area to OCR
        debug (bool): If True, saves the cropped area as an image file
        debug_output (str): Path where the debug image will be saved
    
    Returns:
        str: The text extracted from the specified area
    
    Example:
        area = {'x_start': 2658, 'x_end': 2870, 'y_start': 509, 'y_end': 620}
        text = ocr_read_area('image.png', area, debug=True)
        print(text)
    """
    try:
        # Open the image
        img = Image.open(file_path)
        
        # Extract the coordinates
        x_start = area['x_start']
        x_end = area['x_end']
        y_start = area['y_start']
        y_end = area['y_end']
        
        # Crop the image to the specified area
        # PIL uses (left, top, right, bottom) format
        cropped_img = img.crop((x_start, y_start, x_end, y_end))
        
        # Save debug image if requested
        if debug:
            cropped_img.save(debug_output)
            print(f"Debug: Cropped area saved to '{debug_output}'")
        
        # Perform OCR on the cropped area
        text = pytesseract.image_to_string(cropped_img)
        
        # Return the text, stripped of leading/trailing whitespace
        return text.strip()
    
    except FileNotFoundError:
        return f"Error: File '{file_path}' not found"
    except KeyError as e:
        return f"Error: Missing required key in area dictionary: {e}"
    except Exception as e:
        return f"Error: {str(e)}"


# Example usage
if __name__ == "__main__":
    # Define the area to read
    suoja_area = {
        'x_start': 2658,
        'x_end': 2870,
        'y_start': 509,
        'y_end': 620
    }
    
    # Read text from the specified area
    file_path = 'your_image.png'
    result = ocr_read_area(file_path, suoja_area, debug=True, debug_output='cropped_area.png')
    
    print("OCR Result:")
    print(result)