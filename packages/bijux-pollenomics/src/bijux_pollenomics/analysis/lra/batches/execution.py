"""Bounded standard-library execution over the existing verified LRA cache."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import FIRST_COMPLETED, Future, ProcessPoolExecutor, wait
import hashlib
from itertools import islice
import multiprocessing
import os
from pathlib import Path
import signal

from ..engine.errors import LRARefusal
from .models import (
    LRABatchItem,
    LRABatchItemResult,
    LRABatchLimits,
    LRABatchResult,
    canonical_json,
)
from .receipts import begin_attempt, finish_attempt, record_item

_THREAD_CONTROLS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)


def _initialize_worker() -> None:
    # Parent handles cooperative interruption; let a bounded current cache
    # publication finish rather than leaving a killed writer's reservation.
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def _error_record(envelope: dict[str, object]) -> str:
    try:
        return canonical_json(envelope)
    except (TypeError, ValueError):
        # Do not discard the original reason or silently drop rich diagnostics.
        return canonical_json(
            {
                "reason_code": envelope.get("reason_code"),
                "detail": str(envelope.get("detail", "")),
                "diagnostics_representation": "repr_non_json_envelope",
                "original_envelope_repr": repr(envelope),
            }
        )


def _failed(index: int, item: LRABatchItem, error: BaseException) -> LRABatchItemResult:
    return LRABatchItemResult(
        index,
        item.item_id,
        item.request_sha256,
        "failed",
        canonical_error=_error_record(
            {
                "reason_code": "lra_batch_worker_failed",
                "detail": str(error),
                "exception_type": f"{type(error).__module__}.{type(error).__qualname__}",
            }
        ),
    )


def _calculate_item(
    index: int, item: LRABatchItem, input_root: Path, cache_root: Path
) -> LRABatchItemResult:
    # Lazy import keeps spawned workers' numerical imports after startup with
    # the already validated inherited environment. No equations live here.
    from ..execution.cache import run_lra_cached

    try:
        cached = run_lra_cached(
            item.payload(), input_root=input_root, cache_root=cache_root
        )
        return LRABatchItemResult(
            index,
            item.item_id,
            item.request_sha256,
            "completed",
            cached.product,
            cached.cache_key,
            cached.cache_hit,
        )
    except LRARefusal as error:
        return LRABatchItemResult(
            index,
            item.item_id,
            item.request_sha256,
            "refused",
            canonical_error=_error_record(error.as_dict()),
        )
    except Exception as error:
        return _failed(index, item, error)


def _admit(
    items: Iterable[LRABatchItem], limits: LRABatchLimits
) -> tuple[LRABatchItem, ...]:
    declared = tuple(islice(items, limits.max_items + 1))
    if not declared or len(declared) > limits.max_items:
        raise LRARefusal(
            "invalid_lra_batch_size",
            "Batch must contain between 1 and max_items requests",
        )
    if any(not isinstance(item, LRABatchItem) for item in declared):
        raise LRARefusal("invalid_lra_batch_item", "Every item must be LRABatchItem")
    if len({item.item_id for item in declared}) != len(declared):
        raise LRARefusal("duplicate_lra_batch_item_id", "Batch item IDs must be unique")
    if limits.max_workers > (os.cpu_count() or 1):
        raise LRARefusal(
            "lra_batch_worker_budget_exceeded",
            "Worker count exceeds available CPU count",
        )
    missing = [name for name in _THREAD_CONTROLS if os.environ.get(name) != "1"]
    if missing:
        raise LRARefusal(
            "lra_batch_thread_budget_required",
            "Set numerical thread controls to 1 before spawning workers: "
            + ", ".join(missing),
        )
    return declared


def run_lra_batch(
    items: Iterable[LRABatchItem],
    *,
    input_root: Path,
    cache_root: Path,
    report_root: Path,
    limits: LRABatchLimits | None = None,
    cancel_requested: Callable[[], bool] | None = None,
) -> LRABatchResult:
    """Run bounded independent requests; resume by calling the verified cache.

    The report directory must be new for each attempt. Cooperative cancellation
    stops submission and drains at most max_workers submitted model calls; it
    cannot preempt an individual calculation. Hard-kill recovery never deletes
    another process's cache locks or pending publication evidence.
    """
    limits = limits if limits is not None else LRABatchLimits()
    declared = _admit(items, limits)
    input_root, cache_root, report_root = (
        input_root.absolute(),
        cache_root.absolute(),
        report_root.absolute(),
    )
    if report_root == cache_root:
        raise LRARefusal(
            "invalid_lra_batch_report_path",
            "Attempt reports and cache need distinct roots",
        )
    identity = [
        {"item_id": item.item_id, "request_sha256": item.request_sha256}
        for item in declared
    ]
    batch_sha256 = hashlib.sha256(canonical_json(identity).encode()).hexdigest()
    begin_attempt(report_root, declared, batch_sha256, limits, input_root, cache_root)
    outcomes: dict[int, LRABatchItemResult] = {}
    pending: dict[Future[LRABatchItemResult], int] = {}
    waiting = list(range(len(declared)))
    interrupted = False
    reason: str | None = None

    def cancellation() -> bool:
        nonlocal interrupted, reason
        if not interrupted and cancel_requested is not None:
            try:
                if cancel_requested():
                    interrupted, reason = True, "cancellation_requested"
            except Exception as error:
                interrupted, reason = True, f"cancellation_check_failed: {error}"
        return interrupted

    with ProcessPoolExecutor(
        max_workers=limits.max_workers,
        mp_context=multiprocessing.get_context("spawn"),
        initializer=_initialize_worker,
    ) as executor:
        while pending or (waiting and not interrupted):
            try:
                cancellation()
                while not interrupted and waiting and len(pending) < limits.max_workers:
                    active = {
                        declared[index].request_sha256 for index in pending.values()
                    }
                    # Avoid knowingly competing for an identical cache request;
                    # later independent inputs can still fill free worker slots.
                    position = next(
                        (
                            index
                            for index in waiting
                            if declared[index].request_sha256 not in active
                        ),
                        None,
                    )
                    if position is None:
                        break
                    waiting.remove(position)
                    try:
                        future = executor.submit(
                            _calculate_item,
                            position,
                            declared[position],
                            input_root,
                            cache_root,
                        )
                    except Exception as error:
                        outcome = _failed(position, declared[position], error)
                        outcomes[position] = outcome
                        record_item(report_root, outcome)
                        interrupted, reason = True, "executor_submission_failed"
                        break
                    pending[future] = position
                if not pending:
                    break
                finished, _ = wait(pending, timeout=0.25, return_when=FIRST_COMPLETED)
                for future in sorted(finished, key=lambda value: pending[value]):
                    index = pending[future]
                    try:
                        # A transported worker BaseException is data here. Do
                        # not re-raise it into the parent's SIGINT drain path.
                        remote_error = future.exception()
                        outcome = (
                            _failed(index, declared[index], remote_error)
                            if remote_error is not None
                            else future.result()
                        )
                    except Exception as error:
                        outcome = _failed(index, declared[index], error)
                    record_item(report_root, outcome)
                    outcomes[index] = outcome
                    pending.pop(future)
            except KeyboardInterrupt:
                interrupted, reason = True, "keyboard_interrupt"
    for index, item in enumerate(declared):
        if index not in outcomes:
            outcome = LRABatchItemResult(
                index,
                item.item_id,
                item.request_sha256,
                "not_run" if index in waiting else "unobserved",
                canonical_error=canonical_json(
                    {"reason_code": "lra_batch_interrupted", "detail": reason}
                ),
            )
            outcomes[index] = outcome
            record_item(report_root, outcome)
    result = LRABatchResult(
        batch_sha256,
        report_root,
        tuple(outcomes[index] for index in range(len(declared))),
        interrupted,
        reason,
    )
    finish_attempt(result)
    return result
