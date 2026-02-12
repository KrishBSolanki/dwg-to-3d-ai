
# import sys
# from pathlib import Path

# from src.perception.cubicasa.infer import CubiCasaInference
# from src.perception.cubicasa.postprocess import build_structure as build_structure_from_ai
# from src.geometry.mesh_from_polygons import build_mesh_from_structure

# # NEW IMPORT
# from src.dwg_parser.dxf_to_structure import build_structure_from_dxf


# def run_pipeline(input_path: str, output_path: str):

#     print("🚀 Starting CAD → 3D pipeline")

#     input_file = Path(input_path)

#     # ==============================
#     # 1️⃣ Decide Pipeline
#     # ==============================

#     if input_file.suffix.lower() == ".dxf":
#         print("📐 DXF detected → Using CAD pipeline")
#         structure = build_structure_from_dxf(input_file)

#     else:
#         print("🧠 Image detected → Using AI segmentation pipeline")

#         infer = CubiCasaInference()
#         class_map = infer.predict(input_path)

#         print("✅ Segmentation complete")

#         structure = build_structure_from_ai(class_map)

#     # ==============================
#     # 2️⃣ Structure → Mesh
#     # ==============================

#     print("✅ Structure built")
#     print("Walls:", len(structure.walls))

#     mesh = build_mesh_from_structure(structure)

#     if mesh is None:
#         print("❌ No mesh generated")
#         return

#     # ==============================
#     # 3️⃣ Export
#     # ==============================

#     mesh.export(output_path)
#     print(f"🎉 GLB exported to: {output_path}")


# if __name__ == "__main__":

#     if len(sys.argv) < 3:
#         print("Usage: python -m src.main input_file output.glb")
#         sys.exit(1)

#     input_file = sys.argv[1]
#     output_file = sys.argv[2]

#     run_pipeline(input_file, output_file)
import sys
from pathlib import Path

# -------------------------------
# CAD PIPELINE
# -------------------------------
from src.dwg_parser.dxf_to_structure import build_structure_from_dxf

# -------------------------------
# AI PIPELINE
# -------------------------------
from src.perception.cubicasa.infer import CubiCasaInference
from src.perception.cubicasa.postprocess import build_structure as build_structure_from_ai

# -------------------------------
# UNIFIED MESH BUILDER
# -------------------------------
from src.geometry.mesh_from_polygons import build_mesh_from_structure


def run_pipeline(input_path: str, output_path: str):

    print("🚀 Starting CAD / AI → 3D pipeline")

    input_file = Path(input_path)
    output_file = Path(output_path)

    # ==================================================
    # 1️⃣ SELECT PIPELINE (DXF or AI Image)
    # ==================================================

    if input_file.suffix.lower() == ".dxf":

        print("📐 DXF detected → Using CAD pipeline")
        structure = build_structure_from_dxf(input_file)

    else:

        print("🧠 Image detected → Using AI segmentation pipeline")

        infer = CubiCasaInference()
        class_map = infer.predict(str(input_file))

        print("✅ Segmentation complete")

        structure = build_structure_from_ai(class_map)

    # ==================================================
    # 2️⃣ STRUCTURE → MESH (Unified Builder)
    # ==================================================

    if structure is None:
        print("❌ No structure generated")
        return

    print("🏗 Building mesh from unified structure...")
    print("🧱 Walls:", len(structure.walls))

    mesh = build_mesh_from_structure(structure)

    if mesh is None:
        print("❌ Mesh generation failed")
        return

    # ==================================================
    # 3️⃣ EXPORT
    # ==================================================

    output_file.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(output_file)

    print(f"🎉 GLB exported: {output_file}")


# ==================================================
# ENTRY POINT
# ==================================================

if __name__ == "__main__":

    if len(sys.argv) < 3:
        print("Usage: python -m src.main input_file output.glb")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    run_pipeline(input_file, output_file)
