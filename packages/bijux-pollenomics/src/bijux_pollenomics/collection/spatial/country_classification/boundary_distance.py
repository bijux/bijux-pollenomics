"""Boundary-distance primitives for strict country review decisions."""

from __future__ import annotations

from itertools import pairwise
import math

from ....core.geospatial.geojson import (
    JsonObject,
    LinearRing,
    Polygon,
    parse_multipolygon,
    parse_polygon,
)


def geometry_boundary_distance(
    longitude: float, latitude: float, geometry: JsonObject
) -> float:
    """Return the minimum distance from a point to a polygon or multipolygon boundary."""
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])
    if geometry_type == "Polygon":
        polygon = parse_polygon(coordinates)
        return (
            polygon_boundary_distance(longitude, latitude, polygon)
            if polygon is not None
            else math.inf
        )
    if geometry_type == "MultiPolygon":
        multipolygon = parse_multipolygon(coordinates)
        distances = [
            polygon_boundary_distance(longitude, latitude, polygon)
            for polygon in multipolygon or []
        ]
        return min(distances) if distances else math.inf
    return math.inf


def polygon_boundary_distance(
    longitude: float, latitude: float, polygon: Polygon
) -> float:
    """Return the minimum distance from a point to any ring in one polygon."""
    distances = [
        ring_boundary_distance(longitude, latitude, ring) for ring in polygon if ring
    ]
    return min(distances) if distances else math.inf


def ring_boundary_distance(
    longitude: float, latitude: float, ring: LinearRing
) -> float:
    """Return the minimum distance from a point to one linear-ring edge."""
    if len(ring) < 2:
        return math.inf
    return min(
        point_to_segment_distance(
            longitude, latitude, start[0], start[1], end[0], end[1]
        )
        for start, end in pairwise(ring)
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
