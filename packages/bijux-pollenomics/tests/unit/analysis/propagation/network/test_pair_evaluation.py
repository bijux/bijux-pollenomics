"""Temporal, spatial, and cross-border pair evaluation."""

from __future__ import annotations

from dataclasses import replace

from bijux_pollenomics.analysis.propagation.candidates import (
    DEFAULT_PROPAGATION_SCENARIO,
    CandidatePropagationScenario,
)
from bijux_pollenomics.analysis.propagation.network import (
    PropagationCandidate,
    PropagationPairRefusal,
    evaluate_propagation_pair,
    generate_propagation_network,
)
from bijux_pollenomics.core.geospatial.distance import wgs84_inverse_geodesic
from pyproj import Geod

from .support import event, scenario


def test_malmo_5600_to_lund_5500_is_exact_temporal_boundary_candidate() -> None:
    malmo = event("malmo", site_id="malmo", younger_bp=5600, older_bp=5600)
    lund = event(
        "lund",
        site_id="lund",
        latitude=55.7047,
        longitude=13.191,
        younger_bp=5500,
        older_bp=5500,
    )

    result = scenario(
        generate_propagation_network((lund, malmo)),
        DEFAULT_PROPAGATION_SCENARIO.scenario_id,
    )
    candidate = next(
        row
        for row in result.directed_candidates
        if row.source_event_id == malmo.event_id
    )

    assert candidate.target_event_id == lund.event_id
    assert candidate.minimum_lag_years == 100
    assert candidate.maximum_lag_years == 100
    assert candidate.distance_km_unrounded < 100
    assert candidate.directional_arrow_allowed is True
    assert candidate.route_interpretation_allowed is False
    assert result.reconciliation.status_counts == (
        ("definite_candidate", 1),
        ("possible_candidate", 0),
        ("indeterminate_order", 0),
        ("unresolved", 0),
        ("excluded_spatial", 0),
        ("excluded_temporal_nonpositive", 1),
        ("excluded_temporal_too_large", 0),
    )


def test_same_time_and_overlapping_intervals_never_emit_ambiguous_arrows() -> None:
    same_a = event("same-a", younger_bp=5500, older_bp=5500)
    same_b = event(
        "same-b", latitude=55.61, longitude=13.01, younger_bp=5500, older_bp=5500
    )
    overlap_a = event("overlap-a", younger_bp=5500, older_bp=5600)
    overlap_b = event(
        "overlap-b",
        latitude=55.62,
        longitude=13.02,
        younger_bp=5550,
        older_bp=5650,
    )

    same = scenario(
        generate_propagation_network((same_a, same_b)),
        DEFAULT_PROPAGATION_SCENARIO.scenario_id,
    )
    overlap = scenario(
        generate_propagation_network((overlap_a, overlap_b)),
        DEFAULT_PROPAGATION_SCENARIO.scenario_id,
    )

    assert {row.candidate_status for row in same.evaluated_pairs} == {
        "excluded_temporal_nonpositive"
    }
    assert {row.candidate_status for row in overlap.evaluated_pairs} == {
        "indeterminate_order"
    }
    assert all(not row.directional_arrow_allowed for row in same.evaluated_pairs)
    assert all(not row.directional_arrow_allowed for row in overlap.evaluated_pairs)
    assert not overlap.directed_candidates


def test_null_chronology_is_unresolved_while_zero_remains_numeric() -> None:
    undated = event(
        "undated",
        younger_bp=None,
        older_bp=None,
        comparability_status="unresolved",
    )
    zero = event(
        "zero-target",
        latitude=55.61,
        longitude=13.01,
        younger_bp=0,
        older_bp=0,
    )

    result = scenario(
        generate_propagation_network((undated, zero)),
        DEFAULT_PROPAGATION_SCENARIO.scenario_id,
    )

    assert {row.candidate_status for row in result.evaluated_pairs} == {"unresolved"}
    assert all(row.minimum_lag_years is None for row in result.evaluated_pairs)
    assert all(row.maximum_lag_years is None for row in result.evaluated_pairs)
    assert all(not row.directional_arrow_allowed for row in result.evaluated_pairs)


def test_unrounded_distance_controls_exact_boundary_and_epsilon_outside() -> None:
    geod = Geod(ellps="WGS84")
    longitude, latitude, _ = geod.fwd(15.0, 60.0, 90.0, 100_000.0)
    boundary_distance = wgs84_inverse_geodesic(
        latitude_a=60.0,
        longitude_a=15.0,
        latitude_b=latitude,
        longitude_b=longitude,
    ).distance_km_unrounded
    source = event(
        "distance-source",
        latitude=60.0,
        longitude=15.0,
        younger_bp=5600,
        older_bp=5600,
    )
    boundary = event(
        "distance-boundary",
        latitude=latitude,
        longitude=longitude,
        younger_bp=5500,
        older_bp=5500,
    )
    exact_scenario = CandidatePropagationScenario(
        scenario_id="measured_100km_boundary_v1",
        maximum_distance_km=boundary_distance,
        maximum_lag_years=100,
    )

    exact = evaluate_propagation_pair(source, boundary, scenario=exact_scenario)
    assert isinstance(exact, PropagationCandidate)
    assert exact.distance_km_unrounded == exact_scenario.maximum_distance_km
    assert exact.candidate_status == "definite_candidate"

    outside_longitude, outside_latitude, _ = geod.fwd(15.0, 60.0, 90.0, 100_001.0)
    outside = event(
        "distance-outside",
        latitude=outside_latitude,
        longitude=outside_longitude,
        younger_bp=5500,
        older_bp=5500,
    )
    excluded = evaluate_propagation_pair(source, outside)
    assert isinstance(excluded, PropagationCandidate)
    assert excluded.distance_km_unrounded > 100
    assert excluded.distance_km_display == 100.001
    assert excluded.candidate_status == "excluded_spatial"


def test_cross_border_metadata_does_not_change_scientific_decision() -> None:
    source = event("source", country_code="SE", younger_bp=5600, older_bp=5600)
    domestic_target = event(
        "target",
        country_code="SE",
        latitude=55.7,
        longitude=13.19,
        younger_bp=5500,
        older_bp=5500,
    )
    cross_border_target = replace(domestic_target, country_code="DK")

    domestic = evaluate_propagation_pair(source, domestic_target)
    cross_border = evaluate_propagation_pair(source, cross_border_target)

    assert isinstance(domestic, PropagationCandidate)
    assert isinstance(cross_border, PropagationCandidate)
    assert domestic.candidate_status == cross_border.candidate_status
    assert domestic.distance_km_unrounded == cross_border.distance_km_unrounded
    assert domestic.cross_border is False
    assert cross_border.cross_border is True
    assert cross_border.source_country_code == "SE"
    assert cross_border.target_country_code == "DK"


def test_direct_incompatible_pair_is_refused_before_candidate_assignment() -> None:
    taxon = event("taxon")
    role = event(
        "role",
        resolution="ecological_role",
        feature_key="role:cereal_indicator",
    )

    refusal = evaluate_propagation_pair(taxon, role)

    assert isinstance(refusal, PropagationPairRefusal)
    assert refusal.reason_code == "incompatible_feature"
