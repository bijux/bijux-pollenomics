"""Coordinate admission shared by map-document state and static indexes."""

from __future__ import annotations

import math
from collections.abc import Mapping


def finite_coordinate(value: object, *, minimum: float, maximum: float) -> float | None:
    """Return a finite coordinate within its geographic axis range."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        number = float(value) if isinstance(value, (int, float, str)) else math.nan
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(number) or not minimum <= number <= maximum:
        return None
    return number


def point_coordinate_pair(feature: Mapping[str, object]) -> tuple[float, float] | None:
    """Return an admitted latitude/longitude pair without synthesizing zeroes."""
    latitude = finite_coordinate(feature.get("latitude"), minimum=-90, maximum=90)
    longitude = finite_coordinate(feature.get("longitude"), minimum=-180, maximum=180)
    if latitude is None or longitude is None:
        return None
    return latitude, longitude


__all__ = ["finite_coordinate", "point_coordinate_pair"]
