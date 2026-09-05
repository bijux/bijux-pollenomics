from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypeAlias

JsonObject: TypeAlias = Mapping[str, object]
GeoJsonFeature: TypeAlias = JsonObject
GeoJsonFeatureCollection: TypeAlias = JsonObject
CountryBoundaryCollection: TypeAlias = Mapping[str, GeoJsonFeatureCollection]
Position: TypeAlias = tuple[float, float]
LinearRing: TypeAlias = list[Position]
Polygon: TypeAlias = list[LinearRing]
MultiPolygon: TypeAlias = list[Polygon]

__all__ = [
    "CountryBoundaryCollection",
    "GeoJsonFeature",
    "GeoJsonFeatureCollection",
    "JsonObject",
    "LinearRing",
    "MultiPolygon",
    "Polygon",
    "Position",
    "as_mapping",
    "feature_list",
    "parse_linear_ring",
    "parse_multipolygon",
    "parse_polygon",
    "parse_position",
]


def as_mapping(value: object) -> JsonObject | None:
    """Return one JSON-like mapping when the input is object-shaped."""
    if isinstance(value, Mapping):
        return value
    return None


def feature_list(collection: JsonObject) -> list[GeoJsonFeature]:
    """Extract GeoJSON features while enforcing object-shaped items."""
    raw_features = collection.get("features")
    if not isinstance(raw_features, list):
        return []
    return [feature for feature in raw_features if isinstance(feature, Mapping)]


def parse_position(value: object) -> Position | None:
    """Parse one lon/lat coordinate pair from nested GeoJSON coordinates."""
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return None
    if len(value) < 2:
        return None
    longitude = value[0]
    latitude = value[1]
    if not isinstance(longitude, (int, float)) or not isinstance(
        latitude, (int, float)
    ):
        return None
    return float(longitude), float(latitude)


def parse_linear_ring(value: object) -> LinearRing | None:
    """Parse one GeoJSON linear ring into a normalized list of lon/lat pairs."""
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return None
    ring: LinearRing = []
    for item in value:
        position = parse_position(item)
        if position is None:
            return None
        ring.append(position)
    return ring


def parse_polygon(value: object) -> Polygon | None:
    """Parse one GeoJSON polygon into normalized linear rings."""
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return None
    polygon: Polygon = []
    for item in value:
        ring = parse_linear_ring(item)
        if ring is None:
            return None
        polygon.append(ring)
    return polygon


def parse_multipolygon(value: object) -> MultiPolygon | None:
    """Parse one GeoJSON multipolygon into normalized polygons."""
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return None
    multipolygon: MultiPolygon = []
    for item in value:
        polygon = parse_polygon(item)
        if polygon is None:
            return None
        multipolygon.append(polygon)
    return multipolygon
