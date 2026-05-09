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
from .temporal_semantics import (
    TEMPORAL_COMPARABILITY_POSTURES,
    TEMPORAL_WINDOW_ROWS,
    TemporalSemantics,
    build_temporal_semantics,
    normalize_temporal_semantics_payload,
    resolve_temporal_window,
    temporal_semantics_has_numeric_interval,
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
    "TEMPORAL_COMPARABILITY_POSTURES",
    "TEMPORAL_WINDOW_ROWS",
    "TemporalSemantics",
    "as_mapping",
    "build_temporal_semantics",
    "feature_list",
    "haversine_km",
    "normalize_temporal_semantics_payload",
    "parse_linear_ring",
    "parse_multipolygon",
    "parse_polygon",
    "parse_position",
    "resolve_temporal_window",
    "temporal_semantics_has_numeric_interval",
]
