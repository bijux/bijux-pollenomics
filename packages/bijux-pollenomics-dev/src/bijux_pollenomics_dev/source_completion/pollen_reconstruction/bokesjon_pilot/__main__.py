"""Run the Bökesjön source audit into an absent artifact destination."""

import argparse
from pathlib import Path

from .workflow import run


def main() -> None:
    """Parse explicit source-audit inputs and an absent artifact destination."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--workbook", type=Path)
    parser.add_argument("--author-lookup", type=Path)
    args = parser.parse_args()
    print(
        run(
            args.repository,
            args.output,
            workbook=args.workbook,
            author_lookup=args.author_lookup,
        )
    )


if __name__ == "__main__":
    main()
