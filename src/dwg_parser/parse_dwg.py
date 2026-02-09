
# import ezdxf
# import json
# from pathlib import Path


# IGNORE_ENTITY_TYPES = ["TEXT", "MTEXT", "DIMENSION", "HATCH", "INSERT"]


# def parse_dwg(file_path):
#     doc = ezdxf.readfile(file_path)
#     msp = doc.modelspace()

#     entities = []
#     layers_found = set()
#     ignored_count = 0

#     for e in msp:
#         etype = e.dxftype()

#         # Ignore noise entities
#         if etype in IGNORE_ENTITY_TYPES:
#             ignored_count += 1
#             continue

#         layer = e.dxf.layer.lower() if hasattr(e.dxf, "layer") else "default"
#         layers_found.add(layer)

#         # -------- LINE --------
#         if etype == "LINE":
#             entities.append({
#                 "type": "LINE",
#                 "start": [float(e.dxf.start.x), float(e.dxf.start.y), 0],
#                 "end": [float(e.dxf.end.x), float(e.dxf.end.y), 0],
#                 "layer": layer
#             })

#         # -------- POLYLINE / LWPOLYLINE --------
#         elif etype in ["LWPOLYLINE", "POLYLINE"]:
#             points = []
#             for p in e.get_points():
#                 points.append([float(p[0]), float(p[1]), 0])

#             entities.append({
#                 "type": "POLYLINE",
#                 "points": points,
#                 "closed": bool(e.closed),
#                 "layer": layer
#             })

#         # -------- SPLINE --------
#         elif etype == "SPLINE":
#             points = []
#             for p in e.control_points:
#                 points.append([float(p[0]), float(p[1]), 0])

#             entities.append({
#                 "type": "SPLINE",
#                 "points": points,
#                 "layer": layer
#             })

#         else:
#             ignored_count += 1
#             continue

#     print("Parsed entities:", len(entities))
#     print("Ignored entities:", ignored_count)
#     print("DXF Layers found:", layers_found)

#     return entities


# def save_json(data, path):
#     Path(path).parent.mkdir(parents=True, exist_ok=True)
#     with open(path, "w") as f:
#         json.dump(data, f, indent=2)
import ezdxf
from pathlib import Path
from typing import List, Dict

# =========================
# CONFIG
# =========================

IGNORE_ENTITY_TYPES = {
    "TEXT", "MTEXT", "DIMENSION", "HATCH", "INSERT", "LEADER"
}

# Industry-style layer hints
LAYER_KEYWORDS = {
    "wall": ["a-wall", "wall", "partition"],
    "door": ["a-door", "door"],
    "window": ["a-win", "window", "glaz"],
    "floor": ["a-floor", "floor", "slab"],
    "furniture": ["a-furn", "furniture"],
}

# =========================
# HELPERS
# =========================

def infer_semantic_type(layer_name: str):
    lname = layer_name.lower()
    for semantic, keys in LAYER_KEYWORDS.items():
        if any(k in lname for k in keys):
            return semantic
    return "unknown"


# =========================
# MAIN PARSER
# =========================

def parse_dwg(file_path: Path) -> List[Dict]:
    doc = ezdxf.readfile(str(file_path))
    msp = doc.modelspace()

    entities = []
    ignored = 0

    for e in msp:
        etype = e.dxftype()

        if etype in IGNORE_ENTITY_TYPES:
            ignored += 1
            continue

        layer = e.dxf.layer.lower() if hasattr(e.dxf, "layer") else "default"
        semantic = infer_semantic_type(layer)

        base = {
            "entity_type": etype,
            "layer": layer,
            "semantic": semantic,
            "confidence": 0.7 if semantic != "unknown" else 0.2
        }

        # -------- LINE --------
        if etype == "LINE":
            base["geometry"] = {
                "type": "line",
                "points": [
                    (float(e.dxf.start.x), float(e.dxf.start.y)),
                    (float(e.dxf.end.x), float(e.dxf.end.y))
                ]
            }
            entities.append(base)

        # -------- POLYLINE --------
        elif etype in {"LWPOLYLINE", "POLYLINE"}:
            pts = [(float(p[0]), float(p[1])) for p in e.get_points()]
            if len(pts) < 2:
                continue

            base["geometry"] = {
                "type": "polyline",
                "points": pts,
                "closed": bool(e.closed)
            }
            entities.append(base)

        # -------- SPLINE --------
        elif etype == "SPLINE":
            pts = [(float(p[0]), float(p[1])) for p in e.control_points]
            if len(pts) < 2:
                continue

            base["geometry"] = {
                "type": "spline",
                "points": pts
            }
            entities.append(base)

        else:
            ignored += 1

    print(f"✔ Parsed entities: {len(entities)}")
    print(f"✖ Ignored entities: {ignored}")

    return entities
