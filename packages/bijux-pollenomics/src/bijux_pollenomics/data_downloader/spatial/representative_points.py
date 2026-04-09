from __future__ import annotations

from itertools import pairwise


def geometry_to_representative_point(
    geometry: dict[str, object],
) -> tuple[float, float, str] | None:
    """Reduce a GeoJSON geometry to one representative point for map display."""
    geometry_type = str(geometry.get("type", "")).strip()
    coordinates = geometry.get("coordinates")
    if coordinates is None:
        return None

    if geometry_type == "Point":
        longitude, latitude = coordinates
        return float(longitude), float(latitude), geometry_type
    if geometry_type == "Polygon":
        representative_point = polygon_representative_point(coordinates)
        if representative_point is not None:
            return (*representative_point, geometry_type)
    if geometry_type == "MultiPolygon":
        representative_point = multipolygon_representative_point(coordinates)
        if representative_point is not None:
            return (*representative_point, geometry_type)

    flattened = flatten_positions(coordinates)
    if not flattened:
        return None

    longitudes = [position[0] for position in flattened]
    latitudes = [position[1] for position in flattened]
    return (
        (min(longitudes) + max(longitudes)) / 2,
        (min(latitudes) + max(latitudes)) / 2,
        geometry_type,
    )


def flatten_positions(coordinates: object) -> list[tuple[float, float]]:
    """Flatten nested GeoJSON coordinate arrays into lon/lat pairs."""
    if not isinstance(coordinates, list):
        return []
    if (
        len(coordinates) >= 2
        and isinstance(coordinates[0], (int, float))
        and isinstance(coordinates[1], (int, float))
    ):
        return [(float(coordinates[0]), float(coordinates[1]))]

    positions: list[tuple[float, float]] = []
    for item in coordinates:
        positions.extend(flatten_positions(item))
    return positions


def polygon_representative_point(polygon: object) -> tuple[float, float] | None:
    """Return a representative point for one polygon using its outer ring centroid when possible."""
    if not isinstance(polygon, list) or not polygon:
        return None
    outer_ring = polygon[0]
    if not isinstance(outer_ring, list) or len(outer_ring) < 4:
        return None

    centroid = ring_centroid(outer_ring)
    if centroid is not None and point_in_polygon(centroid[0], centroid[1], polygon):
        return centroid

    flattened = flatten_positions(polygon)
    if not flattened:
        return None
    average_longitude = sum(longitude for longitude, _ in flattened) / len(flattened)
    average_latitude = sum(latitude for _, latitude in flattened) / len(flattened)
    if point_in_polygon(average_longitude, average_latitude, polygon):
        return average_longitude, average_latitude

    return flattened[0]


def multipolygon_representative_point(
    multipolygon: object,
) -> tuple[float, float] | None:
    """Return a representative point from the largest polygon inside a multipolygon."""
    if not isinstance(multipolygon, list) or not multipolygon:
        return None
    polygon_candidates = [
        (polygon_area(polygon[0]), polygon)
        for polygon in multipolygon
        if isinstance(polygon, list) and polygon and isinstance(polygon[0], list)
    ]
    if not polygon_candidates:
        return None
    _, largest_polygon = max(polygon_candidates, key=lambda item: item[0])
    return polygon_representative_point(largest_polygon)


def ring_centroid(ring: list[object]) -> tuple[float, float] | None:
    """Return the centroid of a closed linear ring using the shoelace formula."""
    if len(ring) < 4:
        return None
    twice_area = 0.0
    centroid_x = 0.0
    centroid_y = 0.0
    for start, end in pairwise(ring):
        if len(start) < 2 or len(end) < 2:
            return None
        cross = float(start[0]) * float(end[1]) - float(end[0]) * float(start[1])
        twice_area += cross
        centroid_x += (float(start[0]) + float(end[0])) * cross
        centroid_y += (float(start[1]) + float(end[1])) * cross
    if abs(twice_area) < 1e-12:
        return None
    return centroid_x / (3 * twice_area), centroid_y / (3 * twice_area)


def polygon_area(outer_ring: list[object]) -> float:
    """Return the absolute area of one outer polygon ring."""
    if len(outer_ring) < 4:
        return 0.0
    area = 0.0
    for start, end in pairwise(outer_ring):
        if len(start) < 2 or len(end) < 2:
            return 0.0
        area += float(start[0]) * float(end[1]) - float(end[0]) * float(start[1])
    return abs(area) / 2


def point_in_polygon(longitude: float, latitude: float, polygon: list[object]) -> bool:
    """Ray-casting point-in-polygon with support for holes."""
    if not polygon:
        return False
    if not point_in_ring(longitude, latitude, polygon[0]):
        return False
    return all(not point_in_ring(longitude, latitude, hole) for hole in polygon[1:])


def point_in_ring(longitude: float, latitude: float, ring: list[object]) -> bool:
    """Return True when a point is inside a linear ring."""
    inside = False
    previous = ring[-1]
    for current in ring:
        x1, y1 = previous[0], previous[1]
        x2, y2 = current[0], current[1]
        crosses = ((y1 > latitude) != (y2 > latitude)) and (
            longitude < (x2 - x1) * (latitude - y1) / ((y2 - y1) or 1e-12) + x1
        )
        if crosses:
            inside = not inside
        previous = current
    return inside


__all__ = [
    "flatten_positions",
    "geometry_to_representative_point",
    "multipolygon_representative_point",
    "polygon_area",
    "polygon_representative_point",
    "ring_centroid",
]
