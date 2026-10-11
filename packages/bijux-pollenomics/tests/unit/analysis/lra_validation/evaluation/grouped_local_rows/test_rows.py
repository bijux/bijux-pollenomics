"""Grouped local vegetation pairs retain causal pollen and baseline boundaries."""

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from bijux_pollenomics.analysis.lra_validation.channels import (
    ObservationChannels,
    PollenChannel,
)
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
from bijux_pollenomics.analysis.lra_validation.evaluation.grouped_local_rows import (
    rows as grouped_local_rows,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    FITTED_METHODS,
    LOCAL_METHOD,
    TRAINING_MEAN_METHOD,
)


def _scope() -> EvaluationScope:
    fold = Fold("fold:p3", ("p1", "p2"), ("p3",), ("g1", "g2"), ("g3",))
    fit = "experiment-fit:" + "4" * 64
    support_id = "experiment-support:" + "5" * 64
    support = Support(
        60.1,
        18.2,
        1000,
        25,
        0,
        100,
        "6" * 64,
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
            EvaluationSite("p3", "s3", "g3", "b", "bin", (), "v3", "o3", support),
        ),
        (fold,),
        (
            ("p1", ()),
            ("p2", ()),
            ("p3", ()),
            ("raw:p1", ()),
            ("raw:p2", ()),
            ("raw:p3", ()),
            (fit, ("p1", "p2")),
            (support_id, ()),
        ),
        ("Alnus", "Betula"),
        external_inputs=(
            ExternalInput(fit, "training_derived_product", "4" * 64, None),
            ExternalInput(support_id, "fixed_parameter", "5" * 64, None),
        ),
        observation_channels=tuple(
            ObservationChannels(
                f"p{index}",
                f"g{index}",
                (PollenChannel(f"raw:p{index}", str(index) * 64),),
                (f"v{index}",),
            )
            for index in range(1, 4)
        ),
    )


def _local() -> dict[str, object]:
    fold = _scope().folds[0]
    channel = {
        "pollen_input_ids": ["raw:p3", "raw:p1"],
        "pollen_channel_closure": ["raw:p1", "raw:p3"],
        "quantitative_lineage": {"raw:p1": [], "raw:p3": []},
        "consumed_pollen_sources": [
            {
                "record_id": "p1",
                "group_id": "g1",
                "input_id": "raw:p1",
                "source_sha256": "1" * 64,
            },
            {
                "record_id": "p3",
                "group_id": "g3",
                "input_id": "raw:p3",
                "source_sha256": "3" * 64,
            },
        ],
        "observed_pollen": {
            "record_id": "p3",
            "group_id": "g3",
            "pollen_channels": [{"input_id": "raw:p3", "source_sha256": "3" * 64}],
        },
    }
    return {
        "profile": "synthetic-local-pollen-available-v1",
        "method": LOCAL_METHOD,
        "method_kind": "local_pollen_assimilation",
        "fold_id": fold.fold_id,
        "record_id": "p3",
        "group_id": "g3",
        "bin_id": "bin",
        "outer_fold": fold.as_dict(),
        "vegetation_fraction": {"Alnus": 0.6, "Betula": 0.4},
        "channel_admission": channel,
        "request_sha256": "7" * 64,
        "numerical_product": {"scientific_content_sha256": "8" * 64},
        "engine_build": {"api": "v1"},
        "target_geometry_sha256": "6" * 64,
        "support_profile": "same-outer-radius-homogeneous-v1",
        "local_support_radius_m": 1000,
        "preparation_profile": "prep",
        "forward_method_profile": "forward",
        "prediction_manifest_sha256": "9" * 64,
    }


def _baseline() -> dict[str, object]:
    fold = _scope().folds[0]
    fit = "experiment-fit:" + "4" * 64
    support_id = "experiment-support:" + "5" * 64
    model = {
        "training_input_ids": ["p1", "p2", fit, support_id],
        "training_external_ids": [fit, support_id],
        "input_lineage": {
            "p1": [],
            "p2": [],
            fit: ["p1", "p2"],
            support_id: [],
        },
    }
    return {
        "method": TRAINING_MEAN_METHOD,
        "fold_id": fold.fold_id,
        "record_id": "p3",
        "group_id": "g3",
        "bin_id": "bin",
        "outer_fold": fold.as_dict(),
        "vegetation_fraction": {"Alnus": 0.5, "Betula": 0.5},
        "baseline_model_manifest": model,
        "baseline_model_sha256": manifest_sha256(model),
        "target_geometry_sha256": "6" * 64,
        "support": {
            "support_profile": "same-outer-radius-homogeneous-v1",
            "local_support_radius_m": 1000,
        },
    }


def _install(
    monkeypatch: pytest.MonkeyPatch,
    *,
    local: dict[str, object] | None = None,
    baseline: dict[str, object] | None = None,
    local_failure: dict[str, object] | None = None,
    baseline_failure: dict[str, object] | None = None,
    local_folds: dict[str, dict[str, object]] | None = None,
    baseline_methods: tuple[str, ...] = FITTED_METHODS,
) -> None:
    scope = _scope()
    fold = scope.folds[0]
    local = _local() if local is None else local
    baseline = _baseline() if baseline is None else baseline
    folds = {fold.fold_id: fold.as_dict()}
    monkeypatch.setattr(
        grouped_local_rows,
        "read_local_pollen_predictions",
        lambda *args, **kwargs: (
            SimpleNamespace(manifest_sha256="a" * 64),
            {
                "scientific_payload": {
                    "failures": [] if local_failure is None else [local_failure]
                }
            },
            folds if local_folds is None else local_folds,
            {} if local_failure is not None else {fold.fold_id: local},
        ),
    )
    monkeypatch.setattr(
        grouped_local_rows,
        "read_withheld_predictions",
        lambda *args, **kwargs: (
            SimpleNamespace(manifest_sha256="b" * 64),
            {
                "scientific_payload": {
                    "failures": [] if baseline_failure is None else [baseline_failure]
                }
            },
            folds,
            {}
            if baseline_failure is not None
            else {(fold.fold_id, TRAINING_MEAN_METHOD): baseline},
            baseline_methods,
        ),
    )


def test_adapter_freezes_local_love_and_pollen_free_training_mean(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install(monkeypatch)
    model, baseline = (
        grouped_local_rows.adapt_authenticated_grouped_local_vegetation_rows(
            tmp_path / "local",
            expected_local_manifest_sha256="a" * 64,
            baseline_predictions=tmp_path / "baseline",
            expected_baseline_manifest_sha256="b" * 64,
            scope=_scope(),
        )
    )
    assert model.model_id == LOCAL_METHOD
    assert model.source_model is not None
    assert model.source_model.kind == "local_pollen_assimilation"
    assert model.observed_pollen is not None
    assert model.observed_pollen.record_id == "p3"
    assert model.fit_input_ids == ("raw:p3", "raw:p1")
    assert baseline.model_id == TRAINING_MEAN_METHOD
    assert baseline.source_model is not None
    assert baseline.source_model.kind == "admitted_reconstruction_training_mean"
    assert baseline.observed_pollen is None
    assert baseline.fitted_model_sha256 is None
    assert all(
        row.observation is row.interval is None
        and validate_frozen_prediction(row) == "pollenomics-evaluation-prediction.v2"
        for row in (model, baseline)
    )


@pytest.mark.parametrize("parent", ["local", "baseline"])
@pytest.mark.parametrize(
    "status,reason",
    [("refused", "parent_refused"), ("not_run", "experiment_interrupted")],
)
def test_independent_parent_failure_remains_value_free(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    parent: str,
    status: str,
    reason: str,
) -> None:
    fold = _scope().folds[0]
    failure = {
        "fold_id": fold.fold_id,
        "record_ids": ["p3"],
        "status": status,
        "reason_code": reason,
    }
    if parent == "baseline":
        failure["method"] = TRAINING_MEAN_METHOD
    _install(
        monkeypatch,
        local_failure=failure if parent == "local" else None,
        baseline_failure=failure if parent == "baseline" else None,
    )
    rows = grouped_local_rows.adapt_authenticated_grouped_local_vegetation_rows(
        tmp_path / "local",
        expected_local_manifest_sha256="a" * 64,
        baseline_predictions=tmp_path / "baseline",
        expected_baseline_manifest_sha256="b" * 64,
        scope=_scope(),
    )
    selected = rows[0 if parent == "local" else 1]
    other = rows[1 if parent == "local" else 0]
    assert selected.status == "prediction_failed"
    assert selected.reason == f"parent_{status}:{reason}"
    assert selected.prediction is selected.source_model is None
    assert selected.prediction_sha256 is selected.prediction_manifest_json is None
    assert selected.fit_input_ids == ()
    assert other.status == "predicted"


@pytest.mark.parametrize(
    "mutation",
    [
        "fold",
        "methods",
        "group",
        "bin",
        "taxa",
        "geometry",
        "radius",
        "pair_support",
        "pollen_digest",
        "regional_digest",
        "pollen_graph",
        "baseline_graph",
        "baseline_external",
        "baseline_external_omitted",
    ],
)
def test_scope_source_or_support_contradiction_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    scope = _scope()
    local = deepcopy(_local())
    baseline = deepcopy(_baseline())
    local_folds = None
    methods = FITTED_METHODS
    if mutation == "fold":
        fold = scope.folds[0]
        local_folds = {fold.fold_id: {**fold.as_dict(), "train_record_ids": ["p1"]}}
    elif mutation == "methods":
        methods = (TRAINING_MEAN_METHOD,)
    elif mutation == "group":
        local["group_id"] = "g2"
    elif mutation == "bin":
        baseline["bin_id"] = "other"
    elif mutation == "taxa":
        local["vegetation_fraction"] = {"Alnus": 1.0}
    elif mutation == "geometry":
        baseline["target_geometry_sha256"] = "7" * 64
    elif mutation == "radius":
        local["local_support_radius_m"] = 2000
    elif mutation == "pair_support":
        baseline["outer_fold"] = {
            **scope.folds[0].as_dict(),
            "train_record_ids": ["p1"],
        }
    elif mutation == "pollen_digest":
        observed = local["channel_admission"]["observed_pollen"]
        observed["pollen_channels"][0]["source_sha256"] = "8" * 64
    elif mutation == "regional_digest":
        consumed = local["channel_admission"]["consumed_pollen_sources"]
        consumed[0]["source_sha256"] = "8" * 64
    elif mutation == "pollen_graph":
        local["channel_admission"]["quantitative_lineage"]["raw:p3"] = ["p3"]
    elif mutation == "baseline_graph":
        fit = "experiment-fit:" + "4" * 64
        baseline["baseline_model_manifest"]["input_lineage"][fit] = ["p1"]
    elif mutation == "baseline_external":
        baseline["baseline_model_manifest"]["training_external_ids"] = [
            "experiment-fit:" + "7" * 64
        ]
    else:
        baseline["baseline_model_manifest"]["training_external_ids"] = [
            "experiment-fit:" + "4" * 64
        ]
    _install(
        monkeypatch,
        local=local,
        baseline=baseline,
        local_folds=local_folds,
        baseline_methods=methods,
    )
    with pytest.raises(ValidationRefusal):
        grouped_local_rows.adapt_authenticated_grouped_local_vegetation_rows(
            tmp_path / "local",
            expected_local_manifest_sha256="a" * 64,
            baseline_predictions=tmp_path / "baseline",
            expected_baseline_manifest_sha256="b" * 64,
            scope=scope,
        )


def test_typed_scope_is_required_before_either_reader_opens(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    touched = False

    def opened(*args: object, **kwargs: object) -> object:
        nonlocal touched
        touched = True
        raise AssertionError("reader must remain unopened")

    monkeypatch.setattr(grouped_local_rows, "read_local_pollen_predictions", opened)
    monkeypatch.setattr(grouped_local_rows, "read_withheld_predictions", opened)
    with pytest.raises(ValidationRefusal):
        grouped_local_rows.adapt_authenticated_grouped_local_vegetation_rows(
            tmp_path / "local",
            expected_local_manifest_sha256="a" * 64,
            baseline_predictions=tmp_path / "baseline",
            expected_baseline_manifest_sha256="b" * 64,
            scope=object(),  # type: ignore[arg-type]
        )
    assert touched is False
