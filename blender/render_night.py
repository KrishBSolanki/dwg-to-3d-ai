import bpy
import sys
import os
import math
from mathutils import Vector

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

# ---------------------------------------------------
# VALIDATE FILES
# ---------------------------------------------------

if not os.path.exists(GLB_PATH):
    print("❌ GLB not found:", GLB_PATH)
    sys.exit(1)

if not os.path.exists(HDRI_PATH):
    print("❌ HDRI not found:", HDRI_PATH)
    sys.exit(1)

print("🌙 Night render | Importing:", GLB_PATH)

# ---------------------------------------------------
# CLEAN SCENE
# ---------------------------------------------------

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------
# IMPORT GLB
# ---------------------------------------------------

bpy.ops.import_scene.gltf(filepath=GLB_PATH)

# ---------------------------------------------------
# CYCLES SETTINGS
# ---------------------------------------------------

scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 256
scene.cycles.use_denoising = True

scene.cycles.max_bounces = 8
scene.cycles.diffuse_bounces = 3
scene.cycles.glossy_bounces = 4
scene.cycles.transmission_bounces = 6

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

scene.view_settings.view_transform = "Filmic"
scene.view_settings.look = "High Contrast"
scene.view_settings.exposure = -1.0

# ---------------------------------------------------
# WORLD HDRI — NIGHT
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
bg.inputs["Strength"].default_value = 0.12

out = nodes.new("ShaderNodeOutputWorld")

links.new(env.outputs["Color"], bg.inputs["Color"])
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
        bbox_min = Vector((min(bbox_min.x, w.x), min(bbox_min.y, w.y), min(bbox_min.z, w.z)))
        bbox_max = Vector((max(bbox_max.x, w.x), max(bbox_max.y, w.y), max(bbox_max.z, w.z)))

center = (bbox_min + bbox_max) / 2
size = (bbox_max - bbox_min)

# ---------------------------------------------------
# MATERIALS (BLENDER 4.x SAFE)
# ---------------------------------------------------

def make_material(name, color, roughness):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness

    # ✅ Blender 4.x compatible specular control
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.45

    out = nodes.new("ShaderNodeOutputMaterial")
    mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

plaster_mat = make_material("Plaster", (0.92, 0.92, 0.90), 0.65)
concrete_mat = make_material("Concrete", (0.70, 0.70, 0.72), 0.85)
paint_mat = make_material("Paint", (0.85, 0.88, 0.92), 0.55)

# ---------------------------------------------------
# APPLY MATERIALS AUTOMATICALLY
# ---------------------------------------------------

for obj in objects:
    dims = obj.dimensions

    obj.data.materials.clear()

    if dims.z > dims.x and dims.z > dims.y:
        obj.data.materials.append(plaster_mat)
    elif dims.z < 0.5:
        obj.data.materials.append(concrete_mat)
    else:
        obj.data.materials.append(paint_mat)

print("🏗️ Exterior materials applied")

# ---------------------------------------------------
# CAMERA
# ---------------------------------------------------

camera_data = bpy.data.cameras.new("ExteriorCamera")
camera = bpy.data.objects.new("ExteriorCamera", camera_data)
scene.collection.objects.link(camera)
scene.camera = camera

camera.location = (
    center.x + size.x * 1.2,
    center.y - size.y * 1.5,
    center.z + size.z * 0.8
)

direction = center - camera.location
camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

camera.data.lens = 40
camera.data.clip_start = 0.1
camera.data.clip_end = 2000

# ---------------------------------------------------
# LIGHTING
# ---------------------------------------------------

moon = bpy.data.lights.new("Moon", type="SUN")
moon.energy = 1.2
moon.color = (0.6, 0.7, 1.0)
moon_obj = bpy.data.objects.new("Moon", moon)
scene.collection.objects.link(moon_obj)
moon_obj.rotation_euler = (math.radians(50), math.radians(-20), math.radians(30))

for i in range(6):
    light = bpy.data.lights.new(f"Interior_{i}", type="POINT")
    light.energy = 120
    light.color = (1.0, 0.85, 0.65)
    obj = bpy.data.objects.new(f"Interior_{i}", light)
    scene.collection.objects.link(obj)
    obj.location = (
        bbox_min.x + (i + 1) * size.x / 7,
        bbox_min.y + size.y * 0.5,
        bbox_min.z + size.z * 0.5,
    )

facade = bpy.data.lights.new("Facade", type="AREA")
facade.energy = 180
facade.color = (1.0, 0.85, 0.7)
facade.size = size.x * 0.4
facade_obj = bpy.data.objects.new("Facade", facade)
scene.collection.objects.link(facade_obj)
facade_obj.location = (center.x, bbox_min.y - size.y * 0.3, bbox_max.z * 0.85)

# ---------------------------------------------------
# RENDER
# ---------------------------------------------------

scene.render.filepath = OUTPUT_IMAGE
bpy.ops.render.render(write_still=True)

print("🎉 Night exterior render completed:", OUTPUT_IMAGE)
