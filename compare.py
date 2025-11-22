import numpy as np
from PIL import Image

def are_images_different(path_image1: str, path_image2: str, 
                         pixel_threshold: int = 5, 
                         diff_ratio_threshold: float = 0.01,
                         allow_size_diff: bool = True,
                         max_size_diff: int = 5) -> bool:
    
    img1 = Image.open(path_image1)
    img2 = Image.open(path_image2)
    
    # Check size difference
    if img1.size != img2.size:
        if not allow_size_diff:
            return True
        
        width_diff = abs(img1.size[0] - img2.size[0])
        height_diff = abs(img1.size[1] - img2.size[1])
        
        if width_diff > max_size_diff or height_diff > max_size_diff:
            return True
        
        # Crop to smaller size for comparison
        min_width = min(img1.size[0], img2.size[0])
        min_height = min(img1.size[1], img2.size[1])
        
        img1 = img1.crop((0, 0, min_width, min_height))
        img2 = img2.crop((0, 0, min_width, min_height))
    
    arr1 = np.array(img1)
    arr2 = np.array(img2)
    
    # Calculate absolute difference per pixel
    abs_diff = np.abs(arr1.astype(np.int32) - arr2.astype(np.int32))
    
    # Count pixels that differ by more than threshold
    significant_diff = abs_diff > pixel_threshold
    num_diff_pixels = np.sum(np.any(significant_diff, axis=2))  # Any channel differs
    total_pixels = arr1.shape[0] * arr1.shape[1]
    
    diff_ratio = num_diff_pixels / total_pixels
    
    print(f"Size diff: {abs(img1.size[0]-img2.size[0])}x{abs(img1.size[1]-img2.size[1])}")
    print(f"Pixels with diff > {pixel_threshold}: {num_diff_pixels}/{total_pixels} ({100*diff_ratio:.2f}%)")
    
    return diff_ratio > diff_ratio_threshold

img1 = "extracted_cells/page_2_cell_0_y390_l206_t308_r1027_b472.png"
img2 = "extracted_cells/page_2_cell_2_y720_l206_t637_r1027_b803.png"

print("Different images:", are_images_different(img1, img2))