from __future__ import annotations

from bijux_pollenomics.analysis import CandidateSiteContext, score_candidate_site
from bijux_pollenomics.reporting.models import LocalitySummary


def _locality(sample_count: int) -> LocalitySummary:
    return LocalitySummary(
        locality="Lake Example",
        latitude=59.0,
        longitude=18.0,
        latitude_text="59.0",
        longitude_text="18.0",
        sample_count=sample_count,
        sample_ids=("I1",) * sample_count,
        datasets=("dataset",),
    )


def test_score_candidate_site_rewards_combined_signals() -> None:
    candidate = CandidateSiteContext(
        locality=_locality(4),
        nearby_context_points=8,
        nearest_context_distance_km=5.0,
        temporal_overlap_points=3,
    )

    score = score_candidate_site(candidate)

    assert score.total_score > 0.6
    assert "AADR samples anchor the locality" in score.rationale[0]


def test_score_candidate_site_handles_missing_distance() -> None:
    candidate = CandidateSiteContext(
        locality=_locality(1),
        nearby_context_points=0,
        nearest_context_distance_km=None,
        temporal_overlap_points=0,
    )

    score = score_candidate_site(candidate)

    assert score.distance_signal == 0.0
    assert score.total_score > 0.0
