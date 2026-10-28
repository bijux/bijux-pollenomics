"""Exact rational WGS84 distance enclosures independent of inverse-geodesic code.

The ellipsoid metric lies between b²/a and a²/b times the unit-sphere metric.
Latitude variation bounds every path below; a meridian/parallel path bounds
distance above. For endpoints within ±60 degrees, haversine additionally
bounds central angle below by shortest longitude difference in degrees / 180.
"""

from __future__ import annotations

from fractions import Fraction
import math
from typing import Any

A = Fraction(6378137)
B = A * (1 - Fraction(1_000_000_000, 298_257_223_563))
LOWER_METRIC = B * B / A
UPPER_METRIC = A * A / B


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError("Independent geodesic bound: " + message)


def _number(value: Any) -> Fraction:
    _require(type(value) in (int, float), "native numeric scalar required")
    native = float(value)
    _require(math.isfinite(native), "finite geometry scalar required")
    return Fraction.from_float(native)


def distance_bounds(
    first: dict[str, Any], second: dict[str, Any]
) -> tuple[Fraction, Fraction]:
    """Bound the inverse geodesic independently of the host's pyproj call."""
    latitudes = [_number(row["latitude"]) for row in (first, second)]
    longitudes = [_number(row["longitude"]) for row in (first, second)]
    _require(
        all(abs(value) <= 90 for value in latitudes)
        and all(abs(value) <= 180 for value in longitudes),
        "WGS84 latitude/longitude domain",
    )
    latitude_difference = abs(latitudes[0] - latitudes[1])
    longitude_difference = abs(longitudes[0] - longitudes[1])
    longitude_difference = min(longitude_difference, 360 - longitude_difference)
    angular_lower = latitude_difference * 3 / 180
    if all(abs(value) <= 60 for value in latitudes):
        # cos(phi1)*cos(phi2)>=1/4, sigma>=2*sin(sigma/2), and
        # sin(delta_lambda/2)>=delta_lambda/pi on the shorter longitude arc.
        angular_lower = max(angular_lower, longitude_difference / 180)
    return (
        LOWER_METRIC * angular_lower,
        UPPER_METRIC
        * (latitude_difference + longitude_difference)
        * Fraction(22, 7)
        / 180,
    )
