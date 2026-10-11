"""Challenge the closed outcome-free six-cell product factory."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation.channels import (
    ObservedPollenAdmission,
    PollenChannel,
)
from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.evaluation.contracts import (
    EvaluationRow,
    _authenticated_source_model,
    freeze_evaluation_prediction,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.policy import (
    validate_evaluation_policy,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.prediction_product import (
    ProtocolProductLocators,
    RetainedProductLocator,
    SixCellPredictionProduct,
    SixCellProductLocators,
    build_six_cell_prediction_product,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.prediction_product import (
    product as prediction_product_module,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.release import (
    FinalEvaluationProtocol,
    admit_final_evaluation_release,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    FITTED_METHOD,
    LOCAL_METHOD,
    TRAINING_MEAN_METHOD,
)

from ..support import ACCESS, policy_payload
from ..test_release import _protocols as release_protocols


def _protocols() -> tuple[FinalEvaluationProtocol, FinalEvaluationProtocol]:
    result = []
    for protocol in release_protocols():
        payload = policy_payload(protocol.scope)
        base: dict[str, Any] = {
            key: value
            for key, value in payload["cells"][0].items()
            if key not in {"cell_id", "experiment", "target", "model_id", "baseline_id"}
        }
        payload["cells"] = [
            dict(
                base,
                cell_id="local-vegetation",
                experiment="local_pollen_available",
                target="vegetation_cover",
                model_id=LOCAL_METHOD,
                baseline_id=TRAINING_MEAN_METHOD,
            ),
            dict(
                base,
                cell_id="withheld-vegetation",
                experiment="all_target_pollen_withheld",
                target="vegetation_cover",
                model_id=FITTED_METHOD,
                baseline_id=TRAINING_MEAN_METHOD,
            ),
            dict(
                base,
                cell_id="withheld-pollen",
                experiment="all_target_pollen_withheld",
                target="pollen_composition",
                model_id=FITTED_METHOD,
                baseline_id=TRAINING_MEAN_METHOD,
                interval_profile_id="conditional-test",
            ),
        ]
        result.append(
            replace(
                protocol,
                policy=validate_evaluation_policy(
                    payload, scope=protocol.scope, first_test_access_at=ACCESS
                ),
            )
        )
    return result[0], result[1]


def _locators(tmp_path: Path) -> SixCellProductLocators:
    def protocol(name: str, digit: str) -> ProtocolProductLocators:
        return ProtocolProductLocators(
            RetainedProductLocator(tmp_path / f"{name}-local", digit * 64),
            RetainedProductLocator(
                tmp_path / f"{name}-withheld", str(int(digit) + 1) * 64
            ),
            RetainedProductLocator(
                tmp_path / f"{name}-uncertainty", str(int(digit) + 2) * 64
            ),
        )

    return SixCellProductLocators(protocol("grouped", "1"), protocol("block", "4"))


def _row(
    fold_id: str,
    record_id: str,
    model_id: str,
    *,
    experiment: str,
    target: str,
    interval_profile: str = "conditional-test",
) -> EvaluationRow:
    from bijux_pollenomics.analysis.lra_validation.evaluation.contracts import (
        PredictiveInterval,
    )

    kind = {
        LOCAL_METHOD: "local_pollen_assimilation",
        FITTED_METHOD: "fitted_spatial",
        TRAINING_MEAN_METHOD: "admitted_reconstruction_training_mean",
    }[model_id]
    source_sha256 = {
        LOCAL_METHOD: "a",
        FITTED_METHOD: "b",
        TRAINING_MEAN_METHOD: "c",
    }[model_id] * 64
    interval = (
        PredictiveInterval(
            interval_profile,
            0.8,
            ("observation_process",),
            "predictive_observation",
            (("a", 0.2, 0.8), ("b", 0.2, 0.8)),
        )
        if target == "pollen_composition"
        else None
    )
    observed = (
        ObservedPollenAdmission(
            record_id,
            next(
                site.group_id
                for protocol in _protocols()
                for site in protocol.scope.sites
                if site.record_id == record_id
            ),
            (PollenChannel(f"raw:{record_id}", "d" * 64),),
        )
        if experiment == "local_pollen_available" and model_id == LOCAL_METHOD
        else None
    )
    return freeze_evaluation_prediction(
        EvaluationRow(
            fold_id=fold_id,
            record_id=record_id,
            model_id=model_id,
            target=target,  # type: ignore[arg-type]
            experiment=experiment,  # type: ignore[arg-type]
            status="predicted",
            prediction=(("a", 0.6), ("b", 0.4)),
            observation=None,
            observation_reference_id=None,
            observation_kind=None,
            observation_support=None,
            prediction_sha256=None,
            prediction_manifest_json=None,
            fitted_model_sha256=source_sha256 if model_id == FITTED_METHOD else None,
            prediction_frozen_at=None,
            fit_input_ids=("train:a",),
            interval=interval,
            observed_pollen=observed,
            source_model=_authenticated_source_model(kind, source_sha256),
        )
    )


def _rows(
    protocol: FinalEvaluationProtocol, experiment: str, target: str
) -> tuple[EvaluationRow, ...]:
    methods = (
        (LOCAL_METHOD, TRAINING_MEAN_METHOD)
        if experiment == "local_pollen_available"
        else (FITTED_METHOD, TRAINING_MEAN_METHOD)
    )
    return tuple(
        _row(fold.fold_id, record_id, method, experiment=experiment, target=target)
        for fold in protocol.scope.folds
        for record_id in fold.test_record_ids
        for method in methods
    )


def _install(
    monkeypatch: pytest.MonkeyPatch,
    protocols: tuple[FinalEvaluationProtocol, ...],
) -> None:
    grouped, block = protocols
    values = {
        "adapt_authenticated_grouped_local_vegetation_rows": _rows(
            grouped, "local_pollen_available", "vegetation_cover"
        ),
        "adapt_authenticated_grouped_withheld_vegetation_rows": _rows(
            grouped, "all_target_pollen_withheld", "vegetation_cover"
        ),
        "adapt_authenticated_grouped_withheld_pollen_rows": _rows(
            grouped, "all_target_pollen_withheld", "pollen_composition"
        ),
        "adapt_authenticated_spatial_block_local_vegetation_rows": _rows(
            block, "local_pollen_available", "vegetation_cover"
        ),
        "adapt_authenticated_spatial_block_withheld_vegetation_rows": _rows(
            block, "all_target_pollen_withheld", "vegetation_cover"
        ),
        "adapt_authenticated_spatial_block_withheld_pollen_rows": _rows(
            block, "all_target_pollen_withheld", "pollen_composition"
        ),
    }
    for name, rows in values.items():
        monkeypatch.setattr(
            prediction_product_module,
            name,
            lambda *args, _rows=rows, **kwargs: _rows,
        )


def _build(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SixCellPredictionProduct:
    protocols = _protocols()
    _install(monkeypatch, protocols)
    admission = admit_final_evaluation_release(protocols)
    return build_six_cell_prediction_product(
        admission, protocols=protocols, locators=_locators(tmp_path)
    )


def test_factory_mints_exact_outcome_free_six_cell_product(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product = _build(tmp_path, monkeypatch)
    payload = json.loads(product.canonical_product_json)
    assert payload["engineering_prediction_product"] == "authenticated"
    assert payload["empirical_evaluation_performed"] is False
    assert payload["scientific_acceptance"] == "not_evaluated"
    assert len(payload["protocols"]) == 2
    assert sum(len(item["cells"]) for item in payload["protocols"]) == 6
    assert product.outcome_free_rows
    assert all(row.observation is None for row in product.outcome_free_rows)
    assert product.rows_for("grouped_outer")
    assert product.rows_for("spatial_block")


def test_constructor_and_untyped_locator_inputs_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product = _build(tmp_path, monkeypatch)
    with pytest.raises(ValidationRefusal, match="governed factory"):
        SixCellPredictionProduct(
            product.canonical_product_json,
            product.product_sha256,
            product.release_admission_sha256,
            product.scope_sha256,
            product.protocols,
            product.outcome_free_rows,
        )
    with pytest.raises(ValidationRefusal, match="fixed typed locator"):
        build_six_cell_prediction_product(
            admit_final_evaluation_release(_protocols()),
            protocols=_protocols(),
            locators={"rows": product.outcome_free_rows},  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "attack",
    ["missing", "duplicate", "outcome", "v1", "wrong_method", "semantic_rehash"],
)
def test_adapter_row_attacks_refuse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    attack: str,
) -> None:
    protocols = _protocols()
    _install(monkeypatch, protocols)
    rows = list(_rows(protocols[0], "all_target_pollen_withheld", "vegetation_cover"))
    if attack == "missing":
        rows.pop()
    elif attack == "duplicate":
        rows[-1] = rows[0]
    elif attack == "outcome":
        rows[0] = replace(rows[0], observation=(("a", 1.0),))
    elif attack == "v1":
        rows[0] = replace(rows[0], source_model=None)
    elif attack == "wrong_method":
        rows[0] = replace(rows[0], model_id="invented")
    else:
        target = rows[0]
        coherent = replace(
            target,
            prediction_sha256=None,
            prediction_manifest_json=None,
            prediction_frozen_at=None,
            observed_pollen=ObservedPollenAdmission(
                target.record_id,
                protocols[0].scope.sites[0].group_id,
                (PollenChannel(f"raw:{target.record_id}", "d" * 64),),
            ),
        )
        rows[0] = freeze_evaluation_prediction(coherent)
    monkeypatch.setattr(
        prediction_product_module,
        "adapt_authenticated_grouped_withheld_vegetation_rows",
        lambda *args, **kwargs: tuple(rows),
    )
    with pytest.raises(ValidationRefusal):
        build_six_cell_prediction_product(
            admit_final_evaluation_release(protocols),
            protocols=protocols,
            locators=_locators(tmp_path),
        )


def test_release_or_policy_mutation_refuses_before_adapter_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocols = _protocols()
    admission = admit_final_evaluation_release(protocols)
    changed = replace(protocols[0], policy=release_protocols()[0].policy)
    called = False

    def unexpected(*args: object, **kwargs: object) -> tuple[EvaluationRow, ...]:
        nonlocal called
        called = True
        return ()

    monkeypatch.setattr(
        prediction_product_module,
        "adapt_authenticated_grouped_local_vegetation_rows",
        unexpected,
    )
    with pytest.raises(ValidationRefusal):
        build_six_cell_prediction_product(
            admission,
            protocols=(changed, protocols[1]),
            locators=_locators(tmp_path),
        )
    assert called is False
