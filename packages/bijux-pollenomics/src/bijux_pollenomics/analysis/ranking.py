from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..core import haversine_km
from ..data_downloader.models import ContextPointRecord
from .site_candidates import (
    CandidateSiteContext,
    CandidateSiteScore,
    build_ranking_profiles,
    resolve_ranking_profile,
    score_candidate_site,
)

__all__ = [
    "CandidateSensitivityRow",
    "CandidateSensitivityReport",
    "build_candidate_context",
    "build_ranking_sensitivity_report",
    "rank_localities",
    "temporal_overlap",
]

if TYPE_CHECKING:
    from ..reporting.models import LocalitySummary


@dataclass(frozen=True)
class CandidateSensitivityRow:
    """Rank movement for one locality across alternate ranking profiles."""

    locality: str
    locality_token: str
    baseline_profile: str
    baseline_rank: int
    profile_ranks: dict[str, int]
    profile_statuses: dict[str, str]
    max_rank_shift: int
    recommendation_ready_profiles: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "locality": self.locality,
            "locality_token": self.locality_token,
            "baseline_profile": self.baseline_profile,
            "baseline_rank": self.baseline_rank,
            "profile_ranks": self.profile_ranks,
            "profile_statuses": self.profile_statuses,
            "max_rank_shift": self.max_rank_shift,
            "recommendation_ready_profiles": list(self.recommendation_ready_profiles),
        }


@dataclass(frozen=True)
class CandidateSensitivityReport:
    """Machine-readable comparison of candidate order under alternate profiles."""

    schema_version: str
    baseline_profile: str
    compared_profiles: tuple[str, ...]
    rows: tuple[CandidateSensitivityRow, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "baseline_profile": self.baseline_profile,
            "compared_profiles": list(self.compared_profiles),
            "rows": [row.as_dict() for row in self.rows],
        }


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
    co_located_localities: Iterable[LocalitySummary] | None = None,
    radius_km: float = 25.0,
) -> CandidateSiteContext:
    """Aggregate direct and contextual evidence for one candidate locality anchor."""
    direct_evidence = tuple(
        sorted(
            co_located_localities or (locality,),
            key=lambda item: (
                -(item.sample_count),
                item.species_latin_name,
                item.source_family,
                item.locality_token,
            ),
        )
    )
    anchor = direct_evidence[0]
    nearby_context_points = 0
    time_aware_context_points = 0
    temporal_overlap_points = 0
    nearest_context_distance_km: float | None = None
    nearby_context_layers: set[str] = set()
    for point in context_points:
        distance_km = haversine_km(
            latitude_a=anchor.latitude,
            longitude_a=anchor.longitude,
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
            nearby_context_layers.add(point.layer_key)
            if point.time_start_bp is not None and point.time_end_bp is not None:
                time_aware_context_points += 1
            if any(temporal_overlap(evidence, point) for evidence in direct_evidence):
                temporal_overlap_points += 1
    return CandidateSiteContext(
        locality=anchor,
        direct_evidence=direct_evidence,
        nearby_context_points=nearby_context_points,
        nearby_context_layer_count=len(nearby_context_layers),
        time_aware_context_points=time_aware_context_points,
        temporal_overlap_points=temporal_overlap_points,
        nearest_context_distance_km=round(nearest_context_distance_km, 4)
        if nearest_context_distance_km is not None
        else None,
    )


def rank_localities(
    localities: Iterable[LocalitySummary],
    context_points: Iterable[ContextPointRecord],
    *,
    radius_km: float = 25.0,
    profile_name: str = "atlas_exploration",
) -> list[CandidateSiteScore]:
    """Rank grouped locality anchors against context layers under one profile."""
    points = tuple(context_points)
    profile = resolve_ranking_profile(profile_name)
    contexts = _build_grouped_contexts(localities, points, radius_km=radius_km)
    scores = [score_candidate_site(context, profile=profile) for context in contexts]
    return sorted(
        scores,
        key=lambda score: (
            _ranking_status_order(score.ranking_status),
            -score.total_score,
            score.locality,
        ),
    )


def build_ranking_sensitivity_report(
    localities: Iterable[LocalitySummary],
    context_points: Iterable[ContextPointRecord],
    *,
    radius_km: float = 25.0,
    baseline_profile_name: str = "atlas_exploration",
    compared_profiles: tuple[str, ...] | None = None,
) -> CandidateSensitivityReport:
    """Compare candidate order across alternate ranking profiles."""
    profile_names = compared_profiles or tuple(
        profile.profile_name for profile in build_ranking_profiles()
    )
    results_by_profile = {
        profile_name: rank_localities(
            localities,
            context_points,
            radius_km=radius_km,
            profile_name=profile_name,
        )
        for profile_name in profile_names
    }
    baseline_scores = results_by_profile[baseline_profile_name]
    rows: list[CandidateSensitivityRow] = []
    for baseline_rank, baseline_score in enumerate(baseline_scores, start=1):
        profile_ranks: dict[str, int] = {}
        profile_statuses: dict[str, str] = {}
        recommendation_ready_profiles: list[str] = []
        for profile_name, scores in results_by_profile.items():
            for rank, score in enumerate(scores, start=1):
                if score.locality_token != baseline_score.locality_token:
                    continue
                profile_ranks[profile_name] = rank
                profile_statuses[profile_name] = score.ranking_status
                if score.sampling_recommendation_ready:
                    recommendation_ready_profiles.append(profile_name)
                break
        max_rank_shift = max(
            abs(baseline_rank - rank) for rank in profile_ranks.values()
        ) if profile_ranks else 0
        rows.append(
            CandidateSensitivityRow(
                locality=baseline_score.locality,
                locality_token=baseline_score.locality_token,
                baseline_profile=baseline_profile_name,
                baseline_rank=baseline_rank,
                profile_ranks=profile_ranks,
                profile_statuses=profile_statuses,
                max_rank_shift=max_rank_shift,
                recommendation_ready_profiles=tuple(sorted(recommendation_ready_profiles)),
            )
        )
    return CandidateSensitivityReport(
        schema_version="candidate-site-sensitivity.v1",
        baseline_profile=baseline_profile_name,
        compared_profiles=tuple(profile_names),
        rows=tuple(rows),
    )


def _build_grouped_contexts(
    localities: Iterable[LocalitySummary],
    context_points: tuple[ContextPointRecord, ...],
    *,
    radius_km: float,
) -> tuple[CandidateSiteContext, ...]:
    grouped: dict[str, list[LocalitySummary]] = defaultdict(list)
    for locality in localities:
        grouped[_group_token(locality)].append(locality)

    contexts: list[CandidateSiteContext] = []
    for token in sorted(grouped):
        evidence = tuple(
            sorted(
                grouped[token],
                key=lambda item: (
                    -(item.sample_count),
                    item.species_latin_name,
                    item.source_family,
                    item.locality_token,
                ),
            )
        )
        contexts.append(
            build_candidate_context(
                evidence[0],
                context_points,
                co_located_localities=evidence,
                radius_km=radius_km,
            )
        )
    return tuple(contexts)


def _group_token(locality: LocalitySummary) -> str:
    if locality.locality_token:
        return locality.locality_token
    latitude = locality.latitude_text or ""
    longitude = locality.longitude_text or ""
    return "|".join(
        (
            locality.locality or "unspecified-locality",
            locality.species_latin_name,
            latitude,
            longitude,
        )
    )


def _ranking_status_order(value: str) -> int:
    order = {
        "ranked": 0,
        "downgraded": 1,
        "refused": 2,
    }
    return order.get(value, 3)
