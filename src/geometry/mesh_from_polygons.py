# import numpy as np
# import trimesh
# from shapely.geometry import Polygon
# from shapely.geometry import LineString
# from shapely.geometry import Polygon as ShapelyPolygon



# PIXEL_TO_METER = 0.01
# WALL_HEIGHT = 3.0
# FLOOR_THICKNESS = 0.05

# def wall_to_polygon(wall):
#     """
#     Convert parametric Wall (centerline + thickness)
#     into rectangular Shapely polygon.
#     """
#     line = LineString([wall.start, wall.end])
#     poly = line.buffer(wall.thickness / 2.0, cap_style=2)  # square caps
#     return poly

# def scale_polygon(poly: Polygon, scale=PIXEL_TO_METER):
#     coords = np.array(poly.exterior.coords)
#     coords = coords * scale
#     return Polygon(coords)


# def extrude_polygon(poly: Polygon, height: float):
#     return trimesh.creation.extrude_polygon(poly, height)


# def build_mesh_from_structure(structure):

#     meshes = []

#     # ---- WALLS ----
#     for wall in structure.walls:

#         # CASE 1️⃣ Segmentation polygon wall
#         if isinstance(wall, Polygon):
#             wall_poly = wall

#         # CASE 2️⃣ Parametric CAD wall
#         else:
#             wall_poly = wall_to_polygon(wall)

#         wall_scaled = scale_polygon(wall_poly)
#         wall_mesh = extrude_polygon(wall_scaled, WALL_HEIGHT)
#         meshes.append(wall_mesh)

#     # ---- FLOORS ----
#     if hasattr(structure, "rooms"):
#         for room in structure.rooms:
#             room_scaled = scale_polygon(room.polygon)
#             floor_mesh = extrude_polygon(room_scaled, FLOOR_THICKNESS)
#             meshes.append(floor_mesh)

#     if not meshes:
#         return None

#     final_mesh = trimesh.util.concatenate(meshes)

#     return final_mesh

import trimesh
from shapely.geometry import Polygon, LineString, MultiPolygon
from shapely.ops import unary_union

from .wall_cleaner import clean_wall_polygons


# --------------------------------------------------------
# GLOBAL CONFIG
# --------------------------------------------------------

UNIT_SCALE = 0.0254  # inches → meters

WALL_HEIGHT = 3.0
FLOOR_THICKNESS = 0.20
CEILING_THICKNESS = 0.15

MIN_WALL_THICKNESS = 0.15  # meters


# --------------------------------------------------------
# WALL → POLYGON
# --------------------------------------------------------

def wall_to_polygon(wall):
    thickness = max(wall.thickness * UNIT_SCALE, MIN_WALL_THICKNESS)

    line = LineString([
        (wall.start[0] * UNIT_SCALE, wall.start[1] * UNIT_SCALE),
        (wall.end[0] * UNIT_SCALE, wall.end[1] * UNIT_SCALE)
    ])

    return line.buffer(thickness / 2.0, cap_style=2)


# --------------------------------------------------------
# EXTRUSION
# --------------------------------------------------------

def extrude_polygon(poly: Polygon, height: float):
    return trimesh.creation.extrude_polygon(
        poly,
        height,
        triangulate_kwargs={"engine": "earcut"}
    )


# --------------------------------------------------------
# CENTERING
# --------------------------------------------------------

def center_mesh(mesh):
    mesh.apply_translation(-mesh.centroid)
    return mesh


# --------------------------------------------------------
# MAIN BUILDER (WALL UNION APPROACH)
# --------------------------------------------------------

def build_mesh_from_structure(structure):

    print("🏗 Building mesh from wall union...")

    # ----------------------------------------------------
    # 1️⃣ BUILD WALL POLYGONS
    # ----------------------------------------------------

    wall_polygons = []

    for wall in structure.walls:
        poly = wall_to_polygon(wall)
        if poly and poly.is_valid:
            wall_polygons.append(poly)

    print(f"🧱 Raw wall polygons: {len(wall_polygons)}")

    if not wall_polygons:
        print("❌ No wall polygons created")
        return None

    # ----------------------------------------------------
    # 2️⃣ CLEAN WALLS
    # ----------------------------------------------------

    cleaned = clean_wall_polygons(wall_polygons)

    print(f"🧱 Cleaned wall masses: {len(cleaned)}")

    if not cleaned:
        print("❌ Wall cleaning failed")
        return None

    # ----------------------------------------------------
    # 3️⃣ UNION WALL MASS
    # ----------------------------------------------------

    wall_union = unary_union(cleaned)

    if wall_union.is_empty:
        print("❌ Wall union failed")
        return None

    # If multiple islands exist → keep largest
    if isinstance(wall_union, MultiPolygon):
        wall_union = max(wall_union.geoms, key=lambda p: p.area)

    print("🧱 Union complete")

    # ----------------------------------------------------
    # 4️⃣ EXTRUDE WALL MASS DIRECTLY
    # ----------------------------------------------------

    walls_mesh = extrude_polygon(wall_union, WALL_HEIGHT)

    # ----------------------------------------------------
    # 5️⃣ FLOOR (from outer boundary)
    # ----------------------------------------------------

    floor_mesh = extrude_polygon(wall_union, FLOOR_THICKNESS)

    # ----------------------------------------------------
    # 6️⃣ CEILING
    # ----------------------------------------------------

    ceiling_mesh = extrude_polygon(wall_union, CEILING_THICKNESS)
    ceiling_mesh.apply_translation((0, 0, WALL_HEIGHT))

    # ----------------------------------------------------
    # 7️⃣ FINAL MERGE
    # ----------------------------------------------------

    final_mesh = trimesh.util.concatenate([
        walls_mesh,
        floor_mesh,
        ceiling_mesh
    ])

    final_mesh = center_mesh(final_mesh)

    print("✅ Final mesh ready")

    return final_mesh
