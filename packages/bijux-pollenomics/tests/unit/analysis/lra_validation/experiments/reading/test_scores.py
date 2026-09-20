"""Retained predictions and complete score rows must agree before adaptation."""

from collections.abc import Callable
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation import ValidationRefusal, manifest_sha256
from bijux_pollenomics.analysis.lra_validation.experiments.outputs import (
    ExperimentProduct,
)
from bijux_pollenomics.analysis.lra_validation.experiments.reading.scores import (
    read_scored_experiment_evidence,
)
from bijux_pollenomics.analysis.lra_validation.experiments.scoring import (
    score_experiment_predictions,
)

from ..fitted.test_reading import publish as publish_block
from ..fitted.test_reading import refusal_inventory
from ..test_scoring import prediction_product


def scored_pair(root: Path) -> tuple[ExperimentProduct, ExperimentProduct]:
    prediction, inventory = prediction_product(root)
    score = score_experiment_predictions(
        prediction.directory,
        expected_manifest_sha256=prediction.manifest_sha256,
        outcome_root=root / "inputs",
        outcome_inventory=inventory,
        destination=root / "scores",
    )
    return prediction, score


def evidence_for(
    prediction: ExperimentProduct, score: ExperimentProduct
) -> dict[str, Any]:
    evidence = read_scored_experiment_evidence(
        prediction.directory,
        expected_prediction_manifest_sha256=prediction.manifest_sha256,
        scores=score.directory,
        expected_scores_manifest_sha256=score.manifest_sha256,
    )
    value: dict[str, Any] = json.loads(evidence.canonical_evidence_json)
    return value


def rewrite_scores(
    score: ExperimentProduct,
    mutate: Callable[[list[dict[str, Any]], dict[str, Any]], None],
) -> ExperimentProduct:
    manifest = json.loads((score.directory / "manifest.json").read_text())
    rows = json.loads((score.directory / "scores.json").read_text())
    mutate(rows, manifest)
    manifest["scientific_payload"]["scores"] = rows
    (score.directory / "scores.json").write_text(
        json.dumps(rows, sort_keys=True) + "\n"
    )
    manifest["files"]["scores.json"] = hashlib.sha256(
        (score.directory / "scores.json").read_bytes()
    ).hexdigest()
    manifest["scientific_content_sha256"] = manifest_sha256(
        manifest["scientific_payload"]
    )
    path = score.directory / "manifest.json"
    path.write_text(json.dumps(manifest, sort_keys=True) + "\n")
    return ExperimentProduct(
        score.directory,
        hashlib.sha256(path.read_bytes()).hexdigest(),
        manifest["scientific_content_sha256"],
    )


def test_admits_real_retained_scores_after_all_original_inputs_removed(
    tmp_path: Path,
) -> None:
    prediction, score = scored_pair(tmp_path)
    original = evidence_for(prediction, score)
    shutil.rmtree(tmp_path / "inputs")
    retained = evidence_for(prediction, score)
    assert retained == original
    assert retained["requested_units"] == len(retained["units"])
    assert {row["target"] for row in retained["units"]} == {
        "vegetation_cover",
        "pollen_composition",
    }
    assert all(
        row["metric_verification"] == "existing_metric_recomputed"
        for row in retained["units"]
    )
    assert retained["first_test_access_at"] is None
    assert retained["prediction_frozen_at"] is None
    assert retained["scientific_acceptance"] == "not_evaluated"


@pytest.mark.parametrize(
    "kind",
    [
        "drop_fold",
        "duplicate",
        "metric",
        "probability_flag",
        "prediction",
        "observation",
        "source_ref",
        "method",
        "target",
        "unit",
        "posture",
        "observation_schema",
        "record_ids",
        "mixed_method",
    ],
)
def test_rehashed_internal_score_contradictions_refuse(
    tmp_path: Path, kind: str
) -> None:
    prediction, score = scored_pair(tmp_path)

    def mutate(rows: list[dict[str, Any]], manifest: dict[str, Any]) -> None:
        if kind == "drop_fold":
            fold = rows[0]["fold_id"]
            rows[:] = [row for row in rows if row["fold_id"] != fold]
        elif kind == "duplicate":
            rows.append(rows[0].copy())
        elif kind == "metric":
            rows[0]["score"]["mae_fraction"] += 0.01
        elif kind == "probability_flag":
            rows[0]["score"]["zero_probability_positive_count"] = True
        elif kind == "prediction":
            rows[0]["prediction"] = {"Alnus": 0.9, "Betula": 0.1}
        elif kind == "observation":
            rows[0]["observation"]["vegetation_fraction"] = {
                "Alnus": 0.9,
                "Betula": 0.1,
            }
        elif kind == "source_ref":
            rows[0]["observation_reference"]["sha256"] = "f" * 64
        elif kind == "method":
            rows[0]["baseline"] = "invented"
        elif kind == "target":
            rows[0]["target"] = "pollen"
        elif kind == "observation_schema":
            rows[0]["observation"]["schema_version"] = "untyped-v1"
        elif kind == "record_ids":
            rows[0]["record_ids"] = ["different-owner"]
        elif kind == "mixed_method":
            rows[0]["method"] = rows[0]["baseline"]
        elif kind == "unit":
            rows[0]["error_unit"] = "percent"
        else:
            manifest["scientific_payload"]["scientific_acceptance"] = "accepted"

    changed = rewrite_scores(score, mutate)
    with pytest.raises(ValidationRefusal):
        evidence_for(prediction, changed)


def test_wrong_score_parent_digest_refuses_before_member_decoding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prediction, score = scored_pair(tmp_path)
    from bijux_pollenomics.analysis.lra_validation.experiments.reading import scores

    def forbidden(*args: object, **kwargs: object) -> object:
        pytest.fail("Numerical member decoded before caller score digest admission")

    with monkeypatch.context() as patch:
        patch.setattr(scores, "read_member", forbidden)
        with pytest.raises(ValidationRefusal, match="Manifest differs"):
            read_scored_experiment_evidence(
                prediction.directory,
                expected_prediction_manifest_sha256=prediction.manifest_sha256,
                scores=score.directory,
                expected_scores_manifest_sha256="0" * 64,
            )


def test_block_score_method_kinds_are_retained_and_authenticated(
    tmp_path: Path,
) -> None:
    scientific = refusal_inventory(tmp_path / "inputs")
    prediction = publish_block(tmp_path / "prediction", scientific)
    inventory = {
        "schema_version": "lra-experiment-outcomes.v1",
        "data_kind": "synthetic",
        "records": {},
    }
    score = score_experiment_predictions(
        prediction.directory,
        expected_manifest_sha256=prediction.manifest_sha256,
        outcome_root=tmp_path / "inputs",
        outcome_inventory=inventory,
        destination=tmp_path / "scores",
    )
    evidence = evidence_for(prediction, score)
    assert len(evidence["units"]) == 36
    assert {
        (row["method_id"], row["source_row"]["method_kind"])
        for row in evidence["units"]
    } == {
        ("clr-wgs84-rbf-ridge-v1", "fitted_spatial"),
        ("training_mean", "admitted_reconstruction_training_mean"),
    }

    def change_kind(rows: list[dict[str, Any]], manifest: dict[str, Any]) -> None:
        del manifest
        rows[0]["method_kind"] = "fitted_spatial"
        if rows[0]["method"] != "training_mean":
            rows[0]["method_kind"] = "admitted_reconstruction_training_mean"

    changed = rewrite_scores(score, change_kind)
    with pytest.raises(ValidationRefusal):
        evidence_for(prediction, changed)
