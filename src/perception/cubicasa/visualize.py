import cv2
import numpy as np


def overlay_mask(image_path, mask, color=(0, 255, 0), alpha=0.4):
    image = cv2.imread(image_path)
    overlay = image.copy()

    colored_mask = np.zeros_like(image)
    colored_mask[mask == 1] = color

    cv2.addWeighted(colored_mask, alpha, overlay, 1 - alpha, 0, overlay)

    return overlay


def save_overlay(output_path, image):
    cv2.imwrite(output_path, image)
