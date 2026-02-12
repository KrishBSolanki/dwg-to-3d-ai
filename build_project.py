import sys
from pathlib import Path
from src.pipeline.orchestrator import CADToRenderPipeline


if __name__ == "__main__":

    if len(sys.argv) < 3:
        print("Usage: python build_project.py input.dxf output_folder")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_folder = Path(sys.argv[2])

    pipeline = CADToRenderPipeline(input_file, output_folder)
    pipeline.run()
