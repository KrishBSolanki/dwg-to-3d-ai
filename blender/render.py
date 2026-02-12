import bpy
import sys
import os
import math
from mathutils import Vector
# ---------------------------------------------------
# MODEL PARAMETERS (must match geometry engine)
# ---------------------------------------------------

WALL_HEIGHT = 3.0  # meters

# ---------------------------------------------------
# ARGUMENT PARSING
# ---------------------------------------------------

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []

if not argv:
    print("❌ No GLB file provided")
    sys.exit(1)

GLB_PATH = os.path.abspath(argv[0])

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
HDRI_PATH = os.path.join(BASE_DIR, "blender", "assets", "hdri", "night.exr")
OUTPUT_DIR = os.path.join(BASE_DIR, "blender", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_IMAGE = os.path.join(OUTPUT_DIR, "exterior_night.png")

print("📦 Importing:", GLB_PATH)

# ---------------------------------------------------
# CLEAN SCENE (⚠ MUST BE FIRST)
# ---------------------------------------------------

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------
# IMPORT GLB
# ---------------------------------------------------

bpy.ops.import_scene.gltf(filepath=GLB_PATH)

# ---------------------------------------------------
# CYCLES RENDER ENGINE (ARCH-VIS SAFE)
# ---------------------------------------------------

scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"

scene.cycles.samples = 256
scene.cycles.use_denoising = True

scene.cycles.max_bounces = 8
scene.cycles.diffuse_bounces = 3
scene.cycles.glossy_bounces = 4
scene.cycles.transmission_bounces = 6
scene.cycles.transparent_max_bounces = 8

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.film_transparent = False

# ---------------------------------------------------
# WORLD HDRI — NIGHT (REALISTIC)
# ---------------------------------------------------

world = bpy.data.worlds.new("NightWorld")
scene.world = world
world.use_nodes = True

nodes = world.node_tree.nodes
links = world.node_tree.links
nodes.clear()

env = nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(HDRI_PATH)

bg = nodes.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 0.15  # 🌙 dark but reflective

out = nodes.new("ShaderNodeOutputWorld")

links.new(env.outputs["Color"], bg.inputs["Color"])
links.new(bg.outputs["Background"], out.inputs["Surface"])

print("🌙 Night HDRI applied")

# ---------------------------------------------------
# FIND MODEL BOUNDS
# ---------------------------------------------------

# ---------------------------------------------------
# COMPUTE FOOTPRINT BOUNDS (ignore height)
# ---------------------------------------------------

objects = [o for o in scene.objects if o.type == "MESH"]

bbox_min = Vector((1e9, 1e9, 1e9))
bbox_max = Vector((-1e9, -1e9, -1e9))

for obj in objects:
    for v in obj.bound_box:
        world_v = obj.matrix_world @ Vector(v)
        bbox_min.x = min(bbox_min.x, world_v.x)
        bbox_min.y = min(bbox_min.y, world_v.y)
        bbox_min.z = min(bbox_min.z, world_v.z)

        bbox_max.x = max(bbox_max.x, world_v.x)
        bbox_max.y = max(bbox_max.y, world_v.y)
        bbox_max.z = max(bbox_max.z, world_v.z)

center = (bbox_min + bbox_max) / 2

# Horizontal footprint size only
footprint_size = max(bbox_max.x - bbox_min.x,
                     bbox_max.y - bbox_min.y)

# Use footprint only
radius = footprint_size


# ---------------------------------------------------
# CAMERA SETUP — EXTERIOR NIGHT
# ---------------------------------------------------

camera_data = bpy.data.cameras.new("ExteriorCamera")
camera = bpy.data.objects.new("ExteriorCamera", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera

camera.location = (
    center.x + radius * 1.2,
    center.y - radius * 1.2,
    center.z + WALL_HEIGHT * 1.5
)


direction = center - camera.location
camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

camera.data.lens = 40
camera.data.clip_start = 0.1
camera.data.clip_end = 2000

print("📷 Exterior camera placed")

# ---------------------------------------------------
# MOON LIGHT (KEY LIGHT)
# ---------------------------------------------------

moon = bpy.data.lights.new(name="Moon", type="SUN")
moon.energy = 1.2
moon.color = (0.6, 0.7, 1.0)

moon_obj = bpy.data.objects.new("Moon", moon)
scene.collection.objects.link(moon_obj)

moon_obj.rotation_euler = (
    math.radians(50),
    math.radians(-20),
    math.radians(30)
)

# ---------------------------------------------------
# WINDOW GLASS — REALISTIC
# ---------------------------------------------------

# ---------------------------------------------------
# FIX PYTHON PATH FOR BLENDER
# ---------------------------------------------------

import pathlib

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from blender.materials import create_window_glass_material

glass_mat = create_window_glass_material(night=True)

for obj in scene.objects:
    if obj.type == "MESH" and "window" in obj.name.lower():
        if not obj.data.materials:
            obj.data.materials.append(glass_mat)
        else:
            obj.data.materials[0] = glass_mat

print("🪟 Window glass applied")

# ---------------------------------------------------
# FAÇADE LIGHTS (ARCH-VIS MAGIC)
# ---------------------------------------------------

for obj in objects:
    light = bpy.data.lights.new(name="FacadeLight", type="AREA")
    light.energy = 200
    light.color = (1.0, 0.85, 0.7)
    light.size = radius * 0.4

    light_obj = bpy.data.objects.new("FacadeLight", light)
    scene.collection.objects.link(light_obj)

    light_obj.location = (
        center.x,
        bbox_min.y - radius * 0.3,
        bbox_max.z * 0.8
    )

    break  # one key façade light is enough

print("💡 Facade lighting added")

bpy.ops.mesh.primitive_plane_add(size=radius * 4)
ground = bpy.context.object
ground.location = (center.x, center.y, bbox_min.z - 0.01)

mat = bpy.data.materials.new("GroundMat")
mat.use_nodes = True
ground.data.materials.append(mat)

# ---------------------------------------------------
# RENDER
# ---------------------------------------------------

scene.render.filepath = OUTPUT_IMAGE
bpy.ops.render.render(write_still=True)

print("🎉 Night exterior render completed:", OUTPUT_IMAGE)
