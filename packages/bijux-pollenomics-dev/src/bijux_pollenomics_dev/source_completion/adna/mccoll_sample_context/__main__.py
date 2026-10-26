"""Read the prepared McColl originals in place for the two AADR conflicts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .workflow import publish


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
                key: result[key]
                for key in (
                    "status",
                    "source_commit",
                    "selected_descriptive_cells",
                    "elapsed_seconds",
                )
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
