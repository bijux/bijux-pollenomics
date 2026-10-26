"""Run the fixed source-bound whole-place-excluded spatial field comparison."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .producer import publish


def main() -> int:
    """Write one fresh artifact output without changing scientific inputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = publish(args.repository, args.source_root, args.output)
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "status",
                    "source_commit",
                    "requested_contexts",
                    "requested_family_outcomes",
                    "elapsed_seconds",
                )
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
