"""CLI phase isolation, stable refusal codes and interrupted/partial accounting."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from bijux_pollenomics.analysis.lra_validation import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    BLOCK_PROFILE,
    FITTED_PROFILE,
    LOCAL_PROFILE,
    PROFILE,
    SOURCE_PROFILE,
    TEMPORAL_PROFILE,
)
from bijux_pollenomics.analysis.lra_validation.experiments.outputs import (
    ExperimentProduct,
)
from bijux_pollenomics.cli import main
from bijux_pollenomics.command_line.runtime import lra_validation as runtime

from ...analysis.lra_validation.experiments.test_assimilation import (
    synthetic_local_product,
)
from ...analysis.lra_validation.experiments.test_scoring import prediction_product


def prepare_args(root: Path) -> list[str]:
    return [
        "prepare-lra-experiment",
        str(root / "request.json"),
        "--input-root",
        str(root),
        "--cache-root",
        str(root / "cache"),
        "--output",
        str(root / "output"),
    ]


def score_args(root: Path, product: ExperimentProduct) -> list[str]:
    return [
        "score-lra-experiment",
        str(product.directory),
        "--expected-manifest-sha256",
        product.manifest_sha256,
        "--outcome-root",
        str(root / "inputs"),
        "--outcome-inventory",
        str(root / "outcomes.json"),
        "--output",
        str(root / "scores"),
    ]


@pytest.mark.parametrize(
    "text", ["[]", '{"profile":"a","profile":"b"}', '{"value":NaN}']
)
def test_invalid_json_never_starts_numerical_work(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], text: str
) -> None:
    (tmp_path / "request.json").write_text(text)
    with patch.object(runtime, "prepare_experiment_predictions") as run:
        assert main(prepare_args(tmp_path)) == 2
    run.assert_not_called()
    assert (
        json.loads(capsys.readouterr().out)["reason_code"]
        == "lra_experiment_io_or_encoding"
    )


@pytest.mark.parametrize(
    "profile,entry",
    [
        (PROFILE, "prepare_experiment_predictions"),
        (SOURCE_PROFILE, "prepare_experiment_predictions"),
        (LOCAL_PROFILE, "prepare_local_pollen_predictions"),
        (FITTED_PROFILE, "prepare_fitted_spatial_predictions"),
        (BLOCK_PROFILE, "prepare_spatial_block_predictions"),
        (TEMPORAL_PROFILE, "prepare_temporal_persistence_predictions"),
    ],
)
@pytest.mark.parametrize(
    "interrupted,complete,expected",
    [(False, True, 0), (False, False, 2), (True, False, 130)],
)
def test_prediction_cli_retains_complete_or_partial_accounting(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    interrupted: bool,
    complete: bool,
    expected: int,
    profile: str,
    entry: str,
) -> None:
    (tmp_path / "request.json").write_text(json.dumps({"profile": profile}))
    product = ExperimentProduct(tmp_path / "output", "a" * 64, "b" * 64)
    scientific = {
        "requested_folds": 3,
        "requested_predictions": 9,
        "generated_predictions": 9 if complete else 0,
        "failed_folds": 0 if complete else 3,
        "interrupted": interrupted,
        "all_predictions_generated": complete,
    }
    with (
        patch.object(runtime, entry, return_value=product) as run,
        patch.object(
            runtime,
            "read_experiment_product",
            return_value=(product, {"scientific_payload": scientific}),
        ),
    ):
        assert main(prepare_args(tmp_path)) == expected
    assert run.call_args.kwargs["workers"] == 1
    result = json.loads(capsys.readouterr().out)
    assert result["scientific_acceptance"] == "not_evaluated"
    assert {k: result[k] for k in scientific} == scientific


def test_changed_prediction_refuses_before_outcome_inventory_access(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    product = ExperimentProduct(tmp_path / "unknown", "a" * 64, "b" * 64)
    with (
        patch.object(
            runtime,
            "read_experiment_product",
            side_effect=ValidationRefusal("invalid_experiment_product", "changed"),
        ) as verify,
        patch.object(runtime, "read_object") as read,
        patch.object(runtime, "score_experiment_predictions") as score,
    ):
        assert main(score_args(tmp_path, product)) == 2
    verify.assert_called_once()
    read.assert_not_called()
    score.assert_not_called()
    assert (
        json.loads(capsys.readouterr().out)["reason_code"]
        == "invalid_experiment_product"
    )


def test_temporal_semantics_refuse_before_outcome_inventory_access(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    product = ExperimentProduct(tmp_path / "unknown", "a" * 64, "b" * 64)
    with (
        patch.object(
            runtime,
            "read_experiment_product",
            return_value=(product, {"profile": TEMPORAL_PROFILE}),
        ),
        patch.object(
            runtime,
            "read_temporal_persistence_predictions",
            side_effect=ValidationRefusal(
                "temporal_request_provenance_mismatch", "changed"
            ),
        ),
        patch.object(runtime, "read_object") as outcomes,
        patch.object(runtime, "score_temporal_persistence_predictions") as score,
    ):
        assert main(score_args(tmp_path, product)) == 2
    outcomes.assert_not_called()
    score.assert_not_called()
    assert (
        json.loads(capsys.readouterr().out)["reason_code"]
        == "temporal_request_provenance_mismatch"
    )


def test_temporal_cli_keeps_both_failed_target_denominators(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from ...analysis.lra_validation.temporal.persistence.support import refused_product

    product, spec = refused_product(tmp_path / "generation")
    assert isinstance(product, ExperimentProduct)
    (tmp_path / "outcomes.json").write_text(
        json.dumps(
            {
                "schema_version": "lra-temporal-outcomes.v1",
                "data_kind": "synthetic",
                "purpose": "exploratory",
                "predictions_manifest_sha256": product.manifest_sha256,
                "records": [
                    {
                        "record_id": spec.temporal_plan.fold.test_record_ids[0],
                        "observation": {"path": "absent.json", "sha256": "c" * 64},
                    }
                ],
            }
        )
    )
    assert main(score_args(tmp_path, product)) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["requested_scores"] == 2
    assert result["score_status_counts"] == {"failed_prediction": 2}
    assert json.loads((tmp_path / "scores/outcome_access.json").read_text()) == []


@pytest.mark.parametrize("missing", [False, True])
def test_actual_score_cli_separates_targets_and_preserves_missing_denominators(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], missing: bool
) -> None:
    product, inventory = prediction_product(tmp_path)
    if missing:
        inventory["records"].pop(next(iter(inventory["records"])))
    (tmp_path / "outcomes.json").write_text(json.dumps(inventory))
    assert main(score_args(tmp_path, product)) == (2 if missing else 0)
    result = json.loads(capsys.readouterr().out)
    assert result["scientific_acceptance"] == "not_evaluated"
    assert sum(result["score_status_counts"].values()) == result["requested_scores"]
    rows = json.loads((tmp_path / "scores/scores.json").read_text())
    assert {r["target"] for r in rows} == {"vegetation_cover", "pollen_composition"}
    assert result["requested_scores"] == len(rows)


@pytest.mark.parametrize("profile", [None, "unknown", {}, False])
def test_unknown_profile_refuses_before_source_or_numerical_access(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], profile: object
) -> None:
    (tmp_path / "request.json").write_text(json.dumps({"profile": profile}))
    with (
        patch.object(runtime, "prepare_experiment_predictions") as baseline,
        patch.object(runtime, "prepare_local_pollen_predictions") as local,
        patch.object(runtime, "prepare_fitted_spatial_predictions") as fitted,
        patch.object(runtime, "prepare_spatial_block_predictions") as block,
    ):
        assert main(prepare_args(tmp_path)) == 2
    for operation in (baseline, local, fitted, block):
        operation.assert_not_called()
    assert (
        json.loads(capsys.readouterr().out)["reason_code"]
        == "unsupported_experiment_profile"
    )


def test_local_score_command_retains_diagnostic_and_heldout_roles(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    product, inventory = synthetic_local_product(tmp_path)
    (tmp_path / "outcomes.json").write_text(json.dumps(inventory))
    assert main(score_args(tmp_path, product)) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["requested_scores"] == 8
    rows = json.loads((tmp_path / "scores/scores.json").read_text())
    for row in rows:
        if row["target"] == "pollen_composition":
            assert row["evaluation_role"] == "in_sample_diagnostic"
            assert row["eligible_for_heldout_acceptance"] is False
        else:
            assert row["evaluation_role"] == "heldout_prediction"
