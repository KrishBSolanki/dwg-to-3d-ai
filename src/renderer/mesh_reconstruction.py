# # src/renderer/mesh_reconstruction.py

# import trimesh
# import numpy as np
# from shapely.geometry import Polygon, LineString
# from shapely.ops import unary_union


# WALL_HEIGHT = 5.0
# WALL_THICKNESS = 0.3
# FLOOR_HEIGHT = 0.2


# def build_mesh(geometry, output_path):
#     meshes = []

#     walls = geometry.get("walls", [])
#     floors = geometry.get("floors", [])

#     print("Building mesh...")
#     print("Walls:", len(walls))
#     print("Floors:", len(floors))

#     # -------- WALLS --------
#     for wall in walls:
#         try:
#             if len(wall) < 2:
#                 continue

#             line = LineString(wall)
#             poly = line.buffer(WALL_THICKNESS)

#             if not poly.is_valid or poly.area == 0:
#                 continue

#             wall_mesh = trimesh.creation.extrude_polygon(poly, height=WALL_HEIGHT)
#             meshes.append(wall_mesh)

#         except Exception as e:
#             print("Wall error:", e)

#     # -------- FLOORS --------
#     for floor in floors:
#         try:
#             if len(floor) < 3:
#                 continue

#             poly = Polygon(floor)

#             if not poly.is_valid or poly.area == 0:
#                 continue

#             floor_mesh = trimesh.creation.extrude_polygon(poly, height=FLOOR_HEIGHT)
#             meshes.append(floor_mesh)

#         except Exception as e:
#             print("Floor error:", e)

#     if not meshes:
#         raise ValueError("No mesh generated")

#     # -------- MERGE --------
#     final_mesh = trimesh.util.concatenate(meshes)

#     # Center model
#     final_mesh.apply_translation(-final_mesh.centroid)

#     # Scale to reasonable size
#     scale = final_mesh.scale
#     if scale > 0:
#         final_mesh.apply_scale(1.0 / scale)

#     final_mesh.export(output_path)
#     print("Mesh saved to:", output_path)

#     return output_path
# src/renderer/mesh_reconstruction.py
import trimesh
from trimesh.visual.material import PBRMaterial
from shapely.geometry import LineString, Polygon, MultiPolygon
from shapely.ops import unary_union, polygonize
from pathlib import Path
from PIL import Image
import numpy as np

from ml.material_predictor import predict_material
from ml.feature_extractor import extract_wall_features

# ======================
# PARAMETERS
# ======================

UNIT_SCALE = 0.001
FLOOR_HEIGHT = 0.3
WALL_HEIGHT = 3.0
WALL_THICKNESS = 0.25

DOOR_HEIGHT = 2.1
WINDOW_HEIGHT = 1.2
WINDOW_BASE = 1.0

TEXTURE_DIR = Path("assets/textures")

# ======================
# PBR MATERIAL CACHE
# ======================

_MATERIAL_CACHE = {}


def load_texture(name):
    img = Image.open(TEXTURE_DIR / name).convert("RGBA")
    return np.array(img)


def get_pbr_material(material_name):
    """
    Create or reuse a PBR material for a semantic class.
    """

    if material_name in _MATERIAL_CACHE:
        return _MATERIAL_CACHE[material_name]

    if material_name == "concrete":
        material = PBRMaterial(
            baseColorTexture=load_texture("concrete.jpg"),
            metallicFactor=0.0,
            roughnessFactor=0.9
        )

    elif material_name == "gypsum":
        material = PBRMaterial(
            baseColorTexture=load_texture("gypsum.jpg"),
            metallicFactor=0.0,
            roughnessFactor=0.8
        )

    elif material_name == "tile":
        material = PBRMaterial(
            baseColorTexture=load_texture("tile.jpg"),
            metallicFactor=0.0,
            roughnessFactor=0.6
        )

    elif material_name == "glass":
        material = PBRMaterial(
            baseColorTexture=load_texture("glass.png"),
            metallicFactor=0.0,
            roughnessFactor=0.1,
            alphaMode="BLEND"
        )

    else:
        material = PBRMaterial(
            baseColorFactor=[0.8, 0.8, 0.8, 1.0],
            metallicFactor=0.0,
            roughnessFactor=0.8
        )

    _MATERIAL_CACHE[material_name] = material
    print(f"🎨 PBR material created: {material_name}")
    return material


# ======================
# UTILS
# ======================

def scale_coords(coords):
    return [(x * UNIT_SCALE, y * UNIT_SCALE) for x, y in coords]


def center_mesh(mesh):
    mesh.apply_translation(-mesh.centroid)
    return mesh


def extrude(poly, height):
    return trimesh.creation.extrude_polygon(poly, height)


def buffer_centerline(line):
    return line.buffer(
        WALL_THICKNESS / 2,
        cap_style=3,
        join_style=2
    )


# ======================
# ROOM DETECTION
# ======================

def detect_rooms_from_walls(walls):
    lines = [LineString(w["points"]) for w in walls if len(w["points"]) >= 2]
    merged = unary_union(lines)

    rooms = []
    for poly in polygonize(merged):
        if poly.is_valid and poly.area > 5:
            rooms.append(poly)

    print(f"🏠 Rooms polygonized: {len(rooms)}")
    return rooms


# ======================
# MAIN BUILDER
# ======================

def build_mesh(geometry, output_path):
    print("🏗️ Starting mesh reconstruction (PBR-enabled)...")

    meshes = []

    # -------------------------
    # FLOOR SLAB
    # -------------------------
    raw_rooms = detect_rooms_from_walls(geometry["walls"])
    rooms = [Polygon(scale_coords(r.exterior.coords)) for r in raw_rooms]

    unioned = unary_union(rooms)
    if isinstance(unioned, MultiPolygon):
        unioned = max(unioned.geoms, key=lambda p: p.area)

    floor_mesh = extrude(unioned, FLOOR_HEIGHT)
    floor_mesh.visual.material = get_pbr_material("tile")
    meshes.append(floor_mesh)

    print("🧱 Floor slab created")

    # -------------------------
    # WALL CENTERLINES
    # -------------------------
    wall_lines = []
    for wall in geometry["walls"]:
        pts = scale_coords(wall["points"])
        if len(pts) >= 2:
            wall_lines.append(LineString(pts))

    merged_lines = unary_union(wall_lines)
    if isinstance(merged_lines, LineString):
        merged_lines = [merged_lines]
    else:
        merged_lines = list(merged_lines.geoms)

    print(f"🧱 Continuous wall centerlines: {len(merged_lines)}")

    wall_meshes = []

    for line in merged_lines:
        poly = buffer_centerline(line)
        if not poly.is_valid:
            continue

        # -------- AI FEATURE EXTRACTION --------
        features = extract_wall_features(
            poly,
            WALL_HEIGHT,
            layer="a-wall"
        )

        material_name = predict_material(features)
        material = get_pbr_material(material_name)

        wall_mesh = extrude(poly, WALL_HEIGHT)
        wall_mesh.visual.material = material
        wall_meshes.append(wall_mesh)

    print("🎨 Wall materials applied")

    walls_combined = trimesh.util.concatenate(wall_meshes)
    meshes.append(walls_combined)

    # -------------------------
    # FINAL EXPORT
    # -------------------------
    final_mesh = trimesh.util.concatenate(meshes)
    final_mesh = center_mesh(final_mesh)

    glb_path = output_path.with_suffix(".glb")
    final_mesh.export(glb_path)

    print("🎉 GLB exported with PBR materials:", glb_path)
