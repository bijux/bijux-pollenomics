"""Filesystem replacement primitives for complete runtime-owned trees."""

from __future__ import annotations

from pathlib import Path
import shutil

__all__ = [
    "build_recovery_output_dir",
    "build_staging_output_dir",
    "remove_output_tree",
    "replace_output_tree",
]


def remove_output_tree(path: Path) -> None:
    """Remove one runtime-owned file or directory tree when it exists."""
    path = Path(path)
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def build_staging_output_dir(final_output_root: Path) -> Path:
    """Return the hidden sibling used to construct a complete candidate tree."""
    final_output_root = Path(final_output_root)
    return final_output_root.parent / f".{final_output_root.name}.staging"


def build_recovery_output_dir(final_output_root: Path) -> Path:
    """Return the hidden sibling that protects the prior governed tree."""
    final_output_root = Path(final_output_root)
    return final_output_root.parent / f".{final_output_root.name}.recovery"


def replace_output_tree(*, final_output_root: Path, staging_output_root: Path) -> None:
    """Replace one owned tree while restoring its predecessor on rename failure."""
    final_output_root = Path(final_output_root)
    staging_output_root = Path(staging_output_root)
    recovery_output_root = build_recovery_output_dir(final_output_root)
    remove_output_tree(recovery_output_root)

    prior_state_exists = final_output_root.exists()
    if prior_state_exists:
        final_output_root.replace(recovery_output_root)

    try:
        staging_output_root.replace(final_output_root)
    except Exception:
        if prior_state_exists and recovery_output_root.exists():
            recovery_output_root.replace(final_output_root)
        raise
    else:
        remove_output_tree(recovery_output_root)
