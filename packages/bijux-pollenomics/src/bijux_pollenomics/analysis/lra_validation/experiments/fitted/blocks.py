"""One train-only reconstruction/model per genuine heldout spatial block."""

from __future__ import annotations

from collections.abc import Mapping
import os
from pathlib import Path
from typing import cast

from ....lra.api import LRABatchLimits, LRARefusal
from ....lra.engine.discovery import load_engine
from ....lra.outputs.identity import capture_code_identity, verify_code_identity
from ...contracts import Fold, TrainingAdmission, ValidationRefusal, manifest_sha256
from ...metrics import closed_composition
from ...prediction import ForwardModel
from ...splits import (
    assert_training_inputs,
    grouped_block_holdouts,
    grouped_leave_one_out,
)
from ..configuration import (
    BLOCK_BASELINE_METHOD,
    BLOCK_METHODS,
    BLOCK_PROFILE,
    FITTED_METHOD,
    FITTED_ROLES,
    ExperimentSite,
    SpatialBlockExperimentSpec,
    identity,
)
from ..inputs import verify_consumed_sources
from ..outputs import ExperimentProduct, publish_phase, stage_directory, write_json
from ..prediction import prepare_target_forward
from ..reconstruction import FoldFits, reconstruct_fold
from ..workflow import _implementation
from .admission import admit_block_training, read_block_supports, verify_block_supports
from .model import (
    FittedTrainingState,
    fit_reconstructed_training,
    fitted_support,
    predict_fitted_target,
    retained_training_state,
)


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
    admission.validate(fold)
    support = fitted_support(spec)
    support_id = "experiment-support:" + manifest_sha256(support)
    fit_ids = tuple(
        "experiment-fit:" + manifest_sha256(value) for value in fits.fit_identities
    )
    inputs = (*admission.admitted_record_ids, *fit_ids, support_id)
    externals = (*fit_ids, support_id)
    anchor = fits.anchor.record.record_id
    ownership = dict(admission.record_groups)
    product_records = tuple(
        identity(value.get("record_id")) for value in fits.fit_identities
    )
    if (
        anchor not in admission.admitted_record_ids
        or len(fit_ids) != len(set(fit_ids))
        or len(product_records) != len(set(product_records))
        or set(product_records) != set(admission.admitted_record_ids) - {anchor}
        or any(
            ownership[record] != identity(value.get("group_id"))
            for record, value in zip(product_records, fits.fit_identities, strict=True)
        )
    ):
        raise ValidationRefusal(
            "block_baseline_training_mismatch",
            "Reconstruction products differ from admitted record/group ownership",
        )
    graph: dict[str, tuple[str, ...]] = dict.fromkeys(admission.admitted_record_ids, ())
    for node, value in zip(fit_ids, fits.fit_identities, strict=True):
        record = identity(value.get("record_id"))
        if record not in admission.admitted_record_ids or node in graph:
            raise ValidationRefusal("block_baseline_training_mismatch", record)
        graph[node] = (record, anchor)
    graph[support_id] = ()
    closure = assert_training_inputs(
        fold,
        inputs,
        graph,
        admitted_external_ids=externals,
        training_admission=admission,
    )
    compositions = {
        group: closed_composition(values)
        for group, values in sorted(fits.compositions.items())
    }
    if not compositions or set(compositions) != set(admission.admitted_group_ids) - {
        ownership[anchor]
    }:
        raise ValidationRefusal(
            "block_baseline_training_mismatch",
            "Require one reconstructed composition per admitted non-anchor group",
        )
    products = list(fits.fit_identities)
    if {
        identity(value.get("group_id")): value.get("composition") for value in products
    } != compositions:
        raise ValidationRefusal(
            "block_baseline_training_mismatch",
            "Retained reconstruction products differ from baseline compositions",
        )
    return {
        "schema_version": "lra-spatial-block-training-mean.v1",
        "method": BLOCK_BASELINE_METHOD,
        "method_kind": "admitted_reconstruction_training_mean",
        "fold": fold.as_dict(),
        "training_admission": admission.as_dict(),
        "predictor_group_ids": sorted(compositions),
        "training_compositions": compositions,
        "training_products": products,
        "training_input_ids": list(inputs),
        "training_external_ids": list(externals),
        "allowed_input_closure": list(closure),
        "input_lineage": {key: sorted(set(graph[key])) for key in closure},
        "support": support,
        "regional_anchor_record_id": anchor,
        "regional_anchor_group_id": ownership[anchor],
        "regional_value_source_record_ids": [anchor],
        "regional_identity_source_record_ids": list(admission.admitted_record_ids),
        "uncertainty_status": "deterministic_point_baseline_no_intervals",
        "scientific_acceptance": "not_evaluated",
    }


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
    binding, prepared, geometry, bin_id = prepare_target_forward(
        spec,
        target,
        fits.anchor,
        fits.regional_cover,
        input_root=input_root,
    )
    compositions = {
        group: closed_composition(values) for group, values in fits.compositions.items()
    }
    taxa = tuple(prepared.taxa)
    if not compositions or any(
        set(values) != set(taxa) for values in compositions.values()
    ):
        raise ValidationRefusal(
            "block_baseline_taxon_mismatch",
            "All admitted training reconstructions require the target taxon "
            "denominator",
        )
    vegetation = closed_composition(
        {
            taxon: sum(values[taxon] for values in compositions.values())
            / len(compositions)
            for taxon in taxa
        }
    )
    forward = cast(ForwardModel, binding.api.forward_deposition)(
        local_cover=tuple(vegetation[taxon] for taxon in taxa),
        regional_deposition=tuple(prepared.regional_deposition),
        local_k=tuple(tuple(ring) for ring in prepared.local_k),
        terrestrial_fraction=tuple(prepared.terrestrial_fraction),
        ppe=tuple(prepared.ppe),
    )
    if forward.method_profile != prepared.method_profile:
        raise ValidationRefusal("block_baseline_forward_profile_mismatch", fold.fold_id)
    pollen = closed_composition(
        dict(zip(taxa, tuple(forward.pollen_fraction), strict=True))
    )
    preparation: dict[str, object] = {
        "preparation_profile": prepared.preparation_profile,
        "forward_method_profile": prepared.method_profile,
        "geometry_profile": prepared.geometry_profile,
        "deposition_units": prepared.deposition_units,
        "taxa": taxa,
        "local_k": [list(ring) for ring in prepared.local_k],
        "terrestrial_fraction": list(prepared.terrestrial_fraction),
        "ppe": list(prepared.ppe),
        "regional_deposition": list(prepared.regional_deposition),
        "regional_cover": list(prepared.regional_cover),
        "ring_bounds_m": [list(ring) for ring in prepared.ring_bounds_m],
        "regional_cutoff_m": prepared.regional_cutoff_m,
        "target_geometry_sha256": target.geometry.sha256,
        "declared_target_inversion_rings": geometry["inversion_rings"],
        "declared_target_forward_rings": geometry["forward_rings"],
    }
    row: dict[str, object] = {
        "profile": BLOCK_PROFILE,
        "method": BLOCK_BASELINE_METHOD,
        "method_kind": "admitted_reconstruction_training_mean",
        "evaluation_roles": FITTED_ROLES,
        "fold_id": fold.fold_id,
        "outer_fold": fold.as_dict(),
        "record_id": target.record.record_id,
        "group_id": groups[target.record.record_id],
        "bin_id": bin_id,
        "vegetation_fraction": vegetation,
        "pollen_fraction": pollen,
        "baseline_model_sha256": manifest_sha256(baseline_model),
        "baseline_model_manifest": baseline_model,
        "training_admission": admission.as_dict(),
        "support": baseline_model["support"],
        "target_geometry_sha256": target.geometry.sha256,
        "forward_preparation": preparation,
        "uncertainty_status": "deterministic_point_baseline_no_intervals",
        "scientific_acceptance": "not_evaluated",
    }
    row["prediction_manifest_sha256"] = manifest_sha256(row)
    return row
