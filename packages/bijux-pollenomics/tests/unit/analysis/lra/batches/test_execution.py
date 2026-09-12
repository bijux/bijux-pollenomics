"""Bounded submission, receipt evidence and explicit interruption outcomes."""

from __future__ import annotations

from collections.abc import Iterable
from concurrent.futures import ALL_COMPLETED, Future, ThreadPoolExecutor, wait
import json
import os
from pathlib import Path
import threading
from unittest.mock import patch

import pytest

from bijux_pollenomics.analysis.lra.batches import execution
from bijux_pollenomics.analysis.lra.batches.models import (
    LRABatchItem,
    LRABatchItemResult,
    LRABatchLimits,
)
from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.execution.cache import CachedLRAProduct
from bijux_pollenomics.analysis.lra.outputs.publication import LRAProduct


@pytest.fixture(autouse=True)
def worker_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in execution._THREAD_CONTROLS:
        monkeypatch.setenv(name, "1")
    monkeypatch.setattr(os, "cpu_count", lambda: 4)


def _items(count: int = 4) -> list[LRABatchItem]:
    return [
        LRABatchItem(f"point-{index}", {"position": index}) for index in range(count)
    ]


def _success(
    index: int, item: LRABatchItem, root: Path, cache: Path
) -> LRABatchItemResult:
    del root
    return LRABatchItemResult(
        index,
        item.item_id,
        item.request_sha256,
        "completed",
        LRAProduct(cache / str(index), "a" * 64, str(index) * 64),
        item.request_sha256,
        False,
    )


def _thread_executor(*, max_workers: int, **kwargs: object) -> ThreadPoolExecutor:
    # Unit-only scheduling substitute; real spawned workers are exercised in the
    # managed frozen synthetic integration workload.
    del kwargs
    return ThreadPoolExecutor(max_workers=max_workers)


def test_completion_order_does_not_change_input_order_and_submission_is_bounded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    release_first = threading.Event()
    submitted_before_first_return: list[int] = []
    second_done = threading.Event()

    def calculate(
        index: int, item: LRABatchItem, root: Path, cache: Path
    ) -> LRABatchItemResult:
        submitted_before_first_return.append(index)
        if index == 0:
            assert release_first.wait(timeout=5)
        elif index == 1:
            second_done.set()
        return _success(index, item, root, cache)

    def cancellation() -> bool:
        if second_done.is_set():
            # The second worker completes first; cancellation prevents any next
            # work from being submitted while the first still needs draining.
            release_first.set()
            return True
        return False

    monkeypatch.setattr(execution, "ProcessPoolExecutor", _thread_executor)
    monkeypatch.setattr(execution, "_calculate_item", calculate)
    result = execution.run_lra_batch(
        _items(),
        input_root=tmp_path,
        cache_root=tmp_path / "cache",
        report_root=tmp_path / "attempt",
        limits=LRABatchLimits(max_workers=2),
        cancel_requested=cancellation,
    )
    assert set(submitted_before_first_return) == {0, 1}
    assert [item.index for item in result.items] == [0, 1, 2, 3]
    assert [item.item_status for item in result.items] == [
        "completed",
        "completed",
        "not_run",
        "not_run",
    ]
    assert result.interrupted and not result.all_items_completed
    summary = json.loads((tmp_path / "attempt/summary/receipt.json").read_text())
    assert summary["counts"]["not_run"] == 2
    assert len(list((tmp_path / "attempt/items").iterdir())) == 4


def test_duplicate_requests_do_not_compete_for_the_same_cache_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    active: set[str] = set()
    lock = threading.Lock()
    independent_finished = threading.Event()

    def calculate(
        index: int, item: LRABatchItem, root: Path, cache: Path
    ) -> LRABatchItemResult:
        with lock:
            assert item.request_sha256 not in active
            active.add(item.request_sha256)
        try:
            if index == 0:
                assert independent_finished.wait(timeout=5)
            elif index == 2:
                independent_finished.set()
            return _success(index, item, root, cache)
        finally:
            with lock:
                active.remove(item.request_sha256)

    monkeypatch.setattr(execution, "ProcessPoolExecutor", _thread_executor)
    monkeypatch.setattr(execution, "_calculate_item", calculate)
    items = [
        LRABatchItem("a", {"value": 1}),
        LRABatchItem("b", {"value": 1}),
        LRABatchItem("c", {"value": 2}),
    ]
    result = execution.run_lra_batch(
        items,
        input_root=tmp_path,
        cache_root=tmp_path / "cache",
        report_root=tmp_path / "attempt",
        limits=LRABatchLimits(max_workers=2),
    )
    assert result.all_items_completed


def test_cache_facade_refusal_diagnostics_survive_worker_envelope(
    tmp_path: Path,
) -> None:
    refusal = LRARefusal(
        "nonconvergence",
        "failed solver",
        diagnostics={"evaluations": 23, "values": [0.1, 0.2]},
    )
    with patch(
        "bijux_pollenomics.analysis.lra.execution.cache.run_lra_cached",
        side_effect=refusal,
    ):
        result = execution._calculate_item(
            0, _items(1)[0], tmp_path, tmp_path / "cache"
        )
    assert result.item_status == "refused"
    assert result.as_dict()["error"] == refusal.as_dict()
    assert result.product is None and result.cache_hit is None


def test_worker_success_uses_existing_product_and_cache_identity(
    tmp_path: Path,
) -> None:
    product = LRAProduct(tmp_path / "product", "a" * 64, "b" * 64)
    with patch(
        "bijux_pollenomics.analysis.lra.execution.cache.run_lra_cached",
        return_value=CachedLRAProduct(product, "c" * 64, True),
    ):
        result = execution._calculate_item(
            0, _items(1)[0], tmp_path, tmp_path / "cache"
        )
    assert result.product == product and result.cache_hit
    assert result.cache_key == "c" * 64


@pytest.mark.parametrize(
    "failure", ["duplicate", "too_many", "thread_budget", "existing_report"]
)
def test_batch_admission_refuses_before_submitting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    items = _items(2)
    limits = LRABatchLimits()
    if failure == "duplicate":
        items = [items[0], items[0]]
    elif failure == "too_many":
        limits = LRABatchLimits(max_items=1)
    elif failure == "thread_budget":
        monkeypatch.setenv("OMP_NUM_THREADS", "4")
    else:
        (tmp_path / "attempt").mkdir()
    with (
        patch.object(execution, "ProcessPoolExecutor") as executor,
        pytest.raises(LRARefusal),
    ):
        execution.run_lra_batch(
            items,
            input_root=tmp_path,
            cache_root=tmp_path / "cache",
            report_root=tmp_path / "attempt",
            limits=limits,
        )
    executor.assert_not_called()


@pytest.mark.parametrize(
    "remote_error", [KeyboardInterrupt("worker interrupted"), SystemExit(17)]
)
def test_remote_base_exception_is_accounted_once_and_batch_continues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, remote_error: BaseException
) -> None:
    wait_calls = 0

    def bounded_wait(
        futures: Iterable[Future[LRABatchItemResult]],
        timeout: float | None = None,
        return_when: str = ALL_COMPLETED,
    ) -> tuple[set[Future[LRABatchItemResult]], set[Future[LRABatchItemResult]]]:
        nonlocal wait_calls
        wait_calls += 1
        assert wait_calls <= 4, "Completed worker failure was processed repeatedly"
        return wait(futures, timeout=timeout, return_when=return_when)

    def calculate(
        index: int, item: LRABatchItem, root: Path, cache: Path
    ) -> LRABatchItemResult:
        if index == 0:
            raise remote_error
        return _success(index, item, root, cache)

    monkeypatch.setattr(execution, "ProcessPoolExecutor", _thread_executor)
    monkeypatch.setattr(execution, "_calculate_item", calculate)
    monkeypatch.setattr(execution, "wait", bounded_wait)
    result = execution.run_lra_batch(
        _items(2),
        input_root=tmp_path,
        cache_root=tmp_path / "cache",
        report_root=tmp_path / "attempt",
    )
    assert [item.item_status for item in result.items] == ["failed", "completed"]
    assert not result.interrupted
    error = result.items[0].as_dict()["error"]
    assert isinstance(error, dict)
    assert error["exception_type"] == f"builtins.{type(remote_error).__name__}"
    assert error["detail"] == str(remote_error)
    summary = json.loads((tmp_path / "attempt/summary/receipt.json").read_text())
    assert summary["counts"]["failed"] == 1
    assert summary["counts"]["completed"] == 1


def test_parent_keyboard_interrupt_drains_pending_and_stops_submission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    interrupted = False
    release = threading.Event()
    submitted: list[int] = []

    def parent_interrupt(
        futures: Iterable[Future[LRABatchItemResult]],
        timeout: float | None = None,
        return_when: str = ALL_COMPLETED,
    ) -> tuple[set[Future[LRABatchItemResult]], set[Future[LRABatchItemResult]]]:
        nonlocal interrupted
        if not interrupted:
            interrupted = True
            release.set()
            raise KeyboardInterrupt
        return wait(futures, timeout=timeout, return_when=return_when)

    def calculate(
        index: int, item: LRABatchItem, root: Path, cache: Path
    ) -> LRABatchItemResult:
        submitted.append(index)
        assert release.wait(timeout=5)
        return _success(index, item, root, cache)

    monkeypatch.setattr(execution, "ProcessPoolExecutor", _thread_executor)
    monkeypatch.setattr(execution, "_calculate_item", calculate)
    monkeypatch.setattr(execution, "wait", parent_interrupt)
    result = execution.run_lra_batch(
        _items(3),
        input_root=tmp_path,
        cache_root=tmp_path / "cache",
        report_root=tmp_path / "attempt",
    )
    assert submitted == [0]
    assert result.interruption_reason == "keyboard_interrupt"
    assert [item.item_status for item in result.items] == [
        "completed",
        "not_run",
        "not_run",
    ]
    summary = json.loads((tmp_path / "attempt/summary/receipt.json").read_text())
    assert summary["counts"]["completed"] == 1
    assert summary["counts"]["not_run"] == 2
