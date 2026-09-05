"""Strict polygon containment primitives for country classification."""

from __future__ import annotations

from ....core.geospatial.geojson import (
    JsonObject,
    LinearRing,
    Polygon,
    parse_multipolygon,
    parse_polygon,
)


def point_in_geometry(longitude: float, latitude: float, geometry: JsonObject) -> bool:
    """Check whether a point falls inside a GeoJSON Polygon or MultiPolygon."""
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])
    if geometry_type == "Polygon":
        polygon = parse_polygon(coordinates)
        return (
            point_in_polygon(longitude, latitude, polygon)
            if polygon is not None
            else False
        )
    if geometry_type == "MultiPolygon":
        multipolygon = parse_multipolygon(coordinates)
        return any(
            point_in_polygon(longitude, latitude, polygon)
            for polygon in multipolygon or []
        )
    return False


def point_in_geometry_ignoring_holes(
    longitude: float, latitude: float, geometry: JsonObject
) -> bool:
    """Check outer-ring containment for diagnostics without assigning a country."""
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])
    if geometry_type == "Polygon":
        polygon = parse_polygon(coordinates)
        return (
            point_in_outer_ring(longitude, latitude, polygon)
            if polygon is not None
            else False
        )
    if geometry_type == "MultiPolygon":
        multipolygon = parse_multipolygon(coordinates)
        return any(
            point_in_outer_ring(longitude, latitude, polygon)
            for polygon in multipolygon or []
        )
    return False


def point_in_polygon(longitude: float, latitude: float, polygon: Polygon) -> bool:
    """Ray-casting point-in-polygon with support for holes."""
    if not polygon:
        return False
    if not point_in_ring(longitude, latitude, polygon[0]):
        return False
    return all(not point_in_ring(longitude, latitude, hole) for hole in polygon[1:])


def point_in_outer_ring(longitude: float, latitude: float, polygon: Polygon) -> bool:
    """Check whether a point lies inside the outer ring of one polygon."""
    if not polygon:
        return False
    return point_in_ring(longitude, latitude, polygon[0])


def point_in_ring(longitude: float, latitude: float, ring: LinearRing) -> bool:
    """Return True when a point is inside a linear ring."""
    if len(ring) < 3:
        return False
    inside = False
    previous = ring[-1]
    for current in ring:
        x1, y1 = previous
        x2, y2 = current
        crosses = ((y1 > latitude) != (y2 > latitude)) and (
            longitude < (x2 - x1) * (latitude - y1) / ((y2 - y1) or 1e-12) + x1
        )
        if crosses:
            inside = not inside
        previous = current
    return inside
