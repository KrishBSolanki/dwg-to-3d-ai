from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely.validation import make_valid

MIN_AREA = 0.01        # m² after scaling (small noise removal)
SIMPLIFY_TOL = 0.001   # meters


def clean_wall_polygons(polygons):
    """
    polygons: list of Shapely Polygons (already scaled to meters)
    returns: list of cleaned Shapely Polygons
    """

    shapely_polys = []

    for p in polygons:

        if not p.is_valid:
            p = make_valid(p)

        if p.area > MIN_AREA:
            shapely_polys.append(p)

    if not shapely_polys:
        return []

    # Merge overlapping & touching walls
    merged = unary_union(shapely_polys)

    if isinstance(merged, Polygon):
        merged = [merged]
    elif isinstance(merged, MultiPolygon):
        merged = list(merged.geoms)
    else:
        return []

    cleaned = []

    for p in merged:
        simplified = p.simplify(SIMPLIFY_TOL, preserve_topology=True)

        if simplified.area > MIN_AREA:
            cleaned.append(simplified)

    return cleaned
