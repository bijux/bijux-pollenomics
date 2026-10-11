"""Generate the bounded ESSD reproduction reconciliation package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .reconcile import publish_reconciliation


def main() -> int:
    """Publish the evidence package to a new output directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = publish_reconciliation(args.archive, args.repository, args.output)
    print(
        json.dumps(
            {
                "archive_sha256": result["archive-receipt.json"]["sha256"],
                "output": str(args.output),
                "pft_resolution": result["pft-discrepancy.json"]["resolution_status"],
                "whole_paper_reproduction_certified": result[
                    "publication-profile-crosswalk.json"
                ]["whole_paper_reproduction_certified"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
