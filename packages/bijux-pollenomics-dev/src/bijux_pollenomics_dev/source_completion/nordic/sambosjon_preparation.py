"""Route the original Sämbosjön preparation stage to confined artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from .sambosjon_execution import prepare_to_artifacts


def run(repository: Path, output: Path) -> None:
    """Route the original Sämbosjön preparation stage to confined artifacts."""
    prepare_to_artifacts(repository, output)


def main(argv: list[str] | None = None) -> int:
    """Parse command-line inputs and route the original Sämbosjön preparation stage to confined artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
