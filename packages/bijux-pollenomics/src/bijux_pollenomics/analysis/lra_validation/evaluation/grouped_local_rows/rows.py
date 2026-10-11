"""Join grouped local-pollen vegetation with a pollen-free training mean."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from ...channels import ObservedPollenAdmission, PollenChannel, assert_channel_inputs
from ...contracts import canonical_json, finite_number, manifest_sha256
from ...experiments.configuration import (
    FITTED_METHODS,
    LOCAL_METHOD,
    TRAINING_MEAN_METHOD,
    identity,
    object_list,
    object_mapping,
)
from ...experiments.reading import (
    read_local_pollen_predictions,
    read_withheld_predictions,
)
from ...splits import assert_allowed_inputs
from ..contracts import (
    EvaluationRow,
    EvaluationScope,
    _authenticated_source_model,
    digest,
    freeze_evaluation_prediction,
    refuse,
)


def _observed_pollen(row: dict[str, object]) -> ObservedPollenAdmission:
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
    channel = object_mapping(row["channel_admission"], "channel_admission")
    return manifest_sha256(
        {
            "schema_version": "lra-grouped-local-evaluation-source.v1",
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
            "channel_admission_sha256": manifest_sha256(channel),
            "request_sha256": row["request_sha256"],
            "numerical_product_sha256": manifest_sha256(row["numerical_product"]),
            "engine_build_sha256": manifest_sha256(row["engine_build"]),
            "target_geometry_sha256": row["target_geometry_sha256"],
            "support_profile": row["support_profile"],
            "local_support_radius_m": row["local_support_radius_m"],
            "preparation_profile": row["preparation_profile"],
            "forward_method_profile": row["forward_method_profile"],
        }
    )


def _local_failures(manifest: dict[str, object]) -> dict[str, dict[str, object]]:
    scientific = object_mapping(manifest["scientific_payload"], "scientific_payload")
    result: dict[str, dict[str, object]] = {}
    for value in object_list(scientific["failures"], "failures"):
        row = object_mapping(value, "failure")
        fold_id = identity(row["fold_id"])
        if fold_id in result:
            refuse("Duplicate grouped local terminal")
        result[fold_id] = row
    return result


def _baseline_failures(
    manifest: dict[str, object],
) -> dict[tuple[str, str], dict[str, object]]:
    scientific = object_mapping(manifest["scientific_payload"], "scientific_payload")
    result: dict[tuple[str, str], dict[str, object]] = {}
    for value in object_list(scientific["failures"], "failures"):
        row = object_mapping(value, "failure")
        if row.get("method") != TRAINING_MEAN_METHOD:
            continue
        key = identity(row["fold_id"]), identity(row["method"])
        if key in result:
            refuse("Duplicate grouped baseline terminal")
        result[key] = row
    return result


def _failed_row(
    *, fold_id: str, record_id: str, model_id: str, parent: dict[str, object]
) -> EvaluationRow:
    status = identity(parent["status"])
    reason = identity(parent["reason_code"])
    if status not in {"refused", "not_run"} or (status == "not_run") != (
        reason == "experiment_interrupted"
    ):
        refuse("Grouped local parent has an invalid terminal status")
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
        interval=None,
        reason=f"parent_{status}:{reason}",
        observed_pollen=None,
        source_model=None,
    )


def _prediction(row: dict[str, object]) -> tuple[tuple[str, float], ...]:
    return tuple(
        sorted(
            (identity(taxon), finite_number(value))
            for taxon, value in object_mapping(
                row["vegetation_fraction"], "vegetation_fraction"
            ).items()
        )
    )


def _local_inputs(
    row: dict[str, object], *, scope: EvaluationScope, fold_id: str
) -> tuple[tuple[str, ...], ObservedPollenAdmission]:
    evidence = object_mapping(row["channel_admission"], "channel_admission")
    inputs = tuple(
        identity(value)
        for value in object_list(evidence["pollen_input_ids"], "pollen_input_ids")
    )
    product_graph = {
        identity(key): tuple(
            identity(value) for value in object_list(parents, "lineage_parents")
        )
        for key, parents in object_mapping(
            evidence["quantitative_lineage"], "quantitative_lineage"
        ).items()
    }
    scope_graph = dict(scope.dependency_graph)
    fold = next(value for value in scope.folds if value.fold_id == fold_id)
    observed = _observed_pollen(row)
    closure = assert_channel_inputs(
        fold,
        inputs,
        scope_graph,
        channels=scope.observation_channels,
        observed_pollen=observed,
        admitted_external_ids=tuple(item.input_id for item in scope.external_inputs),
    )
    scope_sources = {
        channel.input_id: (
            owner.record_id,
            owner.group_id,
            channel.source_sha256,
        )
        for owner in scope.observation_channels
        for channel in owner.pollen_channels
    }
    consumed = {
        (
            identity(source["record_id"]),
            identity(source["group_id"]),
            identity(source["input_id"]),
            digest(cast(str, source["source_sha256"])),
        )
        for value in object_list(
            evidence["consumed_pollen_sources"], "consumed_pollen_sources"
        )
        if (source := object_mapping(value, "consumed_pollen_source"))
    }
    expected_sources = {
        (record, group, key, source_sha256)
        for key in closure
        if key in scope_sources
        for record, group, source_sha256 in (scope_sources[key],)
    }
    if (
        object_list(evidence["pollen_channel_closure"], "pollen_channel_closure")
        != list(closure)
        or set(closure) != set(product_graph)
        or consumed != expected_sources
        or any(
            set(scope_graph.get(key, ())) != set(product_graph[key]) for key in closure
        )
    ):
        refuse("Grouped local pollen lineage differs from the frozen scope")
    return inputs, observed


def _baseline_inputs(
    row: dict[str, object], *, scope: EvaluationScope, fold_id: str
) -> tuple[str, ...]:
    model = object_mapping(row["baseline_model_manifest"], "baseline_model")
    inputs = tuple(
        identity(value)
        for value in object_list(model["training_input_ids"], "training_input_ids")
    )
    product_graph = {
        identity(key): tuple(
            identity(value) for value in object_list(parents, "lineage_parents")
        )
        for key, parents in object_mapping(
            model["input_lineage"], "input_lineage"
        ).items()
    }
    external = tuple(
        identity(value)
        for value in object_list(
            model["training_external_ids"], "training_external_ids"
        )
    )
    scope_graph = dict(scope.dependency_graph)
    catalogue = {item.input_id: item for item in scope.external_inputs}
    for key in external:
        item = catalogue.get(key)
        if item is None:
            refuse("Grouped baseline external input is absent from frozen scope")
        if key.startswith("experiment-fit:"):
            role = "training_derived_product"
            source_sha256 = key.removeprefix("experiment-fit:")
        elif key.startswith("experiment-support:"):
            role = "fixed_parameter"
            source_sha256 = key.removeprefix("experiment-support:")
        else:
            refuse("Grouped baseline has an unsupported external input")
        if item.role != role or item.source_manifest_sha256 != digest(source_sha256):
            refuse("Grouped baseline external role or digest differs from scope")
    fold = next(value for value in scope.folds if value.fold_id == fold_id)
    closure = assert_allowed_inputs(
        fold,
        inputs,
        scope_graph,
        admitted_external_ids=tuple(catalogue),
    )
    if set(external) != set(closure) & set(catalogue):
        refuse("Grouped baseline external declarations differ from its closure")
    if set(closure) != set(product_graph) or any(
        set(scope_graph.get(key, ())) != set(product_graph[key]) for key in closure
    ):
        refuse("Grouped baseline lineage differs from the frozen scope")
    return inputs


def _local_row(
    parent: dict[str, object],
    *,
    product_manifest_sha256: str,
    inputs: tuple[str, ...],
    observed: ObservedPollenAdmission,
) -> EvaluationRow:
    return freeze_evaluation_prediction(
        EvaluationRow(
            fold_id=identity(parent["fold_id"]),
            record_id=identity(parent["record_id"]),
            model_id=LOCAL_METHOD,
            target="vegetation_cover",
            experiment="local_pollen_available",
            status="predicted",
            prediction=_prediction(parent),
            observation=None,
            observation_reference_id=None,
            observation_kind=None,
            observation_support=None,
            prediction_sha256=None,
            prediction_manifest_json=None,
            fitted_model_sha256=None,
            prediction_frozen_at=None,
            fit_input_ids=inputs,
            interval=None,
            reason=None,
            observed_pollen=observed,
            source_model=_authenticated_source_model(
                "local_pollen_assimilation",
                _local_source_sha256(
                    parent, product_manifest_sha256=product_manifest_sha256
                ),
            ),
        )
    )


def _baseline_row(
    parent: dict[str, object], *, inputs: tuple[str, ...]
) -> EvaluationRow:
    source_sha256 = digest(cast(str, parent["baseline_model_sha256"]))
    return freeze_evaluation_prediction(
        EvaluationRow(
            fold_id=identity(parent["fold_id"]),
            record_id=identity(parent["record_id"]),
            model_id=TRAINING_MEAN_METHOD,
            target="vegetation_cover",
            experiment="local_pollen_available",
            status="predicted",
            prediction=_prediction(parent),
            observation=None,
            observation_reference_id=None,
            observation_kind=None,
            observation_support=None,
            prediction_sha256=None,
            prediction_manifest_json=None,
            fitted_model_sha256=None,
            prediction_frozen_at=None,
            fit_input_ids=inputs,
            interval=None,
            reason=None,
            observed_pollen=None,
            source_model=_authenticated_source_model(
                "admitted_reconstruction_training_mean", source_sha256
            ),
        )
    )


def adapt_authenticated_grouped_local_vegetation_rows(
    local_predictions: Path,
    *,
    expected_local_manifest_sha256: str,
    baseline_predictions: Path,
    expected_baseline_manifest_sha256: str,
    scope: EvaluationScope,
) -> tuple[EvaluationRow, ...]:
    """Freeze complete local-LOVE/training-mean vegetation pairs without outcomes."""
    if not isinstance(scope, EvaluationScope):
        refuse("A typed frozen evaluation scope is required")
    local_product, local_manifest, local_folds, local_rows = (
        read_local_pollen_predictions(
            local_predictions,
            expected_manifest_sha256=expected_local_manifest_sha256,
        )
    )
    _, baseline_manifest, baseline_folds, baseline_rows, baseline_methods = (
        read_withheld_predictions(
            baseline_predictions,
            expected_manifest_sha256=expected_baseline_manifest_sha256,
        )
    )
    expected_folds = {fold.fold_id: fold.as_dict() for fold in scope.folds}
    if canonical_json(local_folds) != canonical_json(expected_folds) or canonical_json(
        baseline_folds
    ) != canonical_json(expected_folds):
        refuse("Grouped local, baseline and scope folds differ")
    if baseline_methods != FITTED_METHODS:
        refuse("Grouped comparator requires the exact paired method universe")
    expected = set(expected_folds)
    local_failures = _local_failures(local_manifest)
    baseline_failures = _baseline_failures(baseline_manifest)
    baseline_parents = {
        fold_id: row
        for (fold_id, method), row in baseline_rows.items()
        if method == TRAINING_MEAN_METHOD
    }
    if (
        set(local_rows) | set(local_failures) != expected
        or set(local_rows) & set(local_failures)
        or set(baseline_parents) | {fold for fold, _ in baseline_failures} != expected
        or set(baseline_parents) & {fold for fold, _ in baseline_failures}
    ):
        refuse(
            "Grouped local and baseline products need complete independent terminals"
        )
    sites = {site.record_id: site for site in scope.sites}
    result: list[EvaluationRow] = []
    for fold_id in sorted(expected):
        outer = expected_folds[fold_id]
        records = object_list(outer["test_record_ids"], "test_record_ids")
        if len(records) != 1:
            refuse("Grouped local evaluation requires singleton held-out folds")
        record_id = identity(records[0])
        site = sites.get(record_id)
        if site is None:
            refuse("Grouped local target is absent from the frozen scope")
        local = local_rows.get(fold_id)
        baseline = baseline_parents.get(fold_id)
        for label, row in (("local", local), ("baseline", baseline)):
            if row is None:
                continue
            if (
                row.get("method")
                != (LOCAL_METHOD if label == "local" else TRAINING_MEAN_METHOD)
                or row.get("fold_id") != fold_id
                or row.get("record_id") != record_id
                or row.get("group_id") != site.group_id
                or row.get("bin_id") != site.bin_id
                or canonical_json(row.get("outer_fold")) != canonical_json(outer)
                or set(
                    object_mapping(row["vegetation_fraction"], "vegetation_fraction")
                )
                != set(scope.taxa)
            ):
                refuse(f"Grouped {label} target ownership, fold, bin or taxa differ")
            if label == "local":
                radius = finite_number(row["local_support_radius_m"])
            else:
                support = object_mapping(row["support"], "support")
                radius = finite_number(support["local_support_radius_m"])
            if (
                site.support is None
                or row.get("target_geometry_sha256") != site.support.footprint_sha256
                or radius != site.support.radius_m
            ):
                refuse(f"Grouped {label} target support differs from scope")
        if (
            local is not None
            and baseline is not None
            and (
                local.get("target_geometry_sha256")
                != baseline.get("target_geometry_sha256")
                or local.get("bin_id") != baseline.get("bin_id")
                or local.get("support_profile")
                != object_mapping(baseline["support"], "support").get("support_profile")
                or canonical_json(local.get("outer_fold"))
                != canonical_json(baseline.get("outer_fold"))
            )
        ):
            refuse("Grouped local and baseline target support differs")
        if local is None:
            result.append(
                _failed_row(
                    fold_id=fold_id,
                    record_id=record_id,
                    model_id=LOCAL_METHOD,
                    parent=local_failures[fold_id],
                )
            )
        else:
            local_inputs, observed = _local_inputs(local, scope=scope, fold_id=fold_id)
            result.append(
                _local_row(
                    local,
                    product_manifest_sha256=local_product.manifest_sha256,
                    inputs=local_inputs,
                    observed=observed,
                )
            )
        baseline_key = fold_id, TRAINING_MEAN_METHOD
        if baseline is None:
            result.append(
                _failed_row(
                    fold_id=fold_id,
                    record_id=record_id,
                    model_id=TRAINING_MEAN_METHOD,
                    parent=baseline_failures[baseline_key],
                )
            )
        else:
            result.append(
                _baseline_row(
                    baseline,
                    inputs=_baseline_inputs(baseline, scope=scope, fold_id=fold_id),
                )
            )
    return tuple(result)
