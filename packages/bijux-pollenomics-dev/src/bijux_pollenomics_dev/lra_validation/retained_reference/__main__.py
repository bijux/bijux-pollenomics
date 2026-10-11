"""Compare installed current Python with an explicitly supplied source-locked R bundle."""

from __future__ import annotations

import argparse
from pathlib import Path

from .comparison import replay


def main() -> int:
    """Run the separately authenticated retained-reference correspondence consumer."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = replay(args.repository, args.bundle, args.output)
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
