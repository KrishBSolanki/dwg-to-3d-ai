# blender/lighting.py
import bpy
import os

def setup_night_hdri(hdri_path, strength=0.15):
    world = bpy.context.scene.world
    world.use_nodes = True

    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()

    env = nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(hdri_path)

    bg = nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = strength

    out = nodes.new("ShaderNodeOutputWorld")

    links.new(env.outputs["Color"], bg.inputs["Color"])
    links.new(bg.outputs["Background"], out.inputs["Surface"])

    print("🌙 Night HDRI applied")
def add_moon_light():
    light = bpy.data.lights.new(name="Moon", type="SUN")
    light.energy = 1.5
    light.color = (0.6, 0.7, 1.0)  # bluish moonlight

    obj = bpy.data.objects.new("Moon", light)
    bpy.context.collection.objects.link(obj)

    obj.rotation_euler = (1.2, 0.0, -0.8)

    print("🌕 Moon light added")
def make_windows_emissive():
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue

        name = obj.name.lower()
        if "window" in name or "glass" in name:
            mat = bpy.data.materials.new(name="WindowGlow")
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            nodes.clear()

            emission = nodes.new("ShaderNodeEmission")
            emission.inputs["Color"].default_value = (1.0, 0.85, 0.6, 1)
            emission.inputs["Strength"].default_value = 8.0

            out = nodes.new("ShaderNodeOutputMaterial")
            mat.node_tree.links.new(
                emission.outputs["Emission"],
                out.inputs["Surface"]
            )

            obj.data.materials.clear()
            obj.data.materials.append(mat)

    print("💡 Interior window lights added")
def add_facade_lights():
    for i in range(4):
        light = bpy.data.lights.new(name=f"FacadeLight_{i}", type="AREA")
        light.energy = 250
        light.color = (1.0, 0.85, 0.7)

        obj = bpy.data.objects.new(f"FacadeLight_{i}", light)
        bpy.context.collection.objects.link(obj)

        obj.location = (2.5, i * 3.0, 1.5)
        obj.scale = (1.0, 0.3, 0.3)

    print("🏛️ Facade lights added")
def setup_night_render():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 256

    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"

    scene.view_settings.view_transform = "Filmic"
    scene.view_settings.look = "High Contrast"
    scene.view_settings.exposure = -1.0

    print("🎥 Night render settings applied")
