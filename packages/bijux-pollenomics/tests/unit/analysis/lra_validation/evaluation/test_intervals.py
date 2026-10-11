"""Authenticate conditional pollen intervals without opening held-out outcomes."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, cast

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import (
    ValidationRefusal,
    canonical_json,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.api import (
    AUTHENTICATED_CONDITIONAL_INTERVAL_PROFILE,
    EvaluationRow,
    freeze_authenticated_pollen_interval,
)
from bijux_pollenomics.analysis.lra_validation.experiments import (
    ExperimentProduct,
    prepare_fitted_spatial_predictions,
    read_withheld_predictions,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    FITTED_METHOD,
    TRAINING_MEAN_METHOD,
)
from bijux_pollenomics.analysis.lra_validation.observation_uncertainty import (
    EffortDeclaration,
    ObservationUncertaintyPlan,
    generate_pollen_observation_uncertainty,
)

from ..experiments.fitted.test_model import payload
from ..observation_uncertainty.support import rewrite


def _store_effort(root: Path, record_id: str, effort: int) -> tuple[str, str]:
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{record_id}.json"
    path.write_text(
        canonical_json(
            {
                "schema_version": "lra-synthetic-counting-design.v1",
                "data_kind": "synthetic",
                "record_id": record_id,
                "bin_id": "test-bin",
                "planned_effort": effort,
                "effort_unit": "pollen_grains",
                "timing_declaration": "before_outcome_access",
                "declaration_provenance": "Synthetic adapter fixture, not an outcome",
            }
        )
        + "\n"
    )
    return path.name, hashlib.sha256(path.read_bytes()).hexdigest()


def _evaluation_row(source: dict[str, object], method: str) -> EvaluationRow:
    pollen = cast(dict[str, float], source["pollen_fraction"])
    model = (
        source
        if method == FITTED_METHOD
        else cast(dict[str, object], source["baseline_model_manifest"])
    )
    training_input_ids = cast(list[str], model["training_input_ids"])
    return EvaluationRow(
        fold_id=str(source["fold_id"]),
        record_id=str(source["record_id"]),
        model_id=method,
        target="pollen_composition",
        experiment="all_target_pollen_withheld",
        status="predicted",
        prediction=tuple(sorted(pollen.items())),
        observation=None,
        observation_reference_id=None,
        observation_kind=None,
        observation_support=None,
        prediction_sha256=None,
        prediction_manifest_json=None,
        fitted_model_sha256=(
            str(source["model_sha256"]) if method == FITTED_METHOD else None
        ),
        prediction_frozen_at=None,
        fit_input_ids=tuple(training_input_ids),
    )


@pytest.fixture(scope="module")
def products(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[ExperimentProduct, ExperimentProduct, EvaluationRow]:
    tmp_path = tmp_path_factory.mktemp("authenticated-interval")
    inputs = tmp_path / "inputs"
    predictions = prepare_fitted_spatial_predictions(
        payload(inputs),
        input_root=inputs,
        cache_root=tmp_path / "cache",
        destination=tmp_path / "predictions",
        workers=1,
    )
    _, _, folds, rows, methods = read_withheld_predictions(
        predictions.directory,
        expected_manifest_sha256=predictions.manifest_sha256,
    )
    generated = next(iter(rows.values()))
    generated_pollen = cast(dict[str, float], generated["pollen_fraction"])
    taxa = tuple(sorted(generated_pollen))
    bin_id = str(generated["bin_id"])
    entries: list[EffortDeclaration] = []
    effort_root = tmp_path / "effort"
    for fold_id in sorted(folds):
        for method in methods:
            record_ids = cast(list[str], folds[fold_id]["test_record_ids"])
            record_id = record_ids[0]
            evidence_path, evidence_sha256 = _store_effort(effort_root, record_id, 10)
            entries.append(
                EffortDeclaration(
                    fold_id,
                    record_id,
                    bin_id,
                    method,
                    taxa,
                    10,
                    len(entries),
                    evidence_path,
                    evidence_sha256,
                )
            )
    plan = ObservationUncertaintyPlan(
        predictions.manifest_sha256, tuple(entries), 10, 0.9
    )
    uncertainty = generate_pollen_observation_uncertainty(
        predictions.directory,
        plan,
        evidence_root=effort_root,
        destination=tmp_path / "uncertainty",
    )
    fold_id, method = next(key for key in sorted(rows) if key[1] == FITTED_METHOD)
    source = rows[(fold_id, method)]
    row = _evaluation_row(source, method)
    return predictions, uncertainty, row


def _freeze(
    products: tuple[ExperimentProduct, ExperimentProduct, EvaluationRow],
    *,
    row: EvaluationRow | None = None,
    uncertainty: ExperimentProduct | None = None,
) -> EvaluationRow:
    predictions, original_uncertainty, original_row = products
    selected = original_uncertainty if uncertainty is None else uncertainty
    return freeze_authenticated_pollen_interval(
        original_row if row is None else row,
        predictions=predictions.directory,
        expected_prediction_manifest_sha256=predictions.manifest_sha256,
        uncertainty=selected.directory,
        expected_uncertainty_manifest_sha256=selected.manifest_sha256,
    )


def test_governed_conditional_interval_is_bound_before_outcomes(
    products: tuple[ExperimentProduct, ExperimentProduct, EvaluationRow],
) -> None:
    _, uncertainty, _ = products
    frozen = _freeze(products)
    assert frozen.interval is not None
    assert frozen.interval.uncertainty_kind == "predictive_observation"
    assert frozen.interval.propagated_sources == ("observation_process",)
    assert frozen.interval.nominal_coverage == 0.9
    assert frozen.interval.profile_id.startswith(
        f"{AUTHENTICATED_CONDITIONAL_INTERVAL_PROFILE}:{uncertainty.manifest_sha256}:"
    )
    assert frozen.observation is None
    assert frozen.prediction_frozen_at is not None
    assert frozen.prediction_sha256 is not None
    assert frozen.source_model is not None
    assert frozen.source_model.kind == "fitted_spatial"
    envelope = json.loads(str(frozen.prediction_manifest_json))
    assert envelope["schema_version"] == "pollenomics-evaluation-prediction.v2"
    assert envelope["interval"]["limits"] == [
        list(item) for item in frozen.interval.limits
    ]


def test_training_mean_interval_uses_distinct_authenticated_source(
    products: tuple[ExperimentProduct, ExperimentProduct, EvaluationRow],
) -> None:
    predictions, uncertainty, _ = products
    _, _, _, rows, _ = read_withheld_predictions(
        predictions.directory,
        expected_manifest_sha256=predictions.manifest_sha256,
    )
    _, source = next(
        (key, value)
        for key, value in sorted(rows.items())
        if key[1] == TRAINING_MEAN_METHOD
    )
    frozen = freeze_authenticated_pollen_interval(
        _evaluation_row(source, TRAINING_MEAN_METHOD),
        predictions=predictions.directory,
        expected_prediction_manifest_sha256=predictions.manifest_sha256,
        uncertainty=uncertainty.directory,
        expected_uncertainty_manifest_sha256=uncertainty.manifest_sha256,
    )
    assert frozen.source_model is not None
    assert frozen.source_model.kind == "admitted_reconstruction_training_mean"
    assert frozen.fitted_model_sha256 is None
    envelope = json.loads(str(frozen.prediction_manifest_json))
    assert envelope["schema_version"] == "pollenomics-evaluation-prediction.v2"


@pytest.mark.parametrize(
    "field", ["fitted_model_sha256", "fit_input_ids", "prediction"]
)
def test_fitted_parent_and_prediction_denominator_must_match(
    products: tuple[ExperimentProduct, ExperimentProduct, EvaluationRow], field: str
) -> None:
    row = products[2]
    changes: dict[str, Any] = {
        "fitted_model_sha256": "f" * 64,
        "fit_input_ids": (*row.fit_input_ids, "unbound"),
        "prediction": (("other", 1.0),),
    }
    with pytest.raises(ValidationRefusal):
        _freeze(products, row=replace(row, **{field: changes[field]}))


def test_rehashed_nonconditional_draw_product_refuses(
    tmp_path: Path,
    products: tuple[ExperimentProduct, ExperimentProduct, EvaluationRow],
) -> None:
    original = products[1]
    target = tmp_path / "changed-uncertainty"
    shutil.copytree(original.directory, target)
    copied = ExperimentProduct(
        target, original.manifest_sha256, original.scientific_content_sha256
    )

    def mutate(rows: list[dict[str, Any]]) -> None:
        selected = next(row for row in rows if row["status"] == "generated")
        result = selected["engine_result"]
        result["interval_kind"] = "latent_composition"
        selected["engine_result_canonical_json"] = canonical_json(result)
        from bijux_pollenomics.analysis.lra_validation.contracts import manifest_sha256

        selected["engine_result_sha256"] = manifest_sha256(result)

    changed = rewrite(copied, member="uncertainty.json", member_change=mutate)
    with pytest.raises(ValidationRefusal):
        _freeze(products, uncertainty=changed)


def test_rehashed_timing_authority_claim_refuses(
    tmp_path: Path,
    products: tuple[ExperimentProduct, ExperimentProduct, EvaluationRow],
) -> None:
    original = products[1]
    target = tmp_path / "changed-timing-posture"
    shutil.copytree(original.directory, target)
    copied = ExperimentProduct(
        target, original.manifest_sha256, original.scientific_content_sha256
    )
    changed = rewrite(
        copied,
        payload_change=lambda payload: payload.update(
            declaration_timing_authenticated=True
        ),
    )
    with pytest.raises(ValidationRefusal):
        _freeze(products, uncertainty=changed)


def test_wrong_independently_retained_product_hash_refuses(
    products: tuple[ExperimentProduct, ExperimentProduct, EvaluationRow],
) -> None:
    predictions, uncertainty, row = products
    with pytest.raises(ValidationRefusal):
        freeze_authenticated_pollen_interval(
            row,
            predictions=predictions.directory,
            expected_prediction_manifest_sha256=predictions.manifest_sha256,
            uncertainty=uncertainty.directory,
            expected_uncertainty_manifest_sha256="0" * 64,
        )
