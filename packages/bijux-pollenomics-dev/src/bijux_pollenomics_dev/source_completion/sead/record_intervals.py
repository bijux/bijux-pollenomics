"""Write the retained SEAD record-interval review through a confined owner CLI."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from bijux_pollenomics.collection.sources.sead.evidence.review.interval_sets import (
    write_sead_interval_set_review,
)


def run(repository: Path, output: Path) -> dict[str, Any]:
    """Use the core writer only with an absent destination below artifacts."""
    repository = repository.resolve(strict=True)
    if not repository.is_dir():
        raise ValueError("Repository must be a directory")
    if output.is_symlink():
        raise ValueError("SEAD interval review destination must be absent")
    destination = output.resolve()
    artifacts = repository / "artifacts"
    if (
        destination == artifacts
        or not destination.is_relative_to(artifacts)
        or destination.exists()
    ):
        raise ValueError("Absent repository artifact destination required")
    return write_sead_interval_set_review(repository / "data", destination)


def main(argv: list[str] | None = None) -> int:
    """Run the source-bound SEAD interval-set writer."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
