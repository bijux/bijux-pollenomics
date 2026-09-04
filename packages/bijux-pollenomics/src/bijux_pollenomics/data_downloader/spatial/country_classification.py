from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from itertools import pairwise
import math
from typing import Literal, TypeAlias

from ...core.geojson import (
    CountryBoundaryCollection,
    JsonObject,
    LinearRing,
    Polygon,
    as_mapping,
    feature_list,
    parse_multipolygon,
    parse_polygon,
)

COUNTRY_BOUNDARY_PROXIMITY_TOLERANCE = 0.15
BOUNDARY_CONTACT_EPSILON = 1e-12

CountryDecisionStatus: TypeAlias = Literal[
    "assigned",
    "review",
    "unassigned",
    "refused",
]
CountryDecisionMethod: TypeAlias = Literal[
    "strict_boundary_containment",
    "point_on_boundary",
    "multiple_boundary_containment",
    "boundary_proximity",
    "no_boundary_containment",
    "coordinate_validation",
]
RawCountryComparison: TypeAlias = Literal[
    "not_supplied",
    "agrees",
    "conflicts",
    "unresolved",
]


@dataclass(frozen=True)
class CountryAttributionDecision:
    """Auditable country-membership decision for one point and boundary artifact."""

    derived_country: str | None
    decision_status: CountryDecisionStatus
    decision_method: CountryDecisionMethod
    ambiguity_reason: str | None
    refusal_reason: str | None
    raw_country: str | None
    raw_country_comparison: RawCountryComparison
    candidate_countries: tuple[str, ...]
    boundary_artifact_digest: str
    boundary_version: str


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
    digest = boundary_artifact_digest.strip()
    version = boundary_version.strip()
    if not digest:
        raise ValueError("boundary_artifact_digest must be supplied")
    if not version:
        raise ValueError("boundary_version must be supplied")
    if not math.isfinite(proximity_tolerance) or proximity_tolerance < 0:
        raise ValueError("proximity_tolerance must be a finite non-negative value")

    normalized_raw_country = _optional_country(raw_country)
    coordinate_refusal = _coordinate_refusal_reason(longitude, latitude)
    if coordinate_refusal is not None:
        return CountryAttributionDecision(
            derived_country=None,
            decision_status="refused",
            decision_method="coordinate_validation",
            ambiguity_reason=None,
            refusal_reason=coordinate_refusal,
            raw_country=normalized_raw_country,
            raw_country_comparison=(
                "unresolved" if normalized_raw_country is not None else "not_supplied"
            ),
            candidate_countries=(),
            boundary_artifact_digest=digest,
            boundary_version=version,
        )

    geometries_by_country = _geometries_by_country(country_boundaries)
    boundary_countries = tuple(
        country
        for country, geometries in geometries_by_country.items()
        if any(
            point_on_geometry_boundary(longitude, latitude, geometry)
            for geometry in geometries
        )
    )
    if boundary_countries:
        return CountryAttributionDecision(
            derived_country=None,
            decision_status="review",
            decision_method="point_on_boundary",
            ambiguity_reason="point_on_boundary",
            refusal_reason=None,
            raw_country=normalized_raw_country,
            raw_country_comparison=(
                "unresolved" if normalized_raw_country is not None else "not_supplied"
            ),
            candidate_countries=boundary_countries,
            boundary_artifact_digest=digest,
            boundary_version=version,
        )

    containing_countries = tuple(
        country
        for country, geometries in geometries_by_country.items()
        if any(
            point_in_geometry(longitude, latitude, geometry) for geometry in geometries
        )
    )
    if len(containing_countries) > 1:
        return CountryAttributionDecision(
            derived_country=None,
            decision_status="review",
            decision_method="multiple_boundary_containment",
            ambiguity_reason="multiple_boundary_containment",
            refusal_reason=None,
            raw_country=normalized_raw_country,
            raw_country_comparison=(
                "unresolved" if normalized_raw_country is not None else "not_supplied"
            ),
            candidate_countries=containing_countries,
            boundary_artifact_digest=digest,
            boundary_version=version,
        )
    if containing_countries:
        derived_country = containing_countries[0]
        raw_comparison = _compare_raw_country(
            raw_country=normalized_raw_country,
            derived_country=derived_country,
            raw_country_aliases=raw_country_aliases,
        )
        has_raw_conflict = raw_comparison == "conflicts"
        return CountryAttributionDecision(
            derived_country=derived_country,
            decision_status="review" if has_raw_conflict else "assigned",
            decision_method="strict_boundary_containment",
            ambiguity_reason="raw_country_conflict" if has_raw_conflict else None,
            refusal_reason=None,
            raw_country=normalized_raw_country,
            raw_country_comparison=raw_comparison,
            candidate_countries=containing_countries,
            boundary_artifact_digest=digest,
            boundary_version=version,
        )

    hole_countries = tuple(
        country
        for country, geometries in geometries_by_country.items()
        if any(
            point_in_geometry_ignoring_holes(longitude, latitude, geometry)
            for geometry in geometries
        )
    )
    if hole_countries:
        return CountryAttributionDecision(
            derived_country=None,
            decision_status="unassigned",
            decision_method="no_boundary_containment",
            ambiguity_reason=None,
            refusal_reason="inside_boundary_hole",
            raw_country=normalized_raw_country,
            raw_country_comparison=(
                "unresolved" if normalized_raw_country is not None else "not_supplied"
            ),
            candidate_countries=hole_countries,
            boundary_artifact_digest=digest,
            boundary_version=version,
        )

    nearby_countries = tuple(
        country
        for country, geometries in geometries_by_country.items()
        if any(
            geometry_boundary_distance(longitude, latitude, geometry)
            <= proximity_tolerance
            for geometry in geometries
        )
    )
    if nearby_countries:
        return CountryAttributionDecision(
            derived_country=None,
            decision_status="review",
            decision_method="boundary_proximity",
            ambiguity_reason=(
                "near_multiple_boundaries"
                if len(nearby_countries) > 1
                else "near_boundary_without_containment"
            ),
            refusal_reason=None,
            raw_country=normalized_raw_country,
            raw_country_comparison=(
                "unresolved" if normalized_raw_country is not None else "not_supplied"
            ),
            candidate_countries=nearby_countries,
            boundary_artifact_digest=digest,
            boundary_version=version,
        )

    return CountryAttributionDecision(
        derived_country=None,
        decision_status="unassigned",
        decision_method="no_boundary_containment",
        ambiguity_reason=None,
        refusal_reason="outside_governed_boundaries",
        raw_country=normalized_raw_country,
        raw_country_comparison=(
            "unresolved" if normalized_raw_country is not None else "not_supplied"
        ),
        candidate_countries=(),
        boundary_artifact_digest=digest,
        boundary_version=version,
    )


def classify_country(
    longitude: float,
    latitude: float,
    country_boundaries: CountryBoundaryCollection,
) -> str:
    """Return a country only for one strict, non-boundary polygon containment."""
    if _coordinate_refusal_reason(longitude, latitude) is not None:
        return ""
    geometries_by_country = _geometries_by_country(country_boundaries)
    if any(
        point_on_geometry_boundary(longitude, latitude, geometry)
        for geometries in geometries_by_country.values()
        for geometry in geometries
    ):
        return ""
    containing_countries = [
        country
        for country, geometries in geometries_by_country.items()
        if any(
            point_in_geometry(longitude, latitude, geometry) for geometry in geometries
        )
    ]
    return containing_countries[0] if len(containing_countries) == 1 else ""


def _geometries_by_country(
    country_boundaries: CountryBoundaryCollection,
) -> dict[str, tuple[JsonObject, ...]]:
    geometries_by_country: dict[str, tuple[JsonObject, ...]] = {}
    for country in sorted(country_boundaries):
        geometries = tuple(
            geometry
            for feature in feature_list(country_boundaries[country])
            for geometry in (as_mapping(feature.get("geometry")),)
            if geometry is not None
        )
        geometries_by_country[country] = geometries
    return geometries_by_country


def _coordinate_refusal_reason(longitude: float, latitude: float) -> str | None:
    if (
        isinstance(longitude, bool)
        or isinstance(latitude, bool)
        or not isinstance(longitude, (int, float))
        or not isinstance(latitude, (int, float))
    ):
        return "non_numeric_coordinate"
    if not math.isfinite(longitude) or not math.isfinite(latitude):
        return "non_finite_coordinate"
    if longitude < -180 or longitude > 180:
        return "longitude_out_of_range"
    if latitude < -90 or latitude > 90:
        return "latitude_out_of_range"
    return None


def _optional_country(raw_country: str | None) -> str | None:
    if raw_country is None:
        return None
    normalized = raw_country.strip()
    return normalized or None


def _compare_raw_country(
    *,
    raw_country: str | None,
    derived_country: str,
    raw_country_aliases: Mapping[str, str] | None,
) -> RawCountryComparison:
    if raw_country is None:
        return "not_supplied"
    canonical_raw_country = raw_country
    if raw_country_aliases is not None:
        aliases = {
            alias.strip().casefold(): country.strip()
            for alias, country in raw_country_aliases.items()
            if alias.strip() and country.strip()
        }
        canonical_raw_country = aliases.get(raw_country.casefold(), raw_country)
    if canonical_raw_country.casefold() == derived_country.casefold():
        return "agrees"
    return "conflicts"


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


def point_on_geometry_boundary(
    longitude: float,
    latitude: float,
    geometry: JsonObject,
    *,
    epsilon: float = BOUNDARY_CONTACT_EPSILON,
) -> bool:
    """Return whether a point touches a polygon ring within a numeric epsilon."""
    return geometry_boundary_distance(longitude, latitude, geometry) <= epsilon


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


def nearest_country_by_boundary_distance(
    longitude: float,
    latitude: float,
    country_boundaries: CountryBoundaryCollection,
    max_distance: float,
) -> str:
    """Return one unique nearest country, leaving equal-distance ties unresolved."""
    distances_by_country: dict[str, float] = {}
    for country, payload in country_boundaries.items():
        for feature in feature_list(payload):
            geometry = as_mapping(feature.get("geometry"))
            if geometry is None:
                continue
            distance = geometry_boundary_distance(longitude, latitude, geometry)
            distances_by_country[country] = min(
                distance,
                distances_by_country.get(country, math.inf),
            )
    if not distances_by_country:
        return ""
    nearest_distance = min(distances_by_country.values())
    if nearest_distance > max_distance:
        return ""
    nearest_countries = sorted(
        country
        for country, distance in distances_by_country.items()
        if math.isclose(
            distance,
            nearest_distance,
            rel_tol=0.0,
            abs_tol=BOUNDARY_CONTACT_EPSILON,
        )
    )
    return nearest_countries[0] if len(nearest_countries) == 1 else ""


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
            longitude,
            latitude,
            start[0],
            start[1],
            end[0],
            end[1],
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
