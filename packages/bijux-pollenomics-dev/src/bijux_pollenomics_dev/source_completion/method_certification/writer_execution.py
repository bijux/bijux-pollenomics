"""Invoke a retained numerical replay at an absent repository artifact directory."""

from __future__ import annotations

from pathlib import Path
import runpy
import sys


def replay_to_artifacts(repository: Path, output: Path, source_relative: Path) -> None:
    """Preserve the replay's CLI and algorithm while confining its output."""
    repository = repository.resolve(strict=True)
    source = repository / source_relative
    artifacts = repository / "artifacts"
    if (
        not source.is_file()
        or source.is_symlink()
        or source.resolve() != source
        or not source.is_relative_to(repository / "docs/report/method-certification")
        or not artifacts.is_dir()
        or artifacts.is_symlink()
    ):
        raise ValueError("constructed covariance source or artifact root is invalid")
    if output.is_symlink():
        raise ValueError("constructed covariance output may not be a symlink")
    destination = output.resolve()
    for ancestor in output.absolute().parents:
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError(
                "constructed covariance output ancestor may not be a symlink"
            )
    else:
        raise ValueError("constructed covariance output lies outside repository")
    if (
        destination == artifacts
        or not destination.is_relative_to(artifacts)
        or destination.exists()
    ):
        raise ValueError("absent repository artifact directory required")
    original = sys.argv
    try:
        sys.argv = [
            str(source),
            "--repository",
            str(repository),
            "--output",
            str(destination),
        ]
        runpy.run_path(str(source), run_name="__main__")
    finally:
        sys.argv = original
