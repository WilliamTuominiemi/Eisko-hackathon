import cv2

def are_images_different(
    path_image1: str,
    path_image2: str,
    threshold: float = 0.5
) -> bool:
    img1 = cv2.imread(path_image1, 0)
    img2 = cv2.imread(path_image2, 0)
    
    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)
    
    if des1 is None or des2 is None:
        return True  # If no features detected, consider different
    
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    
    # Calculate match ratio relative to the smaller set of keypoints
    match_ratio = len(matches) / min(len(kp1), len(kp2))
    
    print(f'Matches: {len(matches)}, Keypoints: {len(kp1)}/{len(kp2)}, Ratio: {match_ratio:.2f}')
    
    return match_ratio < threshold  # Different if ratio is below threshold