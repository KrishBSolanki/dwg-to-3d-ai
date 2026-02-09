# from dwg_parser.parse_dwg import parse_dwg, save_json
# from preprocessing.extract_geometry import geometry_to_3d
# from renderer.render_obj import save_obj
# from renderer.render_png import render_png
# from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parent.parent

# INPUT_DWG =  "data/input_dwg/sample.dxf"
# JSON_OUT =  "data/processed/geometry.json"
# OBJ_OUT =  "data/output_3d/model.obj"
# PNG_OUT =  "data/output_3d/model.png"


# def main():
#     print("Parsing DWG...")
#     entities = parse_dwg(str(INPUT_DWG))
#     save_json(entities, JSON_OUT)

#     print("Extracting geometry...")
#     vertices = geometry_to_3d(JSON_OUT)

#     print("Saving OBJ...")
#     save_obj(vertices, OBJ_OUT)

#     print("Rendering PNG...")
#     render_png(OBJ_OUT, PNG_OUT)

#     print("Pipeline complete!")


# if __name__ == "__main__":
#     main()
import sys
from pathlib import Path

from src.dwg_parser.parse_dwg import parse_dwg
from src.preprocessing.extract_geometry import extract_walls_floors_doors_windows
from src.renderer.mesh_reconstruction import build_mesh


BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = (BASE_DIR / "../data/input_dwg").resolve()
OUTPUT_DIR = (BASE_DIR / "../data/output_3d").resolve()

INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_pipeline(dxf_path: Path):
    print("📂 Loading DXF:", dxf_path)

    entities = parse_dwg(dxf_path)
    if not entities:
        raise RuntimeError("No entities parsed")

    geometry = extract_walls_floors_doors_windows(entities)
    if not geometry["walls"]:
        raise RuntimeError("No walls detected")

    output_path = OUTPUT_DIR / dxf_path.stem
    build_mesh(geometry, output_path)

    print("🎉 Pipeline completed successfully!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_dxf>")
        sys.exit(1)

    dxf_file = Path(sys.argv[1])
    if not dxf_file.exists():
        print("❌ File not found:", dxf_file)
        sys.exit(1)

    run_pipeline(dxf_file)
