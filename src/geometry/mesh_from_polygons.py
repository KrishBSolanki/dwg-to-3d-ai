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

import numpy as np
import trimesh
import math

from shapely.geometry import Polygon, LineString, MultiPolygon
from shapely.ops import unary_union


# --------------------------------------------------------
# GLOBAL CONFIG
# --------------------------------------------------------

# DXF units = inches → meters
UNIT_SCALE = 0.0254

WALL_HEIGHT = 3.0
FLOOR_THICKNESS = 0.20
CEILING_THICKNESS = 0.15


# --------------------------------------------------------
# WALL CONVERSION
# --------------------------------------------------------

def wall_to_polygon(wall):
    """
    Convert parametric Wall (centerline + thickness)
    into rectangular Shapely polygon.
    """

    line = LineString([wall.start, wall.end])

    # square caps = clean wall ends
    poly = line.buffer(wall.thickness / 2.0, cap_style=2)

    return poly


# --------------------------------------------------------
# SCALE UTIL
# --------------------------------------------------------

def scale_polygon(poly: Polygon):
    coords = np.array(poly.exterior.coords)
    coords = coords * UNIT_SCALE
    return Polygon(coords)


# --------------------------------------------------------
# EXTRUSION
# --------------------------------------------------------

def extrude_polygon(poly: Polygon, height: float):
    """
    Extrude polygon using mapbox-earcut engine (CI safe)
    """
    return trimesh.creation.extrude_polygon(
        poly,
        height,
        triangulate_kwargs={"engine": "earcut"}
    )


# --------------------------------------------------------
# MESH CENTERING
# --------------------------------------------------------

def center_mesh(mesh):
    mesh.apply_translation(-mesh.centroid)
    return mesh


# --------------------------------------------------------
# MAIN BUILDER
# --------------------------------------------------------

def build_mesh_from_structure(structure):

    print("🏗 Building mesh from unified structure...")

    meshes = []
    wall_polygons = []

    # ----------------------------------------------------
    # WALLS
    # ----------------------------------------------------

    for wall in structure.walls:

        # AI segmentation polygon case
        if isinstance(wall, Polygon):
            wall_poly = wall

        # CAD parametric wall case
        else:
            wall_poly = wall_to_polygon(wall)

        if wall_poly is None or not wall_poly.is_valid:
            continue

        wall_polygons.append(wall_poly)

        scaled = scale_polygon(wall_poly)

        wall_mesh = extrude_polygon(scaled, WALL_HEIGHT)
        meshes.append(wall_mesh)

    print(f"🧱 Walls created: {len(wall_polygons)}")

    # ----------------------------------------------------
    # FLOOR
    # ----------------------------------------------------

    floor_polygon = None

    # If AI rooms exist → use them
    if hasattr(structure, "rooms") and structure.rooms:

        room_polys = [room.polygon for room in structure.rooms]
        unioned = unary_union(room_polys)

        if isinstance(unioned, MultiPolygon):
            unioned = max(unioned.geoms, key=lambda p: p.area)

        floor_polygon = unioned

    # If DXF only → generate floor from wall union
    elif wall_polygons:
        unioned = unary_union(wall_polygons)

        if isinstance(unioned, MultiPolygon):
            unioned = max(unioned.geoms, key=lambda p: p.area)

        floor_polygon = unioned

    if floor_polygon:
        floor_scaled = scale_polygon(floor_polygon)
        floor_mesh = extrude_polygon(floor_scaled, FLOOR_THICKNESS)
        meshes.append(floor_mesh)
        print("🧱 Floor slab created")

    # ----------------------------------------------------
    # CEILING
    # ----------------------------------------------------

    if floor_polygon:
        ceiling_scaled = scale_polygon(floor_polygon)
        ceiling_mesh = extrude_polygon(ceiling_scaled, CEILING_THICKNESS)

        ceiling_mesh.apply_translation((0, 0, WALL_HEIGHT))
        meshes.append(ceiling_mesh)

        print("🧱 Ceiling slab created")

    # ----------------------------------------------------
    # DOOR & WINDOW CUTOUTS
    # ----------------------------------------------------

    openings = []

    if hasattr(structure, "doors"):
        openings.extend(structure.doors)

    if hasattr(structure, "windows"):
        openings.extend(structure.windows)

    if openings and meshes:

        print("🚪 Cutting door & window openings...")

        opening_meshes = []

        for opening in openings:

            if isinstance(opening, Polygon):
                poly = opening
            else:
                poly = wall_to_polygon(opening)

            if poly is None or not poly.is_valid:
                continue

            scaled = scale_polygon(poly)
            cut_mesh = extrude_polygon(scaled, WALL_HEIGHT)
            opening_meshes.append(cut_mesh)

        if opening_meshes:
            openings_mesh = trimesh.util.concatenate(opening_meshes)

            # Walls are first meshes
            walls_mesh = meshes[0]

            try:
                cut_result = walls_mesh.difference(openings_mesh)
                meshes[0] = cut_result
                print("✂ Boolean subtraction complete")
            except Exception as e:
                print("⚠ Boolean failed:", e)

    # ----------------------------------------------------
    # FINAL MERGE
    # ----------------------------------------------------

    if not meshes:
        print("❌ No mesh generated")
        return None

    final_mesh = trimesh.util.concatenate(meshes)
    final_mesh = center_mesh(final_mesh)

    print("✅ Final mesh ready")

    return final_mesh
