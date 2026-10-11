"""Publish the pinned LOVE example parameter comparison from its verifier."""

from __future__ import annotations

import argparse
from pathlib import Path
import runpy
import sys

VERIFIER = Path("docs/report/method-certification/love-paper-correspondence/verify.py")


def run(repository: Path, output: Path) -> None:
    """Invoke the exact governed comparison writer with an absent output."""
    repository = repository.resolve(strict=True)
    if output.is_symlink():
        raise ValueError("LOVE correspondence output may not be a symlink")
    destination = output.resolve()
    artifacts = repository / "artifacts"
    if (
        destination == artifacts
        or not destination.is_relative_to(artifacts)
        or destination.exists()
    ):
        raise ValueError("Absent repository artifact destination required")
    verifier = repository / VERIFIER
    if (
        verifier.is_symlink()
        or not verifier.is_file()
        or verifier.resolve() != verifier
    ):
        raise ValueError(
            "LOVE correspondence verifier is not a regular repository file"
        )
    original = sys.argv
    try:
        sys.argv = [
            str(verifier),
            "--repository",
            str(repository),
            "--output",
            str(destination),
        ]
        runpy.run_path(str(verifier), run_name="__main__")
    finally:
        sys.argv = original


def main(argv: list[str] | None = None) -> int:
    """Parse command-line inputs and publish the pinned LOVE example parameter comparison from its verifier."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
