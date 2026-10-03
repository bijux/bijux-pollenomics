"""Publish the retained LandClim study-metadata bundle from repository inputs."""

from __future__ import annotations

import argparse
from pathlib import Path

from bijux_pollenomics_dev.essd_reproduction.study_inputs import (
    publish_study_input_products,
)


def run(repository: Path, output: Path) -> None:
    """Call the five-file publisher with its fixed, pinned workbook directory."""
    repository = repository.resolve(strict=True)
    if output.is_symlink():
        raise ValueError("LandClim metadata output may not be a symlink")
    destination = output.resolve()
    artifacts = repository / "artifacts"
    if (
        destination == artifacts
        or not destination.is_relative_to(artifacts)
        or destination.exists()
    ):
        raise ValueError("Absent repository artifact destination required")
    publish_study_input_products(repository / "data/landclim/raw", destination)


def main(argv: list[str] | None = None) -> int:
    """Publish the retained LandClim study-metadata bundle from repository inputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
