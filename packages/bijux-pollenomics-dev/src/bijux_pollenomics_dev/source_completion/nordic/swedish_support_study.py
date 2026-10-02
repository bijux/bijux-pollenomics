"""Route the retained swedish-support-sensitivity study through its original source stages."""

from __future__ import annotations

import argparse
from pathlib import Path

from .study_execution import run_study

SOURCE = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/swedish_support_sensitivity.py"
)
REPORT = Path("docs/report/regions/nordic/swedish-support-sensitivity")


def run(repository: Path, output: Path) -> None:
    run_study(repository, output, SOURCE, REPORT)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
