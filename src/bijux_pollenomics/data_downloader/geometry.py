from __future__ import annotations


def geometry_to_representative_point(geometry: dict[str, object]) -> tuple[float, float, str] | None:
    """Reduce a GeoJSON geometry to one representative point for map display."""
    geometry_type = str(geometry.get("type", "")).strip()
    coordinates = geometry.get("coordinates")
    if coordinates is None:
        return None

    if geometry_type == "Point":
        longitude, latitude = coordinates
        return float(longitude), float(latitude), geometry_type

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
