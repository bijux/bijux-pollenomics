"""Deterministic extraction of country boundary geometries."""

from __future__ import annotations

from ....core.geospatial.geojson import (
    CountryBoundaryCollection,
    JsonObject,
    as_mapping,
    feature_list,
)


def geometries_by_country(
    country_boundaries: CountryBoundaryCollection,
) -> dict[str, tuple[JsonObject, ...]]:
    """Return valid boundary geometries grouped in deterministic country order."""
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
