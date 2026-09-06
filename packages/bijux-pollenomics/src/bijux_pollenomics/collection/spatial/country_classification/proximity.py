"""Nearest-country resolution with explicit tie refusal."""

from __future__ import annotations

import math
from collections.abc import Callable

from ....core.geospatial.geojson import (
    CountryBoundaryCollection,
    JsonObject,
    as_mapping,
    feature_list,
)
from .model import BOUNDARY_CONTACT_EPSILON

BoundaryDistance = Callable[[float, float, JsonObject], float]


def nearest_country_by_boundary_distance(
    longitude: float,
    latitude: float,
    country_boundaries: CountryBoundaryCollection,
    max_distance: float,
    *,
    boundary_distance: BoundaryDistance,
) -> str:
    """Return one unique nearest country, leaving equal-distance ties unresolved."""
    distances_by_country: dict[str, float] = {}
    for country, payload in country_boundaries.items():
        for feature in feature_list(payload):
            geometry = as_mapping(feature.get("geometry"))
            if geometry is None:
                continue
            distance = boundary_distance(longitude, latitude, geometry)
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
