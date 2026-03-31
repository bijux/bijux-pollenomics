from __future__ import annotations

from .spatial.bboxes import point_in_bbox as point_in_bbox
from .spatial.country_classification import (
    COUNTRY_BOUNDARY_PROXIMITY_TOLERANCE as COUNTRY_BOUNDARY_PROXIMITY_TOLERANCE,
    classify_country as classify_country,
    point_in_geometry as point_in_geometry,
)
from .spatial.representative_points import (
    flatten_positions as flatten_positions,
    geometry_to_representative_point as geometry_to_representative_point,
)


def geometry_bbox(geometry: dict[str, object]) -> tuple[float, float, float, float]:
    """Return the bounding box of a GeoJSON geometry."""
    flattened = flatten_positions(geometry.get("coordinates", []))
    longitudes = [position[0] for position in flattened]
    latitudes = [position[1] for position in flattened]
    return min(longitudes), min(latitudes), max(longitudes), max(latitudes)


def build_grid_cell_geometry(
    min_longitude: float,
    min_latitude: float,
    cell_size: float,
) -> dict[str, object]:
    """Build a rectangular polygon used for density aggregation."""
    max_longitude = min_longitude + cell_size
    max_latitude = min_latitude + cell_size
    return {
        "type": "Polygon",
        "coordinates": [[
            [min_longitude, min_latitude],
            [max_longitude, min_latitude],
            [max_longitude, max_latitude],
            [min_longitude, max_latitude],
            [min_longitude, min_latitude],
        ]],
    }


def grid_cell_relevant(ring: list[object], geometry: dict[str, object]) -> bool:
    """Keep a density cell when its center or corners overlap the Sweden boundary."""
    center_longitude = (ring[0][0] + ring[2][0]) / 2
    center_latitude = (ring[0][1] + ring[2][1]) / 2
    if point_in_geometry(center_longitude, center_latitude, geometry):
        return True
    return any(point_in_geometry(point[0], point[1], geometry) for point in ring[:-1])


__all__ = [
    "COUNTRY_BOUNDARY_PROXIMITY_TOLERANCE",
    "build_grid_cell_geometry",
    "classify_country",
    "geometry_bbox",
    "geometry_to_representative_point",
    "grid_cell_relevant",
    "point_in_bbox",
    "point_in_geometry",
]
