"""Observed local pollen inversion with genuinely deferred vegetation scoring."""

from __future__ import annotations

from collections.abc import Mapping
import os
from pathlib import Path

from ...lra.api import LRABatchItem, LRABatchLimits, LRARefusal, run_lra_batch
from ...lra.engine.discovery import load_engine
from ...lra.outputs.identity import capture_code_identity, verify_code_identity
from ..contracts import Fold, ValidationRefusal, finite_number, manifest_sha256
from ..metrics import closed_composition, score_pollen, score_vegetation
from ..splits import grouped_leave_one_out
from .configuration import (
    LOCAL_EVALUATION_ROLES,
    LOCAL_METHOD,
    LOCAL_PROFILE,
    ExperimentSite,
    InputReference,
    LocalPollenSpec,
    identity,
    object_list,
    object_mapping,
)
from .inputs import (
    admitted_pollen_counts,
    channel_catalogue,
    make_request,
    read_reference,
    verify_consumed_sources,
)
from .outputs import (
    ExperimentProduct,
    local_prediction_rows,
    publish_phase,
    read_experiment_product,
    read_member,
    stage_directory,
    write_json,
)
from .prediction import predict_assimilated_local
from .workflow import _implementation

ROLES = LOCAL_EVALUATION_ROLES


def prepare_local_pollen_predictions(
    spec: LocalPollenSpec | Mapping[str, object],
    *,
    input_root: Path,
    cache_root: Path,
    destination: Path,
    workers: int = 1,
) -> ExperimentProduct:
    """Observe the declared local pollen channel; accept no vegetation outcome source."""
    spec = spec if isinstance(spec, LocalPollenSpec) else LocalPollenSpec(spec)
    limits = LRABatchLimits(max_workers=workers, max_items=len(spec.sites))
    if workers > (os.cpu_count() or 1):
        raise ValidationRefusal("experiment_worker_budget_exceeded", str(workers))
    folds = grouped_leave_one_out([site.record for site in spec.sites])
    by_record = {site.record.record_id: site for site in spec.sites}
    binding = load_engine()
    code = capture_code_identity(binding)
    implementation = _implementation()
    stage = stage_directory(destination)
    admitted: dict[
        str, tuple[Fold, ExperimentSite, ExperimentSite, dict[str, object]]
    ] = {}
    items = []
    failures: list[dict[str, object]] = []
    interrupted = False
    for fold in folds:
        if interrupted:
            failures.append(_not_run(fold))
            continue
        try:
            if len(fold.test_record_ids) != 1 or len(fold.train_group_ids) != len(
                fold.train_record_ids
            ):
                raise ValidationRefusal(
                    "unsupported_multi_record_group",
                    "Explicit within-group observation selection is required",
                )
            eligible = [
                record
                for record in spec.regional_priority
                if record in fold.train_record_ids
            ]
            if not eligible:
                raise ValidationRefusal("missing_regional_anchor", fold.fold_id)
            target, anchor = by_record[fold.test_record_ids[0]], by_record[eligible[0]]
            request = make_request(spec, target, anchor, fold, input_root)
            admitted[target.record.record_id] = (fold, target, anchor, request)
            items.append(LRABatchItem(target.record.record_id, request))
        except KeyboardInterrupt:
            interrupted = True
            failures.append(_not_run(fold))
        except (ValidationRefusal, LRARefusal) as exc:
            failures.append(
                {
                    "fold_id": fold.fold_id,
                    "record_ids": fold.test_record_ids,
                    "status": "refused",
                    "reason_code": exc.reason_code,
                    "detail": str(exc),
                }
            )
    predictions = []
    operations: dict[str, object] = {}
    if interrupted:
        failures.extend(_not_run(fold) for fold, _, _, _ in admitted.values())
    if items and not interrupted:
        batch = run_lra_batch(
            items,
            input_root=input_root,
            cache_root=cache_root,
            report_root=stage / "batch",
            limits=limits,
        )
        operations = batch.as_dict()
        interrupted = batch.interrupted
        projection_interrupted = False
        for item in batch.items:
            fold, target, anchor, request = admitted[item.item_id]
            if projection_interrupted:
                failures.append(_not_run(fold))
                continue
            if item.product is None:
                failures.append(
                    {
                        "fold_id": fold.fold_id,
                        "record_ids": fold.test_record_ids,
                        "status": item.item_status,
                        "reason_code": "local_reconstruction_incomplete",
                        "batch_item_id": item.item_id,
                    }
                )
                continue
            try:
                predictions.append(
                    predict_assimilated_local(
                        spec,
                        fold,
                        target,
                        anchor,
                        item.product,
                        request,
                        input_root=input_root,
                    )
                )
            except KeyboardInterrupt:
                projection_interrupted = True
                interrupted = True
                failures.append(_not_run(fold))
            except (ValidationRefusal, LRARefusal, ValueError) as exc:
                failures.append(
                    {
                        "fold_id": fold.fold_id,
                        "record_ids": fold.test_record_ids,
                        "status": "refused",
                        "reason_code": getattr(
                            exc, "reason_code", "local_prediction_refused"
                        ),
                        "detail": str(exc),
                    }
                )
    if _implementation() != implementation:
        raise ValidationRefusal("experiment_implementation_changed", str(stage))
    verify_code_identity(binding, code)
    scientific: dict[str, object] = {
        "profile": LOCAL_PROFILE,
        "method": LOCAL_METHOD,
        "method_kind": "local_pollen_assimilation",
        "evaluation_roles": ROLES,
        "pollen_eligible_for_heldout_acceptance": False,
        "folds": [fold.as_dict() for fold in folds],
        "predictions": predictions,
        "failures": failures,
        "requested_folds": len(folds),
        "generated_predictions": len(predictions),
        "failed_folds": len(failures),
        "interrupted": interrupted,
        "all_predictions_generated": not failures,
        "implementation": implementation,
        "engine_identity": code.payload(),
        "uncertainty_status": "point_predictions_only_intervals_not_implemented",
    }
    for name, value in (
        ("predictions.json", predictions),
        ("folds.json", scientific["folds"]),
        ("failures.json", failures),
        ("operations.json", operations),
    ):
        write_json(stage, name, value)
    write_json(
        stage,
        "experiment.json",
        {
            "profile": LOCAL_PROFILE,
            "method": LOCAL_METHOD,
            "request_template": spec.template(),
            "regional_priority": spec.regional_priority,
            "local_ring_count": spec.local_ring_count,
            "local_support_radius_m": spec.local_support_radius_m,
            "support_profile": spec.support_profile,
            "observation_channels": channel_catalogue(spec),
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
    consumed = {
        site.record.record_id
        for _, target, anchor, _ in admitted.values()
        for site in (target, anchor)
    }
    verify_consumed_sources(
        spec,
        input_root,
        pollen_record_ids=consumed,
        geometry_record_ids=consumed,
        template_used=bool(operations),
    )
    return publish_phase(
        stage,
        destination,
        phase="predictions",
        scientific=scientific,
        profile=LOCAL_PROFILE,
    )


def _score_local_pollen_predictions(
    predictions: Path,
    *,
    expected_manifest_sha256: str,
    outcome_root: Path,
    outcome_inventory: Mapping[str, object],
    destination: Path,
) -> ExperimentProduct:
    """Score deferred vegetation; pollen diagnostics use only previously assimilated counts."""
    inventory = object_mapping(outcome_inventory, "outcomes")
    if (
        set(inventory) != {"schema_version", "data_kind", "records"}
        or inventory["schema_version"] != "lra-local-pollen-outcomes.v1"
        or inventory["data_kind"] != "synthetic"
    ):
        raise ValidationRefusal(
            "unsupported_local_outcomes",
            "Explicit synthetic vegetation-only outcome inventory is required",
        )
    product, manifest = read_experiment_product(
        predictions, expected_manifest_sha256=expected_manifest_sha256
    )
    folds, rows = local_prediction_rows(
        manifest,
        read_member(product, "predictions.json"),
        object_mapping(read_member(product, "experiment.json"), "experiment")[
            "observation_channels"
        ],
    )
    references = {
        identity(key): InputReference.parse(value, key)
        for key, value in object_mapping(inventory["records"], "records").items()
    }
    catalogue = {
        identity(record)
        for fold in folds.values()
        for record in object_list(fold["test_record_ids"], "test_record_ids")
    }
    if not set(references).issubset(catalogue):
        raise ValidationRefusal(
            "unknown_experiment_outcome",
            "Outcome reference is outside the held-out catalogue",
        )
    stage = stage_directory(destination)
    scores: list[dict[str, object]] = []
    accesses: list[dict[str, object]] = []
    for fold_id, fold in sorted(folds.items()):
        prediction = rows.get(fold_id)
        outcome = None
        refusal = None
        record_id = identity(object_list(fold["test_record_ids"], "test_record_ids")[0])
        if prediction is not None and record_id in references:
            accesses.append(
                {
                    "record_id": record_id,
                    "observation_sha256": references[record_id].sha256,
                    "prediction_manifest_sha256": product.manifest_sha256,
                    "ordering": "published_predictions_before_vegetation_open",
                }
            )
            write_json(stage, "outcome_access.json", accesses)
            try:
                outcome = read_reference(outcome_root, references[record_id])
                if (
                    set(outcome)
                    != {
                        "schema_version",
                        "data_kind",
                        "record_id",
                        "bin_id",
                        "vegetation_unit",
                        "vegetation_fraction",
                    }
                    or outcome["schema_version"]
                    != "lra-local-vegetation-observation.v1"
                    or outcome["data_kind"] != "synthetic"
                    or outcome["record_id"] != record_id
                    or outcome["bin_id"] != prediction["bin_id"]
                    or outcome["vegetation_unit"] != "fraction"
                ):
                    raise ValidationRefusal(
                        "local_vegetation_outcome_mismatch",
                        "No substituted pollen or mismatched identity/unit is admitted",
                    )
            except ValidationRefusal as exc:
                refusal = exc
        for target, role in ROLES.items():
            row: dict[str, object] = {
                "fold_id": fold_id,
                "group_id": object_list(fold["test_group_ids"], "test_group_ids")[0],
                "record_id": record_id,
                "method": LOCAL_METHOD,
                "method_kind": "local_pollen_assimilation",
                "target": target,
                "evaluation_role": role,
                "eligible_for_heldout_acceptance": target == "vegetation_cover",
                "error_unit": "fraction",
            }
            score: dict[str, object] = {
                "status": "prediction_failed",
                "mae_fraction": None,
            }
            if prediction is not None:
                vector = closed_composition(
                    {
                        taxon: finite_number(value)
                        for taxon, value in object_mapping(
                            prediction[
                                "vegetation_fraction"
                                if target == "vegetation_cover"
                                else "pollen_fraction"
                            ],
                            "prediction",
                        ).items()
                    }
                )
                row.update(
                    bin_id=prediction["bin_id"],
                    prediction=vector,
                    prediction_manifest_sha256=prediction["prediction_manifest_sha256"],
                )
                if target == "pollen_composition":
                    counts = admitted_pollen_counts(
                        prediction["observed_pollen_count"], tuple(vector)
                    )
                    score = score_pollen(vector, counts).as_dict()
                    row.update(
                        observation=counts,
                        observation_unit="count",
                        observation_reference=prediction[
                            "observed_local_pollen_source"
                        ],
                    )
                elif refusal is not None:
                    score = {
                        "status": "observation_refused",
                        "reason_code": refusal.reason_code,
                        "detail": str(refusal),
                        "mae_fraction": None,
                    }
                elif outcome is None or outcome["vegetation_fraction"] is None:
                    score = {"status": "missing_observation", "mae_fraction": None}
                else:
                    try:
                        observed = {
                            taxon: None if value is None else finite_number(value)
                            for taxon, value in object_mapping(
                                outcome["vegetation_fraction"], "vegetation_fraction"
                            ).items()
                        }
                        score = score_vegetation(vector, observed).as_dict()
                        row.update(
                            observation=observed,
                            observation_unit="fraction",
                            observation_reference={
                                "path": references[record_id].path,
                                "sha256": references[record_id].sha256,
                            },
                        )
                    except ValidationRefusal as exc:
                        score = {
                            "status": "observation_refused",
                            "reason_code": exc.reason_code,
                            "detail": str(exc),
                            "mae_fraction": None,
                        }
            row["score"] = score
            scores.append(row)
    summaries = []
    for target, role in ROLES.items():
        values = [
            object_mapping(row["score"], "score")
            for row in scores
            if row["target"] == target
        ]
        statuses = {identity(row["status"]) for row in values}
        errors = [
            finite_number(row["mae_fraction"])
            for row in values
            if row["status"] == "scored"
        ]
        summaries.append(
            {
                "method": LOCAL_METHOD,
                "target": target,
                "evaluation_role": role,
                "eligible_for_heldout_acceptance": target == "vegetation_cover",
                "requested": len(folds),
                "scored": len(errors),
                "by_status": {
                    status: sum(value["status"] == status for value in values)
                    for status in sorted(statuses)
                },
                "mean_mae_fraction": sum(errors) / len(errors) if errors else None,
                "interval_coverage": None,
                "uncertainty_status": "intervals_not_implemented",
            }
        )
    read_experiment_product(
        predictions, expected_manifest_sha256=expected_manifest_sha256
    )
    scientific: dict[str, object] = {
        "profile": LOCAL_PROFILE,
        "prediction_manifest_sha256": product.manifest_sha256,
        "prediction_scientific_content_sha256": product.scientific_content_sha256,
        "outcome_inventory_sha256": manifest_sha256(inventory),
        "scores": scores,
        "summaries": summaries,
        "scientific_acceptance": "not_evaluated",
    }
    for name, value in (
        ("scores.json", scores),
        ("summaries.json", summaries),
        ("outcome_inventory.json", inventory),
        ("outcome_access.json", accesses),
    ):
        write_json(stage, name, value)
    return publish_phase(
        stage, destination, phase="scores", scientific=scientific, profile=LOCAL_PROFILE
    )


def _not_run(fold: Fold) -> dict[str, object]:
    return {
        "fold_id": fold.fold_id,
        "record_ids": fold.test_record_ids,
        "status": "not_run",
        "reason_code": "experiment_interrupted",
    }
