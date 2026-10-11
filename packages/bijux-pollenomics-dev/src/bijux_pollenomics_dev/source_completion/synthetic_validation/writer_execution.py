"""Keep constructed-case owner outputs inside absent repository artifacts."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path


def run_writer(repository: Path, output: Path, writer: Callable[[], int]) -> int:
    """Call an existing report CLI after checking its exact source and destination."""
    repository = repository.resolve(strict=True)
    artifacts = repository / "artifacts"
    source = Path(writer.__code__.co_filename)
    if (
        artifacts.is_symlink()
        or not artifacts.is_dir()
        or source.is_symlink()
        or not source.is_file()
        or source.resolve() != source
        or not source.is_relative_to(repository / "packages/bijux-pollenomics-dev/src")
    ):
        raise ValueError("constructed-case writer source or artifact root is invalid")
    if output.is_symlink():
        raise ValueError("constructed-case output may not be a symlink")
    destination = output.resolve()
    for ancestor in output.absolute().parents:
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("constructed-case output ancestor may not be a symlink")
    else:
        raise ValueError("constructed-case output lies outside repository")
    if not destination.is_relative_to(artifacts) or destination.exists():
        raise ValueError("absent repository artifact file required")
    return writer()
