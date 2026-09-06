"""Strict country-attribution policy and auditable outcomes."""

from __future__ import annotations

import math
from collections.abc import Mapping

from ....core.geospatial.geojson import CountryBoundaryCollection
from .dependencies import CountryClassificationDependencies
from .model import (
    COUNTRY_BOUNDARY_PROXIMITY_TOLERANCE,
    CountryAttributionDecision,
    CountryDecisionMethod,
    CountryDecisionStatus,
    RawCountryComparison,
)


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
    dependencies: CountryClassificationDependencies,
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
    normalized_raw = dependencies._optional_country(raw_country)
    refusal = dependencies._coordinate_refusal_reason(longitude, latitude)
    if refusal is not None:
        return _decision(
            digest,
            version,
            raw_country=normalized_raw,
            status="refused",
            method="coordinate_validation",
            refusal=refusal,
        )
    geometries = dependencies._geometries_by_country(country_boundaries)
    boundary = tuple(
        country
        for country, shapes in geometries.items()
        if any(
            dependencies.point_on_geometry_boundary(longitude, latitude, shape)
            for shape in shapes
        )
    )
    if boundary:
        return _decision(
            digest,
            version,
            raw_country=normalized_raw,
            status="review",
            method="point_on_boundary",
            ambiguity="point_on_boundary",
            candidates=boundary,
        )
    containing = tuple(
        country
        for country, shapes in geometries.items()
        if any(
            dependencies.point_in_geometry(longitude, latitude, shape)
            for shape in shapes
        )
    )
    if len(containing) > 1:
        return _decision(
            digest,
            version,
            raw_country=normalized_raw,
            status="review",
            method="multiple_boundary_containment",
            ambiguity="multiple_boundary_containment",
            candidates=containing,
        )
    if containing:
        derived = containing[0]
        comparison = dependencies._compare_raw_country(
            raw_country=normalized_raw,
            derived_country=derived,
            raw_country_aliases=raw_country_aliases,
        )
        conflict = comparison == "conflicts"
        return CountryAttributionDecision(
            derived,
            "review" if conflict else "assigned",
            "strict_boundary_containment",
            "raw_country_conflict" if conflict else None,
            None,
            normalized_raw,
            comparison,
            containing,
            digest,
            version,
        )
    holes = tuple(
        country
        for country, shapes in geometries.items()
        if any(
            dependencies.point_in_geometry_ignoring_holes(longitude, latitude, shape)
            for shape in shapes
        )
    )
    if holes:
        return _decision(
            digest,
            version,
            raw_country=normalized_raw,
            status="unassigned",
            method="no_boundary_containment",
            refusal="inside_boundary_hole",
            candidates=holes,
        )
    nearby = tuple(
        country
        for country, shapes in geometries.items()
        if any(
            dependencies.geometry_boundary_distance(longitude, latitude, shape)
            <= proximity_tolerance
            for shape in shapes
        )
    )
    if nearby:
        ambiguity = (
            "near_multiple_boundaries"
            if len(nearby) > 1
            else "near_boundary_without_containment"
        )
        return _decision(
            digest,
            version,
            raw_country=normalized_raw,
            status="review",
            method="boundary_proximity",
            ambiguity=ambiguity,
            candidates=nearby,
        )
    return _decision(
        digest,
        version,
        raw_country=normalized_raw,
        status="unassigned",
        method="no_boundary_containment",
        refusal="outside_governed_boundaries",
    )


def _decision(
    digest: str,
    version: str,
    *,
    raw_country: str | None,
    status: CountryDecisionStatus,
    method: CountryDecisionMethod,
    ambiguity: str | None = None,
    refusal: str | None = None,
    candidates: tuple[str, ...] = (),
) -> CountryAttributionDecision:
    comparison: RawCountryComparison = (
        "unresolved" if raw_country is not None else "not_supplied"
    )
    return CountryAttributionDecision(
        None,
        status,
        method,
        ambiguity,
        refusal,
        raw_country,
        comparison,
        candidates,
        digest,
        version,
    )


def classify_country(
    longitude: float,
    latitude: float,
    country_boundaries: CountryBoundaryCollection,
    *,
    dependencies: CountryClassificationDependencies,
) -> str:
    """Return a country only for one strict, non-boundary polygon containment."""
    if dependencies._coordinate_refusal_reason(longitude, latitude) is not None:
        return ""
    geometries = dependencies._geometries_by_country(country_boundaries)
    if any(
        dependencies.point_on_geometry_boundary(longitude, latitude, geometry)
        for shapes in geometries.values()
        for geometry in shapes
    ):
        return ""
    containing = [
        country
        for country, shapes in geometries.items()
        if any(
            dependencies.point_in_geometry(longitude, latitude, geometry)
            for geometry in shapes
        )
    ]
    return containing[0] if len(containing) == 1 else ""
