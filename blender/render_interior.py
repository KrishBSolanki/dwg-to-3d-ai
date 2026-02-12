import bpy
import sys
import os
from mathutils import Vector
import math

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
OUTPUT_DIR = os.path.join(BASE_DIR, "blender", "output", "interiors")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------
# CLEAN SCENE
# ---------------------------------------------------

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------
# IMPORT GLB
# ---------------------------------------------------

print("🏠 Interior render | Importing:", GLB_PATH)
bpy.ops.import_scene.gltf(filepath=GLB_PATH)

# ---------------------------------------------------
# CYCLES SETTINGS (INTERIOR)
# ---------------------------------------------------

scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"

scene.cycles.samples = 256
scene.cycles.use_denoising = True

scene.cycles.max_bounces = 10
scene.cycles.diffuse_bounces = 4
scene.cycles.glossy_bounces = 4
scene.cycles.transmission_bounces = 8

scene.render.resolution_x = 1600
scene.render.resolution_y = 1000

scene.view_settings.view_transform = "Filmic"
scene.view_settings.look = "High Contrast"
scene.view_settings.exposure = 0.0

# ---------------------------------------------------
# WORLD (DIM INTERIOR AMBIENCE)
# ---------------------------------------------------

world = bpy.data.worlds.new("InteriorWorld")
scene.world = world
world.use_nodes = True

nodes = world.node_tree.nodes
links = world.node_tree.links
nodes.clear()

bg = nodes.new("ShaderNodeBackground")
bg.inputs["Color"].default_value = (0.02, 0.02, 0.02, 1)
bg.inputs["Strength"].default_value = 0.3

out = nodes.new("ShaderNodeOutputWorld")
links.new(bg.outputs["Background"], out.inputs["Surface"])

# ---------------------------------------------------
# FIND MODEL BOUNDS
# ---------------------------------------------------

objects = [o for o in scene.objects if o.type == "MESH"]

bbox_min = Vector((1e9, 1e9, 1e9))
bbox_max = Vector((-1e9, -1e9, -1e9))

for obj in objects:
    for v in obj.bound_box:
        w = obj.matrix_world @ Vector(v)
        bbox_min.x = min(bbox_min.x, w.x)
        bbox_min.y = min(bbox_min.y, w.y)
        bbox_min.z = min(bbox_min.z, w.z)

        bbox_max.x = max(bbox_max.x, w.x)
        bbox_max.y = max(bbox_max.y, w.y)
        bbox_max.z = max(bbox_max.z, w.z)

size = bbox_max - bbox_min

# ---------------------------------------------------
# AUTO INTERIOR LIGHTS (SOFT + REALISTIC)
# ---------------------------------------------------

def add_soft_interior_lights():
    for i in range(6):
        light = bpy.data.lights.new(f"InteriorLight_{i}", type="POINT")
        light.energy = 180
        light.color = (1.0, 0.9, 0.75)
        light.shadow_soft_size = 1.5

        obj = bpy.data.objects.new(light.name, light)
        scene.collection.objects.link(obj)

        obj.location = (
            bbox_min.x + (i + 1) * size.x / 7,
            bbox_min.y + size.y * 0.5,
            bbox_min.z + size.z * 0.6,
        )

add_soft_interior_lights()

# ---------------------------------------------------
# INTERIOR CAMERA GENERATOR
# ---------------------------------------------------

def generate_interior_cameras(count=3):
    cameras = []

    for i in range(count):
        cam_data = bpy.data.cameras.new(f"InteriorCam_{i}")
        cam = bpy.data.objects.new(f"InteriorCam_{i}", cam_data)
        scene.collection.objects.link(cam)

        cam.location = (
            bbox_min.x + (i + 1) * size.x / (count + 1),
            bbox_min.y + size.y * 0.45,
            bbox_min.z + size.z * 0.5,
        )

        target = Vector((
            bbox_min.x + size.x * 0.5,
            bbox_min.y + size.y * 0.5,
            bbox_min.z + size.z * 0.5,
        ))

        direction = target - cam.location
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

        cam.data.lens = 22  # wide interior lens
        cam.data.clip_start = 0.05
        cam.data.clip_end = 1000

        cameras.append(cam)

    return cameras

cameras = generate_interior_cameras(count=3)

# ---------------------------------------------------
# RENDER EACH INTERIOR VIEW
# ---------------------------------------------------

for idx, cam in enumerate(cameras):
    scene.camera = cam
    scene.render.filepath = os.path.join(OUTPUT_DIR, f"interior_{idx+1}.png")
    bpy.ops.render.render(write_still=True)
    print(f"🖼️ Interior view rendered: interior_{idx+1}.png")

print("🎉 Interior rendering completed")
