from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .reporting import generate_country_report, generate_multi_country_map, slugify


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface."""
    parser = argparse.ArgumentParser(
        prog="bijux-pollen-aadr",
        description="Generate country-level AADR reports from local anno files.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    report_parser = subparsers.add_parser(
        "report-country",
        help="Filter AADR anno files by country and write a report bundle.",
    )
    report_parser.add_argument("country", help="Political Entity value to filter, for example Sweden.")
    report_parser.add_argument(
        "--aadr-root",
        type=Path,
        default=Path("data/aadr"),
        help="Root directory containing AADR versions. Default: data/aadr",
    )
    report_parser.add_argument(
        "--version",
        default="v62.0",
        help="AADR version directory under the AADR root. Default: v62.0",
    )
    report_parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("docs/report"),
        help="Directory where country report folders should be written. Default: docs/report",
    )

    multi_map_parser = subparsers.add_parser(
        "report-multi-country-map",
        help="Build one interactive map for multiple countries with country toggles.",
    )
    multi_map_parser.add_argument(
        "countries",
        nargs="+",
        help="Political Entity values to include, for example Sweden Norway Finland.",
    )
    multi_map_parser.add_argument(
        "--name",
        default="nordic",
        help="Stable output directory and file slug. Default: nordic",
    )
    multi_map_parser.add_argument(
        "--title",
        default="Nordic Countries",
        help="Human-readable title shown in the shared map. Default: Nordic Countries",
    )
    multi_map_parser.add_argument(
        "--aadr-root",
        type=Path,
        default=Path("data/aadr"),
        help="Root directory containing AADR versions. Default: data/aadr",
    )
    multi_map_parser.add_argument(
        "--version",
        default="v62.0",
        help="AADR version directory under the AADR root. Default: v62.0",
    )
    multi_map_parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("docs/report"),
        help="Directory where report folders should be written. Default: docs/report",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "report-country":
        version_dir = args.aadr_root / args.version
        output_dir = args.output_root / slugify(args.country)
        report = generate_country_report(version_dir=version_dir, country=args.country, output_dir=output_dir)
        print(
            f"Wrote {report.country} AADR {report.version} report with "
            f"{report.total_unique_samples} unique samples to {output_dir}"
        )
        return 0

    if args.command == "report-multi-country-map":
        version_dir = args.aadr_root / args.version
        output_dir = args.output_root / slugify(args.name)
        report = generate_multi_country_map(
            version_dir=version_dir,
            countries=args.countries,
            output_dir=output_dir,
            title=args.title,
            slug=slugify(args.name),
        )
        print(
            f"Wrote {report.title} AADR {report.version} map with "
            f"{report.total_unique_samples} unique samples to {output_dir}"
        )
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
