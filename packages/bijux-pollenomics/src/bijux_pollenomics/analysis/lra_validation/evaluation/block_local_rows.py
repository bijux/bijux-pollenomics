"""Adapt authenticated block-local products into outcome-free evaluation rows."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from ..channels import ObservedPollenAdmission, PollenChannel
from ..contracts import canonical_json, finite_number, manifest_sha256
from ..experiments.configuration import (
    BLOCK_BASELINE_METHOD,
    LOCAL_METHOD,
    identity,
    object_list,
    object_mapping,
)
from ..experiments.reading.products import (
    read_spatial_block_local_pollen_predictions,
    read_spatial_block_predictions,
)
from .contracts import (
    EvaluationRow,
    EvaluationScope,
    _authenticated_source_model,
    digest,
    freeze_evaluation_prediction,
    refuse,
)


def _failures(
    manifest: dict[str, object], *, method: str
) -> dict[tuple[str, str, str], dict[str, object]]:
    scientific = object_mapping(manifest["scientific_payload"], "scientific_payload")
    result: dict[tuple[str, str, str], dict[str, object]] = {}
    for value in object_list(scientific["failures"], "failures"):
        row = object_mapping(value, "failure")
        key = (
            identity(row["fold_id"]),
            identity(row["record_id"]),
            identity(row["method"]),
        )
        if key[2] == method:
            result[key] = row
    return result


def _pollen_admission(row: dict[str, object]) -> ObservedPollenAdmission:
    evidence = object_mapping(row["channel_admission"], "channel_admission")
    observed = object_mapping(evidence["observed_pollen"], "observed_pollen")
    channels = tuple(
        PollenChannel(
            identity(channel["input_id"]),
            digest(cast(str, channel["source_sha256"])),
        )
        for value in object_list(observed["pollen_channels"], "pollen_channels")
        if (channel := object_mapping(value, "pollen_channel"))
    )
    return ObservedPollenAdmission(
        identity(observed["record_id"]),
        identity(observed["group_id"]),
        channels,
    )


def _local_source_sha256(
    row: dict[str, object], *, product_manifest_sha256: str
) -> str:
    """Bind the complete authenticated, target-specific local model source."""
    channel = object_mapping(row["channel_admission"], "channel_admission")
    return manifest_sha256(
        {
            "schema_version": "lra-block-local-evaluation-source.v1",
            "product_manifest_sha256": digest(product_manifest_sha256),
            "prediction_manifest_sha256": digest(
                cast(str, row["prediction_manifest_sha256"])
            ),
            "profile": row["profile"],
            "method": row["method"],
            "method_kind": row["method_kind"],
            "fold_id": row["fold_id"],
            "record_id": row["record_id"],
            "group_id": row["group_id"],
            "bin_id": row["bin_id"],
            "training_admission_sha256": row["training_admission_sha256"],
            "channel_admission_sha256": manifest_sha256(channel),
            "request_sha256": row["request_sha256"],
            "numerical_product_sha256": manifest_sha256(row["numerical_product"]),
            "engine_build_sha256": manifest_sha256(row["engine_build"]),
            "target_geometry_sha256": row["target_geometry_sha256"],
            "target_support_sha256": manifest_sha256(row["target_support"]),
            "preparation_profile": row["preparation_profile"],
            "forward_method_profile": row["forward_method_profile"],
        }
    )


def _failed_row(
    *, fold_id: str, record_id: str, model_id: str, parent: dict[str, object]
) -> EvaluationRow:
    status = identity(parent["status"])
    reason = identity(parent["reason_code"])
    return EvaluationRow(
        fold_id=fold_id,
        record_id=record_id,
        model_id=model_id,
        target="vegetation_cover",
        experiment="local_pollen_available",
        status="prediction_failed",
        prediction=None,
        observation=None,
        observation_reference_id=None,
        observation_kind=None,
        observation_support=None,
        prediction_sha256=None,
        prediction_manifest_json=None,
        fitted_model_sha256=None,
        prediction_frozen_at=None,
        fit_input_ids=(),
        reason=f"parent_{status}:{reason}",
    )


def _local_row(
    parent: dict[str, object], *, product_manifest_sha256: str
) -> EvaluationRow:
    evidence = object_mapping(parent["channel_admission"], "channel_admission")
    inputs = tuple(
        identity(value)
        for value in object_list(evidence["pollen_input_ids"], "pollen_input_ids")
    )
    prediction = tuple(
        sorted(
            (identity(taxon), finite_number(value))
            for taxon, value in object_mapping(
                parent["vegetation_fraction"], "vegetation_fraction"
            ).items()
        )
    )
    return freeze_evaluation_prediction(
        EvaluationRow(
            fold_id=identity(parent["fold_id"]),
            record_id=identity(parent["record_id"]),
            model_id=LOCAL_METHOD,
            target="vegetation_cover",
            experiment="local_pollen_available",
            status="predicted",
            prediction=prediction,
            observation=None,
            observation_reference_id=None,
            observation_kind=None,
            observation_support=None,
            prediction_sha256=None,
            prediction_manifest_json=None,
            fitted_model_sha256=None,
            prediction_frozen_at=None,
            fit_input_ids=inputs,
            observed_pollen=_pollen_admission(parent),
            source_model=_authenticated_source_model(
                "local_pollen_assimilation",
                _local_source_sha256(
                    parent, product_manifest_sha256=product_manifest_sha256
                ),
            ),
        )
    )


def _baseline_row(parent: dict[str, object]) -> EvaluationRow:
    model = object_mapping(parent["baseline_model_manifest"], "baseline_model")
    inputs = tuple(
        identity(value)
        for value in object_list(model["training_input_ids"], "training_input_ids")
    )
    prediction = tuple(
        sorted(
            (identity(taxon), finite_number(value))
            for taxon, value in object_mapping(
                parent["vegetation_fraction"], "vegetation_fraction"
            ).items()
        )
    )
    source_sha256 = digest(cast(str, parent["baseline_model_sha256"]))
    return freeze_evaluation_prediction(
        EvaluationRow(
            fold_id=identity(parent["fold_id"]),
            record_id=identity(parent["record_id"]),
            model_id=BLOCK_BASELINE_METHOD,
            target="vegetation_cover",
            experiment="local_pollen_available",
            status="predicted",
            prediction=prediction,
            observation=None,
            observation_reference_id=None,
            observation_kind=None,
            observation_support=None,
            prediction_sha256=None,
            prediction_manifest_json=None,
            fitted_model_sha256=None,
            prediction_frozen_at=None,
            fit_input_ids=inputs,
            source_model=_authenticated_source_model(
                "admitted_reconstruction_training_mean", source_sha256
            ),
        )
    )


def adapt_authenticated_spatial_block_local_vegetation_rows(
    local_predictions: Path,
    *,
    expected_local_manifest_sha256: str,
    baseline_predictions: Path,
    expected_baseline_manifest_sha256: str,
    scope: EvaluationScope,
) -> tuple[EvaluationRow, ...]:
    """Freeze the spatial-block local vegetation model and pollen-free baseline.

    No vegetation outcome, threshold or review input is accepted. The returned
    rows remain interval-ineligible until a governed vegetation predictive
    uncertainty producer exists.
    """
    if not isinstance(scope, EvaluationScope):
        refuse("A typed frozen evaluation scope is required")
    local_product, local_manifest, local_folds, local_rows = (
        read_spatial_block_local_pollen_predictions(
            local_predictions,
            expected_manifest_sha256=expected_local_manifest_sha256,
        )
    )
    _, baseline_manifest, baseline_folds, baseline_rows, _ = (
        read_spatial_block_predictions(
            baseline_predictions,
            expected_manifest_sha256=expected_baseline_manifest_sha256,
        )
    )
    expected_folds = {fold.fold_id: fold.as_dict() for fold in scope.folds}
    if canonical_json(local_folds) != canonical_json(expected_folds) or canonical_json(
        baseline_folds
    ) != canonical_json(expected_folds):
        refuse("Spatial-block products and frozen scope folds differ")
    local_scientific = object_mapping(
        local_manifest["scientific_payload"], "local_scientific_payload"
    )
    baseline_scientific = object_mapping(
        baseline_manifest["scientific_payload"], "baseline_scientific_payload"
    )
    if canonical_json(local_scientific["block_admissions"]) != canonical_json(
        baseline_scientific["block_admissions"]
    ):
        refuse("Spatial-block products use different training admissions")
    sites = {site.record_id: site for site in scope.sites}
    expected = {
        (fold.fold_id, record)
        for fold in scope.folds
        for record in fold.test_record_ids
    }
    local_failures = _failures(local_manifest, method=LOCAL_METHOD)
    baseline_failures = _failures(baseline_manifest, method=BLOCK_BASELINE_METHOD)
    local_terminals = {
        (fold, record)
        for fold, record, method in {*local_rows, *local_failures}
        if method == LOCAL_METHOD
    }
    baseline_terminals = {
        (fold, record)
        for fold, record, method in {*baseline_rows, *baseline_failures}
        if method == BLOCK_BASELINE_METHOD
    }
    if local_terminals != expected or baseline_terminals != expected:
        refuse("Spatial-block products do not cover the same complete target universe")
    result: list[EvaluationRow] = []
    for fold_id, record_id in sorted(expected):
        site = sites.get(record_id)
        if site is None:
            refuse("Spatial-block product names a target outside the frozen scope")
        local_key = fold_id, record_id, LOCAL_METHOD
        baseline_key = fold_id, record_id, BLOCK_BASELINE_METHOD
        local = local_rows.get(local_key)
        baseline = baseline_rows.get(baseline_key)
        if local is not None and (
            local.get("group_id") != site.group_id
            or local.get("bin_id") != site.bin_id
            or set(object_mapping(local["vegetation_fraction"], "vegetation"))
            != set(scope.taxa)
        ):
            refuse("Local product target ownership, bin or taxa differ from scope")
        if baseline is not None and (
            baseline.get("group_id") != site.group_id
            or baseline.get("bin_id") != site.bin_id
            or set(object_mapping(baseline["vegetation_fraction"], "vegetation"))
            != set(scope.taxa)
        ):
            refuse("Baseline target ownership, bin or taxa differ from scope")
        if (
            local is not None
            and baseline is not None
            and (
                local.get("target_geometry_sha256")
                != baseline.get("target_geometry_sha256")
                or local.get("training_admission_sha256")
                != manifest_sha256(baseline.get("training_admission"))
                or canonical_json(local.get("outer_fold"))
                != canonical_json(baseline.get("outer_fold"))
            )
        ):
            refuse("Local and baseline product admission or geometry differs")
        result.append(
            _local_row(
                local,
                product_manifest_sha256=local_product.manifest_sha256,
            )
            if local is not None
            else _failed_row(
                fold_id=fold_id,
                record_id=record_id,
                model_id=LOCAL_METHOD,
                parent=local_failures[local_key],
            )
        )
        result.append(
            _baseline_row(baseline)
            if baseline is not None
            else _failed_row(
                fold_id=fold_id,
                record_id=record_id,
                model_id=BLOCK_BASELINE_METHOD,
                parent=baseline_failures[baseline_key],
            )
        )
    return tuple(result)
