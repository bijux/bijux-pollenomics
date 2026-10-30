"""Source-bound presentation of the evaluator's short-circuit branch order."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
import pytest

from bijux_pollenomics.analysis.propagation.candidates import (
    CandidatePropagationScenario,
)
from bijux_pollenomics.analysis.propagation.network import (
    PhenomenonEvent,
    PropagationCandidate,
    evaluate_propagation_pair,
    generate_propagation_network,
)
from bijux_pollenomics.analysis.propagation.projection import (
    project_propagation_network,
)
from bijux_pollenomics.analysis.propagation.projection.relation import (
    candidate_relation_details,
)
from bijux_pollenomics.reporting.map_document.evidence import normalize_atlas_evidence

from .support import event

IDS = (
    "spatial_threshold",
    "chronology_available",
    "positive_lag_possible",
    "positive_lag_certain",
    "lag_within_limit_possible",
    "lag_within_limit_certain",
)


def pair(
    source_bounds: tuple[int, int],
    target_bounds: tuple[int, int] | None,
    distance_limit: float = 100,
) -> tuple[
    PropagationCandidate, PhenomenonEvent, PhenomenonEvent, CandidatePropagationScenario
]:
    source = event("source", younger_bp=source_bounds[0], older_bp=source_bounds[1])
    target = event(
        "target",
        latitude=55.61,
        younger_bp=target_bounds[0] if target_bounds else None,
        older_bp=target_bounds[1] if target_bounds else None,
        comparability_status="comparable" if target_bounds else "unresolved",
    )
    scenario = CandidatePropagationScenario("test-scenario", distance_limit, 100)
    row = evaluate_propagation_pair(source, target, scenario=scenario)
    assert isinstance(row, PropagationCandidate)
    return row, source, target, scenario


@pytest.mark.parametrize(
    ("source_bounds", "target_bounds", "distance", "status", "checks"),
    [
        ((5600, 5600), (5500, 5500), 100, "definite_candidate", ["pass"] * 6),
        (
            (5600, 5650),
            (5500, 5500),
            100,
            "possible_candidate",
            ["pass"] * 5 + ["qualify"],
        ),
        (
            (5500, 5600),
            (5550, 5650),
            100,
            "indeterminate_order",
            ["pass"] * 3 + ["qualify"] + ["not_evaluated"] * 2,
        ),
        (
            (5600, 5600),
            None,
            100,
            "unresolved",
            ["pass", "unavailable"] + ["not_evaluated"] * 4,
        ),
        (
            (5500, 5500),
            (5600, 5600),
            100,
            "excluded_temporal_nonpositive",
            ["pass"] * 2 + ["refuse"] + ["not_evaluated"] * 3,
        ),
        (
            (5700, 5700),
            (5500, 5500),
            100,
            "excluded_temporal_too_large",
            ["pass"] * 4 + ["refuse", "not_evaluated"],
        ),
        (
            (5600, 5600),
            (5500, 5500),
            0,
            "excluded_spatial",
            ["refuse"] + ["not_evaluated"] * 5,
        ),
    ],
)
def test_all_candidate_statuses_explain_only_reached_checks(
    source_bounds: tuple[int, int],
    target_bounds: tuple[int, int] | None,
    distance: float,
    status: str,
    checks: list[str],
) -> None:
    row, source, target, scenario = pair(source_bounds, target_bounds, distance)
    original = row.as_dict()
    assert row.candidate_status == status
    details = candidate_relation_details(row, source, target, scenario)
    assert details["basis"] == "derived_governed_evaluator_branch_explanation"
    assert details["scenario_id"] == scenario.scenario_id
    assert details["rule_type"] == "rectangular"
    assert details["maximum_distance_km"] == scenario.maximum_distance_km
    assert details["maximum_lag_years"] == scenario.maximum_lag_years
    predicates = details["predicates"]
    assert isinstance(predicates, list)
    assert [item["predicate_id"] for item in predicates] == list(IDS)
    assert [item["status"] for item in predicates] == checks
    for item in predicates:
        if item["status"] == "not_evaluated":
            assert item["observed"] is None
    # Spatial short-circuit must not claim the already-computed lags were tested.
    if status == "excluded_spatial":
        assert row.minimum_lag_years == 100
    assert row.as_dict() == original
    schema = json.loads(
        Path(
            "configs/scientific-contracts/propagation-candidate.schema.json"
        ).read_text()
    )
    Draft202012Validator(schema).validate(original)
    assert "relation_details" not in original


@pytest.mark.parametrize(
    ("source_bounds", "target_bounds", "expected", "predicate", "outcome"),
    [
        ((5600, 5600), (5500, 5500), "definite_candidate", 5, "pass"),
        ((5600, 5650), (5500, 5500), "possible_candidate", 4, "pass"),
        ((5600, 5600), (5500, 5600), "indeterminate_order", 3, "qualify"),
        ((5500, 5500), (5500, 5500), "excluded_temporal_nonpositive", 2, "refuse"),
    ],
)
def test_exact_zero_and_lag_limit_boundaries(
    source_bounds: tuple[int, int],
    target_bounds: tuple[int, int],
    expected: str,
    predicate: int,
    outcome: str,
) -> None:
    row, source, target, scenario = pair(source_bounds, target_bounds)
    assert row.candidate_status == expected
    predicates = candidate_relation_details(row, source, target, scenario)["predicates"]
    assert isinstance(predicates, list)
    assert predicates[predicate]["status"] == outcome


def test_exact_distance_limit_is_inclusive() -> None:
    row, source, target, scenario = pair((5600, 5600), (5500, 5500))
    exact = replace(scenario, maximum_distance_km=row.distance_km_unrounded)
    predicates = candidate_relation_details(row, source, target, exact)["predicates"]
    assert isinstance(predicates, list)
    assert predicates[0]["status"] == "pass"
    assert predicates[0]["observed"] == predicates[0]["threshold"]


@pytest.mark.parametrize(
    "change",
    [
        {"event_id": "foreign-event"},
        {"site_id": "foreign-site"},
        {"build_id": "foreign-build"},
        {"measurement_semantics_id": "foreign-measurement"},
        {"younger_bp": 5800, "older_bp": 5800},
    ],
)
def test_endpoint_mismatch_is_refused(change: dict[str, Any]) -> None:
    row, source, target, scenario = pair((5600, 5600), (5500, 5500))
    with pytest.raises(ValueError, match="conflicts"):
        candidate_relation_details(row, replace(source, **change), target, scenario)


@pytest.mark.parametrize(
    "change",
    [
        {"candidate_status": "possible_candidate"},
        {"reason_code": "unrecorded-reason"},
        {"minimum_lag_years": 99},
        {"maximum_lag_years": 101},
        {"directional_arrow_allowed": False},
    ],
)
def test_stored_decision_mismatch_is_refused(change: dict[str, Any]) -> None:
    row, source, target, scenario = pair((5600, 5600), (5500, 5500))
    with pytest.raises(ValueError, match="decision"):
        candidate_relation_details(replace(row, **change), source, target, scenario)


@pytest.mark.parametrize(
    "change", [{"scenario_id": "foreign"}, {"maximum_lag_years": 99}]
)
def test_scenario_mismatch_is_refused(change: dict[str, Any]) -> None:
    row, source, target, scenario = pair((5600, 5600), (5500, 5500))
    with pytest.raises(ValueError, match="conflicts"):
        candidate_relation_details(row, source, target, replace(scenario, **change))


def test_current_network_projection_retains_endpoints_and_transport_without_readmission() -> (
    None
):
    _, source, target, _ = pair((5600, 5600), (5500, 5500))
    network = generate_propagation_network((source, target))
    before = network.as_dict()
    products = project_propagation_network(network)
    features = products["directed_candidates.geojson"]["features"]
    assert isinstance(features, list) and len(features) == 1
    properties = features[0]["properties"]
    row = network.scenario_results[0].directed_candidates[0]
    assert all(properties[key] == value for key, value in row.as_dict().items())
    assert properties["source_event"] == source.as_dict()
    assert properties["target_event"] == target.as_dict()
    assert properties["relation_details"]["rule_type"] == "rectangular"
    edge = {
        **properties,
        "signal_id": "selected-signal",
        "source_record_id": source.source_record_id,
        "target_record_id": target.source_record_id,
        "source_country": source.country_code,
        "target_country": target.country_code,
    }
    evidence = normalize_atlas_evidence(
        detail_records=[],
        sequence_records=[],
        edge_records=[edge],
        scientific_signals=[
            {
                "signal_id": "selected-signal",
                "feature_key": source.feature_key,
                "resolution": "taxon",
                "label": "Controlled signal",
                "status": "accepted",
            }
        ],
    )
    assert (
        evidence.edge_records[0]["relation_details"] == properties["relation_details"]
    )
    assert evidence.edge_records[0]["source_event"] == source.as_dict()
    assert network.as_dict() == before
    assert products["directed_candidates.geojson"]["source_refused_pair_count"] == 0


def test_pre_candidate_refusal_does_not_become_a_drawable_relation() -> None:
    _, source, target, _ = pair((5600, 5600), (5500, 5500))
    network = generate_propagation_network(
        (source, replace(target, site_id=source.site_id))
    )
    products = project_propagation_network(network)
    assert products["directed_candidates.geojson"]["features"] == []
    assert products["indeterminate_pairs.geojson"]["features"] == []
    assert products["directed_candidates.geojson"]["source_refused_pair_count"] == 2
