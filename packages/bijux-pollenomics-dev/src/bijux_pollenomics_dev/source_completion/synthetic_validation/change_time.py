"""Route the retained constructed change-time report to an owner artifact."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from bijux_pollenomics_dev.lra_validation.change_time_challenge import (
    main as producer_main,
)

from .writer_execution import run_writer


def run(repository: Path, output: Path) -> None:
    """Preserve the existing writer's fixture, serialization, and refusal status."""
    original = sys.argv
    try:
        sys.argv = ["change_time_challenge", "--output", str(output)]
        status = run_writer(repository, output, producer_main)
    finally:
        sys.argv = original
    if status != 0:
        raise ValueError("constructed change-time contract refused")


def main(argv: list[str] | None = None) -> int:
    """Parse command-line inputs and route the retained constructed change-time report to an owner artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
