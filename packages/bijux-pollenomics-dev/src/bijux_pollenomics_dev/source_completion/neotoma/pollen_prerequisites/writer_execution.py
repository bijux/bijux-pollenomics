"""Confine source-bound pollen prerequisite outputs to repository artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

RAW = Path("data/neotoma/raw/neotoma_pollen_dataset_downloads")
RELATIONAL = Path("data/neotoma/relational")


def arguments(argv: list[str] | None = None) -> tuple[Path, Path]:
    """Parse required repository and absent output paths for a source writer."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parsed = parser.parse_args(argv)
    return parsed.repository, parsed.output


def confined_paths(repository: Path, output: Path) -> tuple[Path, Path, Path, Path]:
    """Check source roots and one absent output without altering any source."""
    repository = repository.resolve(strict=True)
    artifacts = repository / "artifacts"
    if (
        artifacts.is_symlink()
        or not artifacts.is_dir()
        or artifacts.resolve() != artifacts
    ):
        raise ValueError("repository artifact root is not a real directory")
    raw, relational = repository / RAW, repository / RELATIONAL
    for root in (raw, relational):
        if root.is_symlink() or not root.is_dir() or root.resolve() != root:
            raise ValueError("Neotoma source root is not a real repository directory")
    if output.is_symlink():
        raise ValueError("Neotoma output may not be a symlink")
    destination = output.resolve()
    for ancestor in output.absolute().parents:
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("Neotoma output ancestor may not be a symlink")
    else:
        raise ValueError("Neotoma output lies outside repository")
    if (
        destination == artifacts
        or not destination.is_relative_to(artifacts)
        or destination.exists()
    ):
        raise ValueError("absent repository artifact file required")
    return repository, raw, relational, destination


def retained_object(repository: Path, relative: Path) -> dict[str, Any]:
    """Read one real repository-bound Neotoma prerequisite JSON object."""
    source = repository / relative
    if source.is_symlink() or not source.is_file() or source.resolve() != source:
        raise ValueError("retained Neotoma prerequisite is not a real repository file")
    value = json.loads(source.read_bytes())
    if not isinstance(value, dict):
        raise ValueError("retained Neotoma prerequisite must be an object")
    return value


def write_new(destination: Path, content: bytes) -> None:
    """Create a new artifact file without replacing an existing output."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream:
        stream.write(content)
