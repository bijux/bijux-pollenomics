"""Publish complete reports through the shared completed-callback owner."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import shutil
from typing import TypeVar

from ...core.filesystem import callback_publication
from ...core.filesystem.callback_publication import (
    publish_callback_tree,
)
from ...core.filesystem.callback_publication import (
    seal_completed_callback_tree as _completed_report_tree,
)
from ...core.filesystem.replacement import publish_owned_replacement
from ...core.owned_tree import build_staging_output_dir, remove_output_tree

T = TypeVar("T")

# Preserve diagnostic access to the one shared process registry and context.
_CALLBACK_WORKSPACE = callback_publication._CALLBACK_WORKSPACE
_WORKSPACES = callback_publication._WORKSPACES

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
    final_output_root: Path,
    publish: Callable[[Path], T],
    *,
    validate: Callable[[Path], object] | None = None,
) -> T:
    """Publish a trusted, completed Path callback without borrowing another tree.

    Callback generation is not pre-budgeted. Its completed ordinary namespace
    supplies exact seals and finite bounds for subsequent attachment checks.
    Prior and refused trees remain in private recovery; no cleanup deletes them.
    Optional semantic validation runs before attachment and on final readback.
    """
    return publish_callback_tree(
        final_output_root,
        publish,
        namespace="report-publication",
        label="Report",
        validate=validate,
        _replace=publish_owned_replacement,
        _seal=_completed_report_tree,
    )
