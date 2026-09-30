from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import shutil
from typing import TypeVar

from ...core.owned_tree import (
    build_staging_output_dir,
    remove_output_tree,
    replace_output_tree,
)

T = TypeVar("T")

__all__ = [
    "build_staging_output_dir",
    "publish_into_staging_dir",
    "reset_output_dir",
    "retain_existing_report_files",
]


def reset_output_dir(path: Path) -> None:
    """Remove one generated report directory so publication stays deterministic."""
    remove_output_tree(path)


def retain_existing_report_files(existing_root: Path, staging_root: Path) -> None:
    """Carry files outside the current publisher's output into its staged tree."""
    if not existing_root.is_dir():
        return
    for source in existing_root.rglob("*"):
        relative = source.relative_to(existing_root)
        destination = staging_root / relative
        if source.is_symlink():
            raise ValueError(f"report tree contains an unsupported symlink: {relative}")
        if source.is_dir():
            if destination.exists() and not destination.is_dir():
                raise ValueError(
                    f"report tree has a file-directory collision: {relative}"
                )
            continue
        if not source.is_file():
            raise ValueError(f"report tree contains an unsupported entry: {relative}")
        if destination.exists():
            if destination.is_symlink() or not destination.is_file():
                raise ValueError(
                    f"report tree has a file-directory collision: {relative}"
                )
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


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
