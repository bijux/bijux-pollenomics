"""Strict source-coordinate parsing without geographic inference."""

from __future__ import annotations

import math

from .models import AadrCoordinateEvidence, CoordinateStatus


def parse_aadr_coordinates(
    latitude_raw: str, longitude_raw: str
) -> AadrCoordinateEvidence:
    """Parse a coordinate pair while preserving missing, invalid, and zero values."""
    latitude_token = latitude_raw.strip()
    longitude_token = longitude_raw.strip()
    latitude_missing = _is_missing_token(latitude_token)
    longitude_missing = _is_missing_token(longitude_token)
    if latitude_missing and longitude_missing:
        return _refusal(latitude_raw, longitude_raw, "missing")
    if latitude_missing or longitude_missing:
        return _refusal(latitude_raw, longitude_raw, "partial")
    try:
        latitude = float(latitude_token)
        longitude = float(longitude_token)
    except ValueError:
        return _refusal(latitude_raw, longitude_raw, "invalid_numeric")
    if not math.isfinite(latitude) or not math.isfinite(longitude):
        return _refusal(latitude_raw, longitude_raw, "non_finite")
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        return _refusal(latitude_raw, longitude_raw, "out_of_range")
    return AadrCoordinateEvidence(
        latitude_raw=latitude_raw,
        longitude_raw=longitude_raw,
        latitude=latitude,
        longitude=longitude,
        status="admitted",
    )


def _is_missing_token(value: str) -> bool:
    return not value or value == ".."


def _refusal(
    latitude_raw: str,
    longitude_raw: str,
    status: CoordinateStatus,
) -> AadrCoordinateEvidence:
    return AadrCoordinateEvidence(
        latitude_raw=latitude_raw,
        longitude_raw=longitude_raw,
        latitude=None,
        longitude=None,
        status=status,
    )


__all__ = ["parse_aadr_coordinates"]
