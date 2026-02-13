# from typing import List
# from shapely.geometry import LineString
# from .parse_dwg import parse_dwg
# from pathlib import Path

# from dataclasses import dataclass
# from typing import Tuple
# import math

# Point = Tuple[float, float]


# @dataclass
# class Wall:
#     id: int
#     start: Point
#     end: Point
#     thickness: float = 0.2
#     height: float = 3.0


# @dataclass
# class BuildingStructure:
#     walls: List[Wall]


# def build_structure_from_dxf(file_path: Path) -> BuildingStructure:
#     entities = parse_dwg(file_path)

#     walls = []
#     wall_id = 0

#     for ent in entities:
#         if ent["semantic"] != "wall":
#             continue

#         geom = ent["geometry"]

#         if geom["type"] == "line":
#             p1, p2 = geom["points"]
            

#             length = math.dist(p1, p2)

#             # Ignore tiny drafting fragments
#             if length < 50:  # adjust depending on DXF units
#                 continue

#             walls.append(
#                 Wall(
#                     id=wall_id,
#                     start=p1,
#                     end=p2,
#                     thickness=0.2,
#                     height=3.0
#                 )
#             )
#             wall_id += 1

#         elif geom["type"] == "polyline":
#             pts = geom["points"]

#             for i in range(len(pts) - 1):
#                 walls.append(
#                     Wall(
#                         id=wall_id,
#                         start=pts[i],
#                         end=pts[i + 1],
#                         thickness=0.2,
#                         height=3.0
#                     )
#                 )
#                 wall_id += 1

#     print(f"🔹 Walls before merge: {len(walls)}")

#     walls = merge_walls(walls)

#     print(f"🔹 Walls after merge: {len(walls)}")

#     return BuildingStructure(walls=walls)

# TOLERANCE = 1e-2


# def points_close(p1, p2, tol=TOLERANCE):
#     return math.dist(p1, p2) < tol


# def direction(wall):
#     dx = wall.end[0] - wall.start[0]
#     dy = wall.end[1] - wall.start[1]
#     length = math.hypot(dx, dy)
#     if length == 0:
#         return (0, 0)
#     return (dx / length, dy / length)


# def are_collinear(w1, w2, angle_tol=1e-2):
#     d1 = direction(w1)
#     d2 = direction(w2)
#     dot = d1[0]*d2[0] + d1[1]*d2[1]
#     return abs(abs(dot) - 1.0) < angle_tol


# def merge_walls(walls, tol=1e-1):
#     horizontal = []
#     vertical = []

#     for w in walls:
#         dx = w.end[0] - w.start[0]
#         dy = w.end[1] - w.start[1]

#         if abs(dy) < abs(dx):  # horizontal
#             horizontal.append(w)
#         else:
#             vertical.append(w)

#     merged = []

#     # ---- Merge horizontal ----
#     horizontal.sort(key=lambda w: (round(w.start[1], 1), w.start[0]))

#     i = 0
#     while i < len(horizontal):
#         base = horizontal[i]
#         y = base.start[1]

#         x_min = min(base.start[0], base.end[0])
#         x_max = max(base.start[0], base.end[0])

#         j = i + 1
#         while j < len(horizontal):
#             w2 = horizontal[j]

#             if abs(w2.start[1] - y) > tol:
#                 break

#             w2_min = min(w2.start[0], w2.end[0])
#             w2_max = max(w2.start[0], w2.end[0])

#             if w2_min <= x_max + tol:
#                 x_max = max(x_max, w2_max)
#                 j += 1
#             else:
#                 break

#         merged.append(
#             type(base)(
#                 id=base.id,
#                 start=(x_min, y),
#                 end=(x_max, y),
#                 thickness=base.thickness,
#                 height=base.height
#             )
#         )

#         i = j

#     # ---- Merge vertical ----
#     vertical.sort(key=lambda w: (round(w.start[0], 1), w.start[1]))

#     i = 0
#     while i < len(vertical):
#         base = vertical[i]
#         x = base.start[0]

#         y_min = min(base.start[1], base.end[1])
#         y_max = max(base.start[1], base.end[1])

#         j = i + 1
#         while j < len(vertical):
#             w2 = vertical[j]

#             if abs(w2.start[0] - x) > tol:
#                 break

#             w2_min = min(w2.start[1], w2.end[1])
#             w2_max = max(w2.start[1], w2.end[1])

#             if w2_min <= y_max + tol:
#                 y_max = max(y_max, w2_max)
#                 j += 1
#             else:
#                 break

#         merged.append(
#             type(base)(
#                 id=base.id,
#                 start=(x, y_min),
#                 end=(x, y_max),
#                 thickness=base.thickness,
#                 height=base.height
#             )
#         )

#         i = j

#     return merged
from dataclasses import dataclass
from typing import List, Tuple
from pathlib import Path
import math
from shapely.geometry import Polygon

from .parse_dwg import parse_dwg


Point = Tuple[float, float]


# --------------------------------------------------------
# DATA STRUCTURES
# --------------------------------------------------------

@dataclass
class Wall:
    id: int
    start: Point
    end: Point
    thickness: float = 12.0
    height: float = 3.0


@dataclass
class Opening:
    id: int
    start: Point
    end: Point
    thickness: float = 4.0


@dataclass
class BuildingStructure:
    walls: List
    doors: List
    windows: List
    rooms: List


# --------------------------------------------------------
# MAIN BUILDER
# --------------------------------------------------------

def build_structure_from_dxf(file_path: Path) -> BuildingStructure:

    print("📐 Parsing DXF → Unified Geometry")

    entities = parse_dwg(file_path)

    walls = []
    doors = []
    windows = []
    room_polygons = []

    wall_id = 0

    # --------------------------------------------------------
    # 1️⃣ Try Semantic Wall Detection
    # --------------------------------------------------------

    for ent in entities:

        geom = ent.get("geometry")
        if not geom:
            continue

        if geom["type"] == "line" and ent["semantic"] == "wall":
            p1, p2 = geom["points"]
            length = math.dist(p1, p2)

            if length < 50:
                continue

            walls.append(
                Wall(
                    id=wall_id,
                    start=p1,
                    end=p2,
                    thickness=12.0
                )
            )
            wall_id += 1

    print(f"🔎 Raw wall segments: {len(walls)}")

    # --------------------------------------------------------
    # 2️⃣ If No Semantic Walls → Geometric Detection
    # --------------------------------------------------------

    if len(walls) == 0:
        print("⚠ No semantic walls detected — switching to geometric detection")

        poly_id = 0

        for ent in entities:
            geom = ent.get("geometry")
            if not geom:
                continue

            if geom["type"] in {"polyline", "spline"}:
                pts = geom["points"]

                if len(pts) < 3:
                    continue

                try:
                    poly = Polygon(pts)
                    if poly.is_valid and poly.area > 100:
                        room_polygons.append(poly)
                except Exception:
                    continue

        print(f"🧱 Geometric wall polygons: {len(room_polygons)}")

        # Convert polygons to Wall-like structures
        for poly in room_polygons:
            coords = list(poly.exterior.coords)
            for i in range(len(coords) - 1):
                walls.append(
                    Wall(
                        id=wall_id,
                        start=coords[i],
                        end=coords[i + 1],
                        thickness=12.0
                    )
                )
                wall_id += 1

    # --------------------------------------------------------

    print(f"🧱 Final walls: {len(walls)}")

    return BuildingStructure(
        walls=walls,
        doors=doors,
        windows=windows,
        rooms=[]
    )

