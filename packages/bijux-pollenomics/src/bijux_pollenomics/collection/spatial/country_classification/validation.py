"""Coordinate refusal and source-country comparison rules."""

from __future__ import annotations

import math
from collections.abc import Mapping

from .model import RawCountryComparison


def coordinate_refusal_reason(longitude: float, latitude: float) -> str | None:
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


def optional_country(raw_country: str | None) -> str | None:
    if raw_country is None:
        return None
    normalized = raw_country.strip()
    return normalized or None


def compare_raw_country(
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
