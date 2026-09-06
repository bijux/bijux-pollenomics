"""WGS84 distance boundaries and governed-site identity refusal."""

from __future__ import annotations

import pytest
from bijux_pollenomics.analysis.propagation.candidates import (
    CandidatePairRefusalError,
    assess_candidate_propagation,
    classify_candidate_propagation,
)
from bijux_pollenomics.core.temporal_semantics import canonical_bp_interval


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


def test_unrounded_distance_alone_controls_admission() -> None:
    decision = classify_candidate_propagation(
        distance_km_unrounded=100.0000004,
        source_interval=canonical_bp_interval(5600, 5600),
        target_interval=canonical_bp_interval(5500, 5500),
    )

    assert round(100.0000004, 3) == 100.0
    assert decision.candidate_status == "excluded_spatial"


@pytest.mark.parametrize(
    ("distance_km", "expected_status"),
    (
        pytest.param(100.0, "definite_candidate", id="SPACE-002"),
        pytest.param(100.000001, "excluded_spatial", id="SPACE-003"),
    ),
)
def test_exact_spatial_threshold_uses_unrounded_distance(
    distance_km: float,
    expected_status: str,
) -> None:
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


def test_same_governed_site_is_refused_before_candidate_status() -> None:
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
