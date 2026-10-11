"""Route the retained swedish-lake-transfer score stage into owner artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from .score_execution import score_to_artifacts

SOURCE = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/swedish_lake_transfer.py"
)
PREPARED = Path("docs/report/regions/nordic/swedish-lake-transfer")


def run(repository: Path, output: Path) -> None:
    """Route the retained swedish-lake-transfer score stage into owner artifacts."""
    score_to_artifacts(repository, output, SOURCE, PREPARED)


def main(argv: list[str] | None = None) -> int:
    """Parse command-line inputs and route the retained swedish-lake-transfer score stage into owner artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
