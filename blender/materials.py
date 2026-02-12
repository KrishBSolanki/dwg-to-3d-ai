import bpy


# ---------------------------------------------------
# WINDOW GLASS MATERIAL (Blender 4.x Compatible)
# ---------------------------------------------------

def create_window_glass_material(night=False):

    mat = bpy.data.materials.new(name="WindowGlass")
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Principled BSDF (Blender 4.x)
    principled = nodes.new(type="ShaderNodeBsdfPrincipled")
    principled.location = (0, 0)

    # Transparent look
    principled.inputs["Base Color"].default_value = (0.8, 0.9, 1.0, 1.0)
    principled.inputs["Roughness"].default_value = 0.05

    # Blender 4.x transmission input
    if "Transmission Weight" in principled.inputs:
        principled.inputs["Transmission Weight"].default_value = 1.0

    principled.inputs["IOR"].default_value = 1.45

    # Emission glow for night renders
    if night:
        if "Emission Strength" in principled.inputs:
            principled.inputs["Emission Strength"].default_value = 0.2

    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (200, 0)

    links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    return mat
