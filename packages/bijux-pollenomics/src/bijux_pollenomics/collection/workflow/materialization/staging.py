"""Publish completed collector callbacks without borrowing another operation's tree."""

from __future__ import annotations

from collections.abc import Callable
import os
from pathlib import Path
from typing import TypeVar

from ....core.filesystem.callback_publication import publish_callback_tree
from ....core.filesystem.replacement import publish_owned_replacement
from ....core.owned_tree import (
    build_recovery_output_dir,
    build_staging_output_dir,
    remove_output_tree,
)

ReportT = TypeVar("ReportT")

__all__ = ["build_staging_output_dir", "collect_into_staging_dir", "reset_output_dir"]


def reset_output_dir(path: Path) -> None:
    """Remove one generated source directory so recollection is deterministic."""
    remove_output_tree(path)


def _require_no_legacy_recovery(final: Path) -> None:
    recovery = build_recovery_output_dir(final)
    if os.path.lexists(recovery):
        raise FileExistsError(f"Prior output recovery requires review: {recovery}")


def collect_into_staging_dir(
    final_output_root: Path,
    collect: Callable[[Path], ReportT],
) -> ReportT:
    """Publish one complete private candidate while retaining refused evidence.

    Legacy fixed recovery requires review before invoking the collector. A fixed
    staging entry belongs to its existing owner and is never used or removed.
    Callback generation retains its existing uncapped trusted-output contract;
    exact completed namespace bounds govern subsequent attachment checks.
    """
    final = Path(final_output_root).absolute()
    _require_no_legacy_recovery(final)
    return publish_callback_tree(
        final,
        collect,
        namespace="collection-publication",
        label="Collection",
        validate=lambda _: _require_no_legacy_recovery(final),
        _replace=publish_owned_replacement,
    )
