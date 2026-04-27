from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0088

__all__ = ["EARTH_RADIUS_KM", "haversine_km"]


def haversine_km(
    *,
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    """Return the great-circle distance between two latitude/longitude points."""
    latitude_delta = radians(latitude_b - latitude_a)
    longitude_delta = radians(longitude_b - longitude_a)
    latitude_a_radians = radians(latitude_a)
    latitude_b_radians = radians(latitude_b)
    sin_latitude = sin(latitude_delta / 2.0)
    sin_longitude = sin(longitude_delta / 2.0)
    arc = (
        sin_latitude * sin_latitude
        + cos(latitude_a_radians)
        * cos(latitude_b_radians)
        * sin_longitude
        * sin_longitude
    )
    return 2.0 * EARTH_RADIUS_KM * asin(sqrt(arc))
