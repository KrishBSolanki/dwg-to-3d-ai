import trimesh
import numpy as np
from pathlib import Path


def render_preview(glb_path, output_image):
    scene = trimesh.load(glb_path, force="scene")

    # -----------------------------
    # CAMERA SETUP
    # -----------------------------
    scene.set_camera(
        angles=(np.radians(55), 0, np.radians(40)),
        distance=6.0,
        center=scene.centroid
    )

    # -----------------------------
    # LIGHTING SETUP (CORRECT WAY)
    # -----------------------------
    scene.lights = [
        trimesh.scene.lighting.DirectionalLight(
            color=[255, 255, 255],
            intensity=2.5
        ),
        trimesh.scene.lighting.DirectionalLight(
            color=[200, 200, 200],
            intensity=1.2
        ),
        trimesh.scene.lighting.DirectionalLight(
            color=[180, 180, 180],
            intensity=0.6
        )
    ]

    # -----------------------------
    # RENDER
    # -----------------------------
    png = scene.save_image(
        resolution=(1920, 1080),
        visible=True
    )

    Path(output_image).write_bytes(png)
    print("📸 Preview rendered:", output_image)


if __name__ == "__main__":
    render_preview(
        "data/output_3d/sample31.glb",
        "data/output_3d/sample31_preview.png"
    )
