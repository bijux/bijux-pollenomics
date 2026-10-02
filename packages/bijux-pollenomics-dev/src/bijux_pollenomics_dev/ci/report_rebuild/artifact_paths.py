"""Confine configured report-owner outputs to absent artifact paths."""

from __future__ import annotations

from pathlib import Path
import stat

from .contracts import ReportRebuildError


def require_absent_artifact_output(repository: Path, output: Path) -> Path:
    """Require a new output beneath real repository artifact directories."""
    if ".." in output.parts:
        raise ReportRebuildError("configured owner output path is not canonical")
    output = output.absolute()
    artifact_root = repository / "artifacts"
    if (
        not output.is_relative_to(artifact_root)
        or output == artifact_root
        or not output.resolve().is_relative_to(artifact_root)
    ):
        raise ReportRebuildError(
            "configured owner output must be below repository artifacts"
        )
    if output.exists() or output.is_symlink():
        raise ReportRebuildError("configured owner output must be absent")
    parent = output.parent
    while parent != repository:
        if not stat.S_ISDIR(parent.lstat().st_mode):
            raise ReportRebuildError("configured owner output has a non-real ancestor")
        parent = parent.parent
    return output
