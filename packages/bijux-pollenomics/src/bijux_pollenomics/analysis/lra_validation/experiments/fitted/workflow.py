"""Actual train-only LRA reconstructions followed by an explicit fitted spatial model."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from ....lra.api import LRABatchLimits, LRARefusal
from ....lra.engine.discovery import load_engine
from ....lra.outputs.identity import capture_code_identity, verify_code_identity
from ...contracts import Fold, ValidationRefusal, manifest_sha256
from ...splits import grouped_leave_one_out
from ..configuration import (
    FITTED_METHOD,
    FITTED_METHODS,
    FITTED_PROFILE,
    FITTED_ROLES,
    TRAINING_MEAN_METHOD,
    FittedSpatialExperimentSpec,
)
from ..inputs import verify_consumed_sources
from ..outputs import (
    ExperimentProduct,
    publish_phase,
    stage_directory,
    write_json,
)
from ..reconstruction import reconstruct_fold
from ..workflow import _implementation
from .model import (
    FittedTrainingState,
    fit_reconstructed_training,
    fitted_support,
    predict_fitted_target,
)
from .training_mean import predict_training_mean_target, training_mean_model


def _failure(
    fold: Fold,
    method: str,
    exc: BaseException,
    interrupted: bool,
) -> dict[str, object]:
    fold_id = fold.fold_id
    reason = getattr(exc, "reason_code", "experiment_target_refused")
    row: dict[str, object] = {
        "fold_id": fold_id,
        "record_ids": fold.test_record_ids,
        "method": method,
        "status": "not_run" if interrupted else "refused",
        "reason_code": "experiment_interrupted" if interrupted else reason,
        "detail": str(exc),
        "exception_type": type(exc).__name__,
    }
    if isinstance(exc, LRARefusal):
        row["original_error"] = exc.as_dict()
    return row


def prepare_fitted_spatial_predictions(
    spec: FittedSpatialExperimentSpec | Mapping[str, object],
    *,
    input_root: Path,
    cache_root: Path,
    destination: Path,
    workers: int = 1,
) -> ExperimentProduct:
    """Publish actual fitted predictions without accepting either target outcome inventory."""
    spec = (
        spec
        if isinstance(spec, FittedSpatialExperimentSpec)
        else FittedSpatialExperimentSpec(spec)
    )
    LRABatchLimits(max_workers=workers)
    if workers > (os.cpu_count() or 1):
        raise ValidationRefusal("experiment_worker_budget_exceeded", str(workers))
    folds = grouped_leave_one_out([site.record for site in spec.sites])
    by_record = {site.record.record_id: site for site in spec.sites}
    groups = {
        record: fold.test_group_ids[0]
        for fold in folds
        for record in fold.test_record_ids
    }
    implementation = _implementation()
    binding = load_engine()
    engine_identity = capture_code_identity(binding)
    stage = stage_directory(destination)
    predictions: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    operations: list[dict[str, object]] = []
    interrupted = False
    consumed_pollen: set[str] = set()
    consumed_geometry: set[str] = set()
    for index, fold in enumerate(folds):
        try:
            if interrupted:
                raise ValidationRefusal(
                    "experiment_interrupted", "Remaining fold not submitted"
                )
            if len(fold.test_record_ids) != 1:
                raise ValidationRefusal("unsupported_multi_record_target", fold.fold_id)
            record_id = fold.test_record_ids[0]
            target = by_record[record_id]
            fits = reconstruct_fold(
                spec,
                fold,
                groups,
                input_root=input_root,
                cache_root=cache_root,
                report_root=stage / "batches" / f"fold-{index:04}",
                workers=workers,
                consumed_pollen=consumed_pollen,
                consumed_geometry=consumed_geometry,
            )
            baseline_model = training_mean_model(spec, fold, fits, groups)
            operations.append(
                {"fold_id": fold.fold_id, "batch": fits.operational_batch}
            )
        except (KeyboardInterrupt, ValidationRefusal, LRARefusal, ValueError) as exc:
            interrupted = (
                interrupted
                or isinstance(exc, KeyboardInterrupt)
                or getattr(exc, "reason_code", None) == "experiment_interrupted"
            )
            for method in FITTED_METHODS:
                failures.append(
                    _failure(
                        fold,
                        method,
                        exc,
                        interrupted,
                    )
                )
            continue
        state: FittedTrainingState | None = None
        fit_failure: BaseException | None = None
        try:
            state = fit_reconstructed_training(
                spec,
                fold,
                fits,
                groups,
                input_root=input_root,
                consumed_geometry=consumed_geometry,
            )
        except (KeyboardInterrupt, ValidationRefusal, LRARefusal, ValueError) as exc:
            fit_failure = exc
            interrupted = (
                interrupted
                or isinstance(exc, KeyboardInterrupt)
                or getattr(exc, "reason_code", None) == "experiment_interrupted"
            )
        for method in FITTED_METHODS:
            try:
                if interrupted:
                    raise ValidationRefusal(
                        "experiment_interrupted", "Remaining method not submitted"
                    )
                if method == FITTED_METHOD:
                    if state is None:
                        assert fit_failure is not None
                        raise fit_failure
                    row, _ = predict_fitted_target(
                        spec,
                        target,
                        state,
                        groups,
                        input_root=input_root,
                        consumed_geometry=consumed_geometry,
                    )
                elif method == TRAINING_MEAN_METHOD:
                    row = predict_training_mean_target(
                        spec,
                        target,
                        fold,
                        fits,
                        groups,
                        baseline_model,
                        input_root=input_root,
                        consumed_geometry=consumed_geometry,
                    )
                else:  # pragma: no cover - the closed tuple is defined locally.
                    raise ValidationRefusal("unsupported_fitted_method", method)
                predictions.append(row)
            except (
                KeyboardInterrupt,
                ValidationRefusal,
                LRARefusal,
                ValueError,
            ) as exc:
                interrupted = (
                    interrupted
                    or isinstance(exc, KeyboardInterrupt)
                    or getattr(exc, "reason_code", None) == "experiment_interrupted"
                )
                failures.append(
                    _failure(
                        fold,
                        method,
                        exc,
                        interrupted,
                    )
                )
    if _implementation() != implementation:
        raise ValidationRefusal("experiment_implementation_changed", str(stage))
    verify_code_identity(binding, engine_identity)
    fold_rows = [fold.as_dict() for fold in folds]
    ordered = [(fold.fold_id, method) for fold in folds for method in FITTED_METHODS]
    expected = set(ordered)
    predicted = {(str(row["fold_id"]), str(row["method"])) for row in predictions}
    failed = {(str(row["fold_id"]), str(row["method"])) for row in failures}
    terminal = dict.fromkeys(predicted, "predicted")
    terminal.update(
        {
            (str(row["fold_id"]), str(row["method"])): str(row["status"])
            for row in failures
        }
    )
    first_not_run = next(
        (index for index, key in enumerate(ordered) if terminal.get(key) == "not_run"),
        None,
    )
    if (
        predicted & failed
        or predicted | failed != expected
        or len(predicted) != len(predictions)
        or len(failed) != len(failures)
        or (
            first_not_run is not None
            and any(terminal.get(key) != "not_run" for key in ordered[first_not_run:])
        )
    ):
        raise ValidationRefusal("incomplete_fitted_accounting", str(stage))
    refused = sum(row["status"] == "refused" for row in failures)
    not_run = sum(row["status"] == "not_run" for row in failures)
    scientific: dict[str, object] = {
        "schema_version": "lra-grouped-outer-paired-predictions.v1",
        "profile": FITTED_PROFILE,
        "experiment": "all_target_pollen_withheld_fitted_spatial",
        "folds": fold_rows,
        "methods": list(FITTED_METHODS),
        "evaluation_roles": FITTED_ROLES,
        "predictions": predictions,
        "failures": failures,
        "implementation": implementation,
        "engine_identity": engine_identity.payload(),
        "split_manifest_sha256": manifest_sha256(fold_rows),
        "requested_folds": len(folds),
        "requested_predictions": len(expected),
        "generated_predictions": len(predictions),
        "failed_predictions": len(failures),
        "refused_predictions": refused,
        "not_run_predictions": not_run,
        "failed_folds": len({str(row["fold_id"]) for row in failures}),
        "interrupted": interrupted,
        "all_predictions_generated": not failures,
        "uncertainty_status": "point_predictions_only_intervals_not_implemented",
        "scientific_acceptance": "not_evaluated",
    }
    write_json(
        stage,
        "experiment.json",
        {
            "profile": FITTED_PROFILE,
            "request_template": spec.template(),
            "support": fitted_support(spec),
            "regional_priority": spec.regional_priority,
            "method": {
                "profile": FITTED_METHOD,
                "length_scale_km": spec.length_scale_km,
                "ridge_penalty": spec.ridge_penalty,
            },
            "source_catalogue": [
                {
                    "record_id": site.record.record_id,
                    "site_id": site.record.site_id,
                    "identity_keys": site.record.identity_keys,
                    "raw_path": site.raw.path,
                    "raw_sha256": site.raw.sha256,
                    "geometry_path": site.geometry.path,
                    "geometry_sha256": site.geometry.sha256,
                }
                for site in spec.sites
            ],
        },
    )
    for name, value in (
        ("folds.json", fold_rows),
        ("predictions.json", predictions),
        ("failures.json", failures),
        ("operations.json", operations),
    ):
        write_json(stage, name, value)
    verify_consumed_sources(
        spec,
        input_root,
        pollen_record_ids=consumed_pollen,
        geometry_record_ids=consumed_geometry,
        template_used=bool(consumed_pollen),
    )
    return publish_phase(
        stage,
        destination,
        phase="predictions",
        scientific=scientific,
        profile=FITTED_PROFILE,
    )
