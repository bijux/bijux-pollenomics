from __future__ import annotations

import math


COUNTRY_BOUNDARY_PROXIMITY_TOLERANCE = 0.15


def classify_country(
    longitude: float,
    latitude: float,
    country_boundaries: dict[str, dict[str, object]],
) -> str:
    """Assign a point to one of the Nordic countries based on polygon containment."""
    for country, payload in country_boundaries.items():
        for feature in payload.get("features", []):
            geometry = feature.get("geometry", {})
            if isinstance(geometry, dict) and point_in_geometry(longitude, latitude, geometry):
                return country

    for country, payload in country_boundaries.items():
        for feature in payload.get("features", []):
            geometry = feature.get("geometry", {})
            if isinstance(geometry, dict) and point_in_geometry_ignoring_holes(longitude, latitude, geometry):
                return country

    nearest_country = nearest_country_by_boundary_distance(
        longitude=longitude,
        latitude=latitude,
        country_boundaries=country_boundaries,
        max_distance=COUNTRY_BOUNDARY_PROXIMITY_TOLERANCE,
    )
    if nearest_country:
        return nearest_country
    return ""


def point_in_geometry(longitude: float, latitude: float, geometry: dict[str, object]) -> bool:
    """Check whether a point falls inside a GeoJSON Polygon or MultiPolygon."""
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])
    if geometry_type == "Polygon":
        return point_in_polygon(longitude, latitude, coordinates)
    if geometry_type == "MultiPolygon":
        return any(point_in_polygon(longitude, latitude, polygon) for polygon in coordinates)
    return False


def point_in_geometry_ignoring_holes(longitude: float, latitude: float, geometry: dict[str, object]) -> bool:
    """Check containment using only polygon outer rings for country-assignment fallbacks."""
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])
    if geometry_type == "Polygon":
        return point_in_outer_ring(longitude, latitude, coordinates)
    if geometry_type == "MultiPolygon":
        return any(point_in_outer_ring(longitude, latitude, polygon) for polygon in coordinates)
    return False


def point_in_polygon(longitude: float, latitude: float, polygon: list[object]) -> bool:
    """Ray-casting point-in-polygon with support for holes."""
    if not polygon:
        return False
    if not point_in_ring(longitude, latitude, polygon[0]):
        return False
    for hole in polygon[1:]:
        if point_in_ring(longitude, latitude, hole):
            return False
    return True


def point_in_outer_ring(longitude: float, latitude: float, polygon: list[object]) -> bool:
    """Check whether a point lies inside the outer ring of one polygon."""
    if not polygon:
        return False
    return point_in_ring(longitude, latitude, polygon[0])


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


def nearest_country_by_boundary_distance(
    longitude: float,
    latitude: float,
    country_boundaries: dict[str, dict[str, object]],
    max_distance: float,
) -> str:
    """Return the nearest country when a point falls just outside tracked boundaries."""
    nearest_country = ""
    nearest_distance = math.inf
    for country, payload in country_boundaries.items():
        for feature in payload.get("features", []):
            geometry = feature.get("geometry", {})
            if not isinstance(geometry, dict):
                continue
            distance = geometry_boundary_distance(longitude, latitude, geometry)
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_country = country
    if nearest_distance <= max_distance:
        return nearest_country
    return ""


def geometry_boundary_distance(longitude: float, latitude: float, geometry: dict[str, object]) -> float:
    """Return the minimum distance from a point to a polygon or multipolygon boundary."""
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])
    if geometry_type == "Polygon":
        return polygon_boundary_distance(longitude, latitude, coordinates)
    if geometry_type == "MultiPolygon":
        distances = [
            polygon_boundary_distance(longitude, latitude, polygon)
            for polygon in coordinates
            if isinstance(polygon, list)
        ]
        return min(distances) if distances else math.inf
    return math.inf


def polygon_boundary_distance(longitude: float, latitude: float, polygon: list[object]) -> float:
    """Return the minimum distance from a point to any ring in one polygon."""
    distances = [
        ring_boundary_distance(longitude, latitude, ring)
        for ring in polygon
        if isinstance(ring, list) and ring
    ]
    return min(distances) if distances else math.inf


def ring_boundary_distance(longitude: float, latitude: float, ring: list[object]) -> float:
    """Return the minimum distance from a point to one linear-ring edge."""
    if len(ring) < 2:
        return math.inf
    return min(
        point_to_segment_distance(
            longitude,
            latitude,
            float(start[0]),
            float(start[1]),
            float(end[0]),
            float(end[1]),
        )
        for start, end in zip(ring, ring[1:])
        if len(start) >= 2 and len(end) >= 2
    )


def point_to_segment_distance(
    px: float,
    py: float,
    ax: float,
    ay: float,
    bx: float,
    by: float,
) -> float:
    """Return the Euclidean distance from a point to one line segment in lon/lat degrees."""
    dx = bx - ax
    dy = by - ay
    if dx == 0.0 and dy == 0.0:
        return math.hypot(px - ax, py - ay)

    projection = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    projection = max(0.0, min(1.0, projection))
    closest_x = ax + projection * dx
    closest_y = ay + projection * dy
    return math.hypot(px - closest_x, py - closest_y)


__all__ = [
    "COUNTRY_BOUNDARY_PROXIMITY_TOLERANCE",
    "classify_country",
    "geometry_boundary_distance",
    "nearest_country_by_boundary_distance",
    "point_in_geometry",
    "point_in_geometry_ignoring_holes",
    "point_in_outer_ring",
    "point_in_polygon",
    "point_in_ring",
    "point_to_segment_distance",
    "polygon_boundary_distance",
    "ring_boundary_distance",
]
