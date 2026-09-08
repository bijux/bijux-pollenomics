"""Mutation-aware preparation of reusable country-boundary topology."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass
from threading import RLock

from ....core.geospatial.geojson import (
    JsonObject,
    Polygon,
    parse_multipolygon,
    parse_polygon,
)

_CACHE_CAPACITY = 512
BoundarySegment = tuple[float, float, float, float, float, float, float, float]


@dataclass(frozen=True, slots=True)
class _PreparedGeometry:
    source: JsonObject
    geometry_type: object
    coordinates: object
    polygons: tuple[Polygon, ...]
    boundary_segments: tuple[BoundarySegment, ...]


_PREPARED_GEOMETRIES: OrderedDict[int, _PreparedGeometry] = OrderedDict()
_PREPARATION_LOCK = RLock()


def polygons_from_geometry(geometry: JsonObject) -> tuple[Polygon, ...]:
    """Return parsed polygons while invalidating entries after source mutation."""
    with _PREPARATION_LOCK:
        return _cached_polygons_from_geometry(geometry)


def boundary_segments_from_geometry(
    geometry: JsonObject,
) -> tuple[BoundarySegment, ...]:
    """Return boundary segments and their precomputed axis-aligned bounds."""
    with _PREPARATION_LOCK:
        return _prepare_geometry(geometry).boundary_segments


def _cached_polygons_from_geometry(geometry: JsonObject) -> tuple[Polygon, ...]:
    return _prepare_geometry(geometry).polygons


def _prepare_geometry(geometry: JsonObject) -> _PreparedGeometry:
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])
    key = id(geometry)
    cached = _PREPARED_GEOMETRIES.get(key)
    if (
        cached is not None
        and cached.source is geometry
        and cached.geometry_type == geometry_type
        and cached.coordinates == coordinates
    ):
        _PREPARED_GEOMETRIES.move_to_end(key)
        return cached

    polygons = _parse_polygons(geometry_type, coordinates)
    prepared = _PreparedGeometry(
        source=geometry,
        geometry_type=geometry_type,
        coordinates=deepcopy(coordinates),
        polygons=polygons,
        boundary_segments=tuple(
            (
                start[0],
                start[1],
                end[0],
                end[1],
                min(start[0], end[0]),
                max(start[0], end[0]),
                min(start[1], end[1]),
                max(start[1], end[1]),
            )
            for polygon in polygons
            for ring in polygon
            for start, end in zip(ring, ring[1:], strict=False)
        ),
    )
    _PREPARED_GEOMETRIES[key] = prepared
    _PREPARED_GEOMETRIES.move_to_end(key)
    if len(_PREPARED_GEOMETRIES) > _CACHE_CAPACITY:
        _PREPARED_GEOMETRIES.popitem(last=False)
    return prepared


def _parse_polygons(geometry_type: object, coordinates: object) -> tuple[Polygon, ...]:
    if geometry_type == "Polygon":
        polygon = parse_polygon(coordinates)
        return (polygon,) if polygon is not None else ()
    if geometry_type == "MultiPolygon":
        return tuple(parse_multipolygon(coordinates) or ())
    return ()
