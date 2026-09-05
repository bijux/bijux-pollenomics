from __future__ import annotations

from ...core.geojson import JsonObject, LinearRing
from .country_classification import point_in_geometry
from .representative_points import flatten_positions


def geometry_bbox(geometry: JsonObject) -> tuple[float, float, float, float]:
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
        "coordinates": [
            [
                [min_longitude, min_latitude],
                [max_longitude, min_latitude],
                [max_longitude, max_latitude],
                [min_longitude, max_latitude],
                [min_longitude, min_latitude],
            ]
        ],
    }


def grid_cell_relevant(ring: LinearRing, geometry: JsonObject) -> bool:
    """Keep a density cell when its center or corners overlap the Sweden boundary."""
    center_longitude = (ring[0][0] + ring[2][0]) / 2
    center_latitude = (ring[0][1] + ring[2][1]) / 2
    if point_in_geometry(center_longitude, center_latitude, geometry):
        return True
    return any(point_in_geometry(point[0], point[1], geometry) for point in ring[:-1])


__all__ = ["build_grid_cell_geometry", "geometry_bbox", "grid_cell_relevant"]
