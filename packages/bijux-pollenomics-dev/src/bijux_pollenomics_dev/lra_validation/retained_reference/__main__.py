"""Compare installed current Python with an authenticated source-locked R bundle."""

from __future__ import annotations

import argparse
from pathlib import Path

from .comparison import replay
from .source_packet import repository_reference_bundle


def main() -> int:
    """Run the separately authenticated retained-reference correspondence consumer."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument(
        "--bundle",
        type=Path,
        help="Explicit authenticated reference; defaults to the fixed repository source packet",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    bundle = args.bundle
    if bundle is None:
        bundle = repository_reference_bundle(args.repository)
    result = replay(args.repository, bundle, args.output)
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
