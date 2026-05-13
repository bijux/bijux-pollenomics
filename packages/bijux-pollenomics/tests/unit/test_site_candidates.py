from __future__ import annotations

from bijux_pollenomics.adna import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaLocalitySummary,
)
from bijux_pollenomics.analysis.site_candidates import (
    CandidateSiteContext,
    resolve_ranking_profile,
    score_candidate_site,
)


def _locality(
    sample_count: int,
    *,
    species_latin_name: str = "Homo sapiens",
    species_common_name: str = "human",
    modality: str = "metadata_only",
    review_strength: str = "curated_release_metadata",
    provenance_quality: str = "release_manifest_pinned",
    locality_token: str = "shared:sweden:lake-example",
    chronology: tuple[int | None, int | None, int | None] = (3500, 2500, 3000),
) -> AdnaLocalitySummary:
    return AdnaLocalitySummary(
        identity=AdnaLocalityIdentity(
            namespace="shared_locality",
            stable_token=locality_token,
            locality_text="Lake Example",
            political_entity="Sweden",
            source_anchor_tokens=("AADR", "59.0", "18.0"),
        ),
        species_latin_name=species_latin_name,
        species_common_name=species_common_name,
        source_family="AADR" if species_latin_name == "Homo sapiens" else "ENA",
        source_releases=("v66",),
        record_modalities=(modality,),
        review_strengths=(review_strength,),
        provenance_qualities=(provenance_quality,),
        locality="Lake Example",
        coordinates=AdnaCoordinate(
            latitude=59.0,
            longitude=18.0,
            latitude_text="59.0",
            longitude_text="18.0",
            confidence="unknown",
        ),
        sample_count=sample_count,
        sample_ids=tuple(f"I{index}" for index in range(sample_count)),
        datasets=("dataset",),
        chronology=AdnaChronology(
            original_text="3000 BP" if chronology[2] is not None else "",
            time_start_bp=chronology[0],
            time_end_bp=chronology[1],
            time_mean_bp=chronology[2],
            dating_basis="bp_window" if chronology[0] is not None else "unknown",
        ),
        sample_namespace="shared:sample",
    )


def test_score_candidate_site_surfaces_explicit_score_families() -> None:
    candidate = CandidateSiteContext(
        locality=_locality(4),
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
        locality=_locality(2),
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
        locality=_locality(
            3,
            modality="genotypes",
            review_strength="primary_paper_pinned",
        ),
        direct_evidence=(
            _locality(
                3,
                modality="genotypes",
                review_strength="primary_paper_pinned",
            ),
            _locality(
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
