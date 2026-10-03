"""Freeze existing Norway-excluded author-target predictions at supported ages."""

from __future__ import annotations

import argparse
from pathlib import Path
import runpy
import sys

REPLAY = Path(
    "docs/report/regions/nordic/dalmutladdo-author-target-age-interval/replay.py"
)


def run(repository: Path, output: Path) -> None:
    """Invoke the retained freeze stage without entering its scoring route."""
    repository = repository.resolve(strict=True)
    if output.is_symlink():
        raise ValueError("Dalmutladdo freeze output may not be a symlink")
    destination = output.resolve()
    artifacts = repository / "artifacts"
    if (
        destination == artifacts
        or not destination.is_relative_to(artifacts)
        or destination.exists()
    ):
        raise ValueError("Absent repository artifact destination required")
    replay = repository / REPLAY
    if replay.is_symlink() or not replay.is_file() or replay.resolve() != replay:
        raise ValueError("Dalmutladdo replay is not a regular repository file")
    original = sys.argv
    try:
        sys.argv = [
            str(replay),
            "freeze",
            "--repository",
            str(repository),
            "--output",
            str(destination),
        ]
        runpy.run_path(str(replay), run_name="__main__")
    finally:
        sys.argv = original


def main(argv: list[str] | None = None) -> int:
    """Freeze existing Norway-excluded author-target predictions at supported ages."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
