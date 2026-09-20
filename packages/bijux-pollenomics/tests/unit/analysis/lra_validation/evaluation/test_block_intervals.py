"""The block interval adapter never relabels a baseline as a fitted model."""

import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import (
    ValidationRefusal,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.api import (
    AUTHENTICATED_BLOCK_CONDITIONAL_INTERVAL_PROFILE,
    freeze_authenticated_block_pollen_interval,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.contracts import EvaluationRow
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    BLOCK_BASELINE_METHOD,
)
from bijux_pollenomics.analysis.lra_validation.observation_uncertainty import (
    BlockEffortDeclaration,
    BlockObservationUncertaintyPlan,
)


def test_block_plan_identity_survives_json_tuple_normalization() -> None:
    entry = BlockEffortDeclaration(
        "block:a",
        "p1",
        "bin",
        "model",
        ("Alnus", "Betula"),
        100,
        1,
        "p1.json",
        "a" * 64,
    )
    plan = BlockObservationUncertaintyPlan("b" * 64, (entry,), 10, 0.9)
    reopened = json.loads(json.dumps(plan.as_dict()))
    assert manifest_sha256(reopened) == plan.sha256


def test_baseline_refuses_before_product_access(tmp_path: Path) -> None:
    assert AUTHENTICATED_BLOCK_CONDITIONAL_INTERVAL_PROFILE.startswith(
        "pollenomics-authenticated-spatial-block"
    )
    row = EvaluationRow(
        fold_id="block:a",
        record_id="p1",
        model_id=BLOCK_BASELINE_METHOD,
        target="pollen_composition",
        experiment="all_target_pollen_withheld",
        status="predicted",
        prediction=(("Alnus", 0.5), ("Betula", 0.5)),
        observation=None,
        observation_reference_id=None,
        observation_kind=None,
        observation_support=None,
        prediction_sha256=None,
        prediction_manifest_json=None,
        fitted_model_sha256=None,
        prediction_frozen_at=None,
        fit_input_ids=(),
    )
    with pytest.raises(ValidationRefusal, match="generic source-model identity"):
        freeze_authenticated_block_pollen_interval(
            row,
            predictions=tmp_path / "must-not-open",
            expected_prediction_manifest_sha256="a" * 64,
            uncertainty=tmp_path / "must-not-open",
            expected_uncertainty_manifest_sha256="b" * 64,
        )
