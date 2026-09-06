"""Network refusal, sensitivity, and determinism accounting."""

from __future__ import annotations

import json

from bijux_pollenomics.analysis.propagation.candidates import (
    DEFAULT_PROPAGATION_SCENARIO,
    CandidatePropagationScenario,
)
from bijux_pollenomics.analysis.propagation.network import (
    COUNTRY_CODES,
    PROPAGATION_SENSITIVITY_SCENARIOS,
    generate_propagation_network,
    generate_propagation_network_exhaustive,
    run_propagation_sensitivity,
)
from hypothesis import given, settings
from hypothesis import strategies as st

from .support import event, scenario


def test_refusal_ledger_accounts_same_site_duplicate_and_missing_coordinates() -> None:
    same_a = event("same-site-a", site_id="governed-site")
    same_b = event(
        "same-site-b", site_id="governed-site", younger_bp=5500, older_bp=5500
    )
    duplicate = event(
        "duplicate",
        latitude=55.7,
        longitude=13.19,
        observation_ids=same_a.observation_ids,
        younger_bp=5500,
        older_bp=5500,
    )
    missing = event(
        "missing", latitude=None, longitude=None, younger_bp=5500, older_bp=5500
    )

    result = scenario(
        generate_propagation_network((same_a, same_b, duplicate, missing)),
        DEFAULT_PROPAGATION_SCENARIO.scenario_id,
    )
    reasons = {row.reason_code for row in result.refusals}

    assert {
        "same_governed_site",
        "duplicate_underlying_observation",
        "invalid_or_missing_coordinate",
    } <= reasons
    assert result.reconciliation.refused_pair_count == len(result.refusals)
    assert not (
        {row.pair_id for row in result.refusals}
        & {row.edge_id for row in result.evaluated_pairs}
    )


def test_sensitivity_runs_declared_scenarios_and_all_country_pair_bins() -> None:
    malmo = event("sensitivity-source", country_code="SE")
    lund = event(
        "sensitivity-target",
        country_code="DK",
        latitude=55.7047,
        longitude=13.191,
        younger_bp=5500,
        older_bp=5500,
    )

    result = run_propagation_sensitivity((malmo, lund))
    scenario_ids = {row.scenario.scenario_id for row in result.scenario_results}

    assert len(PROPAGATION_SENSITIVITY_SCENARIOS) == 16
    assert len(result.scenario_results) == 16
    assert DEFAULT_PROPAGATION_SCENARIO.scenario_id in scenario_ids
    for result_scenario in result.scenario_results:
        country_counts = dict(
            result_scenario.reconciliation.ordered_country_pair_counts
        )
        assert tuple(country_counts) == tuple(
            f"{source}-{target}" for source in COUNTRY_CODES for target in COUNTRY_CODES
        )
        assert sum(dict(result_scenario.reconciliation.status_counts).values()) == len(
            result_scenario.evaluated_pairs
        )
        assert all(
            sum(dict(counts).values()) >= 0 for counts in country_counts.values()
        )
    lag_50 = scenario(result, "rectangular_100km_50yr_v1")
    lag_100 = scenario(result, "rectangular_100km_100yr_v1")
    assert not lag_50.directed_candidates
    assert len(lag_100.directed_candidates) == 1
    assert lag_100.directed_candidates[0].cross_border is True


def test_duplicate_input_and_shuffled_input_are_content_deterministic() -> None:
    events = (
        event("det-a"),
        event("det-b", latitude=55.7, longitude=13.19, younger_bp=5500, older_bp=5500),
        event("det-c", latitude=56.0, longitude=13.3, younger_bp=5450, older_bp=5450),
    )

    forward = generate_propagation_network((*events, events[0]))
    shuffled = generate_propagation_network(
        (events[2], events[0], events[0], events[1])
    )

    assert forward.duplicate_input_event_count == 1
    assert json.dumps(forward.as_dict(), sort_keys=True) == json.dumps(
        shuffled.as_dict(), sort_keys=True
    )


@settings(max_examples=30, deadline=None)
@given(
    points=st.lists(
        st.tuples(
            st.floats(54, 71, allow_nan=False, allow_infinity=False),
            st.floats(5, 32, allow_nan=False, allow_infinity=False),
            st.integers(0, 10_000),
        ),
        min_size=2,
        max_size=8,
    )
)
def test_latitude_index_matches_exhaustive_reference(
    points: list[tuple[float, float, int]],
) -> None:
    events = tuple(
        event(
            f"property-{index}",
            latitude=latitude,
            longitude=longitude,
            younger_bp=age,
            older_bp=age,
        )
        for index, (latitude, longitude, age) in enumerate(points)
    )
    propagation_scenario = CandidatePropagationScenario(
        scenario_id="property_200km_500yr_v1",
        maximum_distance_km=200,
        maximum_lag_years=500,
    )

    indexed = generate_propagation_network(events, scenarios=(propagation_scenario,))
    exhaustive = generate_propagation_network_exhaustive(
        events, scenarios=(propagation_scenario,)
    )

    assert indexed.as_dict() == exhaustive.as_dict()
