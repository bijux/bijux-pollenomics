"""Spatial-block vegetation rows retain fitted/baseline causal identities."""

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import (
    Fold,
    ValidationRefusal,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.block_products import (
    rows as block_rows,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.contracts import (
    ExternalInput,
    EvaluationScope,
    EvaluationSite,
    Support,
    validate_frozen_prediction,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    BLOCK_BASELINE_METHOD,
    BLOCK_METHODS,
    FITTED_METHOD,
)


def _scope() -> EvaluationScope:
    fold = Fold("block:b", ("p1",), ("p2",), ("g1",), ("g2",))
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
            EvaluationSite("p2", "s2", "g2", "b", "bin", (), "v2", "o2", target),
        ),
        (fold,),
        (("p1", ()), ("p2", ()), (fit, ("p1",)), (support, ())),
        ("Alnus", "Betula"),
        external_inputs=(
            ExternalInput(fit, "training_derived_product", "3" * 64, None),
            ExternalInput(support, "fixed_parameter", "4" * 64, None),
        ),
    )


def _admission(fold: Fold) -> dict[str, object]:
    return {
        "fold_id": fold.fold_id,
        "record_groups": {"p1": "g1", "p2": "g2"},
        "admitted_record_ids": ["p1"],
    }


def _parent(method: str) -> dict[str, object]:
    fold = _scope().folds[0]
    common: dict[str, object] = {
        "method": method,
        "fold_id": fold.fold_id,
        "record_id": "p2",
        "group_id": "g2",
        "bin_id": "bin",
        "outer_fold": fold.as_dict(),
        "vegetation_fraction": {"Alnus": 0.6, "Betula": 0.4},
        "pollen_fraction": {"Alnus": 0.6, "Betula": 0.4},
        "training_admission": _admission(fold),
        "target_geometry_sha256": "5" * 64,
        "support": {"local_support_radius_m": 1000},
    }
    fit = "experiment-fit:" + "3" * 64
    support = "experiment-support:" + "4" * 64
    inputs = ["p1", fit, support]
    graph = {"p1": [], fit: ["p1"], support: []}
    if method == FITTED_METHOD:
        return {
            **common,
            "model_sha256": "f" * 64,
            "training_input_ids": inputs,
            "training_external_ids": [fit, support],
            "training_dependency_graph": graph,
        }
    model = {
        "training_input_ids": inputs,
        "training_external_ids": [fit, support],
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
    parents: dict[tuple[str, str, str], dict[str, object]] | None = None,
    failures: list[dict[str, object]] | None = None,
    folds: dict[str, dict[str, object]] | None = None,
) -> None:
    scope = _scope()
    fold = scope.folds[0]
    parents = (
        {(fold.fold_id, "p2", method): _parent(method) for method in BLOCK_METHODS}
        if parents is None
        else parents
    )
    monkeypatch.setattr(
        block_rows,
        "read_spatial_block_predictions",
        lambda *args, **kwargs: (
            SimpleNamespace(manifest_sha256="a" * 64),
            {"scientific_payload": {"failures": failures or []}},
            {fold.fold_id: fold.as_dict()} if folds is None else folds,
            parents,
            BLOCK_METHODS,
        ),
    )


def test_adapter_freezes_fitted_and_training_mean_vegetation_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install(monkeypatch)
    rows = block_rows.adapt_authenticated_spatial_block_withheld_vegetation_rows(
        tmp_path / "product", expected_manifest_sha256="a" * 64, scope=_scope()
    )
    by_method = {row.model_id: row for row in rows}
    baseline = by_method[BLOCK_BASELINE_METHOD]
    fitted = by_method[FITTED_METHOD]
    assert (baseline.model_id, baseline.source_model.kind) == (
        BLOCK_BASELINE_METHOD,
        "admitted_reconstruction_training_mean",
    )
    assert baseline.fitted_model_sha256 is None
    assert (fitted.model_id, fitted.source_model.kind) == (
        FITTED_METHOD,
        "fitted_spatial",
    )
    assert fitted.fitted_model_sha256 == "f" * 64
    assert all(
        row.observed_pollen is row.observation is row.interval is None for row in rows
    )
    assert all(
        validate_frozen_prediction(row) == "pollenomics-evaluation-prediction.v2"
        for row in rows
    )


def test_parent_refusal_preserves_denominator_without_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fold = _scope().folds[0]
    fitted = _parent(FITTED_METHOD)
    failure = {
        "fold_id": fold.fold_id,
        "record_id": "p2",
        "method": BLOCK_BASELINE_METHOD,
        "status": "not_run",
        "reason_code": "experiment_interrupted",
    }
    _install(
        monkeypatch,
        parents={(fold.fold_id, "p2", FITTED_METHOD): fitted},
        failures=[failure],
    )
    rows = block_rows.adapt_authenticated_spatial_block_withheld_vegetation_rows(
        tmp_path / "product", expected_manifest_sha256="a" * 64, scope=_scope()
    )
    by_method = {row.model_id: row for row in rows}
    baseline = by_method[BLOCK_BASELINE_METHOD]
    model = by_method[FITTED_METHOD]
    assert baseline.status == "prediction_failed"
    assert baseline.reason == "parent_not_run:experiment_interrupted"
    assert baseline.prediction is baseline.source_model is None
    assert model.status == "predicted"


def test_pollen_factory_delegates_complete_unfrozen_ledger_to_interval_authenticator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install(monkeypatch)
    captured: dict[str, object] = {}

    def freeze(rows: object, **kwargs: object) -> object:
        captured.update(rows=rows, kwargs=kwargs)
        return rows

    monkeypatch.setattr(block_rows, "freeze_authenticated_block_pollen_rows", freeze)
    result = block_rows.adapt_authenticated_spatial_block_withheld_pollen_rows(
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
        and row.prediction == (("Alnus", 0.6), ("Betula", 0.4))
        and row.source_model is None
        and row.prediction_sha256 is None
        for row in result
    )
    assert {row.model_id for row in result} == set(BLOCK_METHODS)
    assert captured["kwargs"] == {
        "predictions": tmp_path / "product",
        "expected_prediction_manifest_sha256": "a" * 64,
        "uncertainty": tmp_path / "uncertainty",
        "expected_uncertainty_manifest_sha256": "b" * 64,
    }


@pytest.mark.parametrize(
    "mutation",
    ["fold", "group", "bin", "taxa", "missing", "geometry", "pair_support"],
)
def test_scope_or_denominator_contradictions_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    scope = _scope()
    fold = scope.folds[0]
    parents = {
        (fold.fold_id, "p2", method): _parent(method) for method in BLOCK_METHODS
    }
    folds = None
    if mutation == "fold":
        folds = {fold.fold_id: {**fold.as_dict(), "train_record_ids": []}}
    elif mutation == "missing":
        parents.pop((fold.fold_id, "p2", BLOCK_BASELINE_METHOD))
    else:
        changed = deepcopy(parents[(fold.fold_id, "p2", FITTED_METHOD)])
        if mutation == "group":
            changed["group_id"] = "g1"
        elif mutation == "bin":
            changed["bin_id"] = "other"
        elif mutation == "geometry":
            changed["target_geometry_sha256"] = "6" * 64
        elif mutation == "pair_support":
            changed["support"] = {"local_support_radius_m": 2000}
        else:
            changed["vegetation_fraction"] = {"Alnus": 1.0}
        parents[(fold.fold_id, "p2", FITTED_METHOD)] = changed
    _install(monkeypatch, parents=parents, folds=folds)
    with pytest.raises(ValidationRefusal):
        block_rows.adapt_authenticated_spatial_block_withheld_vegetation_rows(
            tmp_path / "product", expected_manifest_sha256="a" * 64, scope=scope
        )


@pytest.mark.parametrize("mutation", ["graph", "external_digest", "external_role"])
def test_scope_lineage_or_external_identity_mismatch_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    scope = _scope()
    if mutation == "graph":
        graph = dict(scope.dependency_graph)
        graph["experiment-fit:" + "3" * 64] = ("p2",)
        scope = EvaluationScope(
            scope.scope_id,
            scope.sites,
            scope.folds,
            tuple(graph.items()),
            scope.taxa,
            scope.external_inputs,
        )
    else:
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
    _install(monkeypatch)
    with pytest.raises(ValidationRefusal):
        block_rows.adapt_authenticated_spatial_block_withheld_vegetation_rows(
            tmp_path / "product", expected_manifest_sha256="a" * 64, scope=scope
        )
