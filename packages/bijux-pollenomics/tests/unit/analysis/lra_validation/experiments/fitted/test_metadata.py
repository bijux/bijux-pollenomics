"""Saved block declarations cannot contradict complete folds or scientific posture."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import (
    ValidationRefusal,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.experiments.fitted.metadata import (
    validate_block_metadata,
)

from .test_reading import refusal_inventory


@pytest.mark.parametrize(
    "mutation",
    [
        "removed_block",
        "catalogue_block",
        "empirical",
        "uncertainty",
        "interrupt_type",
        "hidden_interruption",
        "invented_fit",
    ],
)
def test_complete_metadata_refuses_rehashed_contradictions(
    tmp_path: Path, mutation: str
) -> None:
    scientific = refusal_inventory(tmp_path)
    request = json.loads((tmp_path / "declared-request.json").read_text())
    experiment = {
        "schema_version": "lra-spatial-block-experiment.v1",
        "request": request,
    }
    original = deepcopy(scientific)
    folds = {fold["fold_id"]: fold for fold in scientific["folds"]}
    validate_block_metadata(experiment, scientific, folds, {}, {})
    if mutation == "removed_block":
        removed = scientific["folds"].pop()["fold_id"]
        scientific["failures"] = [
            row for row in scientific["failures"] if row["fold_id"] != removed
        ]
        scientific.update(
            requested_folds=2,
            requested_predictions=6,
            failed_predictions=6,
            failed_folds=2,
            split_manifest_sha256=manifest_sha256(scientific["folds"]),
        )
        folds.pop(removed)
    elif mutation == "catalogue_block":
        request["sites"][0]["block_id"] = request["sites"][4]["block_id"]
    elif mutation == "empirical":
        request["request_template"]["data_kind"] = "empirical"
    elif mutation == "uncertainty":
        scientific["uncertainty_status"] = "validated_joint_intervals"
    elif mutation == "interrupt_type":
        scientific["interrupted"] = 0
    elif mutation == "hidden_interruption":
        scientific["failures"][0].update(
            status="not_run", reason_code="experiment_interrupted"
        )
    else:
        scientific["block_model_sha256"] = {next(iter(folds)): "a" * 64}
    with pytest.raises(ValidationRefusal):
        validate_block_metadata(experiment, scientific, folds, {}, {})
    assert original["requested_predictions"] == 9
