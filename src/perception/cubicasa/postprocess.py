# # src/perception/cubicasa/postprocess.py

# import cv2
# import numpy as np
# from shapely.geometry import Polygon
# from shapely.ops import unary_union


# # ---------------------------------------------------------
# # MASK CLEANING
# # ---------------------------------------------------------

# def clean_mask(mask: np.ndarray, min_area: int = 100):
#     """
#     Remove tiny noisy components from segmentation mask.
#     """

#     cleaned = np.zeros_like(mask, dtype=np.uint8)

#     unique_vals = np.unique(mask)

#     for val in unique_vals:
#         if val == 0:
#             continue

#         binary = (mask == val).astype(np.uint8)
#         contours, _ = cv2.findContours(
#             binary,
#             cv2.RETR_EXTERNAL,
#             cv2.CHAIN_APPROX_SIMPLE
#         )

#         for cnt in contours:
#             area = cv2.contourArea(cnt)
#             if area > min_area:
#                 cv2.drawContours(cleaned, [cnt], -1, val, -1)

#     return cleaned


# # ---------------------------------------------------------
# # MASK → POLYGONS
# # ---------------------------------------------------------

# def mask_to_polygons(mask: np.ndarray, simplify_eps: float = 1.5):
#     """
#     Convert segmentation mask into shapely polygons.

#     Returns:
#         list[Polygon]
#     """

#     polygons = []

#     unique_vals = np.unique(mask)

#     for val in unique_vals:
#         if val == 0:
#             continue

#         binary = (mask == val).astype(np.uint8)

#         contours, _ = cv2.findContours(
#             binary,
#             cv2.RETR_EXTERNAL,
#             cv2.CHAIN_APPROX_SIMPLE
#         )

#         for cnt in contours:
#             if len(cnt) < 3:
#                 continue

#             cnt = cnt.squeeze()

#             if cnt.ndim != 2:
#                 continue

#             poly = Polygon(cnt)

#             if not poly.is_valid or poly.area < 200:
#                 continue

#             poly = poly.simplify(simplify_eps)

#             polygons.append(poly)

#     return polygons


# # ---------------------------------------------------------
# # FULL POSTPROCESS PIPELINE
# # ---------------------------------------------------------

# def postprocess_semantic_maps(semantic_maps: dict):
#     """
#     Convert CubiCasa outputs into structured vector geometry.

#     Input:
#         {
#             "rooms": mask,
#             "walls": mask,
#             "doors": mask,
#             "windows": mask
#         }

#     Returns:
#         {
#             "rooms": list[Polygon],
#             "walls": list[Polygon],
#             "doors": list[Polygon],
#             "windows": list[Polygon]
#         }
#     """

#     structured = {}

#     for key, mask in semantic_maps.items():

#         print(f"🔍 Processing {key} mask")

#         cleaned = clean_mask(mask)

#         polygons = mask_to_polygons(cleaned)

#         structured[key] = polygons

#         print(f"   → {len(polygons)} polygons extracted")

#     return structured
from .mask_utils import extract_all_masks
from .vectorize import mask_to_polygons
from .room_extractor import extract_room_polygons
from src.geometry.wall_cleaner import clean_wall_polygons
from .building_structure import BuildingStructure, Room


ROOM_CLASS_IDS = list(range(21, 44))  # adjust if needed


def build_structure(class_map):

    masks = extract_all_masks(class_map)

    # Walls
    wall_polys_raw = mask_to_polygons(masks["walls"])
    wall_polys_clean = clean_wall_polygons(wall_polys_raw)

    # Rooms
    room_polys_raw = extract_room_polygons(class_map, ROOM_CLASS_IDS)
    rooms = [
        Room(r["class_id"], r["polygon"])
        for r in room_polys_raw
    ]

    return BuildingStructure(
        walls=wall_polys_clean,
        rooms=rooms,
        doors=[],
        windows=[]
    )
