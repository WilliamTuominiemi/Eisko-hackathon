import numpy as np
from PIL import Image


def is_diff(path_image1: str, path_image2: str) -> bool:
    img1 = Image.open(path_image1)
    img2 = Image.open(path_image2)

    if img1.size != img2.size:
        return True

    arr1 = np.array(img1)
    arr2 = np.array(img2)

    if arr1.shape != arr2.shape:
        return True

    # Perform pixel-by-pixel comparison
    # If any pixel is different, the images are different
    is_different = not np.array_equal(arr1, arr2)

    return is_different


if __name__ == "__main__":
    comparisons = [
        ("screenshots/a.png", "screenshots/b.png"),
        ("screenshots/b.png", "screenshots/c.png"),
        ("screenshots/a.png", "screenshots/c.png"),
    ]

    for img1, img2 in comparisons:
        result = is_diff(img1, img2)
        status = "DIFFERENT" if result else "IDENTICAL"
        print(f"Comparing {img1} vs {img2}: {status}")
