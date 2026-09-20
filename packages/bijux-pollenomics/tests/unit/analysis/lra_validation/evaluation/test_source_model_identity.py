"""Versioned source identity keeps historical envelopes exact and baselines honest."""

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import (
    ValidationRefusal,
    canonical_json,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.contracts import (
    EvaluationRow,
    SourceModelIdentity,
    _authenticated_source_model,
    prediction_payload,
    validate_frozen_prediction,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    FITTED_METHOD,
)

_FROZEN = datetime(2020, 1, 1, tzinfo=UTC)


def _row() -> EvaluationRow:
    return EvaluationRow(
        fold_id="fold:a",
        record_id="p1",
        model_id="model",
        target="pollen_composition",
        experiment="all_target_pollen_withheld",
        status="predicted",
        prediction=(("Alnus", 0.6), ("Betula", 0.4)),
        observation=None,
        observation_reference_id=None,
        observation_kind=None,
        observation_support=None,
        prediction_sha256=None,
        prediction_manifest_json=None,
        fitted_model_sha256="a" * 64,
        prediction_frozen_at=_FROZEN,
        fit_input_ids=("train:a",),
    )


def _bind(row: EvaluationRow) -> EvaluationRow:
    payload = prediction_payload(row)
    return replace(
        row,
        prediction_sha256=manifest_sha256(payload),
        prediction_manifest_json=canonical_json(payload),
    )


def _fitted_v2_row() -> EvaluationRow:
    return replace(
        _row(),
        model_id=FITTED_METHOD,
        source_model=_authenticated_source_model("fitted_spatial", "a" * 64),
    )


def test_historical_v1_canonical_bytes_remain_exact() -> None:
    row = _row()
    expected = (
        '{"experiment":"all_target_pollen_withheld","fit_input_ids":["train:a"],'
        '"fitted_model_sha256":"'
        + "a"
        * 64
        + '","fold_id":"fold:a","frozen_at":"2020-01-01T00:00:00+00:00",'
        '"interval":null,"model_id":"model","observed_pollen":null,'
        '"prediction":[["Alnus",0.6],["Betula",0.4]],"record_id":"p1",'
        '"schema_version":"pollenomics-evaluation-prediction.v1",'
        '"target":"pollen_composition"}'
    )
    assert canonical_json(prediction_payload(row)) == expected
    assert validate_frozen_prediction(_bind(row)) == (
        "pollenomics-evaluation-prediction.v1"
    )


def test_source_identity_is_factory_only_and_v2_uses_generic_wire_names() -> None:
    with pytest.raises(ValidationRefusal, match="authenticated producer"):
        SourceModelIdentity("fitted_spatial", "a" * 64)
    row = _fitted_v2_row()
    payload = prediction_payload(row)
    assert payload["schema_version"] == "pollenomics-evaluation-prediction.v2"
    assert payload["source_model"] == {
        "kind": "fitted_spatial",
        "sha256": "a" * 64,
    }
    assert payload["model_input_ids"] == ("train:a",)
    assert "fitted_model_sha256" not in payload
    assert "fit_input_ids" not in payload
    assert validate_frozen_prediction(_bind(row)) == (
        "pollenomics-evaluation-prediction.v2"
    )


def test_baseline_source_refuses_a_fitted_alias() -> None:
    row = replace(
        _row(),
        model_id="training_mean",
        source_model=_authenticated_source_model(
            "admitted_reconstruction_training_mean", "b" * 64
        ),
    )
    with pytest.raises(ValidationRefusal, match="cannot populate"):
        prediction_payload(row)


def test_source_kind_cannot_be_relabelled_as_another_method() -> None:
    row = replace(
        _row(),
        fitted_model_sha256=None,
        source_model=_authenticated_source_model(
            "admitted_reconstruction_training_mean", "b" * 64
        ),
    )
    with pytest.raises(ValidationRefusal, match="baseline method"):
        prediction_payload(row)


def test_frozen_v2_refuses_source_or_input_mutation() -> None:
    row = _fitted_v2_row()
    frozen = _bind(row)
    with pytest.raises(ValidationRefusal, match="bytes differ"):
        validate_frozen_prediction(replace(frozen, fit_input_ids=("train:b",)))
    with pytest.raises(ValidationRefusal, match="unique tuple"):
        prediction_payload(replace(row, fit_input_ids=("train:a", "train:a")))


def test_v1_cannot_be_relabelled_with_a_v2_source() -> None:
    frozen = _bind(_row())
    relabelled = replace(
        frozen,
        source_model=_authenticated_source_model("fitted_spatial", "a" * 64),
    )
    with pytest.raises(ValidationRefusal, match="Historical v1"):
        validate_frozen_prediction(relabelled)
