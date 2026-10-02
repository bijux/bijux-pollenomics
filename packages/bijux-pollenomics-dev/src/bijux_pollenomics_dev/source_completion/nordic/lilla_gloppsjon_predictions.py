"""Export the fixed Lilla Gloppsjön retained-input prediction stage."""

from __future__ import annotations

import argparse
from pathlib import Path

from .lilla_gloppsjon_execution import predict_to_artifacts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    predict_to_artifacts(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
