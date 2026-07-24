from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from ...core.owned_tree import (
    build_staging_output_dir,
    remove_output_tree,
    replace_output_tree,
)

T = TypeVar("T")

__all__ = ["build_staging_output_dir", "publish_into_staging_dir", "reset_output_dir"]


def reset_output_dir(path: Path) -> None:
    """Remove one generated report directory so publication stays deterministic."""
    remove_output_tree(path)


def publish_into_staging_dir(
    final_output_root: Path, publish: Callable[[Path], T]
) -> T:
    """Publish into a staging directory and swap it into place only after success."""
    final_output_root = Path(final_output_root)
    staging_output_root = build_staging_output_dir(final_output_root)
    reset_output_dir(staging_output_root)
    staging_output_root.mkdir(parents=True, exist_ok=True)
    try:
        result = publish(staging_output_root)
        replace_output_tree(
            final_output_root=final_output_root,
            staging_output_root=staging_output_root,
        )
        return result
    except Exception:
        reset_output_dir(staging_output_root)
        raise
