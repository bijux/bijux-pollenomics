"""Adapt authenticated spatial-block products into outcome-free evaluation rows."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from ...contracts import canonical_json, finite_number
from ...experiments.configuration import (
    BLOCK_BASELINE_METHOD,
    BLOCK_METHODS,
    FITTED_METHOD,
    identity,
    object_list,
    object_mapping,
)
from ...experiments.reading.products import read_spatial_block_predictions
from ...splits import assert_allowed_inputs
from ..contracts import (
    EvaluationRow,
    EvaluationScope,
    _authenticated_source_model,
    digest,
    freeze_evaluation_prediction,
    refuse,
)


def _failures(
    manifest: dict[str, object],
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
        result[key] = row
    return result


def _failed_row(parent: dict[str, object]) -> EvaluationRow:
    status = identity(parent["status"])
    reason = identity(parent["reason_code"])
    return EvaluationRow(
        fold_id=identity(parent["fold_id"]),
        record_id=identity(parent["record_id"]),
        model_id=identity(parent["method"]),
        target="vegetation_cover",
        experiment="all_target_pollen_withheld",
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


def _prediction(row: dict[str, object]) -> tuple[tuple[str, float], ...]:
    return tuple(
        sorted(
            (identity(taxon), finite_number(value))
            for taxon, value in object_mapping(
                row["vegetation_fraction"], "vegetation_fraction"
            ).items()
        )
    )


def _lineage(
    parent: dict[str, object], *, method: str
) -> tuple[tuple[str, ...], dict[str, tuple[str, ...]], tuple[str, ...]]:
    source = (
        parent
        if method == FITTED_METHOD
        else object_mapping(parent["baseline_model_manifest"], "baseline_model")
    )
    inputs = tuple(
        identity(value)
        for value in object_list(source["training_input_ids"], "training_input_ids")
    )
    graph_field = (
        "training_dependency_graph" if method == FITTED_METHOD else "input_lineage"
    )
    graph = {
        identity(key): tuple(
            identity(value) for value in object_list(parents, "lineage_parents")
        )
        for key, parents in object_mapping(source[graph_field], graph_field).items()
    }
    external = tuple(
        identity(value)
        for value in object_list(
            source["training_external_ids"], "training_external_ids"
        )
    )
    return inputs, graph, external


def _authenticate_scope_lineage(
    parent: dict[str, object],
    *,
    method: str,
    scope: EvaluationScope,
    fold_id: str,
) -> tuple[str, ...]:
    inputs, product_graph, external = _lineage(parent, method=method)
    scope_graph = dict(scope.dependency_graph)
    catalogue = {item.input_id: item for item in scope.external_inputs}
    for key in external:
        item = catalogue.get(key)
        if item is None:
            refuse("Block parent external input is absent from the frozen scope")
        if key.startswith("experiment-fit:"):
            role = "training_derived_product"
            sha256 = key.removeprefix("experiment-fit:")
        elif key.startswith("experiment-support:"):
            role = "fixed_parameter"
            sha256 = key.removeprefix("experiment-support:")
        else:
            refuse("Block parent uses an unsupported external input identity")
        if item.role != role or item.source_manifest_sha256 != digest(sha256):
            refuse("Block parent external role or digest differs from the frozen scope")
    fold = next(value for value in scope.folds if value.fold_id == fold_id)
    closure = assert_allowed_inputs(
        fold,
        inputs,
        scope_graph,
        admitted_external_ids=tuple(catalogue),
    )
    if set(closure) != set(product_graph) or any(
        scope_graph.get(key) != product_graph[key] for key in closure
    ):
        refuse("Block parent lineage differs from the frozen scope")
    return inputs


def _fitted_row(
    parent: dict[str, object], *, fit_input_ids: tuple[str, ...]
) -> EvaluationRow:
    source_sha256 = digest(cast(str, parent["model_sha256"]))
    return freeze_evaluation_prediction(
        EvaluationRow(
            fold_id=identity(parent["fold_id"]),
            record_id=identity(parent["record_id"]),
            model_id=FITTED_METHOD,
            target="vegetation_cover",
            experiment="all_target_pollen_withheld",
            status="predicted",
            prediction=_prediction(parent),
            observation=None,
            observation_reference_id=None,
            observation_kind=None,
            observation_support=None,
            prediction_sha256=None,
            prediction_manifest_json=None,
            fitted_model_sha256=source_sha256,
            prediction_frozen_at=None,
            fit_input_ids=fit_input_ids,
            source_model=_authenticated_source_model("fitted_spatial", source_sha256),
        )
    )


def _baseline_row(
    parent: dict[str, object], *, fit_input_ids: tuple[str, ...]
) -> EvaluationRow:
    source_sha256 = digest(cast(str, parent["baseline_model_sha256"]))
    return freeze_evaluation_prediction(
        EvaluationRow(
            fold_id=identity(parent["fold_id"]),
            record_id=identity(parent["record_id"]),
            model_id=BLOCK_BASELINE_METHOD,
            target="vegetation_cover",
            experiment="all_target_pollen_withheld",
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
            fit_input_ids=fit_input_ids,
            source_model=_authenticated_source_model(
                "admitted_reconstruction_training_mean", source_sha256
            ),
        )
    )


def adapt_authenticated_spatial_block_withheld_vegetation_rows(
    predictions: Path,
    *,
    expected_manifest_sha256: str,
    scope: EvaluationScope,
) -> tuple[EvaluationRow, ...]:
    """Freeze the complete paired block vegetation row universe without outcomes."""
    if not isinstance(scope, EvaluationScope):
        refuse("A typed frozen evaluation scope is required")
    _, manifest, folds, parents, methods = read_spatial_block_predictions(
        predictions, expected_manifest_sha256=expected_manifest_sha256
    )
    expected_folds = {fold.fold_id: fold.as_dict() for fold in scope.folds}
    if canonical_json(folds) != canonical_json(expected_folds):
        refuse("Spatial-block product and frozen scope folds differ")
    if methods != BLOCK_METHODS:
        refuse("Spatial-block product method universe differs")
    sites = {site.record_id: site for site in scope.sites}
    expected = {
        (fold.fold_id, record, method)
        for fold in scope.folds
        for record in fold.test_record_ids
        for method in BLOCK_METHODS
    }
    failures = _failures(manifest)
    if set(parents) | set(failures) != expected or set(parents) & set(failures):
        refuse("Spatial-block product does not cover the complete target universe")
    for fold_id, record_id in sorted({key[:2] for key in expected}):
        fitted = parents.get((fold_id, record_id, FITTED_METHOD))
        baseline = parents.get((fold_id, record_id, BLOCK_BASELINE_METHOD))
        if (
            fitted is not None
            and baseline is not None
            and any(
                canonical_json(fitted.get(field)) != canonical_json(baseline.get(field))
                for field in (
                    "outer_fold",
                    "training_admission",
                    "support",
                    "target_geometry_sha256",
                )
            )
        ):
            refuse("Paired block model and baseline use different support or admission")
    result: list[EvaluationRow] = []
    for key in sorted(expected):
        fold_id, record_id, method = key
        site = sites.get(record_id)
        if site is None:
            refuse("Spatial-block product names a target outside the frozen scope")
        parent = parents.get(key)
        if parent is None:
            result.append(_failed_row(failures[key]))
            continue
        if (
            parent.get("group_id") != site.group_id
            or parent.get("bin_id") != site.bin_id
            or canonical_json(parent.get("outer_fold"))
            != canonical_json(expected_folds[fold_id])
            or set(object_mapping(parent["vegetation_fraction"], "vegetation"))
            != set(scope.taxa)
        ):
            refuse("Block target ownership, fold, bin or taxa differ from scope")
        support = object_mapping(parent["support"], "support")
        if (
            site.support is None
            or parent.get("target_geometry_sha256") != site.support.footprint_sha256
            or finite_number(support["local_support_radius_m"]) != site.support.radius_m
        ):
            refuse("Block target geometry or radius differs from the frozen support")
        inputs = _authenticate_scope_lineage(
            parent, method=method, scope=scope, fold_id=fold_id
        )
        result.append(
            _fitted_row(parent, fit_input_ids=inputs)
            if method == FITTED_METHOD
            else _baseline_row(parent, fit_input_ids=inputs)
        )
    return tuple(result)
