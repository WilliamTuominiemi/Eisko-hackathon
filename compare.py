import cv2

def are_images_different(
    path_image1: str,
    path_image2: str,
) -> bool:
    img1 = cv2.imread(path_image1, 0)
    img2 = cv2.imread(path_image2, 0)

    orb = cv2.ORB_create()

    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    similarity = len(matches)


    return similarity < 100
