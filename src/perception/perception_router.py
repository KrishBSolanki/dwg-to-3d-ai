"""
Routes floorplan understanding between:
- Vision-based (CubiCasa)
- Geometry-based (DXF fallback)
"""

from preprocessing.extract_geometry import extract_walls_floors_doors_windows

def run_perception(
    source_type: str,
    entities=None,
    raster_path: str | None = None
):
    """
    source_type:
        - "geometry" → DXF entities
        - "vision"   → raster PNG (CubiCasa later)
    """

    if source_type == "geometry":
        return extract_walls_floors_doors_windows(entities)

    elif source_type == "vision":
        raise NotImplementedError(
            "CubiCasa inference not wired yet"
        )

    else:
        raise ValueError(f"Unknown perception type: {source_type}")
