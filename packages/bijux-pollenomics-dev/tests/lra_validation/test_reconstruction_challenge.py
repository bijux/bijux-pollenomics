"""Independent expectations and retained negatives for synthetic REVEALS."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import cast

import pandas as pd
import pytest

import bijux_pollenomics_dev.lra_validation.known_landscape as generator
import bijux_pollenomics_dev.lra_validation.reconstruction_challenge as challenge
from bijux_pollenomics_lra.api import RevealsConfig, ValidationError, run_reveals
from bijux_pollenomics_lra.models.results import RevealsResult

JsonObject = dict[str, object]


@pytest.fixture(scope="module")
def report() -> JsonObject:
    return challenge.build_reconstruction_challenge().payload()


def _cases(report: JsonObject) -> list[JsonObject]:
    return cast(list[JsonObject], report["cases"])


def _vector(case: JsonObject, key: str) -> dict[str, float]:
    return cast(dict[str, float], case[key])


def _number(case: JsonObject, key: str) -> float:
    return cast(float, case[key])


def test_public_consumer_executes_all_declared_truth_and_control_cases(
    report: JsonObject,
) -> None:
    assert report["denominators"] == {
        "requested": 8,
        "attempted": 8,
        "predicted": 8,
        "scored": 8,
        "refused": 0,
        "contract_passed": 8,
        "contract_failed": 0,
    }
    assert len({case["case_id"] for case in _cases(report)}) == 8
    assert "bijux_pollenomics_lra" not in inspect.getsource(generator)
    for case in _cases(report):
        manifest = cast(JsonObject, case["production_manifest"])
        assert manifest["algorithm"] == "REVEALS"
        assert case["status"] == "scored"
        assert (
            _number(case, "calculation_max_abs_error_fraction")
            <= challenge.RECOVERY_TOLERANCE
        )
        assert (
            _number(case, "deposition_max_abs_error") <= challenge.DEPOSITION_TOLERANCE
        )
        assert (
            case["input_semantics"]
            == "noise_free_analytic_pollen_weights_not_observed_counts"
        )
    assert cast(JsonObject, report["claims"])["empirical_ecological_accuracy"] is False


def test_matched_recovery_and_ppe_negative_have_independent_algebra(
    report: JsonObject,
) -> None:
    for case in _cases(report):
        if case["control"] not in {"matched_parameters", "ppe_misspecification"}:
            continue
        truth = _vector(case, "true_vegetation_fraction")
        weights = dict(truth)
        if case["control"] == "ppe_misspecification":
            weights["broadleaf"] /= 0.8
        expected = {
            taxon: value / sum(weights.values()) for taxon, value in weights.items()
        }
        assert _vector(case, "reconstructed_vegetation_fraction") == pytest.approx(
            expected, abs=5e-6
        )
        if case["control"] == "matched_parameters":
            assert _number(case, "vegetation_mae_fraction") <= 5e-6
        else:
            assert _number(case, "vegetation_mae_fraction") > 0.02


def test_shuffle_changes_labels_without_changing_support_or_pollen_denominator(
    report: JsonObject,
) -> None:
    for shuffled in _cases(report):
        if shuffled["control"] != "taxon_label_shuffle":
            continue
        baseline = next(
            case
            for case in _cases(report)
            if case["source_case_id"] == shuffled["source_case_id"]
            and case["control"] == "matched_parameters"
        )
        assert baseline["source_case_sha256"] == shuffled["source_case_sha256"]
        assert baseline["config"] == shuffled["config"]
        assert (
            baseline["true_vegetation_fraction"] == shuffled["true_vegetation_fraction"]
        )
        assert sorted(_vector(baseline, "input_pollen_fraction").values()) == sorted(
            _vector(shuffled, "input_pollen_fraction").values()
        )
        assert baseline["input_pollen_fraction"] != shuffled["input_pollen_fraction"]
        assert _number(shuffled, "vegetation_mae_fraction") > 0.02


def test_independent_finite_cell_challenges_retain_model_and_support_mismatch(
    report: JsonObject,
) -> None:
    cases = [case for case in _cases(report) if not case["transport_matched"]]
    assert len(cases) == 2
    for case in cases:
        assert case["inverse_crime_control"] is False
        assert case["interpretation"] == "transport_and_support_mismatch_challenge"
        assert _number(case, "vegetation_mae_fraction") > 0.02
        assert case["vegetation_mae_fraction"] == pytest.approx(
            case["independent_expected_truth_mae_fraction"], abs=5e-6
        )
        assert case["contract_status"] == "passed"


def test_refused_reconstruction_stays_in_attempted_denominator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = run_reveals
    calls = 0

    def refuse_first(
        pollen: pd.DataFrame, params: pd.DataFrame, config: RevealsConfig
    ) -> RevealsResult:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise ValidationError(
                "Synthetic input refusal", reason_code="synthetic_refusal"
            )
        return original(pollen, params, config)

    monkeypatch.setattr(challenge, "run_reveals", refuse_first)
    payload = challenge.build_reconstruction_challenge().payload()
    counts = cast(dict[str, int], payload["denominators"])
    assert counts["requested"] == counts["attempted"] == calls == 8
    assert counts["refused"] == 1
    assert counts["scored"] == counts["contract_passed"] == 7
    refused = [case for case in _cases(payload) if case["status"] == "refused"]
    assert refused[0]["reason_code"] == "synthetic_refusal"
    assert "reconstructed_vegetation_fraction" not in refused[0]


def test_retained_result_matches_scientific_values_on_current_inputs(
    report: JsonObject,
) -> None:
    repository = Path(__file__).resolve().parents[4]
    saved = json.loads(
        (
            repository / "docs/report/synthetic-validation/reconstruction/report.json"
        ).read_text()
    )
    assert saved["denominators"] == report["denominators"]
    current = {case["case_id"]: case for case in _cases(report)}
    assert set(current) == {case["case_id"] for case in saved["cases"]}
    for case in saved["cases"]:
        rebuilt = current[case["case_id"]]
        assert case["control"] == rebuilt["control"]
        assert case["transport_matched"] == rebuilt["transport_matched"]
        assert case["contract_status"] == rebuilt["contract_status"]
        assert case["reconstructed_vegetation_fraction"] == pytest.approx(
            rebuilt["reconstructed_vegetation_fraction"], abs=1e-12
        )
