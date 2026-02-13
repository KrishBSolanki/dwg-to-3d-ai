from shapely.geometry import LineString
from shapely.ops import polygonize, unary_union


MIN_ROOM_AREA = 0.5  # square meters


def detect_room_loops(walls):

    # Convert wall segments into Shapely lines
    lines = []

    for wall in walls:
        line = LineString([wall.start, wall.end])
        lines.append(line)

    if not lines:
        return []

    # Merge all lines into planar graph
    merged = unary_union(lines)

    # Extract closed polygons (faces)
    polygons = list(polygonize(merged))

    # Filter small garbage faces
    clean_polygons = [
        p for p in polygons
        if p.is_valid and p.area > MIN_ROOM_AREA
    ]

    return clean_polygons
