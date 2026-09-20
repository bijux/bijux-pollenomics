"""Operational batch states map to closed scientific terminal accounting."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal, TypeAlias, cast

import pytest

from bijux_pollenomics.analysis.lra.api import LRABatchItemResult, LRABatchResult
from bijux_pollenomics.analysis.lra_validation.experiments import (
    ExperimentProduct,
    prepare_local_pollen_predictions,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    LOCAL_METHOD,
)

from ..test_assimilation import local_payload

BatchStatus: TypeAlias = Literal[
    "completed", "refused", "failed", "not_run", "unobserved"
]


def _patch_local_batch(
    monkeypatch: pytest.MonkeyPatch,
    statuses: tuple[BatchStatus, ...],
    *,
    interrupted: bool,
    projection_interrupt_at: int | None = None,
) -> None:
    from bijux_pollenomics.analysis.lra_validation.experiments import assimilation

    monkeypatch.setattr(assimilation, "load_engine", lambda: object())
    monkeypatch.setattr(
        assimilation,
        "capture_code_identity",
        lambda _: SimpleNamespace(payload=lambda: {"fixture": "engine"}),
    )
    monkeypatch.setattr(assimilation, "verify_code_identity", lambda *args: None)
    monkeypatch.setattr(assimilation, "_implementation", lambda: {"fixture": "code"})
    monkeypatch.setattr(
        assimilation, "verify_consumed_sources", lambda *args, **kwargs: None
    )

    def batch(items: Any, **kwargs: Any) -> LRABatchResult:
        declared = tuple(items)
        assert len(declared) == len(statuses)
        outcomes: list[LRABatchItemResult] = []
        for index, (item, status) in enumerate(zip(declared, statuses, strict=True)):
            product = (
                SimpleNamespace(
                    directory=Path("/retained") / item.item_id,
                    manifest_sha256=(str(index) * 64)[:64],
                    scientific_content_sha256=(str(index + 1) * 64)[:64],
                )
                if status == "completed"
                else None
            )
            outcomes.append(
                LRABatchItemResult(
                    index,
                    item.item_id,
                    item.request_sha256,
                    status,
                    product=cast(Any, product),
                    canonical_error=(
                        None
                        if status == "completed"
                        else json.dumps(
                            {
                                "reason_code": "raw_" + status,
                                "detail": "retained operational detail",
                            }
                        )
                    ),
                )
            )
        return LRABatchResult(
            "a" * 64,
            kwargs["report_root"],
            tuple(outcomes),
            interrupted,
            "synthetic_interruption" if interrupted else None,
        )

    monkeypatch.setattr(assimilation, "run_lra_batch", batch)
    calls = 0

    def prediction(
        spec: Any,
        fold: Any,
        target: Any,
        anchor: Any,
        product: Any,
        *args: Any,
        **kwargs: Any,
    ) -> dict[str, object]:
        nonlocal calls
        current = calls
        calls += 1
        if current == projection_interrupt_at:
            raise KeyboardInterrupt
        return {
            "fold_id": fold.fold_id,
            "record_id": target.record.record_id,
            "method": LOCAL_METHOD,
        }

    monkeypatch.setattr(assimilation, "predict_assimilated_local", prediction)


def _local_scientific(product: ExperimentProduct) -> dict[str, Any]:
    return json.loads((product.directory / "manifest.json").read_text())[
        "scientific_payload"
    ]


def test_failed_and_unobserved_batch_items_publish_only_refusals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    statuses: tuple[BatchStatus, ...] = (
        "completed",
        "failed",
        "unobserved",
        "refused",
    )
    _patch_local_batch(monkeypatch, statuses, interrupted=False)
    product = prepare_local_pollen_predictions(
        local_payload(tmp_path / "inputs"),
        input_root=tmp_path / "inputs",
        cache_root=tmp_path / "cache",
        destination=tmp_path / "product",
    )
    scientific = _local_scientific(product)
    assert scientific["generated_predictions"] == 1
    assert scientific["failed_folds"] == 3
    assert scientific["interrupted"] is False
    assert {row["status"] for row in scientific["failures"]} == {"refused"}
    assert {row["batch_item_id"] for row in scientific["failures"]} == {
        "p01",
        "p02",
        "p03",
    }
    assert all(
        "retained operational detail" in row["detail"] for row in scientific["failures"]
    )


def test_batch_interruption_converts_only_true_terminal_suffix_to_not_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    statuses: tuple[BatchStatus, ...] = (
        "completed",
        "failed",
        "unobserved",
        "completed",
    )
    _patch_local_batch(monkeypatch, statuses, interrupted=True)
    product = prepare_local_pollen_predictions(
        local_payload(tmp_path / "inputs"),
        input_root=tmp_path / "inputs",
        cache_root=tmp_path / "cache",
        destination=tmp_path / "product",
    )
    scientific = _local_scientific(product)
    terminal = {row["fold_id"]: "predicted" for row in scientific["predictions"]}
    terminal.update({row["fold_id"]: row["status"] for row in scientific["failures"]})
    assert list(terminal.values()) == ["predicted", "refused", "not_run", "not_run"]
    assert scientific["generated_predictions"] == 1
    assert scientific["interrupted"] is True
    assert scientific["all_predictions_generated"] is False
    assert all(
        row["reason_code"] == "experiment_interrupted"
        for row in scientific["failures"]
        if row["status"] == "not_run"
    )
    operations = json.loads((product.directory / "operations.json").read_text())
    assert [row["item_status"] for row in operations["items"]] == list(statuses)


def test_projection_interrupt_does_not_fabricate_later_completions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_local_batch(
        monkeypatch,
        ("completed", "completed", "completed", "completed"),
        interrupted=False,
        projection_interrupt_at=1,
    )
    product = prepare_local_pollen_predictions(
        local_payload(tmp_path / "inputs"),
        input_root=tmp_path / "inputs",
        cache_root=tmp_path / "cache",
        destination=tmp_path / "product",
    )
    scientific = _local_scientific(product)
    assert scientific["generated_predictions"] == 1
    assert [row["status"] for row in scientific["failures"]] == [
        "not_run",
        "not_run",
        "not_run",
    ]
    assert scientific["interrupted"] is True
