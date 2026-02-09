
# from shapely.geometry import Polygon, MultiPolygon, LineString


# # ======================
# # FLEXIBLE LAYER DEFINITIONS
# # ======================

# WALL_LAYERS = ["wall", "a-wall", "partition", "a-part"]
# FLOOR_LAYERS = ["floor", "slab", "a-flor"]
# DOOR_LAYERS = ["door", "a-door", "opening"]
# WINDOW_LAYERS = ["window", "a-win", "glaz"]


# # ======================
# # MAIN FUNCTION
# # ======================

# def extract_walls_floors_doors_windows(entities):
#     walls = []
#     floors = []
#     doors = []
#     windows = []

#     for item in entities:
#         layer = item.get("layer", "").lower()
#         etype = item.get("type")

#         pts = []

#         if etype == "LINE":
#             x1, y1, _ = item["start"]
#             x2, y2, _ = item["end"]
#             pts = [(x1, y1), (x2, y2)]

#         elif etype in ["POLYLINE", "LWPOLYLINE", "SPLINE"]:
#             pts = [(p[0], p[1]) for p in item.get("points", [])]

#         if len(pts) < 2:
#             continue

#         # ------------------
#         # WALLS (store layer info!)
#         # ------------------
#         if any(k in layer for k in WALL_LAYERS):
#             walls.append({
#                 "points": pts,
#                 "layer": layer
#             })

#         # ------------------
#         # FLOORS
#         # ------------------
#         elif any(k in layer for k in FLOOR_LAYERS) and etype in ["POLYLINE", "LWPOLYLINE"]:
#             if not item.get("closed", False):
#                 continue
#             try:
#                 poly = Polygon(pts)
#                 if poly.is_valid and poly.area > 10:
#                     floors.append(list(poly.exterior.coords))
#             except:
#                 continue

#         # ------------------
#         # DOORS
#         # ------------------
#         elif any(k in layer for k in DOOR_LAYERS):
#             doors.append(pts)

#         # ------------------
#         # WINDOWS
#         # ------------------
#         elif any(k in layer for k in WINDOW_LAYERS):
#             windows.append(pts)

#     print("Filtered walls:", len(walls))
#     print("Filtered floors:", len(floors))
#     print("Filtered doors:", len(doors))
#     print("Filtered windows:", len(windows))

#     return {
#         "walls": walls,
#         "floors": floors,
#         "doors": doors,
#         "windows": windows
#     }
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union


# =========================================================
# UTILITIES
# =========================================================

def is_closed(points, tol=1e-6):
    if len(points) < 3:
        return False
    x1, y1 = points[0]
    x2, y2 = points[-1]
    return abs(x1 - x2) < tol and abs(y1 - y2) < tol


def polygon_from_points(points):
    try:
        poly = Polygon(points)
        if poly.is_valid and poly.area > 10:
            return poly
    except Exception:
        pass
    return None


def edges_from_boundary(coords):
    edges = []
    for i in range(len(coords) - 1):
        edges.append([coords[i], coords[i + 1]])
    return edges


def segment_length(seg):
    (x1, y1), (x2, y2) = seg
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


# =========================================================
# CORE EXTRACTION WITH DOOR/WINDOW INFERENCE
# =========================================================

def extract_walls_floors_doors_windows(entities):
    walls = []
    doors = []
    windows = []
    floor_polygons = []

    inferred_walls = []
    inferred_rooms = []

    ignored = 0

    # -----------------------------------------------------
    # PASS 1: SEMANTIC EXTRACTION
    # -----------------------------------------------------
    for e in entities:
        semantic = e["semantic"]
        geom = e["geometry"]
        pts = geom.get("points", [])

        if len(pts) < 2:
            continue

        if semantic == "wall":
            walls.append({
                "points": pts,
                "confidence": e["confidence"],
                "layer": e["layer"],
                "inferred": False
            })

        elif semantic == "door":
            doors.append({
                "points": pts,
                "confidence": e["confidence"],
                "inferred": False
            })

        elif semantic == "window":
            windows.append({
                "points": pts,
                "confidence": e["confidence"],
                "inferred": False
            })

        elif semantic == "floor" and geom.get("closed", False):
            poly = polygon_from_points(pts)
            if poly:
                floor_polygons.append(poly)

        else:
            ignored += 1

    # -----------------------------------------------------
    # PASS 2: GEOMETRY-BASED WALL / ROOM INFERENCE
    # -----------------------------------------------------
    if not walls:
        print("⚠ No semantic walls found. Using geometry-based inference.")

        closed_polys = []

        for e in entities:
            pts = e["geometry"].get("points", [])
            if is_closed(pts):
                poly = polygon_from_points(pts)
                if poly:
                    closed_polys.append(poly)

        if closed_polys:
            footprint = max(closed_polys, key=lambda p: p.area)
            floor_polygons.append(footprint)

            inferred_rooms.append(list(footprint.exterior.coords))

            boundary_edges = edges_from_boundary(list(footprint.exterior.coords))

            # -------------------------------------------------
            # DOOR & WINDOW INFERENCE FROM BOUNDARY EDGES
            # -------------------------------------------------
            for edge in boundary_edges:
                length = segment_length(edge)

                # Typical door width: ~0.7–1.2 m (CAD units vary → relative rule)
                if 0.6 < length < 1.4:
                    doors.append({
                        "points": edge,
                        "confidence": 0.55,
                        "inferred": True
                    })

                # Typical window width: ~0.4–2.0 m but thinner than doors
                elif 0.3 < length <= 0.6:
                    windows.append({
                        "points": edge,
                        "confidence": 0.5,
                        "inferred": True
                    })

                else:
                    inferred_walls.append({
                        "points": edge,
                        "confidence": 0.65,
                        "layer": "inferred",
                        "inferred": True,
                        "curved": True
                    })

    # -----------------------------------------------------
    # FLOOR + ROOM LOGIC
    # -----------------------------------------------------
    floor_boundary = []
    rooms = []

    if floor_polygons:
        merged = unary_union(floor_polygons)

        if merged.geom_type == "Polygon":
            floor_boundary = list(merged.exterior.coords)
        else:
            largest = max(merged.geoms, key=lambda p: p.area)
            floor_boundary = list(largest.exterior.coords)

        for poly in floor_polygons:
            if poly.area <= Polygon(floor_boundary).area:
                rooms.append(list(poly.exterior.coords))

    # Merge inferred geometry
    walls.extend(inferred_walls)
    rooms.extend(inferred_rooms)

    # -----------------------------------------------------
    # DEBUG OUTPUT
    # -----------------------------------------------------
    print("✔ Walls:", len(walls))
    print("✔ Doors:", len(doors))
    print("✔ Windows:", len(windows))
    print("✔ Rooms:", len(rooms))
    print("✔ Floor boundary:", bool(floor_boundary))
    print("✖ Ignored:", ignored)

    return {
        "walls": walls,
        "floors": [floor_boundary] if floor_boundary else [],
        "rooms": rooms,
        "doors": doors,
        "windows": windows
    }
