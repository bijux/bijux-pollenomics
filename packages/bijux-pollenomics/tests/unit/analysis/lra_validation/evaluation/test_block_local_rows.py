"""Block-local adaptation preserves causal source and baseline boundaries."""

from dataclasses import replace
import json
from types import SimpleNamespace
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra_validation.channels import (
    ObservationChannels,
    ObservedPollenAdmission,
    PollenChannel,
)
from bijux_pollenomics.analysis.lra_validation.contracts import (
    Fold,
    ValidationRefusal,
    canonical_json,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.api import (
    evaluate_final,
    validate_evaluation_policy,
)
from bijux_pollenomics.analysis.lra_validation.evaluation import block_local_rows
from bijux_pollenomics.analysis.lra_validation.evaluation.contracts import (
    EvaluationScope,
    EvaluationSite,
    _authenticated_source_model,
    prediction_payload,
    validate_frozen_prediction,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    BLOCK_BASELINE_METHOD,
    LOCAL_METHOD,
)

from .support import ACCESS, policy_payload, rows_fixture, scope_fixture


def _scope() -> EvaluationScope:
    fold = Fold("block:b", ("p1",), ("p2",), ("g1",), ("g2",))
    sites = (
        EvaluationSite("p1", "s1", "g1", "a", "bin", (), "v1", "raw:p1", None),
        EvaluationSite("p2", "s2", "g2", "b", "bin", (), "v2", "raw:p2", None),
    )
    return EvaluationScope(
        "scope",
        sites,
        (fold,),
        (("p1", ()), ("p2", ()), ("raw:p1", ()), ("raw:p2", ("p2",))),
        ("Alnus", "Betula"),
        observation_channels=(
            ObservationChannels(
                "p1", "g1", (PollenChannel("raw:p1", "1" * 64),), ("v1",)
            ),
            ObservationChannels(
                "p2", "g2", (PollenChannel("raw:p2", "2" * 64),), ("v2",)
            ),
        ),
    )


def _admission(fold: Fold) -> dict[str, object]:
    return {
        "fold_id": fold.fold_id,
        "record_groups": {"p1": "g1", "p2": "g2"},
        "admitted_record_ids": ["p1"],
    }


def _local(fold: Fold, admission: dict[str, object]) -> dict[str, object]:
    channel = {
        "pollen_input_ids": ["raw:p2", "raw:p1"],
        "pollen_channel_closure": ["p1", "raw:p1", "raw:p2"],
        "observed_pollen": {
            "record_id": "p2",
            "group_id": "g2",
            "pollen_channels": [{"input_id": "raw:p2", "source_sha256": "2" * 64}],
        },
    }
    row: dict[str, object] = {
        "profile": "synthetic-spatial-block-local-pollen-available-v1",
        "method": LOCAL_METHOD,
        "method_kind": "local_pollen_assimilation",
        "fold_id": fold.fold_id,
        "record_id": "p2",
        "group_id": "g2",
        "bin_id": "bin",
        "outer_fold": fold.as_dict(),
        "vegetation_fraction": {"Alnus": 0.6, "Betula": 0.4},
        "training_admission_sha256": manifest_sha256(admission),
        "channel_admission": channel,
        "request_sha256": "3" * 64,
        "numerical_product": {"scientific_content_sha256": "4" * 64},
        "engine_build": {"api": "v1"},
        "target_geometry_sha256": "5" * 64,
        "target_support": {"radius_m": 1000},
        "preparation_profile": "prep",
        "forward_method_profile": "forward",
    }
    row["prediction_manifest_sha256"] = manifest_sha256(row)
    return row


def _baseline(fold: Fold, admission: dict[str, object]) -> dict[str, object]:
    model = {"training_input_ids": ["p1"]}
    return {
        "method": BLOCK_BASELINE_METHOD,
        "fold_id": fold.fold_id,
        "record_id": "p2",
        "group_id": "g2",
        "bin_id": "bin",
        "outer_fold": fold.as_dict(),
        "vegetation_fraction": {"Alnus": 0.5, "Betula": 0.5},
        "baseline_model_manifest": model,
        "baseline_model_sha256": manifest_sha256(model),
        "training_admission": admission,
        "target_geometry_sha256": "5" * 64,
    }


def _install(
    monkeypatch: pytest.MonkeyPatch,
    *,
    local: dict[str, object] | None = None,
    baseline: dict[str, object] | None = None,
    local_failure: dict[str, object] | None = None,
    baseline_failure: dict[str, object] | None = None,
) -> None:
    scope = _scope()
    fold = scope.folds[0]
    admission = _admission(fold)
    local = _local(fold, admission) if local is None else local
    baseline = _baseline(fold, admission) if baseline is None else baseline
    folds = {fold.fold_id: fold.as_dict()}
    local_failures = [] if local_failure is None else [local_failure]
    baseline_failures = [] if baseline_failure is None else [baseline_failure]
    monkeypatch.setattr(
        block_local_rows,
        "read_spatial_block_local_pollen_predictions",
        lambda *args, **kwargs: (
            SimpleNamespace(manifest_sha256="a" * 64),
            {
                "scientific_payload": {
                    "failures": local_failures,
                    "block_admissions": {fold.fold_id: admission},
                }
            },
            folds,
            {}
            if local_failure is not None
            else {(fold.fold_id, "p2", LOCAL_METHOD): local},
        ),
    )
    monkeypatch.setattr(
        block_local_rows,
        "read_spatial_block_predictions",
        lambda *args, **kwargs: (
            SimpleNamespace(manifest_sha256="b" * 64),
            {
                "scientific_payload": {
                    "failures": baseline_failures,
                    "block_admissions": {fold.fold_id: admission},
                }
            },
            folds,
            {}
            if baseline_failure is not None
            else {(fold.fold_id, "p2", BLOCK_BASELINE_METHOD): baseline},
            ("fitted", BLOCK_BASELINE_METHOD),
        ),
    )


def test_adapter_freezes_local_model_and_target_pollen_free_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install(monkeypatch)
    rows = block_local_rows.adapt_authenticated_spatial_block_local_vegetation_rows(
        tmp_path / "local",
        expected_local_manifest_sha256="a" * 64,
        baseline_predictions=tmp_path / "baseline",
        expected_baseline_manifest_sha256="b" * 64,
        scope=_scope(),
    )
    model, baseline = rows
    assert (model.model_id, model.source_model.kind) == (
        LOCAL_METHOD,
        "local_pollen_assimilation",
    )
    assert model.observed_pollen is not None
    assert model.fitted_model_sha256 is None
    assert (baseline.model_id, baseline.source_model.kind) == (
        BLOCK_BASELINE_METHOD,
        "admitted_reconstruction_training_mean",
    )
    assert baseline.observed_pollen is None
    assert baseline.fit_input_ids == ("p1",)
    assert validate_frozen_prediction(model) == "pollenomics-evaluation-prediction.v2"
    assert (
        validate_frozen_prediction(baseline) == "pollenomics-evaluation-prediction.v2"
    )
    assert model.observation is baseline.observation is None
    assert model.interval is baseline.interval is None


def test_cross_product_admission_change_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scope = _scope()
    admission = _admission(scope.folds[0])
    baseline = _baseline(scope.folds[0], admission)
    baseline["training_admission"] = {**admission, "admitted_record_ids": []}
    _install(monkeypatch, baseline=baseline)
    with pytest.raises(ValidationRefusal, match="admission or geometry"):
        block_local_rows.adapt_authenticated_spatial_block_local_vegetation_rows(
            tmp_path / "local",
            expected_local_manifest_sha256="a" * 64,
            baseline_predictions=tmp_path / "baseline",
            expected_baseline_manifest_sha256="b" * 64,
            scope=scope,
        )


def test_parent_refusal_stays_unfrozen_without_invented_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    failure = {
        "fold_id": "block:b",
        "record_id": "p2",
        "method": LOCAL_METHOD,
        "status": "refused",
        "reason_code": "no_admitted_anchor",
    }
    _install(monkeypatch, local_failure=failure)
    rows = block_local_rows.adapt_authenticated_spatial_block_local_vegetation_rows(
        tmp_path / "local",
        expected_local_manifest_sha256="a" * 64,
        baseline_predictions=tmp_path / "baseline",
        expected_baseline_manifest_sha256="b" * 64,
        scope=_scope(),
    )
    model, baseline = rows
    assert model.status == "prediction_failed"
    assert model.reason == "parent_refused:no_admitted_anchor"
    assert model.prediction is model.source_model is model.prediction_sha256 is None
    assert baseline.status == "predicted"


def test_typed_local_model_alone_admits_target_pollen() -> None:
    scope = scope_fixture()
    scope = replace(
        scope,
        observation_channels=tuple(
            ObservationChannels(
                site.record_id,
                site.group_id,
                (PollenChannel(site.pollen_observation_id, "a" * 64),),
                (site.vegetation_observation_id,),
            )
            for site in scope.sites
        ),
        dependency_graph=(
            *scope.dependency_graph,
            *((site.pollen_observation_id, ()) for site in scope.sites),
        ),
    )
    declaration = policy_payload(scope)
    declaration["cells"] = declaration["cells"][:1]
    declaration["cells"][0].update(
        experiment="local_pollen_available",
        model_id=LOCAL_METHOD,
        baseline_id=BLOCK_BASELINE_METHOD,
    )
    policy = validate_evaluation_policy(
        declaration, scope=scope, first_test_access_at=ACCESS
    )
    rows = []
    for original in rows_fixture(scope):
        if original.target != "vegetation_cover":
            continue
        model = original.model_id == "model"
        row = replace(
            original,
            model_id=LOCAL_METHOD if model else BLOCK_BASELINE_METHOD,
            experiment="local_pollen_available",
            fitted_model_sha256=None,
            prediction_sha256=None,
            prediction_manifest_json=None,
            fit_input_ids=(
                (*original.fit_input_ids, "pollen:" + original.record_id[1:])
                if model
                else original.fit_input_ids
            ),
            observed_pollen=(
                ObservedPollenAdmission(
                    original.record_id,
                    "g" + original.record_id[1:],
                    (PollenChannel("pollen:" + original.record_id[1:], "a" * 64),),
                )
                if model
                else None
            ),
            source_model=_authenticated_source_model(
                "local_pollen_assimilation"
                if model
                else "admitted_reconstruction_training_mean",
                ("c" if model else "d") * 64,
            ),
        )
        envelope = prediction_payload(row)
        rows.append(
            replace(
                row,
                prediction_manifest_json=canonical_json(envelope),
                prediction_sha256=manifest_sha256(envelope),
            )
        )
    result = json.loads(
        evaluate_final(policy, scope=scope, rows=tuple(rows)).canonical_result_json
    )
    assert result["schema_version"] == "pollenomics-final-evaluation-result.v3"
    assert all(
        item["model_source"]["kind"] == "local_pollen_assimilation"
        and item["baseline_source"]["kind"] == "admitted_reconstruction_training_mean"
        for item in result["paired_evidence"]
    )
