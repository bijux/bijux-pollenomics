"""Synthetic cross-border source-contract cases, not historical observations."""

from __future__ import annotations

from dataclasses import replace

from bijux_pollenomics.analysis.propagation.candidates import (
    DEFAULT_PROPAGATION_SCENARIO,
)
from bijux_pollenomics.analysis.propagation.network import (
    PhenomenonEvent,
    PropagationCandidate,
    evaluate_propagation_pair,
    generate_propagation_network,
    generate_propagation_network_exhaustive,
    run_propagation_sensitivity,
)

from ..support import event, scenario


def _norway_sweden_events() -> tuple[PhenomenonEvent, PhenomenonEvent]:
    older = event(
        "synthetic-norway-older",
        country_code="NO",
        latitude=60.0,
        longitude=12.3,
        younger_bp=5600,
        older_bp=5600,
    )
    younger = event(
        "synthetic-sweden-younger",
        country_code="SE",
        latitude=60.1,
        longitude=12.8,
        younger_bp=5500,
        older_bp=5500,
    )
    return older, younger


def test_older_norway_to_younger_sweden_is_cross_border_candidate() -> None:
    older, younger = _norway_sweden_events()
    result = scenario(
        generate_propagation_network((younger, older)),
        DEFAULT_PROPAGATION_SCENARIO.scenario_id,
    )

    assert len(result.directed_candidates) == 1
    candidate = result.directed_candidates[0]
    assert (candidate.source_event_id, candidate.target_event_id) == (
        older.event_id,
        younger.event_id,
    )
    assert (candidate.source_country_code, candidate.target_country_code) == (
        "NO",
        "SE",
    )
    assert candidate.cross_border is True
    assert candidate.candidate_status == "definite_candidate"
    assert candidate.distance_km_unrounded < 100
    assert (candidate.minimum_lag_years, candidate.maximum_lag_years) == (100, 100)


def test_swapping_country_labels_preserves_spatiotemporal_eligibility() -> None:
    older, younger = _norway_sweden_events()
    original = evaluate_propagation_pair(older, younger)
    swapped = evaluate_propagation_pair(
        replace(older, country_code="SE"),
        replace(younger, country_code="NO"),
    )

    assert isinstance(original, PropagationCandidate)
    assert isinstance(swapped, PropagationCandidate)
    assert (
        swapped.distance_km_unrounded,
        swapped.minimum_lag_years,
        swapped.maximum_lag_years,
        swapped.candidate_status,
        swapped.reason_code,
        swapped.directional_arrow_allowed,
    ) == (
        original.distance_km_unrounded,
        original.minimum_lag_years,
        original.maximum_lag_years,
        original.candidate_status,
        original.reason_code,
        original.directional_arrow_allowed,
    )
    assert (original.source_country_code, original.target_country_code) == ("NO", "SE")
    assert (swapped.source_country_code, swapped.target_country_code) == ("SE", "NO")
    assert original.cross_border is swapped.cross_border is True


def test_sweden_finland_pair_outside_radius_is_excluded_by_distance() -> None:
    sweden = event(
        "synthetic-sweden-distant",
        country_code="SE",
        latitude=65.7,
        longitude=22.0,
    )
    finland = event(
        "synthetic-finland-distant",
        country_code="FI",
        latitude=65.85,
        longitude=25.0,
        younger_bp=5500,
        older_bp=5500,
    )

    decision = evaluate_propagation_pair(sweden, finland)

    assert isinstance(decision, PropagationCandidate)
    assert decision.distance_km_unrounded > 100
    assert decision.candidate_status == "excluded_spatial"
    assert decision.cross_border is True
    assert decision.directional_arrow_allowed is False
    assert decision.reason_code == "spatial_threshold_exceeded"


def test_overlapping_sweden_denmark_intervals_remain_indeterminate() -> None:
    sweden = event(
        "synthetic-sweden-overlap",
        country_code="SE",
        latitude=55.6,
        longitude=13.0,
        younger_bp=5500,
        older_bp=5600,
    )
    denmark = event(
        "synthetic-denmark-overlap",
        country_code="DK",
        latitude=55.65,
        longitude=12.6,
        younger_bp=5550,
        older_bp=5650,
    )
    result = scenario(
        generate_propagation_network((sweden, denmark)),
        DEFAULT_PROPAGATION_SCENARIO.scenario_id,
    )

    assert len(result.indeterminate_pairs) == 2
    assert not result.directed_candidates
    assert all(row.cross_border for row in result.indeterminate_pairs)
    assert all(not row.directional_arrow_allowed for row in result.indeterminate_pairs)
    assert {row.candidate_status for row in result.evaluated_pairs} == {
        "indeterminate_order"
    }
    assert all(
        not result_scenario.directed_candidates
        for result_scenario in run_propagation_sensitivity(
            (sweden, denmark)
        ).scenario_results
    )


def test_northern_sweden_search_includes_norwegian_finnish_and_swedish_neighbors() -> (
    None
):
    focal = event(
        "synthetic-northern-sweden-focal",
        country_code="SE",
        latitude=68.95,
        longitude=20.8,
        younger_bp=5600,
        older_bp=5600,
    )
    neighbors = (
        event(
            "synthetic-northern-norway",
            country_code="NO",
            latitude=69.02,
            longitude=20.25,
            younger_bp=5650,
            older_bp=5650,
        ),
        event(
            "synthetic-northern-finland",
            country_code="FI",
            latitude=69.1,
            longitude=21.5,
            younger_bp=5650,
            older_bp=5650,
        ),
        event(
            "synthetic-northern-sweden-neighbor",
            country_code="SE",
            latitude=68.9,
            longitude=20.9,
            younger_bp=5650,
            older_bp=5650,
        ),
    )
    events = (focal, *neighbors)
    indexed = scenario(
        generate_propagation_network(events), DEFAULT_PROPAGATION_SCENARIO.scenario_id
    )
    exhaustive = scenario(
        generate_propagation_network_exhaustive(events),
        DEFAULT_PROPAGATION_SCENARIO.scenario_id,
    )

    assert indexed.as_dict() == exhaustive.as_dict()
    incoming = tuple(
        row
        for row in indexed.directed_candidates
        if row.target_event_id == focal.event_id
    )
    assert {row.source_event_id for row in incoming} == {
        neighbor.event_id for neighbor in neighbors
    }
    assert {row.source_country_code for row in incoming} == {"NO", "FI", "SE"}
    assert all(row.distance_km_unrounded < 100 for row in incoming)
    assert all(row.minimum_lag_years == 50 for row in incoming)
