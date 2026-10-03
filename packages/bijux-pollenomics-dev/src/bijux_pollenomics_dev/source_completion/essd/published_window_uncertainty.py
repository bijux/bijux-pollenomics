"""Route the pinned ESSD mean/SE envelope report to an artifact directory."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import runpy
import sys

CORE = "bijux_pollenomics_dev.essd_reproduction.published_window_uncertainty"
CORE_PATH = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/"
    "essd_reproduction/published_window_uncertainty.py"
)
SOURCE = Path("docs/report/publication-replay/landclim-published-window-provenance")


def run(repository: Path, output: Path) -> None:
    """Invoke the existing descriptive comparison with two fixed inputs."""
    repository = repository.resolve(strict=True)
    if output.is_symlink():
        raise ValueError("ESSD envelope output may not be a symlink")
    destination = output.resolve()
    artifacts = repository / "artifacts"
    if (
        destination == artifacts
        or not destination.is_relative_to(artifacts)
        or destination.exists()
    ):
        raise ValueError("Absent repository artifact destination required")
    expected = repository / CORE_PATH
    spec = importlib.util.find_spec(CORE)
    if spec is None or spec.origin is None or Path(spec.origin).resolve() != expected:
        raise ValueError("ESSD envelope writer origin differs from repository")
    original = sys.argv
    try:
        sys.argv = [
            CORE,
            "--correspondence-csv",
            str(repository / SOURCE / "paper-correspondence.csv"),
            "--provenance-report",
            str(repository / SOURCE / "report.json"),
            "--output",
            str(destination),
        ]
        runpy.run_module(CORE, run_name="__main__")
    finally:
        sys.argv = original


def main(argv: list[str] | None = None) -> int:
    """Route the pinned ESSD mean/SE envelope report to an artifact directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
