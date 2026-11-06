"""Bound common PPE covariance using only the qualified saved-cover study."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .producer import publish


def main() -> int:
    """Publish the common PPE covariance comparison and print its summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = publish(args.repository, args.output)
    print(
        json.dumps(
            {
                "status": result["status"],
                "source_commit": result["source_commit"],
                "summary": result["summary"],
                "elapsed_seconds": result["elapsed_seconds"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
