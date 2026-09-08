"""Classify registry lakes for defensible field sampling."""

from __future__ import annotations

from ..metrics import _weighted_average
from ..models import (
    _ENGINEERED_WATER_TERMS,
    _LAKE_NAME_TERMS,
    _WETLAND_TERMS,
)
from .naming import _normalize_text

__all__ = []


def _classify_sampling_lake(
    lake_name: str,
    *,
    lake_area_km2: float | None,
) -> tuple[str, tuple[str, ...]]:
    normalized_name = _normalize_text(lake_name)
    has_lake_term = any(term in normalized_name for term in _LAKE_NAME_TERMS)
    has_wetland_term = any(term in normalized_name for term in _WETLAND_TERMS)
    has_engineered_term = any(
        term in normalized_name for term in _ENGINEERED_WATER_TERMS
    )
    notes: list[str] = []
    if has_wetland_term and not has_lake_term:
        notes.append("registry name points to a wetland-style basin rather than a lake")
        return ("wetland_context_excluded", tuple(notes))
    if has_engineered_term and not has_lake_term:
        notes.append(
            "registry name points to an engineered water body rather than a natural lake"
        )
        return ("engineered_waterbody_excluded", tuple(notes))
    if lake_area_km2 is not None and lake_area_km2 < 0.05:
        notes.append(
            "very small mapped water surface; treat as a micro-basin until field validation confirms suitability"
        )
        return ("small_lake_review", tuple(notes))
    if lake_area_km2 is not None and lake_area_km2 < 0.15:
        notes.append(
            "small mapped water surface; prefer checking basin depth and access before field planning"
        )
        return ("compact_lake_candidate", tuple(notes))
    return ("sampling_lake_candidate", tuple(notes))


def _lake_sampling_fit(
    *,
    lake_area_km2: float | None,
    lake_sampling_posture: str,
) -> float:
    if lake_sampling_posture in {
        "engineered_waterbody_excluded",
        "wetland_context_excluded",
    }:
        return 0.0
    if lake_area_km2 is None:
        area_score = 0.7
    elif lake_area_km2 < 0.03:
        area_score = 0.15
    elif lake_area_km2 < 0.05:
        area_score = 0.3
    elif lake_area_km2 < 0.15:
        area_score = 0.55
    elif lake_area_km2 < 0.5:
        area_score = 0.78
    elif lake_area_km2 < 20:
        area_score = 1.0
    else:
        area_score = 0.9
    posture_score = {
        "small_lake_review": 0.45,
        "compact_lake_candidate": 0.75,
        "sampling_lake_candidate": 1.0,
    }.get(lake_sampling_posture, 0.6)
    return round(_weighted_average((area_score, 0.6), (posture_score, 0.4)), 4)
