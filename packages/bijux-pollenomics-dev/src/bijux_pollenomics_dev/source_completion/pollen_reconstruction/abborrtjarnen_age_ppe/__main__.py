"""Consume saved ABBO ages once under the frozen conditional moment protocol."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .producer import publish


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = publish(args.repository, args.source_root, args.output)
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "status",
                    "source_commit",
                    "requested_draws",
                    "complete_draws",
                    "undefined_draws",
                    "elapsed_seconds",
                )
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
