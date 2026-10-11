"""Export fixed Lilla Gloppsjön scores from its retained prediction freeze."""

from __future__ import annotations

import argparse
from pathlib import Path

from .lilla_gloppsjon_execution import score_to_artifacts


def main(argv: list[str] | None = None) -> int:
    """Parse command-line inputs and export fixed Lilla Gloppsjön scores from its retained prediction freeze."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    score_to_artifacts(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
