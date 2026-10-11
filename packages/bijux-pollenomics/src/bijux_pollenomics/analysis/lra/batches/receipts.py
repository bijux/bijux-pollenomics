"""Small immutable attempt receipts built on host no-replace publication."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import tempfile

from ..engine.errors import LRARefusal
from ..outputs.atomic import publish_directory
from .models import (
    LRABatchItem,
    LRABatchItemResult,
    LRABatchLimits,
    LRABatchResult,
    canonical_json,
)


def _publish(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{path.name}.pending-", dir=path.parent))
    (stage / "receipt.json").write_text(
        canonical_json(payload) + "\n", encoding="utf-8"
    )
    publish_directory(stage, path)


def begin_attempt(
    report_root: Path,
    items: tuple[LRABatchItem, ...],
    batch_sha256: str,
    limits: LRABatchLimits,
    input_root: Path,
    cache_root: Path,
) -> None:
    """Claim a fresh attempt without replacing an older attempt's evidence."""
    _publish(
        report_root,
        {
            "schema_version": "lra-batch-attempt.v1",
            "event": "attempt_started",
            "completion_receipt": "summary/receipt.json",
            "batch_sha256": batch_sha256,
            "limits": asdict(limits),
            "numerical_threads_per_worker": 1,
            "input_root": str(input_root),
            "cache_root": str(cache_root),
            "items": [
                {
                    "item_id": item.item_id,
                    "request_sha256": item.request_sha256,
                    "request": item.payload(),
                }
                for item in items
            ],
            "resume_authority": "verified_cache_products_only_not_attempt_receipts",
        },
    )


def record_item(report_root: Path, result: LRABatchItemResult) -> None:
    path = report_root / "items" / f"{result.index:06d}"
    expected = canonical_json(result.as_dict()) + "\n"
    # A KeyboardInterrupt may arrive just after an atomic rename. Re-observing
    # that same future can retain the identical receipt without overwriting it.
    if path.exists():
        if (
            path.is_symlink()
            or (path / "receipt.json").is_symlink()
            or (path / "receipt.json").read_text(encoding="utf-8") != expected
        ):
            raise LRARefusal("lra_batch_receipt_conflict", str(path))
        return
    _publish(path, result.as_dict())


def finish_attempt(result: LRABatchResult) -> None:
    _publish(result.report_root / "summary", result.as_dict())
