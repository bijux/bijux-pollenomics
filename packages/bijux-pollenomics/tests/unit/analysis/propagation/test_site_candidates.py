from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st
import pytest

from bijux_pollenomics.adna import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaLocalitySummary,
)
from bijux_pollenomics.analysis.propagation.candidates import (
    DEFAULT_PROPAGATION_SCENARIO,
    CandidatePairRefusalError,
    CandidateSiteContext,
    assess_candidate_propagation,
    classify_candidate_propagation,
    resolve_ranking_profile,
    score_candidate_site,
)
from bijux_pollenomics.analysis.propagation.candidates.scoring import _windows_overlap
from bijux_pollenomics.core.temporal_semantics import canonical_bp_interval


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


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    (
        pytest.param((100, 200, 150), (150, 250, 200), True, id="overlap"),
        pytest.param((100, 300, 200), (150, 200, 175), True, id="containment"),
        pytest.param((100, 200, 150), (200, 300, 250), True, id="endpoint-touch"),
        pytest.param((100, 199, 150), (200, 300, 250), False, id="disjoint"),
        pytest.param((300, 100, 200), (150, 200, 175), False, id="reversed"),
        pytest.param((-1, 100, 50), (0, 50, 25), False, id="negative"),
        pytest.param((None, None, None), (0, 0, 0), False, id="null"),
        pytest.param((None, 100, None), (0, 0, 0), False, id="partial-null"),
        pytest.param((0, 0, 0), (0, 0, 0), True, id="zero-bp"),
    ),
)
def test_direct_chronology_overlap_uses_canonical_closed_bp_intervals(
    left: tuple[int | None, int | None, int | None],
    right: tuple[int | None, int | None, int | None],
    expected: bool,
) -> None:
    assert (
        _windows_overlap(
            _locality(1, chronology=left),
            _locality(1, chronology=right),
        )
        is expected
    )


@pytest.mark.parametrize(
    (
        "fixture_id",
        "distance_km",
        "source",
        "target",
        "expected_status",
        "expected_arrow",
    ),
    (
        (
            "PROP-001",
            16.0,
            (5600, 5600),
            (5500, 5500),
            "definite_candidate",
            True,
        ),
        (
            "PROP-002",
            100.0,
            (5600, 5600),
            (5500, 5500),
            "definite_candidate",
            True,
        ),
        (
            "PROP-003",
            100.001,
            (5600, 5600),
            (5500, 5500),
            "excluded_spatial",
            False,
        ),
        (
            "PROP-004",
            16.0,
            (5600, 5600),
            (5499, 5499),
            "excluded_temporal_too_large",
            False,
        ),
        (
            "PROP-005",
            16.0,
            (5590, 5610),
            (5490, 5510),
            "possible_candidate",
            True,
        ),
        (
            "PROP-006",
            16.0,
            (5580, 5620),
            (5500, 5600),
            "indeterminate_order",
            False,
        ),
        ("PROP-007", 16.0, None, (5500, 5500), "unresolved", False),
        (
            "zero-lag",
            16.0,
            (5500, 5500),
            (5500, 5500),
            "excluded_temporal_nonpositive",
            False,
        ),
    ),
)
def test_golden_candidate_propagation_statuses(
    fixture_id: str,
    distance_km: float,
    source: tuple[int, int] | None,
    target: tuple[int, int] | None,
    expected_status: str,
    expected_arrow: bool,
) -> None:
    del fixture_id
    decision = classify_candidate_propagation(
        distance_km_unrounded=distance_km,
        source_interval=canonical_bp_interval(*source) if source else None,
        target_interval=canonical_bp_interval(*target) if target else None,
    )

    assert decision.candidate_status == expected_status
    assert decision.directional_arrow_allowed is expected_arrow
    assert decision.reason_code


def test_malmo_lund_golden_pair_retains_geodesic_identity() -> None:
    assessment = assess_candidate_propagation(
        source_site_id="malmo",
        target_site_id="lund",
        source_latitude=55.6050,
        source_longitude=13.0038,
        target_latitude=55.7047,
        target_longitude=13.1910,
        source_younger_bp=5600,
        source_older_bp=5600,
        target_younger_bp=5500,
        target_older_bp=5500,
    )

    assert assessment.scenario_id == "rectangular_100km_100yr_v1"
    assert assessment.status.candidate_status == "definite_candidate"
    assert assessment.status.minimum_lag_years == 100
    assert assessment.status.maximum_lag_years == 100
    assert assessment.distance.distance_km_unrounded < 100.0
    assert assessment.distance.distance_algorithm == "WGS84 inverse geodesic"
    assert assessment.shared_location is False


@pytest.mark.parametrize("_fixture_id", [pytest.param("SPACE-010", id="SPACE-010")])
def test_unrounded_distance_alone_controls_admission(_fixture_id: str) -> None:
    decision = classify_candidate_propagation(
        distance_km_unrounded=100.0000004,
        source_interval=canonical_bp_interval(5600, 5600),
        target_interval=canonical_bp_interval(5500, 5500),
    )

    assert round(100.0000004, 3) == 100.0
    assert decision.candidate_status == "excluded_spatial"


@pytest.mark.parametrize(
    ("fixture_id", "distance_km", "expected_status"),
    (
        pytest.param("SPACE-002", 100.0, "definite_candidate", id="SPACE-002"),
        pytest.param("SPACE-003", 100.000001, "excluded_spatial", id="SPACE-003"),
    ),
)
def test_exact_spatial_threshold_uses_unrounded_distance(
    fixture_id: str,
    distance_km: float,
    expected_status: str,
) -> None:
    del fixture_id
    decision = classify_candidate_propagation(
        distance_km_unrounded=distance_km,
        source_interval=canonical_bp_interval(5600, 5600),
        target_interval=canonical_bp_interval(5500, 5500),
    )

    assert decision.candidate_status == expected_status


def test_distinct_co_located_pair_is_spatially_eligible_and_flagged() -> None:
    assessment = assess_candidate_propagation(
        source_site_id="site-a",
        target_site_id="site-b",
        source_latitude=59.0,
        source_longitude=18.0,
        target_latitude=59.0,
        target_longitude=18.0,
        source_younger_bp=100,
        source_older_bp=100,
        target_younger_bp=0,
        target_older_bp=0,
    )

    assert assessment.distance.distance_km_unrounded == 0.0
    assert assessment.shared_location is True
    assert assessment.status.candidate_status == "definite_candidate"


@pytest.mark.parametrize(
    "_fixture_id",
    [pytest.param("SPACE-008/PROP-012", id="SPACE-008-PROP-012")],
)
def test_same_governed_site_is_refused_before_candidate_status(
    _fixture_id: str,
) -> None:
    with pytest.raises(CandidatePairRefusalError) as refusal:
        assess_candidate_propagation(
            source_site_id="same-site",
            target_site_id="same-site",
            source_latitude=59.0,
            source_longitude=18.0,
            target_latitude=59.0,
            target_longitude=18.0,
            source_younger_bp=100,
            source_older_bp=100,
            target_younger_bp=0,
            target_older_bp=0,
        )

    assert refusal.value.reason_code == "same_governed_site"


@given(
    distance=st.floats(
        min_value=0,
        max_value=500,
        allow_nan=False,
        allow_infinity=False,
    ),
    source_age=st.integers(min_value=0, max_value=100_000),
    target_age=st.integers(min_value=0, max_value=100_000),
)
def test_candidate_status_is_mutually_exclusive_and_arrow_safe(
    distance: float,
    source_age: int,
    target_age: int,
) -> None:
    decision = classify_candidate_propagation(
        distance_km_unrounded=distance,
        source_interval=canonical_bp_interval(source_age, source_age),
        target_interval=canonical_bp_interval(target_age, target_age),
        scenario=DEFAULT_PROPAGATION_SCENARIO,
    )

    assert decision.candidate_status in {
        "definite_candidate",
        "possible_candidate",
        "indeterminate_order",
        "unresolved",
        "excluded_spatial",
        "excluded_temporal_nonpositive",
        "excluded_temporal_too_large",
    }
    assert decision.directional_arrow_allowed is (
        decision.candidate_status in {"definite_candidate", "possible_candidate"}
    )
