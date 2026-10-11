"""The preserved singleton workflow refuses invalid scheduling before numerical work."""

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation import Fold, ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.experiments import (
    prepare_fitted_spatial_predictions,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    FITTED_METHOD,
    FITTED_METHODS,
    TRAINING_MEAN_METHOD,
)

from .test_model import payload


@pytest.mark.parametrize("workers", [0, -1, True, 1000000])
def test_singleton_worker_budget_precedes_backend_and_cache(
    tmp_path: Path, workers: int
) -> None:
    request = payload(tmp_path / "inputs")
    with pytest.raises(ValueError):
        prepare_fitted_spatial_predictions(
            request,
            input_root=tmp_path / "inputs",
            cache_root=tmp_path / "cache",
            destination=tmp_path / "product",
            workers=workers,
        )
    assert not (tmp_path / "product").exists() and not (tmp_path / "cache").exists()


def test_failed_fitted_fold_rechecks_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ..test_workflow import check_failed_source_revalidation

    check_failed_source_revalidation(
        tmp_path,
        monkeypatch,
        "bijux_pollenomics.analysis.lra_validation.experiments.fitted.workflow",
        "prepare_fitted_spatial_predictions",
        payload(tmp_path / "inputs"),
    )


def _paired_fixture(
    monkeypatch: pytest.MonkeyPatch, *, fit_failure: BaseException
) -> None:
    from bijux_pollenomics.analysis.lra_validation.experiments.fitted import workflow

    monkeypatch.setattr(workflow, "load_engine", lambda: object())
    monkeypatch.setattr(
        workflow,
        "capture_code_identity",
        lambda _: SimpleNamespace(payload=lambda: {"fixture": "engine"}),
    )
    monkeypatch.setattr(workflow, "verify_code_identity", lambda *args: None)
    monkeypatch.setattr(workflow, "_implementation", lambda: {"fixture": "code"})
    monkeypatch.setattr(workflow, "verify_consumed_sources", lambda *args, **kw: None)

    def reconstruct(*args: Any, **kwargs: Any) -> Any:
        return SimpleNamespace(operational_batch={"status": "completed"})

    monkeypatch.setattr(workflow, "reconstruct_fold", reconstruct)
    monkeypatch.setattr(
        workflow,
        "training_mean_model",
        lambda *args, **kwargs: {"support": {}, "method": TRAINING_MEAN_METHOD},
    )

    def fail_fit(*args: Any, **kwargs: Any) -> Any:
        raise fit_failure

    monkeypatch.setattr(workflow, "fit_reconstructed_training", fail_fit)

    def baseline(
        spec: Any, target: Any, fold: Any, *args: Any, **kwargs: Any
    ) -> dict[str, object]:
        return {
            "profile": spec.template()["method_profile"],
            "fold_id": fold.fold_id,
            "record_id": target.record.record_id,
            "method": TRAINING_MEAN_METHOD,
        }

    monkeypatch.setattr(workflow, "predict_training_mean_target", baseline)


def test_fitted_refusal_keeps_complete_paired_denominator_and_baseline_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _paired_fixture(
        monkeypatch,
        fit_failure=ValidationRefusal("injected_fit_refusal", "fit unavailable"),
    )
    product = prepare_fitted_spatial_predictions(
        payload(tmp_path / "inputs"),
        input_root=tmp_path / "inputs",
        cache_root=tmp_path / "cache",
        destination=tmp_path / "product",
    )
    scientific = json.loads((product.directory / "manifest.json").read_text())[
        "scientific_payload"
    ]
    folds = scientific["requested_folds"]
    assert scientific["schema_version"] == ("lra-grouped-outer-paired-predictions.v1")
    assert tuple(scientific["methods"]) == FITTED_METHODS
    assert scientific["requested_predictions"] == folds * len(FITTED_METHODS)
    assert scientific["generated_predictions"] == folds
    assert scientific["refused_predictions"] == folds
    assert scientific["not_run_predictions"] == 0
    assert {row["method"] for row in scientific["predictions"]} == {
        TRAINING_MEAN_METHOD
    }
    assert {row["method"] for row in scientific["failures"]} == {FITTED_METHOD}


def test_reconstruction_refusal_applies_to_both_methods(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _paired_fixture(
        monkeypatch,
        fit_failure=ValidationRefusal("unused", "fit must not be reached"),
    )
    from bijux_pollenomics.analysis.lra_validation.experiments.fitted import workflow

    def refuse_reconstruction(*args: Any, **kwargs: Any) -> Any:
        raise ValidationRefusal("injected_reconstruction_refusal", "no reconstruction")

    monkeypatch.setattr(workflow, "reconstruct_fold", refuse_reconstruction)
    product = prepare_fitted_spatial_predictions(
        payload(tmp_path / "inputs"),
        input_root=tmp_path / "inputs",
        cache_root=tmp_path / "cache",
        destination=tmp_path / "product",
    )
    scientific = json.loads((product.directory / "manifest.json").read_text())[
        "scientific_payload"
    ]
    assert scientific["generated_predictions"] == 0
    assert scientific["refused_predictions"] == scientific["requested_predictions"]
    assert all(
        row["reason_code"] == "injected_reconstruction_refusal"
        for row in scientific["failures"]
    )
    assert {(row["fold_id"], row["method"]) for row in scientific["failures"]} == {
        (fold["fold_id"], method)
        for fold in scientific["folds"]
        for method in FITTED_METHODS
    }


def test_fit_interrupt_marks_exact_remaining_method_suffix_not_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _paired_fixture(monkeypatch, fit_failure=KeyboardInterrupt())
    product = prepare_fitted_spatial_predictions(
        payload(tmp_path / "inputs"),
        input_root=tmp_path / "inputs",
        cache_root=tmp_path / "cache",
        destination=tmp_path / "product",
    )
    scientific = json.loads((product.directory / "manifest.json").read_text())[
        "scientific_payload"
    ]
    assert scientific["generated_predictions"] == 0
    assert scientific["refused_predictions"] == 0
    assert scientific["not_run_predictions"] == scientific["requested_predictions"]
    assert scientific["interrupted"] is True
    assert all(
        row["status"] == "not_run" and row["reason_code"] == "experiment_interrupted"
        for row in scientific["failures"]
    )


def test_unsupported_multi_record_fold_is_accounted_for_each_method(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _paired_fixture(
        monkeypatch,
        fit_failure=ValidationRefusal("unused", "fit must not be reached"),
    )
    from bijux_pollenomics.analysis.lra_validation.experiments.fitted import workflow

    fold = Fold(
        "fold:multi",
        ("p01", "p02"),
        ("p03", "p04"),
        ("site:p01", "site:p02"),
        ("site:p03", "site:p04"),
    )
    monkeypatch.setattr(workflow, "grouped_leave_one_out", lambda records: (fold,))
    product = prepare_fitted_spatial_predictions(
        payload(tmp_path / "inputs"),
        input_root=tmp_path / "inputs",
        cache_root=tmp_path / "cache",
        destination=tmp_path / "product",
    )
    scientific = json.loads((product.directory / "manifest.json").read_text())[
        "scientific_payload"
    ]
    assert scientific["generated_predictions"] == 0
    assert scientific["refused_predictions"] == len(FITTED_METHODS)
    assert tuple(row["method"] for row in scientific["failures"]) == FITTED_METHODS
    assert all(
        row["record_ids"] == ["p03", "p04"]
        and row["reason_code"] == "unsupported_multi_record_target"
        for row in scientific["failures"]
    )
