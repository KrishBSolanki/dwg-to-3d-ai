from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely.validation import make_valid


MIN_AREA = 20.0        # remove noise
SIMPLIFY_TOL = 2.0     # simplify edges


def clean_wall_polygons(polygons):
    """
    polygons: list of Nx2 numpy arrays
    returns: list of shapely Polygons (cleaned)
    """

    shapely_polys = []

    for poly in polygons:
        p = Polygon(poly)
        if not p.is_valid:
            p = make_valid(p)

        if p.area > MIN_AREA:
            shapely_polys.append(p)

    if not shapely_polys:
        return []

    # Merge overlapping walls
    merged = unary_union(shapely_polys)

    # Handle MultiPolygon result
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
