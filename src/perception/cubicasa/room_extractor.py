import cv2
import numpy as np
from shapely.geometry import Polygon

MIN_ROOM_AREA = 500


def extract_room_polygons(class_map, room_class_ids):
    """
    class_map: HxW numpy array
    room_class_ids: list of int (CubiCasa room ids)
    """

    room_polygons = []

    for class_id in room_class_ids:
        mask = (class_map == class_id).astype(np.uint8) * 255

        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        for cnt in contours:
            if len(cnt) < 3:
                continue

            poly = cnt.squeeze()

            shapely_poly = Polygon(poly)

            if shapely_poly.area > MIN_ROOM_AREA:
                room_polygons.append({
                    "class_id": class_id,
                    "polygon": shapely_poly
                })

    return room_polygons
