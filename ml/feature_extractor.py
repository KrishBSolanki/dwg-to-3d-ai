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
    Extract rich wall features for ML material prediction.
    This version adds architectural intelligence while remaining
    backward-compatible with the existing model.
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

    wall_thickness = min(width, height)
    wall_length = max(width, height)

    # Avoid divide-by-zero
    aspect_ratio = wall_length / max(0.01, wall_thickness)

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
    # NORMALIZED VALUES
    # -------------------------
    norm_length = min(wall_length / 10.0, 1.0)
    norm_height = min(wall_height / 5.0, 1.0)
    norm_thickness = min(wall_thickness / 1.0, 1.0)

    # -------------------------
    # ROOM CONTEXT (SAFE)
    # -------------------------
    has_bathroom = int("bathroom" in adjacent_room_types)
    has_kitchen = int("kitchen" in adjacent_room_types)
    has_living = int("living_room" in adjacent_room_types)
    has_bedroom = int("bedroom" in adjacent_room_types)

    # -------------------------
    # FEATURE DICT
    # -------------------------
    features = {
        # Geometry
        "wall_thickness": wall_thickness,
        "wall_length": wall_length,
        "wall_height": wall_height,
        "area": area,
        "aspect_ratio": aspect_ratio,

        # Normalized (model-friendly)
        "norm_length": norm_length,
        "norm_height": norm_height,
        "norm_thickness": norm_thickness,

        # Orientation
        "orientation_flag": orientation_flag,

        # Semantics
        "is_exterior": int(is_exterior),
        "adj_bathroom": has_bathroom,
        "adj_kitchen": has_kitchen,
        "adj_living": has_living,
        "adj_bedroom": has_bedroom,

        # Layer (keep string for encoder)
        "layer": layer.lower()
    }

    # -------------------------
    # DEBUG LOG (OPTIONAL)
    # -------------------------
    print(
        f"🧠 Wall features | len={wall_length:.2f}m | "
        f"thk={wall_thickness:.2f}m | "
        f"h={wall_height:.2f}m | "
        f"{orientation} | "
        f"{'exterior' if is_exterior else 'interior'}"
    )

    return features
