from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from ...core.owned_tree import (
    build_staging_output_dir,
    remove_output_tree,
    replace_output_tree,
)

ReportT = TypeVar("ReportT")

__all__ = ["build_staging_output_dir", "collect_into_staging_dir", "reset_output_dir"]


def reset_output_dir(path: Path) -> None:
    """Remove one generated source directory so recollection is deterministic."""
    remove_output_tree(path)


def collect_into_staging_dir(
    final_output_root: Path,
    collect: Callable[[Path], ReportT],
) -> ReportT:
    """Collect into a staging directory and swap it into place only after success."""
    final_output_root = Path(final_output_root)
    staging_output_root = build_staging_output_dir(final_output_root)
    reset_output_dir(staging_output_root)
    staging_output_root.mkdir(parents=True, exist_ok=True)
    try:
        report = collect(staging_output_root)
        replace_output_tree(
            final_output_root=final_output_root,
            staging_output_root=staging_output_root,
        )
        return report
    except Exception:
        reset_output_dir(staging_output_root)
        raise
