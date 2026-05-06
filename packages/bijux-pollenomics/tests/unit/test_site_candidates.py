from __future__ import annotations

from bijux_pollenomics.adna import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaLocalitySummary,
)
from bijux_pollenomics.analysis import CandidateSiteContext, score_candidate_site


def _locality(sample_count: int) -> AdnaLocalitySummary:
    return AdnaLocalitySummary(
        identity=AdnaLocalityIdentity(
            namespace="homo_sapiens:locality",
            stable_token="homo_sapiens:aadr:sweden:lake-example:59-0-18-0",
            locality_text="Lake Example",
            political_entity="Sweden",
            source_anchor_tokens=("AADR", "59.0", "18.0"),
        ),
        species_latin_name="Homo sapiens",
        species_common_name="human",
        source_family="AADR",
        source_releases=("v66",),
        record_modalities=("metadata_only",),
        review_strengths=("curated_release_metadata",),
        provenance_qualities=("release_manifest_pinned",),
        locality="Lake Example",
        coordinates=AdnaCoordinate(
            latitude=59.0,
            longitude=18.0,
            latitude_text="59.0",
            longitude_text="18.0",
            confidence="unknown",
        ),
        sample_count=sample_count,
        sample_ids=("I1",) * sample_count,
        datasets=("dataset",),
        chronology=AdnaChronology(
            original_text="3000 BP",
            time_start_bp=None,
            time_end_bp=None,
            time_mean_bp=None,
            dating_basis="unknown",
        ),
        sample_namespace="homo_sapiens:aadr_genetic_id",
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
    assert "ancient-DNA samples anchor the locality" in score.rationale[0]


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
