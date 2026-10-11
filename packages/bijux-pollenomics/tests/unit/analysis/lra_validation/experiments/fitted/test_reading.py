"""Original block accounting stays explicit even when no scientific prediction succeeds."""

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import (
    ValidationRefusal,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.experiments import (
    read_spatial_block_predictions,
    score_experiment_predictions,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    BLOCK_BASELINE_METHOD,
    BLOCK_PROFILE,
    FITTED_METHOD,
    FITTED_ROLES,
    SpatialBlockExperimentSpec,
)
from bijux_pollenomics.analysis.lra_validation.experiments.outputs import (
    publish_phase,
    stage_directory,
    write_json,
)
from bijux_pollenomics.analysis.lra_validation.experiments.reading.blocks import (
    _refuse_outcome_fields,
    _validate_block_baseline,
)
from bijux_pollenomics.analysis.lra_validation.splits import (
    grouped_block_holdouts,
    grouped_leave_one_out,
)

from .test_admission import block_payload
from .test_blocks import training_mean_row_fixture


def refusal_inventory(root: Path) -> dict[str, Any]:
    spec = SpatialBlockExperimentSpec(block_payload(root))
    (root / "declared-request.json").write_text(json.dumps(spec.request()))
    records = [site.record for site in spec.sites]
    folds = grouped_block_holdouts(records)
    groups = {
        record: f.test_group_ids[0]
        for f in grouped_leave_one_out(records)
        for record in f.test_record_ids
    }
    fold_rows = json.loads(json.dumps([fold.as_dict() for fold in folds]))
    failures = [
        {
            "fold_id": fold.fold_id,
            "record_id": record,
            "group_id": groups[record],
            "method": method,
            "status": "refused",
            "reason_code": "synthetic_training_refusal",
        }
        for fold in folds
        for record in fold.test_record_ids
        for method in (FITTED_METHOD, BLOCK_BASELINE_METHOD)
    ]
    return {
        "profile": BLOCK_PROFILE,
        "experiment": "all_target_pollen_withheld_spatial_blocks",
        "uncertainty_status": "point_predictions_only_intervals_not_implemented",
        "interrupted": False,
        "block_fit_records": {},
        "folds": fold_rows,
        "record_groups": groups,
        "methods": [FITTED_METHOD, BLOCK_BASELINE_METHOD],
        "evaluation_roles": FITTED_ROLES,
        "predictions": [],
        "failures": failures,
        "block_admissions": {},
        "block_model_sha256": {},
        "block_baseline_model_sha256": {},
        "split_manifest_sha256": manifest_sha256(fold_rows),
        "requested_folds": 3,
        "requested_predictions": 18,
        "generated_predictions": 0,
        "failed_predictions": 18,
        "refused_predictions": 18,
        "not_run_predictions": 0,
        "failed_folds": 3,
        "all_predictions_generated": False,
        "scientific_acceptance": "not_evaluated",
    }


def publish(root: Path, scientific: dict[str, Any]) -> Any:
    stage = stage_directory(root)
    write_json(stage, "predictions.json", scientific["predictions"])
    write_json(stage, "models.json", scientific["block_fit_records"])
    write_json(
        stage,
        "experiment.json",
        {
            "schema_version": "lra-spatial-block-experiment.v1",
            "request": json.loads(
                (root.parent / "inputs/declared-request.json").read_text()
            ),
        },
    )
    return publish_phase(
        stage, root, phase="predictions", profile=BLOCK_PROFILE, scientific=scientific
    )


def test_failed_block_targets_are_scored_without_opening_outcomes(
    tmp_path: Path,
) -> None:
    scientific = refusal_inventory(tmp_path / "inputs")
    product = publish(tmp_path / "product", scientific)
    _, _, folds, predictions, _ = read_spatial_block_predictions(
        product.directory, expected_manifest_sha256=product.manifest_sha256
    )
    assert len(folds) == 3 and not predictions
    inventory = {
        "schema_version": "lra-experiment-outcomes.v1",
        "data_kind": "synthetic",
        "records": {
            record: {"path": record + "-never-created.json", "sha256": "a" * 64}
            for record in scientific["record_groups"]
        },
    }
    score = score_experiment_predictions(
        product.directory,
        expected_manifest_sha256=product.manifest_sha256,
        outcome_root=tmp_path / "inputs",
        outcome_inventory=inventory,
        destination=tmp_path / "scores",
    )
    rows = json.loads((score.directory / "scores.json").read_text())
    assert len(rows) == 36 and all(
        row["score"]["status"] == "prediction_failed" for row in rows
    )
    assert {(row["method"], row["method_kind"]) for row in rows} == {
        (FITTED_METHOD, "fitted_spatial"),
        (BLOCK_BASELINE_METHOD, "admitted_reconstruction_training_mean"),
    }
    assert json.loads((score.directory / "outcome_access.json").read_text()) == []


def test_baseline_row_does_not_require_retained_fitted_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scientific = refusal_inventory(tmp_path / "inputs")
    row, _, admission, model_sha256 = training_mean_row_fixture(
        tmp_path / "inputs", monkeypatch
    )
    key = (row["fold_id"], row["record_id"], row["method"])
    scientific["failures"] = [
        failure
        for failure in scientific["failures"]
        if (failure["fold_id"], failure["record_id"], failure["method"]) != key
    ]
    scientific["predictions"] = [row]
    scientific["block_admissions"] = {row["fold_id"]: admission}
    scientific["block_baseline_model_sha256"] = {row["fold_id"]: model_sha256}
    scientific["generated_predictions"] = 1
    scientific["failed_predictions"] = 17
    scientific["refused_predictions"] = 17
    product = publish(tmp_path / "product", scientific)
    _, _, _, rows, methods = read_spatial_block_predictions(
        product.directory, expected_manifest_sha256=product.manifest_sha256
    )
    assert methods == (FITTED_METHOD, BLOCK_BASELINE_METHOD)
    assert rows[key]["baseline_model_sha256"] == model_sha256


@pytest.mark.parametrize("method", [FITTED_METHOD, BLOCK_BASELINE_METHOD])
def test_all_block_methods_refuse_outcome_fields(method: str) -> None:
    with pytest.raises(ValidationRefusal, match="target outcomes"):
        _refuse_outcome_fields({"method": method, "observed_cover": {}})


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "unknown_record",
        "wrong_group",
        "wrong_count",
        "boolean_count",
        "wrong_refused_count",
        "wrong_not_run_count",
        "missing_fold",
        "invented_method",
    ],
)
def test_rehashed_block_accounting_contradictions_refuse(
    tmp_path: Path, mutation: str
) -> None:
    scientific = deepcopy(refusal_inventory(tmp_path / "inputs"))
    if mutation == "missing":
        scientific["failures"].pop()
    elif mutation == "duplicate":
        scientific["failures"][0] = scientific["failures"][1]
    elif mutation == "unknown_record":
        scientific["failures"][0]["record_id"] = "unknown"
    elif mutation == "wrong_group":
        scientific["failures"][0]["group_id"] = next(
            failure["group_id"]
            for failure in scientific["failures"]
            if failure["group_id"] != scientific["failures"][0]["group_id"]
        )
    elif mutation == "wrong_count":
        scientific["requested_predictions"] = 8
    elif mutation == "boolean_count":
        scientific["generated_predictions"] = False
    elif mutation == "wrong_refused_count":
        scientific["refused_predictions"] = 17
    elif mutation == "wrong_not_run_count":
        scientific["not_run_predictions"] = 1
    elif mutation == "missing_fold":
        scientific["folds"].pop()
    else:
        scientific["methods"] = ["invented_method"]
    product = publish(tmp_path / "product", scientific)
    with pytest.raises(ValidationRefusal):
        read_spatial_block_predictions(
            product.directory, expected_manifest_sha256=product.manifest_sha256
        )


@pytest.mark.parametrize(
    "mutation",
    ["cover", "model_composition", "excluded_lineage", "outcome_reference"],
)
def test_rehashed_block_baseline_mutations_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    row, outer, admission, expected_model = training_mean_row_fixture(
        tmp_path, monkeypatch
    )
    _validate_block_baseline(row, outer, admission, expected_model)
    changed = deepcopy(row)
    if mutation == "cover":
        changed["vegetation_fraction"] = {"Alnus": 0.1, "Betula": 0.9}
    elif mutation == "model_composition":
        model = changed["baseline_model_manifest"]
        first = next(iter(model["training_compositions"]))
        model["training_compositions"][first] = {"Alnus": 0.1, "Betula": 0.9}
        changed["baseline_model_sha256"] = manifest_sha256(model)
        expected_model = changed["baseline_model_sha256"]
    elif mutation == "excluded_lineage":
        model = changed["baseline_model_manifest"]
        excluded = admission["excluded_training_record_ids"][0]
        model["input_lineage"][excluded] = []
        model["training_input_ids"].append(excluded)
        model["allowed_input_closure"].append(excluded)
        model["allowed_input_closure"].sort()
        changed["baseline_model_sha256"] = manifest_sha256(model)
        expected_model = changed["baseline_model_sha256"]
    else:
        changed["outcome_reference"] = "not-allowed"
    changed["prediction_manifest_sha256"] = manifest_sha256(
        {
            key: value
            for key, value in changed.items()
            if key != "prediction_manifest_sha256"
        }
    )
    with pytest.raises(ValidationRefusal):
        _validate_block_baseline(changed, outer, admission, expected_model)
