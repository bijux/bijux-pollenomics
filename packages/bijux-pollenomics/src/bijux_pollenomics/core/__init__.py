"""Shared infrastructure used across package domains."""

from .geojson import (
    CountryBoundaryCollection,
    GeoJsonFeature,
    GeoJsonFeatureCollection,
    JsonObject,
    LinearRing,
    MultiPolygon,
    Polygon,
    Position,
    as_mapping,
    feature_list,
    parse_linear_ring,
    parse_multipolygon,
    parse_polygon,
    parse_position,
)

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
