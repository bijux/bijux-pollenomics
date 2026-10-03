"""Publish the governed Neotoma relational ownership summary."""

from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import io
from pathlib import Path
import runpy
import sys

VERIFIER = Path("docs/report/source-relations/neotoma/verify_ownership.py")


def run(repository: Path, output: Path) -> None:
    """Capture the existing verifier's JSON without changing its validation."""
    repository = repository.resolve(strict=True)
    if output.is_symlink():
        raise ValueError("Neotoma summary output may not be a symlink")
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
        raise ValueError("Neotoma verifier is not a regular repository file")
    original = sys.argv
    stream = io.StringIO()
    try:
        sys.argv = [
            str(verifier),
            "--source-root",
            str(repository / "data/neotoma/relational"),
        ]
        script = runpy.run_path(str(verifier), run_name="_neotoma_ownership_verifier")
        with redirect_stdout(stream):
            script["main"]()
    finally:
        sys.argv = original
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(stream.getvalue(), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Publish the governed Neotoma relational ownership summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
