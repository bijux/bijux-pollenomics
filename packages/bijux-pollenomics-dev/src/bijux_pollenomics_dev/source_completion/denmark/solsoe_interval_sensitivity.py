"""Rebuild the retained Solsø interval-support development comparison."""

from __future__ import annotations

import argparse
from pathlib import Path
import runpy
import sys

PRODUCER = Path(
    "docs/report/countries/denmark/solsoe-source-lineage/"
    "legacyage-interval-sensitivity/replay.py"
)


def run(repository: Path, output: Path) -> None:
    """Freeze retained support before scoring the previously exposed observations."""
    repository = repository.resolve(strict=True)
    source = repository / PRODUCER
    if not source.is_file() or source.is_symlink() or source.resolve() != source:
        raise ValueError("Solsø interval producer is not a real repository file")
    if output.is_symlink():
        raise ValueError("Solsø output may not be a symlink")
    destination = output.resolve()
    artifacts = repository / "artifacts"
    if artifacts.is_symlink() or not artifacts.is_dir():
        raise ValueError("repository artifact root must be a real directory")
    for ancestor in output.absolute().parents:
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("output ancestor may not be a symlink")
    else:
        raise ValueError("output lies outside repository")
    if (
        destination == artifacts
        or not destination.is_relative_to(artifacts)
        or destination.exists()
    ):
        raise ValueError("absent repository artifact destination required")
    original = sys.argv
    try:
        for stage in ("freeze", "score"):
            sys.argv = [
                str(source),
                stage,
                "--repository",
                str(repository),
                "--output",
                str(destination),
            ]
            runpy.run_path(str(source), run_name="__main__")
    finally:
        sys.argv = original


def main(argv: list[str] | None = None) -> int:
    """Rebuild the retained Solsø interval-support development comparison."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
