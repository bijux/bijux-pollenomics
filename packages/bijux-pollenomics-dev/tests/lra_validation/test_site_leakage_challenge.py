"""Known site truth, shuffled training labels and complete exclusion denominators."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics_dev.lra_validation.site_leakage_challenge import (
    build_site_leakage_challenge,
)

JsonObject = dict[str, object]


@pytest.fixture(scope="module")
def report() -> JsonObject:
    return build_site_leakage_challenge()


def _cases(report: JsonObject) -> list[JsonObject]:
    return cast(list[JsonObject], report["cases"])


def test_all_site_rotations_and_control_attempts_remain_visible(
    report: JsonObject,
) -> None:
    assert report["denominators"] == {
        "requested": 24,
        "attempted": 24,
        "predicted": 12,
        "scored": 12,
        "refused": 12,
        "numerical_calls": 12,
        "contract_passed": 24,
        "contract_failed": 0,
    }
    cases = _cases(report)
    assert len({case["target_site_id"] for case in cases}) == 6
    for site in {case["target_site_id"] for case in cases}:
        controls = [case for case in cases if case["target_site_id"] == site]
        assert len(controls) == 4
        for case in controls:
            assert set(cast(list[str], case["excluded_target_record_ids"])) == {
                f"{site}:pollen",
                f"{site}:alias",
            }
            assert case["contract_status"] == "passed"


def test_alias_and_transitive_product_leaks_are_refused_before_engine_call(
    report: JsonObject,
) -> None:
    refused = [case for case in _cases(report) if case["status"] == "refused"]
    assert len(refused) == 12
    for case in refused:
        assert case["reason_code"] == "withheld_input_leakage"
        assert case["numerical_calls"] == 0
        assert "predicted_pollen_fraction" not in case
        if case["control"] == "derived_target_input":
            graph = cast(dict[str, tuple[str, ...]], case["dependency_graph"])
            assert graph["synthetic-derived-product"] == (
                "synthetic-derived-intermediate",
            )
            assert graph["synthetic-derived-intermediate"] == (
                f"{case['target_site_id']}:pollen",
            )


def test_public_predictor_recovers_known_nearest_pair_and_retains_shuffle_scores(
    report: JsonObject,
) -> None:
    summaries = cast(dict[str, JsonObject], report["summaries"])
    baseline = summaries["nearest_site"]
    shuffle = summaries["shuffled_training_sites"]
    assert baseline["sites_scored"] == shuffle["sites_scored"] == 6
    assert cast(float, baseline["site_macro_vegetation_mae_fraction"]) <= 1e-12
    assert cast(float, baseline["site_macro_pollen_mae_fraction"]) <= 1e-12
    assert cast(float, shuffle["site_macro_vegetation_mae_fraction"]) > 0
    assert cast(float, shuffle["site_macro_pollen_hellinger"]) > 0
    for case in _cases(report):
        if case["status"] != "scored":
            continue
        manifest = cast(JsonObject, case["prediction_manifest"])
        closure = cast(list[str], manifest["allowed_input_closure"])
        assert not set(cast(list[str], case["excluded_target_record_ids"])) & set(
            closure
        )
        assert case["prediction_frozen_before_truth_scoring"] is True
        assert case["predicted_vegetation_fraction"] == pytest.approx(
            case["independent_expected_vegetation_fraction"], abs=1e-12
        )
        assert case["predicted_pollen_fraction"] == pytest.approx(
            case["independent_expected_pollen_fraction"], abs=1e-12
        )
        if case["control"] == "shuffled_training_sites":
            assignment = cast(dict[str, str], case["training_site_assignment"])
            assert case["target_site_id"] not in assignment
            assert case["target_site_id"] not in assignment.values()
            assert set(assignment) == set(assignment.values())
            assert all(key != value for key, value in assignment.items())


def test_changing_scoring_store_cannot_change_frozen_predictions(
    report: JsonObject,
) -> None:
    scoring_truth = {
        cast(str, site["site_id"]): {"tree": 0.1, "grass": 0.9}
        for site in cast(list[JsonObject], report["source_sites"])
    }
    changed = build_site_leakage_challenge(scoring_truth=scoring_truth)
    original = {case["case_id"]: case for case in _cases(report)}
    scores_changed = False
    for case in _cases(changed):
        prior = original[case["case_id"]]
        if case["status"] == "scored":
            assert (
                case["prediction_manifest_sha256"]
                == prior["prediction_manifest_sha256"]
            )
            assert (
                case["predicted_pollen_fraction"] == prior["predicted_pollen_fraction"]
            )
            scores_changed |= case["vegetation_score"] != prior["vegetation_score"]
    assert scores_changed


def test_retained_site_result_replays_exact_inputs_and_outputs(
    report: JsonObject,
) -> None:
    repository = Path(__file__).resolve().parents[4]
    saved = json.loads(
        (
            repository / "docs/report/synthetic-validation/site-leakage/report.json"
        ).read_text()
    )
    assert saved == json.loads(json.dumps(report))
    assert cast(JsonObject, report["claims"])["empirical_ecological_accuracy"] is False
    assert cast(JsonObject, report["claims"])["reviewed_source_crosswalk"] is False
