"""Published interval bounds govern temporal eligibility and directional marks."""

from __future__ import annotations

import json

import pytest

from bijux_pollenomics.analysis.propagation.network import (
    EventValidationError,
    PropagationCandidate,
    evaluate_propagation_pair,
    generate_propagation_network,
)
from bijux_pollenomics.core.temporal_semantics import (
    InvalidBpIntervalError,
    canonical_bp_interval,
)

from ..support import event


@pytest.mark.parametrize(
    ("source_bounds", "target_bounds", "lag_bounds", "status", "reason", "arrow"),
    [
        pytest.param(
            (5600, 5600),
            (5500, 5500),
            (100, 100),
            "definite_candidate",
            "all_thresholds_pass",
            True,
            id="TIME-001",
        ),
        pytest.param(
            (5600, 5600),
            (5499, 5499),
            (101, 101),
            "excluded_temporal_too_large",
            "temporal_threshold_exceeded",
            False,
            id="TIME-002",
        ),
        pytest.param(
            (5600, 5600),
            (5501, 5501),
            (99, 99),
            "definite_candidate",
            "all_thresholds_pass",
            True,
            id="TIME-003",
        ),
        pytest.param(
            (5500, 5500),
            (5500, 5500),
            (0, 0),
            "excluded_temporal_nonpositive",
            "temporal_direction_nonpositive",
            False,
            id="TIME-004",
        ),
        pytest.param(
            (5590, 5610),
            (5490, 5510),
            (80, 120),
            "possible_candidate",
            "temporal_threshold_uncertain",
            True,
            id="TIME-005",
        ),
        pytest.param(
            (5580, 5620),
            (5500, 5600),
            (-20, 120),
            "indeterminate_order",
            "temporal_order_indeterminate",
            False,
            id="TIME-006",
        ),
        pytest.param(
            (5610, 5630),
            (5480, 5500),
            (110, 150),
            "excluded_temporal_too_large",
            "temporal_threshold_exceeded",
            False,
            id="TIME-007",
        ),
        pytest.param(
            (5500, 5520),
            (5530, 5550),
            (-50, -10),
            "excluded_temporal_nonpositive",
            "temporal_direction_nonpositive",
            False,
            id="TIME-008",
        ),
        pytest.param(
            (5500, 5500),
            None,
            (None, None),
            "unresolved",
            "chronology_unresolved",
            False,
            id="TIME-009",
        ),
        pytest.param(
            (0, 0),
            None,
            (None, None),
            "unresolved",
            "chronology_unresolved",
            False,
            id="TIME-010",
        ),
    ],
)
def test_temporal_fixture_bounds_survive_pair_publication_and_status_accounting(
    source_bounds: tuple[int, int],
    target_bounds: tuple[int, int] | None,
    lag_bounds: tuple[int | None, int | None],
    status: str,
    reason: str,
    arrow: bool,
) -> None:
    source = event("source", younger_bp=source_bounds[0], older_bp=source_bounds[1])
    target = event(
        "target",
        latitude=55.7047,
        longitude=13.1910,
        younger_bp=target_bounds[0] if target_bounds is not None else None,
        older_bp=target_bounds[1] if target_bounds is not None else None,
        comparability_status="comparable"
        if target_bounds is not None
        else "unresolved",
    )
    pair = evaluate_propagation_pair(source, target)
    assert isinstance(pair, PropagationCandidate)
    assert (pair.minimum_lag_years, pair.maximum_lag_years) == lag_bounds
    assert pair.candidate_status == status
    assert pair.reason_code == reason
    assert pair.directional_arrow_allowed is arrow
    assert pair.route_interpretation_allowed is False
    assert pair.distance_km_unrounded < 100
    published = json.loads(json.dumps(pair.as_dict()))
    assert (
        published["minimum_lag_years"],
        published["maximum_lag_years"],
    ) == lag_bounds
    assert published["candidate_status"] == status
    assert published["directional_arrow_allowed"] is arrow
    assert source.as_dict()["younger_bp"] == source_bounds[0]
    assert target.as_dict()["younger_bp"] == (
        target_bounds[0] if target_bounds is not None else None
    )

    network = generate_propagation_network((source, target)).scenario_results[0]
    assert not network.refusals
    assert len(network.evaluated_pairs) == 2
    assert sum(dict(network.reconciliation.status_counts).values()) == 2
    assert dict(network.reconciliation.status_counts)[status] >= 1
    assert any(row.edge_id == pair.edge_id for row in network.evaluated_pairs)
    assert (
        pair.edge_id in {row.edge_id for row in network.directed_candidates}
    ) is arrow


@pytest.mark.parametrize(
    "bounds",
    [
        pytest.param((5600, 5500), id="TIME-011"),
        pytest.param((5500, None), id="TIME-012"),
    ],
)
def test_invalid_canonical_bounds_refuse_before_pair_status_assignment(
    bounds: tuple[int, int | None],
) -> None:
    with pytest.raises(InvalidBpIntervalError):
        canonical_bp_interval(*bounds)
    with pytest.raises(EventValidationError) as refused:
        event("invalid", younger_bp=bounds[0], older_bp=bounds[1])
    assert refused.value.reason_code == "invalid_event_schema"
