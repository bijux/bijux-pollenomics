"""Partitioned, evidence-bound report rebuild verification."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from .contracts import ReportRebuildError

if TYPE_CHECKING:
    from .workflow import (
        assemble_partition_lane,
        build_owner_output,
        build_partition,
        build_partition_plan,
        verify_partitioned_rebuild,
    )

__all__ = [
    "ReportRebuildError",
    "assemble_partition_lane",
    "build_owner_output",
    "build_partition",
    "build_partition_plan",
    "verify_partitioned_rebuild",
]


def __getattr__(name: str) -> Any:
    """Load execution only when a caller requests a workflow entry point."""
    if name not in __all__ or name == "ReportRebuildError":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(".workflow", __name__), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
