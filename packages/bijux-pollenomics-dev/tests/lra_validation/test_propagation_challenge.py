"""Derived sample events enter every public rectangular network scenario."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics_dev.lra_validation.propagation_challenge import (
    build_propagation_challenge,
)

JsonObject = dict[str, object]


@pytest.fixture(scope="module")
def report() -> JsonObject:
    return build_propagation_challenge()


def _scenario(report: JsonObject, distance: int, lag: int) -> JsonObject:
    return next(
        row
        for row in cast(list[JsonObject], report["scenarios"])
        if cast(JsonObject, row["scenario"])["maximum_distance_km"] == distance
        and cast(JsonObject, row["scenario"])["maximum_lag_years"] == lag
    )


def _pair(scenario: JsonObject, source: str, target: str) -> JsonObject:
    return next(
        row
        for row in cast(list[JsonObject], scenario["complete_pair_ledger"])
        if row["source_case_id"] == source and row["target_case_id"] == target
    )


def test_complete_fixed_matrix_and_all_pair_denominators(report: JsonObject) -> None:
    assert cast(JsonObject, report["denominators"]) == {
        "derivation_requested": 9,
        "derived": 8,
        "derivation_refused": 1,
        "derivation_contract_passed": 9,
        "scenarios_requested": 16,
        "scenarios_attempted": 16,
        "scenario_contract_passed": 16,
        "pair_attempts": 896,
        "pair_contract_passed": 896,
    }
    scenarios = cast(list[JsonObject], report["scenarios"])
    assert {
        (
            cast(JsonObject, row["scenario"])["maximum_distance_km"],
            cast(JsonObject, row["scenario"])["maximum_lag_years"],
        )
        for row in scenarios
    } == {
        (distance, lag)
        for distance in (25, 50, 100, 200)
        for lag in (50, 100, 200, 500)
    }
    assert all(
        cast(JsonObject, row["denominators"])["complete_ordered_pairs"] == 56
        for row in scenarios
    )


def test_rectangular_boundaries_and_uncertainty_use_raw_values(
    report: JsonObject,
) -> None:
    default = _scenario(report, 100, 100)
    assert (
        cast(JsonObject, _pair(default, "older-no", "younger-se")["output"])[
            "candidate_status"
        ]
        == "definite_candidate"
    )
    boundary = cast(JsonObject, _pair(default, "older-no", "boundary-fi")["output"])
    assert boundary["distance_km_unrounded"] == 100.0
    assert boundary["candidate_status"] == "possible_candidate"
    outside = _pair(default, "older-no", "outside-dk")
    assert cast(JsonObject, outside["output"])["candidate_status"] == "excluded_spatial"
    assert (
        cast(float, cast(JsonObject, outside["output"])["distance_km_unrounded"]) > 100
    )
    assert outside["network_membership"] in {"evaluated", "outside_search_envelope"}
    assert (
        _pair(default, "older-no", "distant-se")["network_membership"]
        == "outside_search_envelope"
    )
    assert (
        cast(JsonObject, _pair(default, "boundary-fi", "younger-se")["output"])[
            "candidate_status"
        ]
        == "indeterminate_order"
    )
    assert (
        cast(JsonObject, _pair(default, "boundary-fi", "younger-se")["output"])[
            "directional_arrow_allowed"
        ]
        is False
    )
    assert (
        cast(
            JsonObject,
            _pair(_scenario(report, 50, 50), "older-no", "lag-boundary-no")["output"],
        )["candidate_status"]
        == "definite_candidate"
    )
    assert (
        cast(
            JsonObject,
            _pair(_scenario(report, 200, 500), "older-no", "distant-se")["output"],
        )["candidate_status"]
        == "excluded_temporal_too_large"
    )


def test_alias_refusals_and_country_annotations_stay_in_ledger(
    report: JsonObject,
) -> None:
    for scenario in cast(list[JsonObject], report["scenarios"]):
        same = _pair(scenario, "older-no", "same-site-alias")
        duplicate = _pair(scenario, "younger-se", "dependent-alias")
        assert cast(JsonObject, same["output"])["reason_code"] == "same_governed_site"
        assert (
            cast(JsonObject, duplicate["output"])["reason_code"]
            == "duplicate_underlying_observation"
        )
        assert (
            same["network_membership"] == duplicate["network_membership"] == "refused"
        )
    candidate = cast(
        JsonObject,
        _pair(_scenario(report, 100, 100), "older-no", "younger-se")["output"],
    )
    assert (
        candidate["source_country_code"] == "NO"
        and candidate["target_country_code"] == "SE"
    )
    assert candidate["cross_border"] is True


def test_derived_inputs_and_gap_are_retained(report: JsonObject) -> None:
    derivations = cast(list[JsonObject], report["derivations"])
    assert len(derivations) == 9
    for row in derivations[:8]:
        event = cast(JsonObject, cast(JsonObject, row["output"])["event"])
        assert event["event_type"] == "derived_first_observed"
        assert event["source_snapshot_id"] == "synthetic-sample-topology"
        assert event["feature_key"] == "whole:pollen"
        assert len(cast(list[JsonObject], row["native_samples"])) == 3
    gap = derivations[-1]
    assert cast(JsonObject, gap["output"])["event"] is None
    assert cast(JsonObject, gap["output"])["reason_code"] == "chronology_unresolved"


def test_indexed_network_retains_exact_independent_eligible_edges(
    report: JsonObject,
) -> None:
    for scenario in cast(list[JsonObject], report["scenarios"]):
        ledger = cast(list[JsonObject], scenario["complete_pair_ledger"])
        expected = {
            (row["source_case_id"], row["target_case_id"])
            for row in ledger
            if cast(JsonObject, row["independent_expectation"]).get("arrow_allowed")
            is True
        }
        actual = {
            (row["source_case_id"], row["target_case_id"])
            for row in ledger
            if row["network_membership"] == "evaluated"
            and cast(JsonObject, row["output"]).get("directional_arrow_allowed") is True
        }
        assert actual == expected
        assert cast(JsonObject, scenario["denominators"])["directed_candidates"] == len(
            expected
        )


def test_retained_report_replays_and_limits_claims(report: JsonObject) -> None:
    root = next(
        parent
        for parent in Path(__file__).parents
        if (parent / "configs/pytest.ini").is_file()
    )
    retained = json.loads(
        (root / "docs/report/synthetic-validation/propagation/report.json").read_text()
    )
    assert retained == json.loads(json.dumps(report))
    claims = cast(JsonObject, report["claims"])
    assert claims["real_source_admission"] is False
    assert claims["all_threshold_profiles_challenged"] is False
    assert claims["taxon_and_ecological_hierarchy_challenged"] is False
