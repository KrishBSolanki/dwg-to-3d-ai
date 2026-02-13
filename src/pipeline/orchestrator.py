from pathlib import Path
import subprocess

from src.dwg_parser.dxf_to_structure import build_structure_from_dxf, BuildingStructure
from src.geometry.mesh_from_polygons import build_mesh_from_structure


# --------------------------------------------------------
# CONFIG
# --------------------------------------------------------

BLENDER_EXECUTABLE = "/Applications/Blender.app/Contents/MacOS/Blender"
BLENDER_RENDER_SCRIPT = "blender/render.py"


# --------------------------------------------------------
# MAIN PIPELINE
# --------------------------------------------------------

class CADToRenderPipeline:

    def __init__(self, input_path: Path, output_dir: Path):

        self.input_path = input_path
        self.output_dir = output_dir

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.glb_path = self.output_dir / "model.glb"

    # ----------------------------------------------------
    # STEP 1 — BUILD GEOMETRY
    # ----------------------------------------------------

    def build_geometry(self):

        print("📐 Parsing DXF...")

        structure = build_structure_from_dxf(self.input_path)

        # ----------------------------------------------------
        # 🔥 HARD SAFETY CHECK
        # ----------------------------------------------------
        if not isinstance(structure, BuildingStructure):
            raise TypeError(
                f"Expected BuildingStructure, got {type(structure)}. "
                "Fix dxf_to_structure.py return value."
            )

        mesh = build_mesh_from_structure(structure)

        if mesh is None:
            raise RuntimeError("Mesh generation failed")

        mesh.export(self.glb_path)

        print("✅ GLB exported:", self.glb_path)

    # ----------------------------------------------------
    # STEP 2 — BLENDER RENDER
    # ----------------------------------------------------

    def render_with_blender(self):

        print("🎥 Launching Blender...")

        command = [
            BLENDER_EXECUTABLE,
            "--background",
            "--python",
            BLENDER_RENDER_SCRIPT,
            "--",
            str(self.glb_path)
        ]

        subprocess.run(command, check=True)

        print("🖼 Rendering complete")

    # ----------------------------------------------------
    # RUN
    # ----------------------------------------------------

    def run(self):

        print("🚀 Starting Full CAD → Render Pipeline")

        self.build_geometry()
        self.render_with_blender()

        print("🎉 Pipeline finished")
