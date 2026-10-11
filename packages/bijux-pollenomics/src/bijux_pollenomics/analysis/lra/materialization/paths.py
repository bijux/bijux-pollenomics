"""Shared admission output containment without source-specific assumptions."""

from __future__ import annotations

from collections.abc import Sequence
import os
from pathlib import Path


def checked_output_directory(path: Path, *, input_roots: Sequence[Path]) -> Path:
    """Refuse source overlap and symlink traversal before creating output."""
    absolute = path.absolute()
    if any(parent.is_symlink() for parent in (absolute, *absolute.parents)):
        raise ValueError("Admission output must not traverse symlinks")
    destination = Path(os.path.abspath(absolute))
    for root in input_roots:
        if destination.is_relative_to(root) or root.is_relative_to(destination):
            raise ValueError("Admission output must not overlap a source authority")
    if destination.exists():
        raise FileExistsError(destination)
    return destination
