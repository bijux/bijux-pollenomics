"""Stable public facade for strict country classification."""

from __future__ import annotations

from collections.abc import Mapping
import sys
from typing import cast

from ....core.geospatial.geojson import (
    CountryBoundaryCollection,
    JsonObject,
    LinearRing,
    Polygon,
)
from .boundary_distance import (
    geometry_boundary_distance as _geometry_boundary_distance,
)
from .boundary_distance import (
    point_on_geometry_boundary as _point_on_geometry_boundary,
)
from .boundary_distance import (
    point_to_segment_distance as _point_to_segment_distance,
)
from .boundary_distance import (
    polygon_boundary_distance as _polygon_boundary_distance,
)
from .boundary_distance import (
    ring_boundary_distance as _ring_boundary_distance,
)
from .containment import (
    point_in_geometry as _point_in_geometry,
)
from .containment import (
    point_in_geometry_ignoring_holes as _point_in_geometry_ignoring_holes,
)
from .containment import (
    point_in_outer_ring as _point_in_outer_ring,
)
from .containment import (
    point_in_polygon as _point_in_polygon,
)
from .containment import (
    point_in_ring as _point_in_ring,
)
from .decision import classify_country as _classify_country
from .decision import decide_country_attribution as _decide_country_attribution
from .dependencies import CountryClassificationDependencies
from .model import (
    BOUNDARY_CONTACT_EPSILON,
    COUNTRY_BOUNDARY_PROXIMITY_TOLERANCE,
    CountryAttributionDecision,
    CountryDecisionMethod,
    CountryDecisionStatus,
    RawCountryComparison,
)
from .partitions import geometries_by_country
from .proximity import nearest_country_by_boundary_distance as _nearest_country
from .validation import compare_raw_country, coordinate_refusal_reason, optional_country

CountryAttributionDecision.__module__ = __name__


def decide_country_attribution(
    longitude: float,
    latitude: float,
    country_boundaries: CountryBoundaryCollection,
    *,
    boundary_artifact_digest: str,
    boundary_version: str,
    raw_country: str | None = None,
    raw_country_aliases: Mapping[str, str] | None = None,
    proximity_tolerance: float = COUNTRY_BOUNDARY_PROXIMITY_TOLERANCE,
) -> CountryAttributionDecision:
    """Return a strict country decision without silently repairing spatial evidence."""
    return _decide_country_attribution(
        longitude,
        latitude,
        country_boundaries,
        boundary_artifact_digest=boundary_artifact_digest,
        boundary_version=boundary_version,
        raw_country=raw_country,
        raw_country_aliases=raw_country_aliases,
        proximity_tolerance=proximity_tolerance,
        dependencies=cast(CountryClassificationDependencies, sys.modules[__name__]),
    )


def classify_country(
    longitude: float,
    latitude: float,
    country_boundaries: CountryBoundaryCollection,
) -> str:
    """Return a country only for one strict, non-boundary polygon containment."""
    return _classify_country(
        longitude,
        latitude,
        country_boundaries,
        dependencies=cast(CountryClassificationDependencies, sys.modules[__name__]),
    )


def _geometries_by_country(
    country_boundaries: CountryBoundaryCollection,
) -> dict[str, tuple[JsonObject, ...]]:
    return geometries_by_country(country_boundaries)


def _coordinate_refusal_reason(longitude: float, latitude: float) -> str | None:
    return coordinate_refusal_reason(longitude, latitude)


def _optional_country(raw_country: str | None) -> str | None:
    return optional_country(raw_country)


def _compare_raw_country(
    *,
    raw_country: str | None,
    derived_country: str,
    raw_country_aliases: Mapping[str, str] | None,
) -> RawCountryComparison:
    return compare_raw_country(
        raw_country=raw_country,
        derived_country=derived_country,
        raw_country_aliases=raw_country_aliases,
    )


def point_in_geometry(longitude: float, latitude: float, geometry: JsonObject) -> bool:
    """Check whether a point falls inside a GeoJSON Polygon or MultiPolygon."""
    return _point_in_geometry(longitude, latitude, geometry)


def point_on_geometry_boundary(
    longitude: float,
    latitude: float,
    geometry: JsonObject,
    *,
    epsilon: float = BOUNDARY_CONTACT_EPSILON,
) -> bool:
    """Return whether a point touches a polygon ring within a numeric epsilon."""
    return _point_on_geometry_boundary(longitude, latitude, geometry, epsilon=epsilon)


def point_in_geometry_ignoring_holes(
    longitude: float, latitude: float, geometry: JsonObject
) -> bool:
    """Check outer-ring containment for diagnostics without assigning a country."""
    return _point_in_geometry_ignoring_holes(longitude, latitude, geometry)


def point_in_polygon(longitude: float, latitude: float, polygon: Polygon) -> bool:
    """Ray-casting point-in-polygon with support for holes."""
    return _point_in_polygon(longitude, latitude, polygon)


def point_in_outer_ring(longitude: float, latitude: float, polygon: Polygon) -> bool:
    """Return whether a point lies inside a polygon's outer ring."""
    return _point_in_outer_ring(longitude, latitude, polygon)


def point_in_ring(longitude: float, latitude: float, ring: LinearRing) -> bool:
    """Return True when a point is inside a linear ring."""
    return _point_in_ring(longitude, latitude, ring)


def nearest_country_by_boundary_distance(
    longitude: float,
    latitude: float,
    country_boundaries: CountryBoundaryCollection,
    max_distance: float,
) -> str:
    """Return one unique nearest country, leaving equal-distance ties unresolved."""
    return _nearest_country(
        longitude,
        latitude,
        country_boundaries,
        max_distance,
        boundary_distance=geometry_boundary_distance,
    )


def geometry_boundary_distance(
    longitude: float, latitude: float, geometry: JsonObject
) -> float:
    """Return the minimum distance from a point to a polygon or multipolygon boundary."""
    return _geometry_boundary_distance(longitude, latitude, geometry)


def polygon_boundary_distance(
    longitude: float, latitude: float, polygon: Polygon
) -> float:
    """Return the minimum distance from a point to any ring in one polygon."""
    return _polygon_boundary_distance(longitude, latitude, polygon)


def ring_boundary_distance(
    longitude: float, latitude: float, ring: LinearRing
) -> float:
    """Return the minimum distance from a point to one linear-ring edge."""
    return _ring_boundary_distance(longitude, latitude, ring)


def point_to_segment_distance(
    px: float, py: float, ax: float, ay: float, bx: float, by: float
) -> float:
    """Return the Euclidean distance from a point to one line segment in lon/lat degrees."""
    return _point_to_segment_distance(px, py, ax, ay, bx, by)


__all__ = [
    "BOUNDARY_CONTACT_EPSILON",
    "COUNTRY_BOUNDARY_PROXIMITY_TOLERANCE",
    "CountryAttributionDecision",
    "CountryDecisionMethod",
    "CountryDecisionStatus",
    "RawCountryComparison",
    "classify_country",
    "decide_country_attribution",
    "geometry_boundary_distance",
    "nearest_country_by_boundary_distance",
    "point_in_geometry",
    "point_in_geometry_ignoring_holes",
    "point_on_geometry_boundary",
    "point_in_outer_ring",
    "point_in_polygon",
    "point_in_ring",
    "point_to_segment_distance",
    "polygon_boundary_distance",
    "ring_boundary_distance",
]
