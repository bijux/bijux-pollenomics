"""Immutable identities and operational outcomes for bounded LRA batches."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Literal, cast

from ..engine.errors import LRARefusal
from ..outputs.publication import LRAProduct


def canonical_json(value: object) -> str:
    """Encode finite JSON with a stable object-key order."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


@dataclass(frozen=True, slots=True, init=False)
class LRABatchItem:
    """An owned JSON request, without claiming scientific input admission."""

    item_id: str
    canonical_request: str
    request_sha256: str

    def __init__(self, item_id: str, payload: Mapping[str, object]) -> None:
        if not isinstance(item_id, str) or not item_id.strip():
            raise LRARefusal(
                "invalid_lra_batch_item_id", "A nonempty item ID is required"
            )
        try:
            encoded = canonical_json(dict(payload))
        except (TypeError, ValueError, OverflowError) as exc:
            raise LRARefusal("invalid_lra_batch_payload", str(exc)) from exc
        object.__setattr__(self, "item_id", item_id)
        object.__setattr__(self, "canonical_request", encoded)
        object.__setattr__(
            self, "request_sha256", hashlib.sha256(encoded.encode()).hexdigest()
        )

    def payload(self) -> dict[str, Any]:
        """Return a fresh request for the existing host cache facade."""
        return cast(dict[str, Any], json.loads(self.canonical_request))


@dataclass(frozen=True, slots=True)
class LRABatchLimits:
    """At most max_workers submitted tasks and max_items declared inputs."""

    max_workers: int = 1
    max_items: int = 1000

    def __post_init__(self) -> None:
        for name in ("max_workers", "max_items"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise LRARefusal(
                    "invalid_lra_batch_limit", f"{name} must be a positive integer"
                )


ItemStatus = Literal["completed", "refused", "failed", "not_run", "unobserved"]


@dataclass(frozen=True, slots=True)
class LRABatchItemResult:
    """One observed outcome; missing products cannot imply successful work."""

    index: int
    item_id: str
    request_sha256: str
    item_status: ItemStatus
    product: LRAProduct | None = None
    cache_key: str | None = None
    cache_hit: bool | None = None
    canonical_error: str | None = None

    def as_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "schema_version": "lra-batch-item.v1",
            "index": self.index,
            "item_id": self.item_id,
            "request_sha256": self.request_sha256,
            "item_status": self.item_status,
            "scientific_acceptance": "not_evaluated",
        }
        if self.product is not None:
            result["product"] = {
                "directory": str(self.product.directory),
                "manifest_sha256": self.product.manifest_sha256,
                "scientific_content_sha256": self.product.scientific_content_sha256,
            }
            result["cache_key"] = self.cache_key
            result["cache_hit"] = self.cache_hit
        if self.canonical_error is not None:
            result["error"] = json.loads(self.canonical_error)
        return result


@dataclass(frozen=True, slots=True)
class LRABatchResult:
    """A finished attempt, possibly interrupted or containing explicit failures."""

    batch_sha256: str
    report_root: Path
    items: tuple[LRABatchItemResult, ...]
    interrupted: bool
    interruption_reason: str | None = None

    @property
    def all_items_completed(self) -> bool:
        return all(item.item_status == "completed" for item in self.items)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "lra-batch-result.v1",
            "batch_sha256": self.batch_sha256,
            "batch_status": "interrupted" if self.interrupted else "finished",
            "interruption_reason": self.interruption_reason,
            "all_items_completed": self.all_items_completed,
            "scientific_acceptance": "not_evaluated",
            "counts": {
                status: sum(item.item_status == status for item in self.items)
                for status in (
                    "completed",
                    "refused",
                    "failed",
                    "not_run",
                    "unobserved",
                )
            },
            "items": [item.as_dict() for item in self.items],
        }
