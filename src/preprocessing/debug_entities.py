import ezdxf
from collections import Counter
from pathlib import Path

DXF_PATH = Path("data/input_dwg/sample20.dxf")

doc = ezdxf.readfile(str(DXF_PATH))
msp = doc.modelspace()

types = Counter()
layers = Counter()

for e in msp:
    types[e.dxftype()] += 1
    if hasattr(e.dxf, "layer"):
        layers[e.dxf.layer.lower()] += 1

print("\nEntity types:")
for k, v in types.items():
    print(k, ":", v)

print("\nLayers:")
for k, v in layers.items():
    print(k, ":", v)

