from __future__ import annotations

from collections.abc import Iterable

from ..core import haversine_km
from ..data_downloader.models import ContextPointRecord
from ..reporting.models import LocalitySummary
from .site_candidates import (
    CandidateSiteContext,
    CandidateSiteScore,
    score_candidate_site,
)

__all__ = [
    "build_candidate_context",
    "rank_localities",
    "temporal_overlap",
]


def temporal_overlap(
    locality: LocalitySummary, context_point: ContextPointRecord
) -> bool:
    """Return whether one context point overlaps the locality time window."""
    if locality.time_start_bp is None or locality.time_end_bp is None:
        return False
    if context_point.time_start_bp is None or context_point.time_end_bp is None:
        return False
    return not (
        context_point.time_end_bp > locality.time_start_bp
        or context_point.time_start_bp < locality.time_end_bp
    )


def build_candidate_context(
    locality: LocalitySummary,
    context_points: Iterable[ContextPointRecord],
    *,
    radius_km: float = 25.0,
) -> CandidateSiteContext:
    """Aggregate cross-layer context for one AADR locality."""
    nearby_context_points = 0
    temporal_overlap_points = 0
    nearest_context_distance_km: float | None = None
    for point in context_points:
        distance_km = haversine_km(
            latitude_a=locality.latitude,
            longitude_a=locality.longitude,
            latitude_b=point.latitude,
            longitude_b=point.longitude,
        )
        if (
            nearest_context_distance_km is None
            or distance_km < nearest_context_distance_km
        ):
            nearest_context_distance_km = distance_km
        if distance_km <= radius_km:
            nearby_context_points += 1
            if temporal_overlap(locality, point):
                temporal_overlap_points += 1
    return CandidateSiteContext(
        locality=locality,
        nearby_context_points=nearby_context_points,
        nearest_context_distance_km=round(nearest_context_distance_km, 4)
        if nearest_context_distance_km is not None
        else None,
        temporal_overlap_points=temporal_overlap_points,
    )


def rank_localities(
    localities: Iterable[LocalitySummary],
    context_points: Iterable[ContextPointRecord],
    *,
    radius_km: float = 25.0,
) -> list[CandidateSiteScore]:
    """Rank localities against context layers for atlas-to-engine progression."""
    points = tuple(context_points)
    scores = [
        score_candidate_site(
            build_candidate_context(locality, points, radius_km=radius_km)
        )
        for locality in localities
    ]
    return sorted(scores, key=lambda score: (-score.total_score, score.locality))
