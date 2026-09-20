"""Block intervals bind exact authenticated fitted and baseline model sources."""

from dataclasses import replace
import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import (
    ValidationRefusal,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.evaluation import block_intervals
from bijux_pollenomics.analysis.lra_validation.evaluation.contracts import (
    EvaluationRow,
    validate_frozen_prediction,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    BLOCK_BASELINE_METHOD,
    FITTED_METHOD,
)
from bijux_pollenomics.analysis.lra_validation.observation_uncertainty.block_contracts import (
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


def _entry(method: str) -> BlockEffortDeclaration:
    return BlockEffortDeclaration(
        "block:a",
        "p1",
        "bin",
        method,
        ("Alnus", "Betula"),
        100,
        7,
        "effort.json",
        "e" * 64,
    )


def _row(method: str) -> EvaluationRow:
    return EvaluationRow(
        fold_id="block:a",
        record_id="p1",
        model_id=method,
        target="pollen_composition",
        experiment="all_target_pollen_withheld",
        status="predicted",
        prediction=(("Alnus", 0.6), ("Betula", 0.4)),
        observation=None,
        observation_reference_id=None,
        observation_kind=None,
        observation_support=None,
        prediction_sha256=None,
        prediction_manifest_json=None,
        fitted_model_sha256="f" * 64 if method == FITTED_METHOD else None,
        prediction_frozen_at=None,
        fit_input_ids=("train:a",),
    )


def _parent(method: str) -> dict[str, object]:
    common: dict[str, object] = {
        "method": method,
        "record_id": "p1",
        "pollen_fraction": {"Alnus": 0.6, "Betula": 0.4},
    }
    if method == FITTED_METHOD:
        return {
            **common,
            "model_sha256": "f" * 64,
            "training_input_ids": ["train:a"],
        }
    return {
        **common,
        "method_kind": "admitted_reconstruction_training_mean",
        "baseline_model_sha256": "b" * 64,
        "baseline_model_manifest": {"training_input_ids": ["train:a"]},
    }


def _source() -> dict[str, object]:
    return {
        "status": "generated",
        "engine_result_sha256": "d" * 64,
        "engine_result": {
            "declaration": {
                "taxa": ["Alnus", "Betula"],
                "coverage": 0.9,
            },
            "marginal_predictive_intervals": {
                "Alnus": {"lower_fraction": 0.4, "upper_fraction": 0.8},
                "Betula": {"lower_fraction": 0.2, "upper_fraction": 0.6},
            },
        },
    }


def _install_parent(
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    *,
    parent: dict[str, object] | None = None,
) -> None:
    entry = _entry(method)
    plan = BlockObservationUncertaintyPlan("a" * 64, (entry,), 10, 0.9)
    key = entry.key
    monkeypatch.setattr(
        block_intervals,
        "_authenticated_block_draws",
        lambda *args, **kwargs: (
            plan,
            {key: _parent(method) if parent is None else parent},
            {key: _source()},
        ),
    )


@pytest.mark.parametrize(
    ("method", "kind", "sha256"),
    (
        (FITTED_METHOD, "fitted_spatial", "f" * 64),
        (
            BLOCK_BASELINE_METHOD,
            "admitted_reconstruction_training_mean",
            "b" * 64,
        ),
    ),
)
def test_adapter_mints_v2_only_after_authenticated_parent_mapping(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    kind: str,
    sha256: str,
) -> None:
    _install_parent(monkeypatch, method)
    frozen = block_intervals.freeze_authenticated_block_pollen_interval(
        _row(method),
        predictions=tmp_path / "predictions",
        expected_prediction_manifest_sha256="a" * 64,
        uncertainty=tmp_path / "uncertainty",
        expected_uncertainty_manifest_sha256="c" * 64,
    )
    assert frozen.source_model is not None
    assert (frozen.source_model.kind, frozen.source_model.sha256) == (kind, sha256)
    assert frozen.fitted_model_sha256 == ("f" * 64 if method == FITTED_METHOD else None)
    assert validate_frozen_prediction(frozen) == (
        "pollenomics-evaluation-prediction.v2"
    )
    envelope = json.loads(str(frozen.prediction_manifest_json))
    assert envelope["source_model"] == {"kind": kind, "sha256": sha256}
    assert "fitted_model_sha256" not in envelope


def test_baseline_fitted_alias_refuses_before_product_access(tmp_path: Path) -> None:
    row = replace(_row(BLOCK_BASELINE_METHOD), fitted_model_sha256="b" * 64)
    with pytest.raises(ValidationRefusal, match="outcome-free unfrozen typed"):
        block_intervals.freeze_authenticated_block_pollen_interval(
            row,
            predictions=tmp_path / "must-not-open",
            expected_prediction_manifest_sha256="a" * 64,
            uncertainty=tmp_path / "must-not-open",
            expected_uncertainty_manifest_sha256="c" * 64,
        )


def test_parent_method_kind_or_training_inputs_cannot_be_relabelled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    parent = _parent(BLOCK_BASELINE_METHOD)
    parent["method_kind"] = "fitted_spatial"
    _install_parent(monkeypatch, BLOCK_BASELINE_METHOD, parent=parent)
    with pytest.raises(ValidationRefusal, match="method kind"):
        block_intervals.freeze_authenticated_block_pollen_interval(
            _row(BLOCK_BASELINE_METHOD),
            predictions=tmp_path / "predictions",
            expected_prediction_manifest_sha256="a" * 64,
            uncertainty=tmp_path / "uncertainty",
            expected_uncertainty_manifest_sha256="c" * 64,
        )

    parent = _parent(BLOCK_BASELINE_METHOD)
    parent["baseline_model_manifest"] = {"training_input_ids": ["train:b"]}
    _install_parent(monkeypatch, BLOCK_BASELINE_METHOD, parent=parent)
    with pytest.raises(ValidationRefusal, match="model inputs"):
        block_intervals.freeze_authenticated_block_pollen_interval(
            _row(BLOCK_BASELINE_METHOD),
            predictions=tmp_path / "predictions",
            expected_prediction_manifest_sha256="a" * 64,
            uncertainty=tmp_path / "uncertainty",
            expected_uncertainty_manifest_sha256="c" * 64,
        )
