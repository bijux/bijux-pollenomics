"""Build portable PDF accounts from the canonical paper inventory."""

from __future__ import annotations

import argparse
from pathlib import Path

from .export import export_reports


def main() -> None:
    """Build portable PDF accounts from the canonical paper inventory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--paper-id",
        help="Export one inventory paper while retaining every source hash",
    )
    parser.add_argument(
        "--source-date-epoch", help="Override SOURCE_DATE_EPOCH for this export"
    )
    args = parser.parse_args()
    result = export_reports(
        args.repository,
        args.inventory,
        args.output,
        paper_id=args.paper_id,
        source_date_epoch=args.source_date_epoch,
    )
    print(result)


if __name__ == "__main__":
    main()
