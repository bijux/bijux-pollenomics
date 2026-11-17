"""Build portable paper PDFs or check their retained source bindings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .export import export_reports
from .source import check_retained_sources, repository_file, repository_root


def main() -> None:
    """Build portable paper PDFs or check their retained source bindings."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--check-retained-sources",
        action="store_true",
        help="Check current canonical Markdown against the existing export manifest",
    )
    parser.add_argument(
        "--paper-id",
        help="Export one inventory paper while retaining every source hash",
    )
    parser.add_argument(
        "--source-date-epoch", help="Override SOURCE_DATE_EPOCH for this export"
    )
    args = parser.parse_args()
    if args.check_retained_sources:
        if args.output is not None or args.paper_id or args.source_date_epoch:
            parser.error("source binding checks do not compile or select a paper")
        root = repository_root(args.repository)
        manifest = json.loads(
            repository_file(root, "reports/exports/papers/manifest.json").read_bytes()
        )
        print(
            json.dumps(
                check_retained_sources(root, args.inventory, manifest), sort_keys=True
            )
        )
        return
    if args.output is None:
        parser.error("--output is required for PDF export")
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
