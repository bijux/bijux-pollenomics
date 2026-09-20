"""One train-only reconstruction/model per genuine heldout spatial block."""

from __future__ import annotations

from collections.abc import Mapping
import os
from pathlib import Path

from ....lra.api import LRABatchLimits, LRARefusal
from ....lra.engine.discovery import load_engine
from ....lra.outputs.identity import capture_code_identity, verify_code_identity
from ...contracts import Fold, TrainingAdmission, ValidationRefusal, manifest_sha256
from ...splits import (
    grouped_block_holdouts,
    grouped_leave_one_out,
)
from ..configuration import (
    BLOCK_METHODS,
    BLOCK_PROFILE,
    FITTED_METHOD,
    FITTED_ROLES,
    ExperimentSite,
    SpatialBlockExperimentSpec,
)
from ..inputs import verify_consumed_sources
from ..outputs import ExperimentProduct, publish_phase, stage_directory, write_json
from ..reconstruction import FoldFits, reconstruct_fold
from ..workflow import _implementation
from .admission import admit_block_training, read_block_supports, verify_block_supports
from .model import (
    FittedTrainingState,
    fit_reconstructed_training,
    predict_fitted_target,
    retained_training_state,
)
from .training_mean import predict_training_mean_target, training_mean_model


def prepare_spatial_block_predictions(
    spec: SpatialBlockExperimentSpec | Mapping[str, object],
    *,
    input_root: Path,
    cache_root: Path,
    destination: Path,
    workers: int = 1,
) -> ExperimentProduct:
    """Freeze all block predictions before outcomes; excluded pollen is never accessed."""
    spec = (
        spec
        if isinstance(spec, SpatialBlockExperimentSpec)
        else SpatialBlockExperimentSpec(spec)
    )
    LRABatchLimits(max_workers=workers)
    if workers > (os.cpu_count() or 1):
        raise ValidationRefusal("experiment_worker_budget_exceeded", str(workers))
    records = [site.record for site in spec.sites]
    groups = {
        record: fold.test_group_ids[0]
        for fold in grouped_leave_one_out(records)
        for record in fold.test_record_ids
    }
    folds = grouped_block_holdouts(records)
    if len(set(groups.values())) != len(records):
        raise ValidationRefusal(
            "unsupported_multi_record_group",
            "Explicit observation selection is required within a physical group",
        )
    by_record = {site.record.record_id: site for site in spec.sites}
    supports = read_block_supports(spec, input_root)
    implementation = _implementation()
    binding = load_engine()
    engine_identity = capture_code_identity(binding)
    stage = stage_directory(destination)
    predictions: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    operations: list[dict[str, object]] = []
    admissions: dict[str, object] = {}
    models: dict[str, str] = {}
    baseline_models: dict[str, str] = {}
    block_fits: dict[str, object] = {}
    interrupted = False
    consumed_pollen: set[str] = set()
    for index, fold in enumerate(folds):
        targets = tuple(by_record[record] for record in fold.test_record_ids)
        try:
            if interrupted:
                raise ValidationRefusal(
                    "experiment_interrupted", "Remaining block not submitted"
                )
            admission = admit_block_training(spec, fold, groups, supports)
            admissions[fold.fold_id] = admission.as_dict()
            if len(admission.admitted_group_ids) < 3:
                raise ValidationRefusal(
                    "insufficient_buffered_training_groups",
                    "Need an admitted regional source and at least two local "
                    "predictor groups",
                )
            fits = reconstruct_fold(
                spec,
                fold,
                groups,
                input_root=input_root,
                cache_root=cache_root,
                report_root=stage / "batches" / f"block-{index:04}",
                workers=workers,
                training_admission=admission,
                consumed_pollen=consumed_pollen,
            )
            baseline_model = _training_mean_model(spec, fold, fits, admission)
            baseline_models[fold.fold_id] = manifest_sha256(baseline_model)
            operations.append(
                {"fold_id": fold.fold_id, "batch": fits.operational_batch}
            )
        except (KeyboardInterrupt, ValidationRefusal, LRARefusal, ValueError) as exc:
            interrupted = (
                interrupted
                or isinstance(exc, KeyboardInterrupt)
                or getattr(exc, "reason_code", None) == "experiment_interrupted"
            )
            for target in targets:
                for method in BLOCK_METHODS:
                    failures.append(
                        _failure(
                            fold.fold_id,
                            target.record.record_id,
                            groups[target.record.record_id],
                            exc,
                            interrupted,
                            method=method,
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
                training_admission=admission,
            )
            models[fold.fold_id] = state.model.model_sha256
            block_fits[fold.fold_id] = retained_training_state(state, groups)
        except (KeyboardInterrupt, ValidationRefusal, LRARefusal, ValueError) as exc:
            fit_failure = exc
            interrupted = (
                interrupted
                or isinstance(exc, KeyboardInterrupt)
                or getattr(exc, "reason_code", None) == "experiment_interrupted"
            )
        for target in targets:
            for method in BLOCK_METHODS:
                try:
                    if interrupted:
                        raise ValidationRefusal(
                            "experiment_interrupted", "Remaining target not submitted"
                        )
                    if method == FITTED_METHOD:
                        if state is None:
                            assert fit_failure is not None
                            raise fit_failure
                        row, _ = predict_fitted_target(
                            spec, target, state, groups, input_root=input_root
                        )
                    else:
                        row = _predict_training_mean_target(
                            spec,
                            target,
                            fold,
                            fits,
                            admission,
                            groups,
                            baseline_model,
                            input_root=input_root,
                        )
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
                            fold.fold_id,
                            target.record.record_id,
                            groups[target.record.record_id],
                            exc,
                            interrupted,
                            method=method,
                        )
                    )
    if _implementation() != implementation:
        raise ValidationRefusal("experiment_implementation_changed", str(stage))
    verify_code_identity(binding, engine_identity)
    fold_rows = [fold.as_dict() for fold in folds]
    requested = sum(len(fold.test_record_ids) for fold in folds) * len(BLOCK_METHODS)
    if len(predictions) + len(failures) != requested:
        raise ValidationRefusal("incomplete_block_accounting", str(stage))
    refused = sum(row["status"] == "refused" for row in failures)
    not_run = sum(row["status"] == "not_run" for row in failures)
    scientific: dict[str, object] = {
        "profile": BLOCK_PROFILE,
        "experiment": "all_target_pollen_withheld_spatial_blocks",
        "folds": fold_rows,
        "record_groups": groups,
        "methods": list(BLOCK_METHODS),
        "evaluation_roles": FITTED_ROLES,
        "predictions": predictions,
        "failures": failures,
        "block_admissions": admissions,
        "block_model_sha256": models,
        "block_baseline_model_sha256": baseline_models,
        "block_fit_records": block_fits,
        "implementation": implementation,
        "engine_identity": engine_identity.payload(),
        "split_manifest_sha256": manifest_sha256(fold_rows),
        "requested_folds": len(folds),
        "requested_predictions": requested,
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
            "schema_version": "lra-spatial-block-experiment.v1",
            "request": spec.request(),
        },
    )
    write_json(stage, "models.json", block_fits)
    for name, value in (
        ("folds.json", fold_rows),
        ("predictions.json", predictions),
        ("failures.json", failures),
        ("operations.json", operations),
        ("block_admissions.json", admissions),
    ):
        write_json(stage, name, value)
    verify_consumed_sources(
        spec,
        input_root,
        pollen_record_ids=consumed_pollen,
        geometry_record_ids=set(groups),
        template_used=bool(consumed_pollen),
    )
    verify_block_supports(spec, input_root)
    return publish_phase(
        stage,
        destination,
        phase="predictions",
        scientific=scientific,
        profile=BLOCK_PROFILE,
    )


def _failure(
    fold_id: str,
    record: str,
    group: str,
    exc: BaseException,
    interrupted: bool,
    *,
    method: str = FITTED_METHOD,
) -> dict[str, object]:
    row: dict[str, object] = {
        "fold_id": fold_id,
        "record_id": record,
        "group_id": group,
        "method": method,
        "status": "not_run" if interrupted else "refused",
        "reason_code": "experiment_interrupted"
        if interrupted
        else getattr(exc, "reason_code", "experiment_target_refused"),
        "detail": str(exc),
        "exception_type": type(exc).__name__,
    }
    if isinstance(exc, LRARefusal):
        row["original_error"] = exc.as_dict()
    return row


def _training_mean_model(
    spec: SpatialBlockExperimentSpec,
    fold: Fold,
    fits: FoldFits,
    admission: TrainingAdmission,
) -> dict[str, object]:
    """Freeze the admitted reconstructed compositions used by the block baseline."""
    return training_mean_model(
        spec,
        fold,
        fits,
        dict(admission.record_groups),
        training_admission=admission,
    )


def _predict_training_mean_target(
    spec: SpatialBlockExperimentSpec,
    target: ExperimentSite,
    fold: Fold,
    fits: FoldFits,
    admission: TrainingAdmission,
    groups: dict[str, str],
    baseline_model: dict[str, object],
    *,
    input_root: Path,
) -> dict[str, object]:
    """Project the admitted training mean without opening a target outcome."""
    return predict_training_mean_target(
        spec,
        target,
        fold,
        fits,
        groups,
        baseline_model,
        input_root=input_root,
        training_admission=admission,
    )
