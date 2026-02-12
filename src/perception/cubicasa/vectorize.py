import cv2
import numpy as np


def mask_to_polygons(mask, min_area=200):
    """
    Convert binary mask to list of polygon contours.
    Returns list of Nx2 numpy arrays.
    """

    if mask.dtype != np.uint8:
        mask = mask.astype(np.uint8)

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    polygons = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue

        epsilon = 0.01 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)

        poly = approx.reshape(-1, 2)
        polygons.append(poly)

    return polygons
