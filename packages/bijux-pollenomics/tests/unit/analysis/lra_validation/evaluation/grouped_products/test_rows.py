"""Grouped vegetation rows retain paired source identity and full accounting."""

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import (
    Fold,
    ValidationRefusal,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.contracts import (
    EvaluationScope,
    EvaluationSite,
    ExternalInput,
    Support,
    validate_frozen_prediction,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.grouped_products import (
    rows as grouped_rows,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    FITTED_METHOD,
    FITTED_METHODS,
    TRAINING_MEAN_METHOD,
)


def _scope() -> EvaluationScope:
    fold = Fold("fold:p3", ("p1", "p2"), ("p3",), ("g1", "g2"), ("g3",))
    fit = "experiment-fit:" + "3" * 64
    support = "experiment-support:" + "4" * 64
    target = Support(
        60.1,
        18.2,
        1000,
        25,
        0,
        100,
        "5" * 64,
        "EPSG:4326",
        "BP",
        "bounded-footprint-radius-v1",
        "typed-bp-interval-v1",
    )
    return EvaluationScope(
        "scope",
        (
            EvaluationSite("p1", "s1", "g1", "a", "bin", (), "v1", "o1", None),
            EvaluationSite("p2", "s2", "g2", "a", "bin", (), "v2", "o2", None),
            EvaluationSite("p3", "s3", "g3", "b", "bin", (), "v3", "o3", target),
        ),
        (fold,),
        (
            ("p1", ()),
            ("p2", ()),
            ("p3", ()),
            (fit, ("p1", "p2")),
            (support, ()),
        ),
        ("Alnus", "Betula"),
        external_inputs=(
            ExternalInput(fit, "training_derived_product", "3" * 64, None),
            ExternalInput(support, "fixed_parameter", "4" * 64, None),
        ),
    )


def _parent(method: str) -> dict[str, object]:
    fold = _scope().folds[0]
    fit = "experiment-fit:" + "3" * 64
    support_id = "experiment-support:" + "4" * 64
    inputs = ["p1", "p2", fit, support_id]
    graph = {"p1": [], "p2": [], fit: ["p1", "p2"], support_id: []}
    common: dict[str, object] = {
        "profile": "synthetic-withheld-site-fitted-spatial-v1",
        "method": method,
        "fold_id": fold.fold_id,
        "record_id": "p3",
        "group_id": "g3",
        "bin_id": "bin",
        "outer_fold": fold.as_dict(),
        "vegetation_fraction": {"Alnus": 0.6, "Betula": 0.4},
        "pollen_fraction": {"Alnus": 0.7, "Betula": 0.3},
        "target_geometry_sha256": "5" * 64,
        "support": {"local_support_radius_m": 1000},
        "forward_preparation": {
            "taxa": ["Alnus", "Betula"],
            "target_geometry_sha256": "5" * 64,
            "ring_bounds_m": [[0, 1000]],
        },
    }
    if method == FITTED_METHOD:
        return {
            **common,
            "model_sha256": "f" * 64,
            "training_input_ids": inputs,
            "training_external_ids": [fit, support_id],
            "training_dependency_graph": graph,
        }
    model = {
        "training_input_ids": inputs,
        "training_external_ids": [fit, support_id],
        "input_lineage": graph,
    }
    return {
        **common,
        "baseline_model_manifest": model,
        "baseline_model_sha256": manifest_sha256(model),
    }


def _install(
    monkeypatch: pytest.MonkeyPatch,
    *,
    parents: dict[tuple[str, str], dict[str, object]] | None = None,
    failures: list[dict[str, object]] | None = None,
    folds: dict[str, dict[str, object]] | None = None,
    methods: tuple[str, ...] = FITTED_METHODS,
) -> None:
    scope = _scope()
    fold = scope.folds[0]
    retained = (
        {(fold.fold_id, method): _parent(method) for method in FITTED_METHODS}
        if parents is None
        else parents
    )
    monkeypatch.setattr(
        grouped_rows,
        "read_withheld_predictions",
        lambda *args, **kwargs: (
            SimpleNamespace(manifest_sha256="a" * 64),
            {"scientific_payload": {"failures": failures or []}},
            {fold.fold_id: fold.as_dict()} if folds is None else folds,
            retained,
            methods,
        ),
    )


def test_adapter_freezes_exact_fitted_and_training_mean_vegetation_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install(monkeypatch)
    rows = grouped_rows.adapt_authenticated_grouped_withheld_vegetation_rows(
        tmp_path / "product", expected_manifest_sha256="a" * 64, scope=_scope()
    )
    by_method = {row.model_id: row for row in rows}
    fitted = by_method[FITTED_METHOD]
    baseline = by_method[TRAINING_MEAN_METHOD]
    assert fitted.source_model is not None
    assert fitted.source_model.kind == "fitted_spatial"
    assert fitted.fitted_model_sha256 == "f" * 64
    assert baseline.source_model is not None
    assert baseline.source_model.kind == "admitted_reconstruction_training_mean"
    assert baseline.fitted_model_sha256 is None
    assert all(
        row.status == "predicted"
        and row.prediction == (("Alnus", 0.6), ("Betula", 0.4))
        and row.observation is row.interval is row.observed_pollen is None
        and validate_frozen_prediction(row) == "pollenomics-evaluation-prediction.v2"
        for row in rows
    )


@pytest.mark.parametrize(
    "method,status,reason",
    [
        (FITTED_METHOD, "refused", "fit_refused"),
        (TRAINING_MEAN_METHOD, "not_run", "experiment_interrupted"),
    ],
)
def test_parent_terminal_preserves_denominator_without_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    status: str,
    reason: str,
) -> None:
    scope = _scope()
    fold = scope.folds[0]
    other = next(value for value in FITTED_METHODS if value != method)
    failure = {
        "fold_id": fold.fold_id,
        "record_ids": ["p3"],
        "method": method,
        "status": status,
        "reason_code": reason,
    }
    _install(
        monkeypatch,
        parents={(fold.fold_id, other): _parent(other)},
        failures=[failure],
    )
    rows = grouped_rows.adapt_authenticated_grouped_withheld_vegetation_rows(
        tmp_path / "product", expected_manifest_sha256="a" * 64, scope=scope
    )
    by_method = {row.model_id: row for row in rows}
    failed = by_method[method]
    assert failed.status == "prediction_failed"
    assert failed.reason == f"parent_{status}:{reason}"
    assert failed.prediction is failed.source_model is None
    assert failed.prediction_sha256 is failed.prediction_manifest_json is None
    assert failed.fit_input_ids == ()
    assert by_method[other].status == "predicted"


def test_pollen_factory_delegates_complete_unfrozen_ledger_to_interval_authenticator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install(monkeypatch)
    captured: dict[str, object] = {}

    def freeze(rows: object, **kwargs: object) -> object:
        captured.update(rows=rows, kwargs=kwargs)
        return rows

    monkeypatch.setattr(grouped_rows, "freeze_authenticated_pollen_rows", freeze)
    result = grouped_rows.adapt_authenticated_grouped_withheld_pollen_rows(
        tmp_path / "product",
        expected_prediction_manifest_sha256="a" * 64,
        uncertainty=tmp_path / "uncertainty",
        expected_uncertainty_manifest_sha256="b" * 64,
        scope=_scope(),
    )
    assert captured["rows"] == result
    assert len(result) == 2
    assert all(
        row.target == "pollen_composition"
        and row.prediction == (("Alnus", 0.7), ("Betula", 0.3))
        and row.source_model is None
        and row.prediction_sha256 is None
        for row in result
    )
    assert {row.model_id for row in result} == set(FITTED_METHODS)
    assert captured["kwargs"] == {
        "predictions": tmp_path / "product",
        "expected_prediction_manifest_sha256": "a" * 64,
        "uncertainty": tmp_path / "uncertainty",
        "expected_uncertainty_manifest_sha256": "b" * 64,
    }


@pytest.mark.parametrize(
    "mutation",
    [
        "fold",
        "methods",
        "missing",
        "row_method",
        "group",
        "record",
        "bin",
        "taxa",
        "geometry",
        "radius",
        "pair_support",
        "model_digest",
    ],
)
def test_scope_product_or_denominator_contradictions_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    scope = _scope()
    fold = scope.folds[0]
    parents = {(fold.fold_id, method): _parent(method) for method in FITTED_METHODS}
    folds = None
    methods = FITTED_METHODS
    if mutation == "fold":
        folds = {fold.fold_id: {**fold.as_dict(), "train_record_ids": ["p1"]}}
    elif mutation == "methods":
        methods = (FITTED_METHOD,)
    elif mutation == "missing":
        parents.pop((fold.fold_id, TRAINING_MEAN_METHOD))
    else:
        changed = deepcopy(parents[(fold.fold_id, FITTED_METHOD)])
        if mutation == "row_method":
            changed["method"] = TRAINING_MEAN_METHOD
        elif mutation == "group":
            changed["group_id"] = "g2"
        elif mutation == "record":
            changed["record_id"] = "p2"
        elif mutation == "bin":
            changed["bin_id"] = "other"
        elif mutation == "taxa":
            changed["vegetation_fraction"] = {"Alnus": 1.0}
        elif mutation == "geometry":
            changed["target_geometry_sha256"] = "6" * 64
        elif mutation == "radius":
            changed["support"] = {"local_support_radius_m": 2000}
        elif mutation == "pair_support":
            changed["forward_preparation"] = {"taxa": ["Alnus", "Betula"]}
        else:
            changed["model_sha256"] = "invalid"
        parents[(fold.fold_id, FITTED_METHOD)] = changed
    _install(monkeypatch, parents=parents, folds=folds, methods=methods)
    with pytest.raises(ValidationRefusal):
        grouped_rows.adapt_authenticated_grouped_withheld_vegetation_rows(
            tmp_path / "product", expected_manifest_sha256="a" * 64, scope=scope
        )


@pytest.mark.parametrize(
    "mutation", ["graph", "external_digest", "external_role", "external_omitted"]
)
def test_scope_lineage_and_external_identity_must_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    scope = _scope()
    if mutation == "graph":
        graph = dict(scope.dependency_graph)
        graph["experiment-fit:" + "3" * 64] = ("p1",)
        scope = EvaluationScope(
            scope.scope_id,
            scope.sites,
            scope.folds,
            tuple(graph.items()),
            scope.taxa,
            scope.external_inputs,
        )
    elif mutation != "external_omitted":
        external = list(scope.external_inputs)
        fit = external[0]
        external[0] = ExternalInput(
            fit.input_id,
            "fixed_parameter" if mutation == "external_role" else fit.role,
            "9" * 64 if mutation == "external_digest" else fit.source_manifest_sha256,
            fit.support,
        )
        scope = EvaluationScope(
            scope.scope_id,
            scope.sites,
            scope.folds,
            scope.dependency_graph,
            scope.taxa,
            tuple(external),
        )
    parents = None
    if mutation == "external_omitted":
        fold = scope.folds[0]
        parents = {(fold.fold_id, method): _parent(method) for method in FITTED_METHODS}
        fitted = deepcopy(parents[(fold.fold_id, FITTED_METHOD)])
        fitted["training_external_ids"] = []
        parents[(fold.fold_id, FITTED_METHOD)] = fitted
    _install(monkeypatch, parents=parents)
    with pytest.raises(ValidationRefusal):
        grouped_rows.adapt_authenticated_grouped_withheld_vegetation_rows(
            tmp_path / "product", expected_manifest_sha256="a" * 64, scope=scope
        )


def test_adapter_requires_typed_scope_before_reader_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    touched = False

    def opened(*args: object, **kwargs: object) -> object:
        nonlocal touched
        touched = True
        raise AssertionError("reader must not open")

    monkeypatch.setattr(grouped_rows, "read_withheld_predictions", opened)
    with pytest.raises(ValidationRefusal):
        grouped_rows.adapt_authenticated_grouped_withheld_vegetation_rows(
            tmp_path / "product",
            expected_manifest_sha256="a" * 64,
            scope=object(),  # type: ignore[arg-type]
        )
    assert touched is False
