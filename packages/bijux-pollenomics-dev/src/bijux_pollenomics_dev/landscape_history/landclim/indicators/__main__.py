"""Run source-bound agricultural-context indicator summaries."""

from __future__ import annotations

import argparse
from pathlib import Path

from .workflow import run


def main() -> None:
    """Publish into a new repository artifact destination."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(run(args.repository, args.output))


if __name__ == "__main__":
    main()
