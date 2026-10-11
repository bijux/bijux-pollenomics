"""Known change truth is separate from the public sample estimator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics_dev.lra_validation.change_time_challenge import (
    build_change_time_challenge,
)

JsonObject = dict[str, object]


@pytest.fixture(scope="module")
def report() -> JsonObject:
    return build_change_time_challenge()


def _cases(report: JsonObject) -> dict[str, JsonObject]:
    return {
        cast(str, row["case_id"]): row
        for row in cast(list[JsonObject], report["cases"])
    }


def test_attempt_denominators_include_biased_results_and_refusals(
    report: JsonObject,
) -> None:
    assert report["denominators"] == {
        "requested": 19,
        "attempted": 19,
        "estimated": 7,
        "refused": 12,
        "contract_passed": 19,
        "exact_change_recovered": 4,
        "biased_change_estimates": 3,
    }
    assert report["scored_estimate_mean_absolute_error_years"] == pytest.approx(300 / 7)


def test_sparse_sampling_and_shuffle_bias_remain_visible(report: JsonObject) -> None:
    cases = _cases(report)
    dense = cases["dense-reported_positive_v1"]
    sparse = cases["sparse-reported_positive_v1"]
    assert dense["exact_change_recovered"] is True
    assert sparse["observed_detection_delay_years"] == 100
    assert sparse["exact_change_recovered"] is False
    shuffled = cases["shuffled-sample-values"]
    assert shuffled["signed_age_bias_years"] == 100
    assert shuffled["observed_detection_delay_years"] == -100
    assert shuffled["truth_scoring_status"] == "biased"


def test_chronology_gap_and_nonpersistent_positives_are_not_scored_as_success(
    report: JsonObject,
) -> None:
    cases = _cases(report)
    for name, expected in (
        ("chronology-gap", "chronology_unresolved"),
        ("isolated-positive", "insufficient_persistence"),
        ("terminal-positive", "insufficient_persistence"),
        ("no-change-negative-control", "threshold_not_met"),
    ):
        row = cases[name]
        assert cast(JsonObject, row["output"])["reason_code"] == expected
        assert row["absolute_age_error_years"] is None
        assert row["exact_change_recovered"] is None
    gap_samples = cast(list[JsonObject], cases["chronology-gap"]["native_samples"])
    assert gap_samples[2]["younger_bp"] is None
    assert gap_samples[2]["older_bp"] is None
    context = cast(
        list[JsonObject], cases["uncalibrated-native-ages"]["native_samples"]
    )
    assert context[0]["source_age_value"] == 5600
    assert context[0]["source_age_unit"] == "uncalibrated_radiocarbon_bp"
    assert context[0]["younger_bp"] is None
    assert (
        cast(JsonObject, cases["uncalibrated-native-ages"]["output"])["reason_code"]
        == "chronology_unresolved"
    )


def test_scoring_truth_cannot_change_frozen_predictions(report: JsonObject) -> None:
    alternate = build_change_time_challenge(scoring_change_bp=5600)
    for original, changed in zip(
        cast(list[JsonObject], report["cases"]),
        cast(list[JsonObject], alternate["cases"]),
        strict=True,
    ):
        assert original["output"] == changed["output"]
        assert original["native_samples"] == changed["native_samples"]
    assert (
        report["scored_estimate_mean_absolute_error_years"]
        != alternate["scored_estimate_mean_absolute_error_years"]
    )


def test_claimed_feature_family_and_snapshot_controls_refuse(
    report: JsonObject,
) -> None:
    cases = _cases(report)
    for name, reason in (
        ("mixed-native-feature", "incompatible_sample_feature"),
        ("mixed-source-family", "incompatible_sample_source_family"),
        ("stale-source-snapshot", "incompatible_sample_source_snapshot"),
    ):
        row = cases[name]
        output = cast(JsonObject, row["output"])
        assert output["event"] is None
        assert output["reason_code"] == reason
        assert row["absolute_age_error_years"] is None
        assert row["status"] == "refused"


def test_retained_report_matches_replay_and_scoped_claims(report: JsonObject) -> None:
    root = next(
        parent
        for parent in Path(__file__).parents
        if (parent / "configs/pytest.ini").is_file()
    )
    retained = json.loads(
        (root / "docs/report/synthetic-validation/change-time/report.json").read_text()
    )
    assert retained == json.loads(json.dumps(report))
    assert cast(JsonObject, report["claims"])["empirical_threshold_validation"] is False
    assert (
        cast(JsonObject, report["claims"])["continuous_presence_established"] is False
    )
