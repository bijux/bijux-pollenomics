"""Spatial-block local-pollen predictions without opening vegetation outcomes."""

from __future__ import annotations

from collections.abc import Mapping
import json
import os
from pathlib import Path

from ...lra.api import LRABatchItem, LRABatchLimits, LRARefusal, run_lra_batch
from ...lra.engine.discovery import load_engine
from ...lra.outputs.identity import capture_code_identity, verify_code_identity
from ..contracts import Fold, TrainingAdmission, ValidationRefusal, manifest_sha256
from ..splits import grouped_block_holdouts, grouped_leave_one_out, split_manifest
from .configuration import (
    BLOCK_LOCAL_PROFILE,
    LOCAL_EVALUATION_ROLES,
    LOCAL_METHOD,
    ExperimentSite,
    SpatialBlockLocalPollenSpec,
    identity,
    object_list,
    object_mapping,
)
from .fitted.admission import (
    admit_block_training,
    read_block_supports,
    validate_block_local_request,
    verify_block_supports,
)
from .inputs import channel_catalogue, make_request, verify_consumed_sources
from .outputs import ExperimentProduct, publish_phase, stage_directory, write_json
from .prediction import predict_assimilated_block_local
from .workflow import _implementation


def _failure(
    fold: Fold,
    record_id: str,
    group_id: str,
    exc: BaseException,
    *,
    not_run: bool = False,
) -> dict[str, object]:
    row: dict[str, object] = {
        "fold_id": fold.fold_id,
        "record_id": record_id,
        "group_id": group_id,
        "method": LOCAL_METHOD,
        "status": "not_run" if not_run else "refused",
        "reason_code": "experiment_interrupted"
        if not_run
        else getattr(exc, "reason_code", "local_prediction_refused"),
        "detail": str(exc),
        "exception_type": type(exc).__name__,
    }
    if isinstance(exc, LRARefusal):
        row["original_error"] = exc.as_dict()
    return row


def validate_block_local_prediction_row(
    spec: SpatialBlockLocalPollenSpec,
    fold: Fold,
    admission: TrainingAdmission,
    row: dict[str, object],
    catalogue: object,
) -> None:
    """Recheck one retained target against source, channel and request identities."""
    from ..channels import (
        ObservationChannels,
        ObservedPollenAdmission,
        assert_channel_inputs,
    )
    from .outputs import _pollen_channels

    forbidden = {
        "observed_vegetation",
        "target_vegetation",
        "observed_cover",
        "vegetation_outcome",
        "vegetation_outcome_reference",
        "outcome",
        "score",
        "threshold",
        "release_admission",
    }

    def refuse_outcomes(value: object) -> None:
        if isinstance(value, dict):
            if forbidden & set(value):
                raise ValidationRefusal("block_local_outcome_leakage", "Outcome field")
            for child in value.values():
                refuse_outcomes(child)
        elif isinstance(value, list):
            for child in value:
                refuse_outcomes(child)

    refuse_outcomes(row)
    admission.validate(fold)
    record, group = identity(row["record_id"]), identity(row["group_id"])
    ownership = dict(admission.record_groups)
    sites = {site.record.record_id: site for site in spec.sites}
    source = object_mapping(row["observed_local_pollen_source"], "local_source")
    regional = object_mapping(row["regional_pollen_source"], "regional_source")
    anchor = identity(regional["record_id"])
    eligible = [
        key for key in spec.regional_priority if key in admission.admitted_record_ids
    ]
    if (
        record not in fold.test_record_ids
        or ownership[record] != group
        or not eligible
        or anchor != eligible[0]
    ):
        raise ValidationRefusal("invalid_block_local_target", record)
    target_site, anchor_site = sites[record], sites[anchor]
    owners = [
        object_mapping(value, "owner") for value in object_list(catalogue, "channels")
    ]
    channels = tuple(
        ObservationChannels(
            identity(value["record_id"]),
            identity(value["group_id"]),
            _pollen_channels(value["pollen_channels"]),
            tuple(
                identity(key)
                for key in object_list(value["vegetation_input_ids"], "vegetation")
            ),
        )
        for value in owners
    )
    evidence = object_mapping(row["channel_admission"], "channel_admission")
    declared = object_mapping(evidence["observed_pollen"], "observed_pollen")
    observed = ObservedPollenAdmission(
        identity(declared["record_id"]),
        identity(declared["group_id"]),
        _pollen_channels(declared["pollen_channels"]),
    )
    graph = {
        identity(key): tuple(
            identity(parent) for parent in object_list(value, "parents")
        )
        for key, value in object_mapping(
            evidence["quantitative_lineage"], "lineage"
        ).items()
    }
    inputs = tuple(
        identity(key) for key in object_list(evidence["pollen_input_ids"], "inputs")
    )
    closure = assert_channel_inputs(
        fold, inputs, graph, channels=channels, observed_pollen=observed
    )
    consumed = [
        {
            "record_id": owner.record_id,
            "group_id": owner.group_id,
            "input_id": pollen.input_id,
            "source_sha256": pollen.source_sha256,
        }
        for owner in channels
        for pollen in owner.pollen_channels
        if pollen.input_id in closure
    ]
    criterion = object_mapping(json.loads(admission.criterion_json), "criterion")
    supports = object_mapping(criterion["supports"], "supports")
    validate_block_local_request(spec, row, target_site, anchor_site)
    checks = (
        row.get("training_admission_sha256") == manifest_sha256(admission.as_dict()),
        evidence.get("schema_version") == "lra-block-local-pollen-channel-admission.v1",
        evidence.get("original_fold_sha256") == manifest_sha256(fold.as_dict()),
        evidence.get("training_admission_sha256")
        == manifest_sha256(admission.as_dict()),
        evidence.get("regional_anchor_record_id") == anchor,
        set(closure) == {"raw:" + record, "raw:" + anchor, anchor},
        list(closure) == evidence.get("pollen_channel_closure"),
        consumed == evidence.get("consumed_pollen_sources"),
        observed.record_id == record and observed.group_id == group,
        source
        == {
            "record_id": record,
            "group_id": group,
            "path": target_site.raw.path,
            "sha256": target_site.raw.sha256,
            "role": "observed_local_pollen",
        },
        regional
        == {
            "record_id": anchor,
            "path": anchor_site.raw.path,
            "sha256": anchor_site.raw.sha256,
            "role": "buffer_admitted_training_regional_pollen",
        },
        row.get("target_geometry_sha256") == target_site.geometry.sha256,
        row.get("target_support") == supports[record],
        row.get("regional_anchor_support") == supports[anchor],
        row.get("unused_training_record_ids")
        == [key for key in fold.train_record_ids if key != anchor],
    )
    if not all(checks):
        raise ValidationRefusal("block_local_row_mismatch", record)


def prepare_spatial_block_local_pollen_predictions(
    spec: SpatialBlockLocalPollenSpec | Mapping[str, object],
    *,
    input_root: Path,
    cache_root: Path,
    destination: Path,
    workers: int = 1,
) -> ExperimentProduct:
    """Publish authenticated exploratory point predictions; accept no outcomes."""
    spec = (
        spec
        if isinstance(spec, SpatialBlockLocalPollenSpec)
        else SpatialBlockLocalPollenSpec(spec)
    )
    records = [site.record for site in spec.sites]
    split = split_manifest(records, by_block=True)
    folds = grouped_block_holdouts(records)
    limits = LRABatchLimits(
        max_workers=workers,
        max_items=sum(len(fold.test_record_ids) for fold in folds),
    )
    if workers > (os.cpu_count() or 1):
        raise ValidationRefusal("experiment_worker_budget_exceeded", str(workers))
    groups = {
        record: fold.test_group_ids[0]
        for fold in grouped_leave_one_out(records)
        for record in fold.test_record_ids
    }
    by_record = {site.record.record_id: site for site in spec.sites}
    supports = read_block_supports(spec, input_root)
    implementation = _implementation()
    binding = load_engine()
    code = capture_code_identity(binding)
    stage = stage_directory(destination)
    admitted: dict[
        str,
        tuple[
            Fold,
            ExperimentSite,
            ExperimentSite,
            TrainingAdmission,
            dict[str, object],
        ],
    ] = {}
    items: list[LRABatchItem] = []
    failures: list[dict[str, object]] = []
    admissions: dict[str, object] = {}
    consumed_pollen: set[str] = set()
    consumed_geometry: set[str] = set()
    interrupted = False
    for fold in folds:
        targets = tuple(by_record[record] for record in fold.test_record_ids)
        if interrupted:
            failures.extend(
                _failure(
                    fold,
                    target.record.record_id,
                    groups[target.record.record_id],
                    KeyboardInterrupt(),
                    not_run=True,
                )
                for target in targets
            )
            continue
        try:
            admission = admit_block_training(spec, fold, groups, supports)
            admissions[fold.fold_id] = admission.as_dict()
            anchors = [
                record
                for record in spec.regional_priority
                if record in admission.admitted_record_ids
            ]
            if not anchors:
                raise ValidationRefusal(
                    "missing_buffered_regional_anchor", fold.fold_id
                )
            anchor = by_record[anchors[0]]
        except KeyboardInterrupt as exc:
            interrupted = True
            failures.extend(
                _failure(
                    fold,
                    target.record.record_id,
                    groups[target.record.record_id],
                    exc,
                    not_run=True,
                )
                for target in targets
            )
            continue
        except (ValidationRefusal, LRARefusal, ValueError) as exc:
            failures.extend(
                _failure(
                    fold,
                    target.record.record_id,
                    groups[target.record.record_id],
                    exc,
                )
                for target in targets
            )
            continue
        for target in targets:
            item_id = fold.fold_id + ":" + target.record.record_id
            if interrupted:
                failures.append(
                    _failure(
                        fold,
                        target.record.record_id,
                        groups[target.record.record_id],
                        KeyboardInterrupt(),
                        not_run=True,
                    )
                )
                continue
            try:
                request = make_request(
                    spec,
                    target,
                    anchor,
                    fold,
                    input_root,
                    training_admission=admission,
                    consumed_pollen=consumed_pollen,
                    consumed_geometry=consumed_geometry,
                )
                admitted[item_id] = (fold, target, anchor, admission, request)
                items.append(LRABatchItem(item_id, request))
            except KeyboardInterrupt as exc:
                interrupted = True
                failures.append(
                    _failure(
                        fold,
                        target.record.record_id,
                        groups[target.record.record_id],
                        exc,
                        not_run=True,
                    )
                )
            except (ValidationRefusal, LRARefusal, ValueError) as exc:
                failures.append(
                    _failure(
                        fold,
                        target.record.record_id,
                        groups[target.record.record_id],
                        exc,
                    )
                )
    predictions: list[dict[str, object]] = []
    operations: dict[str, object] = {}
    if interrupted:
        for fold, target, _, _, _ in admitted.values():
            failures.append(
                _failure(
                    fold,
                    target.record.record_id,
                    groups[target.record.record_id],
                    KeyboardInterrupt(),
                    not_run=True,
                )
            )
    elif items:
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
            fold, target, anchor, admission, request = admitted[item.item_id]
            if projection_interrupted or item.product is None:
                failures.append(
                    _failure(
                        fold,
                        target.record.record_id,
                        groups[target.record.record_id],
                        ValidationRefusal(
                            "local_reconstruction_incomplete", item.item_id
                        ),
                        not_run=projection_interrupted or batch.interrupted,
                    )
                )
                continue
            try:
                predictions.append(
                    predict_assimilated_block_local(
                        spec,
                        fold,
                        target,
                        anchor,
                        admission,
                        item.product,
                        request,
                        input_root=input_root,
                        consumed_geometry=consumed_geometry,
                    )
                )
            except KeyboardInterrupt as exc:
                projection_interrupted = True
                interrupted = True
                failures.append(
                    _failure(
                        fold,
                        target.record.record_id,
                        groups[target.record.record_id],
                        exc,
                        not_run=True,
                    )
                )
            except (ValidationRefusal, LRARefusal, ValueError) as exc:
                failures.append(
                    _failure(
                        fold,
                        target.record.record_id,
                        groups[target.record.record_id],
                        exc,
                    )
                )
    if _implementation() != implementation:
        raise ValidationRefusal("experiment_implementation_changed", str(stage))
    verify_code_identity(binding, code)
    ordered = tuple(
        (fold.fold_id, record, LOCAL_METHOD)
        for fold in folds
        for record in fold.test_record_ids
    )
    expected = set(ordered)
    actual = {
        (str(row["fold_id"]), str(row["record_id"]), str(row["method"]))
        for row in (*predictions, *failures)
    }
    if actual != expected or len(actual) != len(predictions) + len(failures):
        raise ValidationRefusal("incomplete_block_local_accounting", str(stage))
    terminal = {
        (str(row["fold_id"]), str(row["record_id"]), str(row["method"])): (
            "predicted" if "status" not in row else str(row["status"])
        )
        for row in (*predictions, *failures)
    }
    first_not_run = next(
        (index for index, key in enumerate(ordered) if terminal[key] == "not_run"),
        None,
    )
    if first_not_run is not None and any(
        terminal[key] != "not_run" for key in ordered[first_not_run:]
    ):
        raise ValidationRefusal("invalid_interruption_accounting", str(stage))
    refused = sum(row["status"] == "refused" for row in failures)
    not_run = sum(row["status"] == "not_run" for row in failures)
    fold_rows = [fold.as_dict() for fold in folds]
    scientific: dict[str, object] = {
        "profile": BLOCK_LOCAL_PROFILE,
        "experiment": "local_pollen_available_spatial_blocks",
        "method": LOCAL_METHOD,
        "method_kind": "local_pollen_assimilation",
        "evaluation_roles": LOCAL_EVALUATION_ROLES,
        "pollen_eligible_for_heldout_acceptance": False,
        "folds": fold_rows,
        "split_manifest": split,
        "split_manifest_sha256": manifest_sha256(split),
        "record_groups": groups,
        "predictions": predictions,
        "failures": failures,
        "block_admissions": admissions,
        "requested_folds": len(folds),
        "requested_predictions": len(expected),
        "generated_predictions": len(predictions),
        "refused_predictions": refused,
        "not_run_predictions": not_run,
        "failed_predictions": len(failures),
        "failed_folds": len({str(row["fold_id"]) for row in failures}),
        "interrupted": bool(not_run),
        "all_predictions_generated": not failures,
        "implementation": implementation,
        "engine_identity": code.payload(),
        "uncertainty_status": "point_predictions_only_intervals_not_implemented",
        "scientific_acceptance": "not_evaluated",
    }
    write_json(
        stage,
        "experiment.json",
        {
            "schema_version": "lra-spatial-block-local-experiment.v1",
            "request": spec.request(),
            "observation_channels": channel_catalogue(spec),
        },
    )
    for name, value in (
        ("split_manifest.json", split),
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
        geometry_record_ids=consumed_geometry,
        template_used=bool(consumed_pollen),
    )
    verify_block_supports(spec, input_root)
    return publish_phase(
        stage,
        destination,
        phase="predictions",
        scientific=scientific,
        profile=BLOCK_LOCAL_PROFILE,
    )
