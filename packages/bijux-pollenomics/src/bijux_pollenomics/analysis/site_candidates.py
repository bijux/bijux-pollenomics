from __future__ import annotations

from dataclasses import dataclass

from ..reporting.models import LocalitySummary

__all__ = [
    "CandidateSiteContext",
    "CandidateSiteScore",
    "ScoringWeights",
    "score_candidate_site",
]


@dataclass(frozen=True)
class CandidateSiteContext:
    locality: LocalitySummary
    nearby_context_points: int
    nearest_context_distance_km: float | None
    temporal_overlap_points: int


@dataclass(frozen=True)
class ScoringWeights:
    sample_presence: float = 0.4
    context_density: float = 0.3
    temporal_overlap: float = 0.2
    distance_bonus: float = 0.1


@dataclass(frozen=True)
class CandidateSiteScore:
    locality: str
    total_score: float
    sample_signal: float
    context_signal: float
    temporal_signal: float
    distance_signal: float
    rationale: tuple[str, ...]


def score_candidate_site(
    candidate: CandidateSiteContext,
    *,
    weights: ScoringWeights | None = None,
) -> CandidateSiteScore:
    """Score one candidate locality for future site-selection workflows."""
    if weights is None:
        weights = ScoringWeights()

    sample_signal = min(1.0, candidate.locality.sample_count / 5.0)
    context_signal = min(1.0, candidate.nearby_context_points / 12.0)
    temporal_signal = min(1.0, candidate.temporal_overlap_points / 6.0)
    if candidate.nearest_context_distance_km is None:
        distance_signal = 0.0
    else:
        distance_signal = max(
            0.0, min(1.0, (25.0 - candidate.nearest_context_distance_km) / 25.0)
        )
    total_score = (
        sample_signal * weights.sample_presence
        + context_signal * weights.context_density
        + temporal_signal * weights.temporal_overlap
        + distance_signal * weights.distance_bonus
    )
    rationale: list[str] = []
    if candidate.locality.sample_count:
        rationale.append(
            f"{candidate.locality.sample_count} AADR samples anchor the locality"
        )
    if candidate.nearby_context_points:
        rationale.append(
            f"{candidate.nearby_context_points} nearby context points increase cross-layer support"
        )
    if candidate.temporal_overlap_points:
        rationale.append(
            f"{candidate.temporal_overlap_points} context points overlap the locality time window"
        )
    if candidate.nearest_context_distance_km is not None:
        rationale.append(
            f"nearest context point is {candidate.nearest_context_distance_km:.1f} km away"
        )
    return CandidateSiteScore(
        locality=candidate.locality.locality,
        total_score=round(total_score, 4),
        sample_signal=round(sample_signal, 4),
        context_signal=round(context_signal, 4),
        temporal_signal=round(temporal_signal, 4),
        distance_signal=round(distance_signal, 4),
        rationale=tuple(rationale),
    )
