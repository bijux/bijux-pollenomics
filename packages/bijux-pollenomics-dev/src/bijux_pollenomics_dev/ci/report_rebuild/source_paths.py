"""Validate repository source paths without importing report execution."""

from __future__ import annotations

from pathlib import Path
import stat

from .contracts import ReportRebuildError, require_relative_path


def safe_source_file(repository: Path, relative: str, label: str) -> Path:
    """Require a regular repository file reached only through real directories."""
    parts = require_relative_path(relative, label).split("/")
    path = repository
    try:
        for component in parts[:-1]:
            path /= component
            if not stat.S_ISDIR(path.lstat().st_mode):
                raise ReportRebuildError(f"{label} has a non-real ancestor: {path}")
        path /= parts[-1]
        if not stat.S_ISREG(path.lstat().st_mode):
            raise ReportRebuildError(f"{label} is not a regular file: {path}")
    except OSError as error:
        raise ReportRebuildError(f"{label} is unreadable: {path}") from error
    if not path.resolve().is_relative_to(repository):
        raise ReportRebuildError(f"{label} escapes the repository")
    return path
