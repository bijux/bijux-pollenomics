"""Publish the source-bound empty governed-edge ledger."""

from __future__ import annotations

import argparse
from pathlib import Path
import runpy
import sys

REPLAY = Path("docs/report/propagation/governed-edge-ledger/replay.py")


def run(repository: Path, output: Path) -> None:
    """Call the retained two-file replay with its exact source paths."""
    repository = repository.resolve(strict=True)
    if output.is_symlink():
        raise ValueError("Governed-edge output may not be a symlink")
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
        raise ValueError("Governed-edge replay is not a regular repository file")
    original = sys.argv
    try:
        sys.argv = [str(replay), "--output-dir", str(destination)]
        runpy.run_path(str(replay), run_name="__main__")
    finally:
        sys.argv = original


def main(argv: list[str] | None = None) -> int:
    """Publish the source-bound empty governed-edge ledger."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
