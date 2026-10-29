"""Protect homogeneous cohort denominators, refusal propagation and scoring admission."""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.optimizer_inputs import (
    cohort_outputs as subject,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.optimizer_inputs import (
    cohort_predictions,
    withheld_fold,
    withheld_pollen,
)

from . import cohort_evidence as artificial

Evidence = tuple[
    dict[str, bytes], dict[str, dict[str, Any]], dict[str, Any], dict[str, bytes]
]


@pytest.fixture(scope="module")
def evidence() -> Evidence:
    return artificial.bundle()


def _replace(
    role: str, value: Any, bodies: dict[str, bytes], pins: dict[str, dict[str, Any]]
) -> None:
    bodies[role] = artificial.raw(value)
    pins[role] = artificial.pin(bodies[role])


def _training(
    value: dict[str, Any], bodies: dict[str, bytes], pins: dict[str, dict[str, Any]]
) -> None:
    _replace("training", value, bodies, pins)
    report = json.loads(bodies["report"])
    report["training"] = pins["training"]
    _replace("report", report, bodies, pins)


def _freeze(
    value: dict[str, Any], bodies: dict[str, bytes], pins: dict[str, dict[str, Any]]
) -> None:
    _replace("prediction_freeze", value, bodies, pins)
    report = json.loads(bodies["report"])
    report["prediction_freeze"] = pins["prediction_freeze"]
    _replace("report", report, bodies, pins)


def test_complete_cohort_preserves_unique_and_logical_denominators(
    evidence: Evidence,
) -> None:
    result = subject.validate_saved_outputs(*evidence)
    assert result["counts"]["logical_attempt_references"] == 12480
    assert result["counts"]["unique_attempts"] == 1728
    assert result["counts"]["new_attempts"] == 896
    assert result["reused_attempts"] == 832
    assert result["accepted"] == 1728 and result["refused"] == 0
    assert result["predicted_folds"] == 15 and result["refused_folds"] == 0
    assert len(result["scores"]) == 15


def test_one_failed_unique_ring_refuses_all_thirteen_dependent_folds(
    evidence: Evidence,
) -> None:
    bodies, pins, protocol, inputs = deepcopy(evidence)
    training = json.loads(bodies["training"])
    pool = training["numerical_requests"]
    checksum = next(key for key, row in pool.items() if row["execution"] == "new")
    for row in training["new_attempts"]:
        if row["request_sha256"] == checksum and row["ring_index"] == 0:
            row["accepted"] = False
            row["result"]["success"] = False
    pool[checksum]["selections"][0] = None
    _training(training, bodies, pins)
    events = []
    for row in training["new_attempts"]:
        begin = {
            key: row[key]
            for key in (
                "item_id",
                "request_sha256",
                "ring_index",
                "outer_m",
                "start_id",
                "start",
                "execution",
            )
        }
        events.extend(
            [
                artificial.raw({"event": "attempt_started", **begin}),
                artificial.raw({"event": "attempt_completed", **row}),
            ]
        )
    bodies["trials"] = b"".join(events)
    pins["trials"] = artificial.pin(bodies["trials"])
    failed = sorted(
        {
            row["fold_id"]
            for row in protocol["logical_requests"]
            if row["request_sha256"] == checksum
        }
    )
    frozen = json.loads(bodies["prediction_freeze"])
    frozen["training"] = pins["training"]
    frozen["slots"] = [
        {
            "fold_id": row["fold_id"],
            "record_id": row["record_id"],
            "baseline": row["baseline"],
            "status": "refused",
            "reason": "training_ring_has_no_accepted_fixed_start",
        }
        if row["fold_id"] in failed
        else row
        for row in frozen["slots"]
    ]
    _freeze(frozen, bodies, pins)
    report = json.loads(bodies["report"])
    report.update(predicted_folds=2, refused_folds=13)
    report["failures"] = [
        {
            "fold_id": fold,
            "reason": "training_ring_has_no_accepted_fixed_start",
            "missing": [{"request_sha256": checksum, "ring_index": 0}],
        }
        for fold in failed
    ]
    report["scores"] = [row for row in report["scores"] if row["fold_id"] not in failed]
    _replace("report", report, bodies, pins)
    access = [json.loads(line) for line in bodies["outcome_access"].splitlines()]
    bodies["outcome_access"] = b"".join(
        artificial.raw({**row, "prediction_freeze": pins["prediction_freeze"]})
        for row in access
        if row["fold_id"] not in failed
    )
    pins["outcome_access"] = artificial.pin(bodies["outcome_access"])
    result = subject.validate_saved_outputs(bodies, pins, protocol, inputs)
    assert result["refused"] == 32 and result["predicted_folds"] == 2
    assert result["refused_folds"] == 13 and len(result["scores"]) == 2
    assert len(frozen["slots"]) == 45


def test_pool_taxon_order_cannot_be_relabelled(evidence: Evidence) -> None:
    bodies, pins, protocol, inputs = deepcopy(evidence)
    training = json.loads(bodies["training"])
    axis = next(iter(training["numerical_requests"].values()))["taxa"]
    axis[0], axis[1] = axis[1], axis[0]
    _training(training, bodies, pins)
    with pytest.raises(ReportRebuildError):
        subject.validate_saved_outputs(bodies, pins, protocol, inputs)


@pytest.mark.parametrize(
    ("field", "changed"),
    [("support_profile", "changed-support"), ("local_support_radius_m", 999)],
)
def test_original_forward_support_is_preserved(
    evidence: Evidence, field: str, changed: object
) -> None:
    bodies, pins, protocol, inputs = deepcopy(evidence)
    frozen = json.loads(bodies["prediction_freeze"])
    frozen["slots"][0]["geometry"][field] = changed
    _freeze(frozen, bodies, pins)
    with pytest.raises(ReportRebuildError):
        subject.validate_saved_outputs(bodies, pins, protocol, inputs)


def test_prediction_freeze_cannot_change_after_scoring(evidence: Evidence) -> None:
    bodies, pins, protocol, inputs = deepcopy(evidence)
    bodies["prediction_freeze"] += b" "
    with pytest.raises(ReportRebuildError):
        subject.validate_saved_outputs(bodies, pins, protocol, inputs)


def test_rehashed_target_ancestry_is_rejected(evidence: Evidence) -> None:
    bodies, pins, protocol, inputs = deepcopy(evidence)
    frozen = json.loads(bodies["prediction_freeze"])
    slot = frozen["slots"][0]
    manifest = slot["prediction"]["prediction_manifest"]
    target = slot["record_id"]
    manifest["allowed_input_closure"].append(target)
    manifest["input_lineage"][target] = []
    slot["prediction"]["prediction_manifest_sha256"] = withheld_fold._canonical_sha(
        manifest
    )
    _freeze(frozen, bodies, pins)
    with pytest.raises(ReportRebuildError):
        subject.validate_saved_outputs(bodies, pins, protocol, inputs)


def test_ring_selection_must_be_the_recorded_certified_minimum(
    evidence: Evidence,
) -> None:
    bodies, pins, protocol, inputs = deepcopy(evidence)
    training = json.loads(bodies["training"])
    next(iter(training["numerical_requests"].values()))["selections"][0][
        "selected_objective"
    ] += 0.1
    _training(training, bodies, pins)
    with pytest.raises(ReportRebuildError):
        subject.validate_saved_outputs(bodies, pins, protocol, inputs)


def test_optimizer_attempts_cannot_disappear_from_denominator(
    evidence: Evidence,
) -> None:
    bodies, pins, protocol, inputs = deepcopy(evidence)
    training = json.loads(bodies["training"])
    training["new_attempts"].pop()
    _training(training, bodies, pins)
    with pytest.raises(ReportRebuildError):
        subject.validate_saved_outputs(bodies, pins, protocol, inputs)


def test_metrics_are_recomputed_from_frozen_point_predictions(
    evidence: Evidence,
) -> None:
    bodies, pins, protocol, inputs = deepcopy(evidence)
    report = json.loads(bodies["report"])
    report["scores"][0]["rmse_fraction"] += 0.2
    _replace("report", report, bodies, pins)
    with pytest.raises(ReportRebuildError):
        subject.validate_saved_outputs(bodies, pins, protocol, inputs)


def test_target_keyword_preserves_legacy_default(evidence: Evidence) -> None:
    bodies, _, _, _ = evidence
    frozen = json.loads(bodies["prediction_freeze"])
    report = json.loads(bodies["report"])
    fold = frozen["slots"][0]["fold_id"]
    predictions = [
        {**row["prediction"], "record_id": "author:BECKHAM"}
        for row in frozen["slots"]
        if row["fold_id"] == fold
    ]
    scores = [
        {**row, "record_id": "author:BECKHAM"}
        for row in report["scores"]
        if row["fold_id"] == fold
    ]
    counts = dict.fromkeys(predictions[0]["pollen_fraction"], 1)
    expected = withheld_pollen.validate_pollen_scores(predictions, scores, counts)
    assert expected == withheld_pollen.validate_pollen_scores(
        predictions, scores, counts, target="author:BECKHAM"
    )
    other_predictions = [
        {**row, "record_id": "artificial:other"} for row in predictions
    ]
    other_scores = [{**row, "record_id": "artificial:other"} for row in scores]
    assert expected == withheld_pollen.validate_pollen_scores(
        other_predictions, other_scores, counts, target="artificial:other"
    )


def test_bad_freeze_is_refused_before_any_scoring_decode(
    evidence: Evidence, monkeypatch: pytest.MonkeyPatch
) -> None:
    bodies, pins, protocol, inputs = deepcopy(evidence)
    raw_counts = {body for name, body in inputs.items() if name.endswith("-raw.json")}
    original = withheld_fold._decode

    def guarded(raw: bytes) -> Any:
        assert raw not in raw_counts, (
            "scoring labels decoded before complete freeze admission"
        )
        return original(raw)

    monkeypatch.setattr(cohort_predictions, "_decode", guarded)
    bodies["prediction_freeze"] += b" "
    with pytest.raises(ReportRebuildError):
        subject.validate_saved_outputs(bodies, pins, protocol, inputs)
