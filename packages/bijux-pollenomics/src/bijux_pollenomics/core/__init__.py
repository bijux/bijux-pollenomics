"""Shared infrastructure used across package domains."""

from .geo_distance import EARTH_RADIUS_KM, haversine_km
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
    "EARTH_RADIUS_KM",
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
    "haversine_km",
    "parse_linear_ring",
    "parse_multipolygon",
    "parse_polygon",
    "parse_position",
]
