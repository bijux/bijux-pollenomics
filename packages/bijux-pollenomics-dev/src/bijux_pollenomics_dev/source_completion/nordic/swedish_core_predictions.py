"""Route the existing Swedish retained-input prediction stage into owner artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from .prediction_execution import predict_to_artifacts

SOURCE = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/swedish_neotoma_holdout.py"
)


PREPARED = Path("docs/report/regions/nordic/swedish-neotoma-holdout")


def run(repository: Path, output: Path) -> None:
    """Route the existing Swedish retained-input prediction stage into owner artifacts."""
    predict_to_artifacts(repository, output, SOURCE, PREPARED)


def main(argv: list[str] | None = None) -> int:
    """Route the existing Swedish retained-input prediction stage into owner artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
