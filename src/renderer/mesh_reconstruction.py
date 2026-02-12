# import trimesh
# from trimesh.visual.material import PBRMaterial
# from shapely.geometry import LineString, Polygon, MultiPolygon
# from shapely.ops import unary_union, polygonize, transform
# from pathlib import Path
# from PIL import Image
# import numpy as np

# from ml.material_predictor import predict_material
# from ml.feature_extractor import extract_wall_features


# # ======================
# # PARAMETERS
# # ======================

# UNIT_SCALE = 0.001
# FLOOR_HEIGHT = 0.3
# WALL_HEIGHT = 3.0
# WALL_THICKNESS = 0.25

# DOOR_HEIGHT = 2.1
# WINDOW_HEIGHT = 1.2
# WINDOW_BASE = 1.0

# TEXTURE_DIR = Path("assets/textures")


# # ======================
# # MATERIAL CACHE
# # ======================

# _MATERIAL_CACHE = {}


# def load_texture(name):
#     img = Image.open(TEXTURE_DIR / name).convert("RGBA")
#     return np.array(img)


# def get_pbr_material(material_name):
#     if material_name in _MATERIAL_CACHE:
#         return _MATERIAL_CACHE[material_name]

#     if material_name == "concrete":
#         material = PBRMaterial(
#             baseColorTexture=load_texture("concrete.jpg"),
#             metallicFactor=0.0,
#             roughnessFactor=0.9
#         )
#     elif material_name == "gypsum":
#         material = PBRMaterial(
#             baseColorTexture=load_texture("gypsum.jpg"),
#             metallicFactor=0.0,
#             roughnessFactor=0.8
#         )
#     elif material_name == "tile":
#         material = PBRMaterial(
#             baseColorTexture=load_texture("tile.jpg"),
#             metallicFactor=0.0,
#             roughnessFactor=0.6
#         )
#     elif material_name == "glass":
#         material = PBRMaterial(
#             baseColorTexture=load_texture("glass.png"),
#             metallicFactor=0.0,
#             roughnessFactor=0.1,
#             alphaMode="BLEND"
#         )
#     else:
#         material = PBRMaterial(
#             baseColorFactor=[0.8, 0.8, 0.8, 1.0],
#             metallicFactor=0.0,
#             roughnessFactor=0.8
#         )

#     _MATERIAL_CACHE[material_name] = material
#     print(f"🎨 PBR material created: {material_name}")
#     return material


# # ======================
# # GEOMETRY UTILS
# # ======================

# def scale_coords(coords):
#     return [(x * UNIT_SCALE, y * UNIT_SCALE) for x, y in coords]


# def force_2d(geom):
#     if geom is None or geom.is_empty:
#         return None
#     return transform(lambda x, y, *z: (x, y), geom)


# def center_mesh(mesh):
#     mesh.apply_translation(-mesh.centroid)
#     return mesh


# def extrude(poly, height):
#     return trimesh.creation.extrude_polygon(poly, height, engine="earcut")


# def is_valid_volume(mesh):
#     return (
#         mesh is not None
#         and mesh.is_watertight
#         and mesh.is_volume
#         and mesh.volume > 0
#     )


# # ======================
# # ROOM DETECTION
# # ======================

# def detect_rooms_from_walls(walls):
#     lines = [LineString(scale_coords(w["points"])) for w in walls if len(w["points"]) >= 2]
#     merged = unary_union(lines)

#     rooms = []
#     for poly in polygonize(merged):
#         if poly.is_valid and poly.area > 5:
#             rooms.append(poly)

#     print(f"🏠 Rooms polygonized: {len(rooms)}")
#     return rooms


# # ======================
# # WALL SOLIDS
# # ======================

# def build_wall_solids(walls):
#     lines = []
#     for w in walls:
#         pts = scale_coords(w["points"])
#         if len(pts) >= 2:
#             lines.append(LineString(pts))

#     merged = unary_union(lines)

#     if isinstance(merged, LineString):
#         merged = [merged]
#     else:
#         merged = list(merged.geoms)

#     buffered = unary_union([
#         line.buffer(
#             WALL_THICKNESS / 2,
#             cap_style=3,
#             join_style=2
#         )
#         for line in merged
#     ])

#     buffered = force_2d(buffered)

#     if isinstance(buffered, Polygon):
#         return [buffered]
#     elif isinstance(buffered, MultiPolygon):
#         return list(buffered.geoms)
#     return []


# # ======================
# # OPENING CUTTERS
# # ======================

# def opening_volume(edge, height, base_z=0.0):
#     line = LineString(scale_coords(edge))
#     rect = line.buffer(WALL_THICKNESS * 0.6, cap_style=3)
#     rect = force_2d(rect)

#     mesh = extrude(rect, height)
#     mesh.apply_translation((0, 0, base_z))
#     return mesh


# # ======================
# # MAIN BUILDER
# # ======================

# def build_mesh(geometry, output_path):
#     print("🏗️ Starting mesh reconstruction (PBR-enabled)...")

#     meshes = []

#     # -------- FLOOR --------
#     raw_rooms = detect_rooms_from_walls(geometry["walls"])

#     if raw_rooms:
#         rooms = [force_2d(r) for r in raw_rooms]
#         unioned = force_2d(unary_union(rooms))

#         if unioned and not unioned.is_empty:
#             if isinstance(unioned, MultiPolygon):
#                 unioned = max(unioned.geoms, key=lambda p: p.area)

#             floor_mesh = extrude(unioned, FLOOR_HEIGHT)
#             floor_mesh.visual.material = get_pbr_material("tile")
#             meshes.append(floor_mesh)
#             print("🧱 Floor slab created")
#         else:
#             print("⚠ No valid floor polygon. Skipping floor.")
#     else:
#         print("⚠ No rooms found. Skipping floor.")

#     # -------- WALLS --------
#     wall_polys = build_wall_solids(geometry["walls"])
#     print(f"🧱 Wall solids generated: {len(wall_polys)}")

#     wall_meshes = []
#     for poly in wall_polys:
#         features = extract_wall_features(poly, WALL_HEIGHT, layer="a-wall")
#         material = get_pbr_material(predict_material(features))

#         mesh = extrude(poly, WALL_HEIGHT)
#         mesh.visual.material = material
#         wall_meshes.append(mesh)

#     walls_mesh = trimesh.util.concatenate(wall_meshes)

#     # -------- DOOR / WINDOW CUTS --------
#     cutters = []

#     for d in geometry["doors"]:
#         c = opening_volume(d["points"], DOOR_HEIGHT, 0.0)
#         if is_valid_volume(c):
#             cutters.append(c)

#     for w in geometry["windows"]:
#         c = opening_volume(w["points"], WINDOW_HEIGHT, WINDOW_BASE)
#         if is_valid_volume(c):
#             cutters.append(c)

#     if cutters:
#         print(f"🚪🪟 Cutting {len(cutters)} openings from walls...")
#         try:
#             merged = trimesh.util.concatenate(cutters)
#             walls_mesh = walls_mesh.difference(merged)
#         except Exception as e:
#             print(f"⚠ Boolean cutting failed: {e}")
#     else:
#         print("⚠ No valid cutters found. Skipping openings.")

#     meshes.append(walls_mesh)

#     # -------- EXPORT --------
#     final_mesh = trimesh.util.concatenate(meshes)
#     final_mesh = center_mesh(final_mesh)

#     glb_path = output_path.with_suffix(".glb")
#     final_mesh.export(glb_path)

#     print("🎉 GLB exported with PBR materials:", glb_path)
#     return glb_path
# src/renderer/mesh_reconstruction.py

import trimesh
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
import numpy as np


# --------------------------------------------------------
# PARAMETERS (DXF is in inches)
# --------------------------------------------------------

UNIT_SCALE = 0.0254# inches → meters (~1 inch = 0.0254m, we approximate here)
WALL_HEIGHT = 120 * UNIT_SCALE        # 10 ft wall
FLOOR_THICKNESS = 6 * UNIT_SCALE      # 6 inches slab

DOOR_HEIGHT = 84 * UNIT_SCALE         # 7 ft door
WINDOW_HEIGHT = 48 * UNIT_SCALE       # 4 ft window
WINDOW_SILL = 36 * UNIT_SCALE         # 3 ft sill height


# --------------------------------------------------------
# UTILS
# --------------------------------------------------------

def scale_polygon(poly: Polygon):
    return Polygon([(x * UNIT_SCALE, y * UNIT_SCALE) for x, y in poly.exterior.coords])


def extrude_polygon(poly: Polygon, height: float):
    return trimesh.creation.extrude_polygon(poly, height)


def center_mesh(mesh):
    mesh.apply_translation(-mesh.centroid)
    return mesh


# --------------------------------------------------------
# MAIN BUILDER (AI + DXF unified)
# --------------------------------------------------------

def build_mesh_from_ai(ai_geometry: dict, output_path):

    print("🏗 Building mesh from unified geometry...")

    meshes = []

    # ----------------------------------------------------
    # FLOOR (Union of Rooms)
    # ----------------------------------------------------

    if ai_geometry["rooms"]:

        scaled_rooms = [scale_polygon(p) for p in ai_geometry["rooms"]]
        unioned = unary_union(scaled_rooms)

        if isinstance(unioned, MultiPolygon):
            unioned = max(unioned.geoms, key=lambda p: p.area)

        floor_mesh = extrude_polygon(unioned, FLOOR_THICKNESS)
        meshes.append(floor_mesh)

        print("🧱 Floor created")

    # ----------------------------------------------------
    # WALLS
    # ----------------------------------------------------

    wall_meshes = []

    for wall_poly in ai_geometry["walls"]:
        scaled = scale_polygon(wall_poly)

        if not scaled.is_valid or scaled.area < 1e-6:
            continue

        wall_mesh = extrude_polygon(scaled, WALL_HEIGHT)
        wall_meshes.append(wall_mesh)

    if not wall_meshes:
        print("❌ No walls generated")
        return

    walls_combined = trimesh.util.concatenate(wall_meshes)
    meshes.append(walls_combined)

    print(f"🧱 Walls created: {len(wall_meshes)}")

    # ----------------------------------------------------
    # BOOLEAN DOORS
    # ----------------------------------------------------

    openings = []

    for door in ai_geometry["doors"]:
        scaled = scale_polygon(door)

        if not scaled.is_valid:
            continue

        cut_mesh = extrude_polygon(scaled, DOOR_HEIGHT)
        openings.append(cut_mesh)

    # ----------------------------------------------------
    # BOOLEAN WINDOWS
    # ----------------------------------------------------

    for window in ai_geometry["windows"]:
        scaled = scale_polygon(window)

        if not scaled.is_valid:
            continue

        cut_mesh = extrude_polygon(scaled, WINDOW_HEIGHT)

        # Move window up to sill height
        cut_mesh.apply_translation([0, 0, WINDOW_SILL])

        openings.append(cut_mesh)

    # ----------------------------------------------------
    # APPLY BOOLEAN CUT
    # ----------------------------------------------------

    if openings:
        print("🚪 Cutting door & window openings...")

        openings_mesh = trimesh.util.concatenate(openings)

        try:
            cut_result = walls_combined.difference(openings_mesh)
            meshes[-1] = cut_result
            print("✂ Boolean subtraction complete")
        except Exception as e:
            print("⚠ Boolean failed:", e)

    # ----------------------------------------------------
    # FINAL EXPORT
    # ----------------------------------------------------

    final_mesh = trimesh.util.concatenate(meshes)
    final_mesh = center_mesh(final_mesh)

    glb_path = output_path.with_suffix(".glb")
    final_mesh.export(glb_path)

    print("🎉 GLB exported:", glb_path)
