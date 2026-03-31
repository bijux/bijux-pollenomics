from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable, TypeVar


T = TypeVar("T")


def reset_output_dir(path: Path) -> None:
    """Remove one generated report directory so publication stays deterministic."""
    if path.exists():
        shutil.rmtree(path)


def build_staging_output_dir(final_output_root: Path) -> Path:
    """Build the sibling staging directory used for safe report publication."""
    final_output_root = Path(final_output_root)
    return final_output_root.parent / f".{final_output_root.name}.tmp"


def publish_into_staging_dir(final_output_root: Path, publish: Callable[[Path], T]) -> T:
    """Publish into a staging directory and swap it into place only after success."""
    final_output_root = Path(final_output_root)
    staging_output_root = build_staging_output_dir(final_output_root)
    reset_output_dir(staging_output_root)
    staging_output_root.mkdir(parents=True, exist_ok=True)
    try:
        result = publish(staging_output_root)
        reset_output_dir(final_output_root)
        staging_output_root.replace(final_output_root)
        return result
    except Exception:
        reset_output_dir(staging_output_root)
        raise
