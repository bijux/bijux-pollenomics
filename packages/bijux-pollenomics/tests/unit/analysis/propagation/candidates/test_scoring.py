"""Candidate evidence scoring and fieldwork recommendation policy."""

from __future__ import annotations

from bijux_pollenomics.analysis.propagation.candidates import (
    CandidateSiteContext,
    resolve_ranking_profile,
    score_candidate_site,
)

from .support import locality


def test_score_candidate_site_surfaces_explicit_score_families() -> None:
    candidate = CandidateSiteContext(
        locality=locality(4),
        nearby_context_points=8,
        nearby_context_layer_count=3,
        time_aware_context_points=5,
        temporal_overlap_points=3,
        nearest_context_distance_km=5.0,
    )

    score = score_candidate_site(candidate)

    assert score.ranking_status == "ranked"
    assert score.total_score > 0.3
    assert score.evidence_density_signal > 0.6
    assert score.contextual_support_signal > 0.5
    assert "metadata_only_direct_evidence" in score.warning_flags
    assert score.recommendation_posture == "exploratory_only"


def test_fieldwork_triage_blocks_metadata_only_single_species_candidates() -> None:
    candidate = CandidateSiteContext(
        locality=locality(2),
        nearby_context_points=4,
        nearby_context_layer_count=2,
        time_aware_context_points=4,
        temporal_overlap_points=2,
        nearest_context_distance_km=7.5,
    )

    score = score_candidate_site(
        candidate,
        profile=resolve_ranking_profile("fieldwork_triage"),
    )

    assert score.sampling_recommendation_ready is False
    assert (
        "cross_species_direct_evidence_required_for_fieldwork"
        in score.recommendation_blockers
    )
    assert (
        "non_metadata_direct_evidence_required_for_fieldwork"
        in score.recommendation_blockers
    )


def test_fieldwork_triage_can_clear_recommendation_gate_with_cross_species_evidence() -> (
    None
):
    candidate = CandidateSiteContext(
        locality=locality(
            3,
            modality="genotypes",
            review_strength="primary_paper_pinned",
        ),
        direct_evidence=(
            locality(
                3,
                modality="genotypes",
                review_strength="primary_paper_pinned",
            ),
            locality(
                2,
                species_latin_name="Equus caballus",
                species_common_name="horse",
                modality="archive_reads",
                review_strength="primary_paper_pinned",
                provenance_quality="archive_project_catalog",
            ),
        ),
        nearby_context_points=6,
        nearby_context_layer_count=3,
        time_aware_context_points=6,
        temporal_overlap_points=3,
        nearest_context_distance_km=4.0,
    )

    score = score_candidate_site(
        candidate,
        profile=resolve_ranking_profile("fieldwork_triage"),
    )

    assert score.ranking_status == "ranked"
    assert score.sampling_recommendation_ready is True
    assert score.species_diversity_signal >= 0.6
    assert not score.recommendation_blockers
