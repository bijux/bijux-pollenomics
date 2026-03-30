from __future__ import annotations

import math


COUNTRY_BOUNDARY_PROXIMITY_TOLERANCE = 0.15

def geometry_to_representative_point(geometry: dict[str, object]) -> tuple[float, float, str] | None:
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
    if len(coordinates) >= 2 and isinstance(coordinates[0], (int, float)) and isinstance(coordinates[1], (int, float)):
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


def multipolygon_representative_point(multipolygon: object) -> tuple[float, float] | None:
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
    for start, end in zip(ring, ring[1:]):
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
    for start, end in zip(outer_ring, outer_ring[1:]):
        if len(start) < 2 or len(end) < 2:
            return 0.0
        area += float(start[0]) * float(end[1]) - float(end[0]) * float(start[1])
    return abs(area) / 2


def point_in_bbox(
    longitude: float,
    latitude: float,
    bbox: tuple[float, float, float, float],
) -> bool:
    """Check whether a lon/lat pair falls inside a bbox."""
    min_longitude, min_latitude, max_longitude, max_latitude = bbox
    return min_longitude <= longitude <= max_longitude and min_latitude <= latitude <= max_latitude


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
