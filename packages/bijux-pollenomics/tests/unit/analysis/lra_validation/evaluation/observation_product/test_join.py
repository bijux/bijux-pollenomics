"""Challenge the closed prediction-to-observation join."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import (
    ValidationRefusal,
    canonical_json,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.observation_product import (
    ObservedRowAttachment,
    ObservedSixCellEvaluationProduct,
    build_authenticated_observation_product,
    build_observed_six_cell_product,
    reopen_observed_six_cell_product,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.observation_sources import (
    read_observation_source_products,
)

from ..observation_sources.test_sources import _started


def _joined(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> ObservedSixCellEvaluationProduct:
    start, _, _ = _started(tmp_path, monkeypatch)
    completion = read_observation_source_products(
        start, completion_destination=tmp_path / "source-completion.json"
    )
    observations = build_authenticated_observation_product(completion)
    return build_observed_six_cell_product(start.plan.prediction_product, observations)


def test_join_preserves_rows_and_attaches_one_model_free_unit_to_each_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product = _joined(tmp_path, monkeypatch)
    parents = product.prediction_product.outcome_free_rows
    assert len(product.attachments) == len(parents)
    pairs: dict[tuple[str, str, str, str], list[ObservedRowAttachment]] = {}
    for attachment, parent in zip(product.attachments, parents, strict=True):
        row = attachment.row
        assert row.prediction_sha256 == parent.prediction_sha256
        assert row.prediction_manifest_json == parent.prediction_manifest_json
        key = (
            attachment.protocol_id,
            attachment.cell_id,
            row.fold_id,
            row.record_id,
        )
        pairs.setdefault(key, []).append(attachment)
        if attachment.observation_status == "available":
            assert row.observation is not None
            assert row.observation_reference_id is not None
            assert row.observation_support is not None
        else:
            assert row.observation is None
            assert row.status == "predicted"
    assert pairs and all(len(values) == 2 for values in pairs.values())
    for values in pairs.values():
        left, right = values
        assert (
            left.observation_status,
            left.observation_reason,
            left.source_product_sha256,
            left.source_unit_sha256,
            left.row.observation,
            left.row.observation_reference_id,
            left.row.observation_kind,
            left.row.observation_support,
        ) == (
            right.observation_status,
            right.observation_reason,
            right.source_product_sha256,
            right.source_unit_sha256,
            right.row.observation,
            right.row.observation_reference_id,
            right.row.observation_kind,
            right.row.observation_support,
        )


def test_source_terminal_is_not_relabelled_as_prediction_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product = _joined(tmp_path, monkeypatch)
    unavailable = [
        value
        for value in product.attachments
        if value.observation_status in {"missing", "refused"}
    ]
    assert unavailable
    assert all(value.prediction_status == "predicted" for value in unavailable)
    assert all(value.row.status == "predicted" for value in unavailable)
    assert all(value.row.observation is None for value in unavailable)
    payload = json.loads(product.canonical_product_json)
    assert payload["observation_status_counts"]["missing"] > 0
    assert payload["observation_status_counts"]["refused"] > 0
    assert payload["empirical_evaluation_performed"] is False


def test_constructor_and_rehashed_attachment_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product = _joined(tmp_path, monkeypatch)
    with pytest.raises(ValidationRefusal, match="governed join"):
        ObservedSixCellEvaluationProduct(
            product.canonical_product_json,
            product.product_sha256,
            product.prediction_product,
            product.observation_product,
        )
    payload = json.loads(product.canonical_product_json)
    payload["row_attachments"][0]["source_unit_sha256"] = "f" * 64
    with pytest.raises(ValidationRefusal, match="bytes or parent join"):
        reopen_observed_six_cell_product(
            canonical_json(payload),
            manifest_sha256(payload),
            prediction_product=product.prediction_product,
            authenticated_observations=product.observation_product,
        )


def test_join_rejects_untyped_parent_before_iteration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product = _joined(tmp_path, monkeypatch)
    with pytest.raises(ValidationRefusal, match="typed canonical parent"):
        build_observed_six_cell_product(
            product.prediction_product,
            {  # type: ignore[arg-type]
                "assignments": product.observation_product.assignments
            },
        )
