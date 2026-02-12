import numpy as np


# Example class mapping (adjust to your CubiCasa label config)
WALL_CLASSES = [1]
ROOM_CLASSES = list(range(2, 12))
DOOR_CLASSES = [12]
WINDOW_CLASSES = [13]


def extract_mask(class_map, target_classes):
    mask = np.isin(class_map, target_classes)
    return mask.astype(np.uint8)


def extract_all_masks(class_map):
    return {
        "walls": extract_mask(class_map, WALL_CLASSES),
        "rooms": extract_mask(class_map, ROOM_CLASSES),
        "doors": extract_mask(class_map, DOOR_CLASSES),
        "windows": extract_mask(class_map, WINDOW_CLASSES),
    }
