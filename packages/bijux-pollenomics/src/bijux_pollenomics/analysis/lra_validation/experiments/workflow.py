"""Reconstruct admitted training folds, freeze predictions and account for failures."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import os
from pathlib import Path

from ...lra.api import LRABatchLimits, LRARefusal
from ...lra.engine.discovery import load_engine
from ...lra.outputs.identity import capture_code_identity, verify_code_identity
from ..contracts import ValidationRefusal, manifest_sha256
from ..splits import grouped_leave_one_out
from .configuration import (
    SOURCE_PROFILE,
    ExperimentSpec,
    SourceExperimentSpec,
)
from .inputs import verify_consumed_sources
from .outputs import ExperimentProduct, publish_phase, stage_directory, write_json
from .prediction import predict_fold
from .reconstruction import reconstruct_fold


def _implementation() -> dict[str, str]:
    root = Path(__file__).resolve().parents[1]
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*.py"))
        if "__pycache__" not in path.parts
    }


def prepare_experiment_predictions(
    spec: ExperimentSpec | Mapping[str, object],
    *,
    input_root: Path,
    cache_root: Path,
    destination: Path,
    workers: int = 1,
) -> ExperimentProduct:
    """Run actual source-profile inversions; no scoring inventory is accepted."""
    if not isinstance(spec, ExperimentSpec):
        spec = (
            SourceExperimentSpec(spec)
            if spec.get("profile") == SOURCE_PROFILE
            else ExperimentSpec(spec)
        )
    LRABatchLimits(max_workers=workers)
    if workers > (os.cpu_count() or 1):
        raise ValidationRefusal("experiment_worker_budget_exceeded", str(workers))
    folds = grouped_leave_one_out([site.record for site in spec.sites])
    by_record = {site.record.record_id: site for site in spec.sites}
    group_by_record = {
        record: fold.test_group_ids[0]
        for fold in folds
        for record in fold.test_record_ids
    }
    implementation = _implementation()
    binding = load_engine()
    identity = capture_code_identity(binding)
    stage = stage_directory(destination)
    predictions: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    fit_rows: list[dict[str, object]] = []
    preparations: list[dict[str, object]] = []
    operational: list[dict[str, object]] = []
    interrupted = False
    consumed_pollen: set[str] = set()
    consumed_geometry: set[str] = set()
    for index, fold in enumerate(folds):
        if interrupted:
            failures.append(
                {
                    "fold_id": fold.fold_id,
                    "record_ids": fold.test_record_ids,
                    "status": "not_run",
                    "reason_code": "experiment_interrupted",
                }
            )
            continue
        try:
            if len(fold.test_record_ids) != 1:
                raise ValidationRefusal(
                    "unsupported_multi_record_target",
                    "A reviewed target aggregation is required",
                )
            fits = reconstruct_fold(
                spec,
                fold,
                group_by_record,
                input_root=input_root,
                cache_root=cache_root,
                report_root=stage / "batches" / f"fold-{index:04}",
                workers=workers,
                consumed_pollen=consumed_pollen,
                consumed_geometry=consumed_geometry,
            )
            rows, geometry = predict_fold(
                spec,
                fold,
                by_record[fold.test_record_ids[0]],
                fits,
                group_by_record,
                input_root=input_root,
                consumed_geometry=consumed_geometry,
            )
            predictions.extend(rows)
            fit_rows.append(
                {
                    "fold_id": fold.fold_id,
                    "outer_fold": fold.as_dict(),
                    "regional_anchor_record_id": fits.anchor.record.record_id,
                    "regional_anchor_group_id": group_by_record[
                        fits.anchor.record.record_id
                    ],
                    "predictor_group_ids": sorted(fits.compositions),
                    "training_products": fits.fit_identities,
                }
            )
            preparations.append({"fold_id": fold.fold_id, **geometry})
            operational.append(
                {"fold_id": fold.fold_id, "batch": fits.operational_batch}
            )
        except KeyboardInterrupt:
            interrupted = True
            failures.append(
                {
                    "fold_id": fold.fold_id,
                    "record_ids": fold.test_record_ids,
                    "status": "not_run",
                    "reason_code": "experiment_interrupted",
                }
            )
        except (ValidationRefusal, LRARefusal, ValueError) as exc:
            error: dict[str, object] = {
                "fold_id": fold.fold_id,
                "record_ids": fold.test_record_ids,
                "status": "refused",
                "reason_code": getattr(exc, "reason_code", "experiment_fold_refused"),
                "detail": str(exc),
                "exception_type": type(exc).__name__,
            }
            if isinstance(exc, LRARefusal):
                error["original_error"] = exc.as_dict()
            if error["reason_code"] == "experiment_interrupted":
                interrupted = True
                error["status"] = "not_run"
            failures.append(error)
    if _implementation() != implementation:
        raise ValidationRefusal("experiment_implementation_changed", str(stage))
    verify_code_identity(binding, identity)
    fold_rows = [fold.as_dict() for fold in folds]
    scientific: dict[str, object] = {
        "profile": spec.profile,
        "experiment": "all_target_pollen_withheld",
        "folds": fold_rows,
        "baselines": spec.baselines,
        "predictions": predictions,
        "training": fit_rows,
        "preparations": preparations,
        "failures": failures,
        "implementation": implementation,
        "engine_identity": identity.payload(),
        "requested_folds": len(folds),
        "requested_predictions": len(folds) * len(spec.baselines),
        "generated_predictions": len(predictions),
        "failed_folds": len(failures),
        "interrupted": interrupted,
        "all_predictions_generated": not failures,
        "uncertainty_status": "point_predictions_only_intervals_not_implemented",
    }
    write_json(
        stage,
        "experiment.json",
        {
            "profile": spec.profile,
            "request_template": spec.template(),
            "regional_priority": spec.regional_priority,
            "local_ring_count": spec.local_ring_count,
            "support_profile": spec.support_profile,
            "local_support_radius_m": spec.local_support_radius_m,
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
        ("training.json", fit_rows),
        ("preparations.json", preparations),
        ("failures.json", failures),
        ("operations.json", operational),
    ):
        write_json(stage, name, value)
    scientific["split_manifest_sha256"] = manifest_sha256(fold_rows)
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
        profile=spec.profile,
    )
