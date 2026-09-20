"""Normalize operational batch states into a closed scientific terminal ledger."""

from __future__ import annotations

import json

from ....lra.api import LRABatchItemResult
from ...contracts import Fold, ValidationRefusal, canonical_json
from ..configuration import identity


def _batch_detail(
    item: LRABatchItemResult,
    *,
    projection: bool = False,
    projection_error: dict[str, str] | None = None,
) -> str:
    error: object = None
    if item.canonical_error is not None:
        try:
            error = json.loads(item.canonical_error)
        except (TypeError, ValueError):
            error = item.canonical_error
    detail: dict[str, object] = {
        "batch_item_status": item.item_status,
        "operational_error": error,
        "projection_interrupted": projection,
    }
    if projection_error is not None:
        detail["projection_error"] = projection_error
    return canonical_json(detail)


def batch_refusal(fold: Fold, item: LRABatchItemResult) -> dict[str, object]:
    """Retain an operational non-completion as a value-free scientific refusal."""
    return {
        "fold_id": fold.fold_id,
        "record_ids": fold.test_record_ids,
        "status": "refused",
        "reason_code": "local_reconstruction_incomplete",
        "detail": _batch_detail(item),
        "batch_item_id": item.item_id,
    }


def projection_refusal(
    fold: Fold, item: LRABatchItemResult, error: Exception
) -> dict[str, object]:
    """Bind a post-completion projection refusal to its raw completed item."""
    reason = getattr(error, "reason_code", "local_prediction_refused")
    return {
        "fold_id": fold.fold_id,
        "record_ids": fold.test_record_ids,
        "status": "refused",
        "reason_code": reason,
        "detail": _batch_detail(
            item,
            projection_error={"reason_code": reason, "detail": str(error)},
        ),
        "batch_item_id": item.item_id,
    }


def not_run(
    fold: Fold,
    *,
    item: LRABatchItemResult | None = None,
    projection: bool = False,
) -> dict[str, object]:
    """Retain a genuine interruption without fabricating a later completion."""
    row: dict[str, object] = {
        "fold_id": fold.fold_id,
        "record_ids": fold.test_record_ids,
        "status": "not_run",
        "reason_code": "experiment_interrupted",
    }
    if item is not None:
        row["detail"] = _batch_detail(item, projection=projection)
        row["batch_item_id"] = item.item_id
    return row


def validate_terminals(
    folds: tuple[Fold, ...],
    predictions: list[dict[str, object]],
    failures: list[dict[str, object]],
) -> bool:
    """Require one terminal per fold and a deterministic interruption suffix."""
    ordered = tuple(fold.fold_id for fold in folds)
    terminal: dict[str, str] = {}
    for row in predictions:
        fold_id = identity(row["fold_id"])
        if fold_id in terminal:
            raise ValidationRefusal("incomplete_local_accounting", fold_id)
        terminal[fold_id] = "predicted"
    for row in failures:
        fold_id = identity(row["fold_id"])
        status = identity(row["status"])
        if fold_id in terminal or status not in {"refused", "not_run"}:
            raise ValidationRefusal("incomplete_local_accounting", fold_id)
        terminal[fold_id] = status
    first = next(
        (
            index
            for index, fold_id in enumerate(ordered)
            if terminal.get(fold_id) == "not_run"
        ),
        None,
    )
    if set(terminal) != set(ordered) or (
        first is not None
        and any(terminal[fold_id] != "not_run" for fold_id in ordered[first:])
    ):
        raise ValidationRefusal(
            "incomplete_local_accounting", "Require one deterministic terminal per fold"
        )
    return first is not None
