"""Challenge the release-only parent-bound scorer."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation.channels import (
    ObservationChannels,
    PollenChannel,
)
from bijux_pollenomics.analysis.lra_validation.contracts import (
    ValidationRefusal,
    canonical_json,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.contracts import (
    freeze_evaluation_prediction,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.observation_product import (
    ObservedSixCellEvaluationResult,
    evaluate_observed_six_cell_product,
    reopen_observed_six_cell_evaluation_result,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    FITTED_METHOD,
    LOCAL_METHOD,
    TRAINING_MEAN_METHOD,
)

from ..observation_sources import test_sources as source_fixture
from ..prediction_product import test_product as prediction_fixture
from .test_join import _joined


def _scorable_joined(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    failed_model_ids: frozenset[str] = frozenset(),
) -> Any:
    """Align the synthetic local channel; ordinary source fixtures need not score."""
    original_protocols = source_fixture._supported_protocols
    original_row = prediction_fixture._row

    def protocols() -> tuple[Any, Any]:
        result = []
        for protocol in original_protocols():
            channels = tuple(
                ObservationChannels(
                    value.record_id,
                    value.group_id,
                    (
                        *value.pollen_channels,
                        PollenChannel(f"raw:{value.record_id}", "d" * 64),
                    ),
                    value.vegetation_input_ids,
                )
                for value in protocol.scope.observation_channels
            )
            graph = dict(protocol.scope.dependency_graph)
            graph.update({f"raw:{value.record_id}": () for value in channels})
            result.append(
                replace(
                    protocol,
                    scope=replace(
                        protocol.scope,
                        observation_channels=channels,
                        dependency_graph=tuple(graph.items()),
                    ),
                )
            )
        return result[0], result[1]

    def row(*args: Any, **kwargs: Any) -> Any:
        value = original_row(*args, **kwargs)
        if value.model_id in failed_model_ids:
            return replace(
                value,
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
                reason="parent_refused:focused-release-scorer",
                observed_pollen=None,
                source_model=None,
            )
        fold = next(
            fold
            for protocol in protocols()
            for fold in protocol.scope.folds
            if fold.fold_id == value.fold_id and value.record_id in fold.test_record_ids
        )
        fit_inputs = (fold.train_record_ids[0],)
        if value.observed_pollen is not None:
            fit_inputs = (*fit_inputs, f"raw:{value.record_id}")
        unfrozen = replace(
            value,
            prediction_sha256=None,
            prediction_manifest_json=None,
            prediction_frozen_at=None,
            fit_input_ids=fit_inputs,
        )
        return freeze_evaluation_prediction(unfrozen)

    monkeypatch.setattr(source_fixture, "_supported_protocols", protocols)
    monkeypatch.setattr(prediction_fixture, "_row", row)
    return _joined(tmp_path, monkeypatch)


@pytest.mark.parametrize(
    "failed_model_ids",
    [
        frozenset({LOCAL_METHOD, FITTED_METHOD}),
        frozenset({TRAINING_MEAN_METHOD}),
        frozenset({LOCAL_METHOD, FITTED_METHOD, TRAINING_MEAN_METHOD}),
    ],
)
def test_release_scorer_preserves_value_free_prediction_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failed_model_ids: frozenset[str],
) -> None:
    result = evaluate_observed_six_cell_product(
        _scorable_joined(tmp_path, monkeypatch, failed_model_ids=failed_model_ids)
    )
    payload = json.loads(result.canonical_result_json)
    nested = [
        json.loads(protocol["canonical_result_json"])
        for protocol in payload["protocol_results"]
    ]
    assert any(
        row["status"] == "prediction_failed"
        for protocol in nested
        for row in protocol["row_statuses"]
    )
    assert all(
        any(cell["failed_prediction_groups"] > 0 for cell in protocol["cells"])
        for protocol in nested
    )


def test_release_scorer_binds_both_protocols_and_source_terminals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product = _scorable_joined(tmp_path, monkeypatch)
    result = evaluate_observed_six_cell_product(product)
    payload = json.loads(result.canonical_result_json)
    assert [value["protocol_id"] for value in payload["protocol_results"]] == [
        protocol.protocol_id for protocol in product.prediction_product.protocols
    ]
    statuses = {
        row["status"]
        for protocol in payload["protocol_results"]
        for row in json.loads(protocol["canonical_result_json"])["row_statuses"]
    }
    assert {"missing_source", "refused_source"} <= statuses
    assert payload["observed_six_cell_product_sha256"] == product.product_sha256
    assert payload["review_authenticity_verified"] is False
    assert payload["scientific_approval_granted"] is False


def test_release_scorer_rejects_raw_or_lazy_rows_before_iteration() -> None:
    from bijux_pollenomics.analysis.lra_validation.evaluation.api import (
        evaluate_observed_six_cell_product as public_evaluate,
    )

    assert public_evaluate is evaluate_observed_six_cell_product

    class Poison:
        def __iter__(self) -> Iterator[object]:
            raise AssertionError("release scorer iterated an untyped input")

    with pytest.raises(ValidationRefusal, match="exact observed six-cell product"):
        evaluate_observed_six_cell_product(())  # type: ignore[arg-type]
    with pytest.raises(ValidationRefusal, match="exact observed six-cell product"):
        evaluate_observed_six_cell_product(Poison())  # type: ignore[arg-type]


def test_release_scorer_refuses_mismatched_local_channel_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(ValidationRefusal, match="pollen digest|consumed closure"):
        evaluate_observed_six_cell_product(_joined(tmp_path, monkeypatch))


def test_result_is_factory_only_and_rehashed_parent_result_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product = _scorable_joined(tmp_path, monkeypatch)
    result = evaluate_observed_six_cell_product(product)
    with pytest.raises(ValidationRefusal, match="governed scorer"):
        ObservedSixCellEvaluationResult(
            result.canonical_result_json,
            result.result_sha256,
            product,
        )
    payload = json.loads(result.canonical_result_json)
    payload["protocol_results"][0]["status"] = "passed"
    with pytest.raises(ValidationRefusal, match="bytes or parents"):
        reopen_observed_six_cell_evaluation_result(
            canonical_json(payload),
            manifest_sha256(payload),
            observed_product=product,
        )
