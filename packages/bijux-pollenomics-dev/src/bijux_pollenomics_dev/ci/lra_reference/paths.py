"""Explicit local input and exclusive output boundaries for reference jobs."""

from __future__ import annotations

import os
from pathlib import Path

from .contracts import ReferenceRefusal


def local_path(value: Path) -> Path:
    """Normalize lexical spelling while refusing symlinks before normalization."""
    raw = value if value.is_absolute() else Path.cwd() / value
    if any(parent.is_symlink() for parent in (raw, *raw.parents)):
        raise ReferenceRefusal(f"Symlink input/output paths are not supported: {value}")
    return Path(os.path.abspath(raw))


def exclusive_outputs(outputs: tuple[Path, ...], inputs: tuple[Path, ...]) -> None:
    """Refuse existing output paths and overlap with reference inputs."""
    for output in outputs:
        if output.exists():
            raise ReferenceRefusal(f"Output already exists: {output}")
        for other in (*inputs, *(item for item in outputs if item != output)):
            if (
                output == other
                or output.is_relative_to(other)
                or other.is_relative_to(output)
            ):
                raise ReferenceRefusal("Reference inputs and outputs must be disjoint")
