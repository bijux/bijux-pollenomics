from __future__ import annotations

from pathlib import Path
import shutil
from typing import Callable

__all__ = ["build_staging_output_dir", "collect_into_staging_dir", "reset_output_dir"]


def reset_output_dir(path: Path) -> None:
    """Remove one generated source directory so recollection is deterministic."""
    if path.exists():
        shutil.rmtree(path)


def build_staging_output_dir(final_output_root: Path) -> Path:
    """Build the sibling staging directory used for safe source recollection."""
    final_output_root = Path(final_output_root)
    return final_output_root.parent / f".{final_output_root.name}.tmp"


def collect_into_staging_dir(
    final_output_root: Path,
    collect: Callable[[Path], object],
) -> object:
    """Collect into a staging directory and swap it into place only after success."""
    final_output_root = Path(final_output_root)
    staging_output_root = build_staging_output_dir(final_output_root)
    reset_output_dir(staging_output_root)
    staging_output_root.mkdir(parents=True, exist_ok=True)
    try:
        report = collect(staging_output_root)
        reset_output_dir(final_output_root)
        staging_output_root.replace(final_output_root)
        return report
    except Exception:
        reset_output_dir(staging_output_root)
        raise
