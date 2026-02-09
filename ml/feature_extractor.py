# import numpy as np


# def extract_wall_features(poly, wall_height, layer):
#     minx, miny, maxx, maxy = poly.bounds
#     width = maxx - minx
#     height = maxy - miny

#     return {
#         "area": poly.area,
#         "perimeter": poly.length,
#         "wall_height": wall_height,
#         "aspect_ratio": max(width, height) / max(0.01, min(width, height)),
#         "layer": layer
#     }


# def extract_window_features(poly, window_height):
#     return {
#         "area": poly.area,
#         "perimeter": poly.length,
#         "window_height": window_height,
#         "layer": "window"
#     }


# def extract_floor_features(poly):
#     return {
#         "area": poly.area,
#         "perimeter": poly.length,
#         "layer": "floor"
#     }
from shapely.geometry import Polygon
import math


def extract_wall_features(
    polygon: Polygon,
    wall_height: float,
    layer: str,
    is_exterior: bool = False,
    adjacent_room_types=None
):
    """
    Production-grade wall feature extraction.
    Backward compatible with existing ML model,
    but enriched for smarter material decisions.
    """

    if adjacent_room_types is None:
        adjacent_room_types = []

    # -------------------------
    # BASIC GEOMETRY
    # -------------------------
    area = polygon.area

    minx, miny, maxx, maxy = polygon.bounds
    width = maxx - minx
    height = maxy - miny

    thickness = max(0.01, min(width, height))
    length = max(width, height)

    aspect_ratio = length / thickness

    # -------------------------
    # ORIENTATION
    # -------------------------
    if width >= height:
        orientation = "horizontal"
        orientation_flag = 0
    else:
        orientation = "vertical"
        orientation_flag = 1

    # -------------------------
    # NORMALIZED (ML SAFE)
    # -------------------------
    norm_length = min(length / 8.0, 1.0)
    norm_height = min(wall_height / 4.0, 1.0)
    norm_thickness = min(thickness / 0.5, 1.0)

    # -------------------------
    # ROOM CONTEXT
    # -------------------------
    adj = set(adjacent_room_types)

    has_bathroom = int("bathroom" in adj)
    has_kitchen = int("kitchen" in adj)
    has_living = int("living_room" in adj)
    has_bedroom = int("bedroom" in adj)

    # -------------------------
    # FEATURE DICT
    # -------------------------
    features = {
        # Raw geometry (used by rules + ML)
        "length": length,
        "thickness": thickness,
        "height": wall_height,
        "area": area,
        "aspect_ratio": aspect_ratio,

        # Normalized
        "norm_length": norm_length,
        "norm_height": norm_height,
        "norm_thickness": norm_thickness,

        # Orientation
        "orientation": orientation,
        "orientation_flag": orientation_flag,

        # Semantics
        "is_exterior": int(is_exterior),
        "adj_bathroom": has_bathroom,
        "adj_kitchen": has_kitchen,
        "adj_living": has_living,
        "adj_bedroom": has_bedroom,

        # Metadata
        "layer": layer.lower()
    }

    # -------------------------
    # DEBUG LOG
    # -------------------------
    print(
        f"🧠 Wall features | "
        f"len={length:.2f}m | "
        f"thk={thickness:.2f}m | "
        f"h={wall_height:.2f}m | "
        f"{orientation} | "
        f"{'exterior' if is_exterior else 'interior'}"
    )

    return features
