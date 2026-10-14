"""Compare the retained spherical distance with pinned WGS84 inverse geodesics."""

from __future__ import annotations

import math

from pyproj import Geod

SPHERE_RADIUS_KM = 6371.0088
WGS84 = Geod(ellps="WGS84")


def number(value: object) -> float:
    """Preserve zero and refuse booleans, nonnumeric and nonfinite coordinates."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Finite numeric coordinate required")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Finite numeric coordinate required")
    return result


def point(latitude: object, longitude: object) -> tuple[float, float]:
    lat, lon = number(latitude), number(longitude)
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError("EPSG:4326 longitude/latitude outside range")
    return lat, lon


def spherical_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Retain the exact declared 6371.0088km haversine expression."""
    lat_a, lon_a = point(*a)
    lat_b, lon_b = point(*b)
    value = (
        math.sin(math.radians(lat_b - lat_a) / 2) ** 2
        + math.cos(math.radians(lat_a))
        * math.cos(math.radians(lat_b))
        * math.sin(math.radians(lon_b - lon_a) / 2) ** 2
    )
    return 2 * SPHERE_RADIUS_KM * math.asin(math.sqrt(value))


def wgs84_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Pass longitude before latitude, degrees in and unrounded metres out."""
    lat_a, lon_a = point(*a)
    lat_b, lon_b = point(*b)
    _, _, distance = WGS84.inv(lon_a, lat_a, lon_b, lat_b, radians=False)
    result = number(distance) / 1000
    if result < 0:
        raise ValueError("Inverse distance must be nonnegative")
    return result


def inside(distance_km: float, radius_km: int) -> bool:
    """Eligibility uses the complete computational distance without rounding."""
    if radius_km not in (10, 20) or not math.isfinite(distance_km) or distance_km < 0:
        raise ValueError("Declared10/20km distance domain required")
    return distance_km <= radius_km
