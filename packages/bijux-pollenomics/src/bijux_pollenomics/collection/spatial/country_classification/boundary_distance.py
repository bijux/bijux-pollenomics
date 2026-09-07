"""Boundary-distance primitives for strict country review decisions."""

from __future__ import annotations

from itertools import pairwise
import math

from ....core.geospatial.geojson import (
    JsonObject,
    LinearRing,
    Polygon,
)
from .topology import boundary_segments_from_geometry, polygons_from_geometry


def geometry_boundary_distance(
    longitude: float, latitude: float, geometry: JsonObject
) -> float:
    """Return the minimum distance from a point to a polygon or multipolygon boundary."""
    distances = [
        polygon_boundary_distance(longitude, latitude, polygon)
        for polygon in polygons_from_geometry(geometry)
    ]
    return min(distances) if distances else math.inf


def point_on_geometry_boundary(
    longitude: float,
    latitude: float,
    geometry: JsonObject,
    *,
    epsilon: float,
) -> bool:
    """Return whether a point is within epsilon of any geometry edge."""
    if not math.isfinite(epsilon) or epsilon < 0:
        return geometry_boundary_distance(longitude, latitude, geometry) <= epsilon
    for ax, ay, bx, by, minimum_x, maximum_x, minimum_y, maximum_y in (
        boundary_segments_from_geometry(geometry)
    ):
        if not (
            minimum_x - epsilon <= longitude <= maximum_x + epsilon
            and minimum_y - epsilon <= latitude <= maximum_y + epsilon
        ):
            continue
        if (
            point_to_segment_distance(
                longitude,
                latitude,
                ax,
                ay,
                bx,
                by,
            )
            <= epsilon
        ):
            return True
    return False


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
