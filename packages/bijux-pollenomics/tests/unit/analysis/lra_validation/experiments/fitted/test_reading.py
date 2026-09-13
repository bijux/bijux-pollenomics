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
from bijux_pollenomics.analysis.lra_validation.splits import (
    grouped_block_holdouts,
    grouped_leave_one_out,
)

from .test_admission import block_payload


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
            "method": FITTED_METHOD,
            "status": "refused",
            "reason_code": "synthetic_training_refusal",
        }
        for fold in folds
        for record in fold.test_record_ids
    ]
    return {
        "profile": BLOCK_PROFILE,
        "experiment": "all_target_pollen_withheld_spatial_blocks",
        "uncertainty_status": "point_predictions_only_intervals_not_implemented",
        "interrupted": False,
        "block_fit_records": {},
        "folds": fold_rows,
        "record_groups": groups,
        "methods": [FITTED_METHOD],
        "evaluation_roles": FITTED_ROLES,
        "predictions": [],
        "failures": failures,
        "block_admissions": {},
        "block_model_sha256": {},
        "split_manifest_sha256": manifest_sha256(fold_rows),
        "requested_folds": 3,
        "requested_predictions": 9,
        "generated_predictions": 0,
        "failed_predictions": 9,
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
    assert len(rows) == 18 and all(
        row["score"]["status"] == "prediction_failed" for row in rows
    )
    assert json.loads((score.directory / "outcome_access.json").read_text()) == []


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "unknown_record",
        "wrong_group",
        "wrong_count",
        "boolean_count",
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
        scientific["failures"][0]["group_id"] = scientific["failures"][1]["group_id"]
    elif mutation == "wrong_count":
        scientific["requested_predictions"] = 8
    elif mutation == "boolean_count":
        scientific["generated_predictions"] = False
    elif mutation == "missing_fold":
        scientific["folds"].pop()
    else:
        scientific["methods"] = ["invented_method"]
    product = publish(tmp_path / "product", scientific)
    with pytest.raises(ValidationRefusal):
        read_spatial_block_predictions(
            product.directory, expected_manifest_sha256=product.manifest_sha256
        )
