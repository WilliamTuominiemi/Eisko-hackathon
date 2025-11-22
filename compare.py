import numpy as np
from PIL import Image


def compare_images(path_image1: str, path_image2: str) -> bool:
    img1 = Image.open(path_image1)
    img2 = Image.open(path_image2)

    if img1.size != img2.size:
        return True

    arr1 = np.array(img1)
    arr2 = np.array(img2)

    if arr1.shape != arr2.shape:
        return True

    return not np.array_equal(arr1, arr2)
