"""Adapt paired grouped-outer products into frozen vegetation rows."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Literal, cast

from ...contracts import canonical_json, finite_number
from ...experiments.configuration import (
    FITTED_METHOD,
    FITTED_METHODS,
    TRAINING_MEAN_METHOD,
    identity,
    object_list,
    object_mapping,
)
from ...experiments.reading import read_withheld_predictions
from ...splits import assert_allowed_inputs
from ..intervals import freeze_authenticated_pollen_rows
from ..contracts import (
    EvaluationRow,
    EvaluationScope,
    _authenticated_source_model,
    digest,
    freeze_evaluation_prediction,
    refuse,
)


def _failure_inventory(
    manifest: dict[str, object],
    folds: dict[str, dict[str, object]],
) -> dict[tuple[str, str], dict[str, object]]:
    scientific = object_mapping(manifest["scientific_payload"], "scientific_payload")
    result: dict[tuple[str, str], dict[str, object]] = {}
    for value in object_list(scientific["failures"], "failures"):
        row = object_mapping(value, "failure")
        key = identity(row["fold_id"]), identity(row["method"])
        outer = folds.get(key[0])
        if (
            outer is None
            or key in result
            or object_list(row["record_ids"], "record_ids")
            != object_list(outer["test_record_ids"], "test_record_ids")
        ):
            refuse("Grouped failure ownership or identity differs")
        result[key] = row
    return result


def _failed_row(
    parent: dict[str, object],
    *,
    record_id: str,
    method: str,
    target: Literal["vegetation_cover", "pollen_composition"],
) -> EvaluationRow:
    status = identity(parent["status"])
    reason = identity(parent["reason_code"])
    if status not in {"refused", "not_run"} or (status == "not_run") != (
        reason == "experiment_interrupted"
    ):
        refuse("Grouped failure has an unsupported terminal status")
    return EvaluationRow(
        fold_id=identity(parent["fold_id"]),
        record_id=record_id,
        model_id=method,
        target=target,
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
        interval=None,
        reason=f"parent_{status}:{reason}",
        observed_pollen=None,
        source_model=None,
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
            refuse("Grouped parent external input is absent from the frozen scope")
        if key.startswith("experiment-fit:"):
            role = "training_derived_product"
            source_sha256 = key.removeprefix("experiment-fit:")
        elif key.startswith("experiment-support:"):
            role = "fixed_parameter"
            source_sha256 = key.removeprefix("experiment-support:")
        else:
            refuse("Grouped parent uses an unsupported external input identity")
        if item.role != role or item.source_manifest_sha256 != digest(source_sha256):
            refuse("Grouped parent external role or digest differs from frozen scope")
    try:
        fold = next(value for value in scope.folds if value.fold_id == fold_id)
    except StopIteration:
        refuse("Grouped parent fold is absent from the frozen scope")
    closure = assert_allowed_inputs(
        fold,
        inputs,
        scope_graph,
        admitted_external_ids=tuple(catalogue),
    )
    if (
        set(external) != set(closure) & set(catalogue)
        or set(closure) != set(product_graph)
        or any(
            set(scope_graph.get(key, ())) != set(product_graph[key]) for key in closure
        )
    ):
        refuse("Grouped parent lineage differs from the frozen scope")
    return inputs


def _prediction(
    parent: dict[str, object], *, field: str
) -> tuple[tuple[str, float], ...]:
    return tuple(
        sorted(
            (identity(taxon), finite_number(value))
            for taxon, value in object_mapping(parent[field], field).items()
        )
    )


def _point_row(
    parent: dict[str, object],
    *,
    method: str,
    target: Literal["vegetation_cover", "pollen_composition"],
    model_input_ids: tuple[str, ...],
) -> EvaluationRow:
    fitted = method == FITTED_METHOD
    source_sha256 = digest(
        cast(
            str,
            parent["model_sha256"] if fitted else parent["baseline_model_sha256"],
        )
    )
    row = EvaluationRow(
        fold_id=identity(parent["fold_id"]),
        record_id=identity(parent["record_id"]),
        model_id=method,
        target=target,
        experiment="all_target_pollen_withheld",
        status="predicted",
        prediction=_prediction(
            parent,
            field=(
                "vegetation_fraction"
                if target == "vegetation_cover"
                else "pollen_fraction"
            ),
        ),
        observation=None,
        observation_reference_id=None,
        observation_kind=None,
        observation_support=None,
        prediction_sha256=None,
        prediction_manifest_json=None,
        fitted_model_sha256=source_sha256 if fitted else None,
        prediction_frozen_at=None,
        fit_input_ids=model_input_ids,
        interval=None,
        reason=None,
        observed_pollen=None,
        source_model=None,
    )
    if target == "pollen_composition":
        return row
    source_kind = (
        "fitted_spatial" if fitted else "admitted_reconstruction_training_mean"
    )
    return freeze_evaluation_prediction(
        replace(
            row,
            source_model=_authenticated_source_model(source_kind, source_sha256),
        )
    )


def _adapt_authenticated_grouped_withheld_rows(
    predictions: Path,
    *,
    expected_manifest_sha256: str,
    scope: EvaluationScope,
    target: Literal["vegetation_cover", "pollen_composition"],
) -> tuple[EvaluationRow, ...]:
    """Authenticate the paired grouped-outer point ledger without outcomes."""
    if not isinstance(scope, EvaluationScope):
        refuse("A typed frozen evaluation scope is required")
    _, manifest, folds, parents, methods = read_withheld_predictions(
        predictions, expected_manifest_sha256=expected_manifest_sha256
    )
    expected_folds = {fold.fold_id: fold.as_dict() for fold in scope.folds}
    if canonical_json(folds) != canonical_json(expected_folds):
        refuse("Grouped product and frozen scope folds differ")
    if methods != FITTED_METHODS:
        refuse("Grouped product method universe differs")
    expected = {
        (fold.fold_id, method) for fold in scope.folds for method in FITTED_METHODS
    }
    failures = _failure_inventory(manifest, folds)
    if set(parents) | set(failures) != expected or set(parents) & set(failures):
        refuse("Grouped product does not cover the complete fold/method universe")
    sites = {site.record_id: site for site in scope.sites}
    for fold_id in sorted(folds):
        fitted = parents.get((fold_id, FITTED_METHOD))
        baseline = parents.get((fold_id, TRAINING_MEAN_METHOD))
        if (
            fitted is not None
            and baseline is not None
            and any(
                canonical_json(fitted.get(field)) != canonical_json(baseline.get(field))
                for field in (
                    "outer_fold",
                    "support",
                    "target_geometry_sha256",
                    "forward_preparation",
                )
            )
        ):
            refuse("Paired grouped methods use different target support")
    result: list[EvaluationRow] = []
    for fold_id, method in sorted(expected):
        outer = folds[fold_id]
        record_ids = object_list(outer["test_record_ids"], "test_record_ids")
        if len(record_ids) != 1:
            refuse("Grouped evaluation requires one exact held-out record per fold")
        record_id = identity(record_ids[0])
        site = sites.get(record_id)
        if site is None:
            refuse("Grouped product target is absent from the frozen scope")
        parent = parents.get((fold_id, method))
        if parent is None:
            result.append(
                _failed_row(
                    failures[(fold_id, method)],
                    record_id=record_id,
                    method=method,
                    target=target,
                )
            )
            continue
        if (
            parent.get("fold_id") != fold_id
            or parent.get("method") != method
            or parent.get("record_id") != record_id
            or parent.get("group_id") != site.group_id
            or parent.get("bin_id") != site.bin_id
            or canonical_json(parent.get("outer_fold")) != canonical_json(outer)
            or set(
                object_mapping(
                    parent[
                        "vegetation_fraction"
                        if target == "vegetation_cover"
                        else "pollen_fraction"
                    ],
                    target,
                )
            )
            != set(scope.taxa)
        ):
            refuse("Grouped target ownership, fold, bin or taxa differ from scope")
        support = object_mapping(parent["support"], "support")
        if (
            site.support is None
            or parent.get("target_geometry_sha256") != site.support.footprint_sha256
            or finite_number(support["local_support_radius_m"]) != site.support.radius_m
        ):
            refuse("Grouped target geometry or radius differs from frozen support")
        inputs = _authenticate_scope_lineage(
            parent, method=method, scope=scope, fold_id=fold_id
        )
        result.append(
            _point_row(
                parent,
                method=method,
                target=target,
                model_input_ids=inputs,
            )
        )
    return tuple(result)


def adapt_authenticated_grouped_withheld_vegetation_rows(
    predictions: Path,
    *,
    expected_manifest_sha256: str,
    scope: EvaluationScope,
) -> tuple[EvaluationRow, ...]:
    """Freeze the complete paired grouped-outer vegetation ledger without outcomes."""
    return _adapt_authenticated_grouped_withheld_rows(
        predictions,
        expected_manifest_sha256=expected_manifest_sha256,
        scope=scope,
        target="vegetation_cover",
    )


def adapt_authenticated_grouped_withheld_pollen_rows(
    predictions: Path,
    *,
    expected_prediction_manifest_sha256: str,
    uncertainty: Path,
    expected_uncertainty_manifest_sha256: str,
    scope: EvaluationScope,
) -> tuple[EvaluationRow, ...]:
    """Freeze the complete grouped pollen ledger with conditional intervals."""
    rows = _adapt_authenticated_grouped_withheld_rows(
        predictions,
        expected_manifest_sha256=expected_prediction_manifest_sha256,
        scope=scope,
        target="pollen_composition",
    )
    return freeze_authenticated_pollen_rows(
        rows,
        predictions=predictions,
        expected_prediction_manifest_sha256=expected_prediction_manifest_sha256,
        uncertainty=uncertainty,
        expected_uncertainty_manifest_sha256=expected_uncertainty_manifest_sha256,
    )
