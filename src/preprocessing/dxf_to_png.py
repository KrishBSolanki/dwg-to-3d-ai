"""
DXF → PNG rasterizer for CubiCasa-style CNNs

This converts CAD geometry into a clean,
high-contrast, axis-aligned raster image.

Output is suitable for:
- CubiCasa5K
- floorplan CNNs
- semantic segmentation
"""

import ezdxf
import numpy as np
import cv2
from pathlib import Path


# ==============================
# CONFIG (CNN-FRIENDLY)
# ==============================

IMAGE_SIZE = 1024          # CubiCasa uses ~1024px
WALL_THICKNESS_PX = 8
DOOR_THICKNESS_PX = 4
WINDOW_THICKNESS_PX = 3
PADDING_RATIO = 0.05       # 5% border


# ==============================
# UTILS
# ==============================

def normalize_points(points, bbox, img_size):
    minx, miny, maxx, maxy = bbox
    scale = img_size / max(maxx - minx, maxy - miny)

    normalized = []
    for x, y in points:
        nx = int((x - minx) * scale)
        ny = int((maxy - y) * scale)  # invert Y
        normalized.append((nx, ny))

    return normalized


def compute_bbox(entities):
    xs, ys = [], []

    for e in entities:
        for x, y in e:
            xs.append(x)
            ys.append(y)

    return min(xs), min(ys), max(xs), max(ys)


# ==============================
# DXF PARSING
# ==============================

def extract_lines(doc):
    walls = []
    doors = []
    windows = []

    for e in doc.modelspace():
        if e.dxftype() in {"LINE", "LWPOLYLINE", "POLYLINE"}:
            layer = e.dxf.layer.lower()

            if e.dxftype() == "LINE":
                pts = [(e.dxf.start.x, e.dxf.start.y),
                       (e.dxf.end.x, e.dxf.end.y)]
            else:
                pts = [(p[0], p[1]) for p in e.get_points()]

            if "door" in layer:
                doors.append(pts)
            elif "window" in layer:
                windows.append(pts)
            else:
                walls.append(pts)

    return walls, doors, windows


# ==============================
# MAIN RASTERIZER
# ==============================

def rasterize_dxf(
    dxf_path: Path,
    output_png: Path
):
    print(f"🧠 Rasterizing DXF for CNN: {dxf_path}")

    doc = ezdxf.readfile(dxf_path)
    walls, doors, windows = extract_lines(doc)

    all_entities = walls + doors + windows
    if not all_entities:
        raise RuntimeError("No drawable geometry found")

    bbox = compute_bbox(all_entities)

    img = np.zeros(
        (IMAGE_SIZE, IMAGE_SIZE),
        dtype=np.uint8
    )

    # --------------------------
    # DRAW WALLS (WHITE)
    # --------------------------
    for poly in walls:
        pts = normalize_points(poly, bbox, IMAGE_SIZE)
        for i in range(len(pts) - 1):
            cv2.line(
                img,
                pts[i],
                pts[i + 1],
                color=255,
                thickness=WALL_THICKNESS_PX
            )

    # --------------------------
    # DRAW DOORS (GRAY)
    # --------------------------
    for poly in doors:
        pts = normalize_points(poly, bbox, IMAGE_SIZE)
        for i in range(len(pts) - 1):
            cv2.line(
                img,
                pts[i],
                pts[i + 1],
                color=180,
                thickness=DOOR_THICKNESS_PX
            )

    # --------------------------
    # DRAW WINDOWS (LIGHT GRAY)
    # --------------------------
    for poly in windows:
        pts = normalize_points(poly, bbox, IMAGE_SIZE)
        for i in range(len(pts) - 1):
            cv2.line(
                img,
                pts[i],
                pts[i + 1],
                color=120,
                thickness=WINDOW_THICKNESS_PX
            )

    # --------------------------
    # SAVE
    # --------------------------
    output_png.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_png), img)

    print(f"✅ Raster saved: {output_png}")
    return output_png


# ==============================
# CLI USAGE
# ==============================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python dxf_to_png.py input.dxf output.png")
        sys.exit(1)

    rasterize_dxf(
        Path(sys.argv[1]),
        Path(sys.argv[2])
    )
