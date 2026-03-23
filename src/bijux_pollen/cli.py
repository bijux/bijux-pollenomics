from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .data_downloader import collect_context_data, download_aadr_anno_files
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
    report_parser.add_argument(
        "--shared-map-label",
        default=None,
        help="Optional label for a shared interactive map link shown in the country README.",
    )
    report_parser.add_argument(
        "--shared-map-path",
        default=None,
        help="Optional relative path to a shared interactive map shown in the country README.",
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

    multi_map_parser.add_argument(
        "--context-root",
        type=Path,
        default=Path("data"),
        help="Directory containing normalized context datasets. Default: data",
    )

    context_parser = subparsers.add_parser(
        "collect-context-data",
        help="Download and normalize archaeology and palaeo data into data/.",
    )
    context_parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data"),
        help="Directory where source data should be written. Default: data",
    )

    aadr_parser = subparsers.add_parser(
        "download-aadr-anno",
        help="Download tracked AADR .anno inputs from the official Harvard Dataverse release.",
    )
    aadr_parser.add_argument(
        "--version",
        default="v62.0",
        help="AADR version to download. Default: v62.0",
    )
    aadr_parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data/aadr"),
        help="Directory where AADR versions should be written. Default: data/aadr",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "report-country":
        version_dir = args.aadr_root / args.version
        output_dir = args.output_root / slugify(args.country)
        map_reference = None
        if args.shared_map_label and args.shared_map_path:
            map_reference = (args.shared_map_label, args.shared_map_path)
        report = generate_country_report(
            version_dir=version_dir,
            country=args.country,
            output_dir=output_dir,
            map_reference=map_reference,
        )
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
            context_root=args.context_root,
        )
        print(
            f"Wrote {report.title} AADR {report.version} map with "
            f"{report.total_unique_samples} unique samples to {output_dir}"
        )
        return 0

    if args.command == "collect-context-data":
        report = collect_context_data(output_root=args.output_root)
        print(
            f"Wrote context data to {report.output_root} with "
            f"{report.neotoma_point_count} Neotoma points, "
            f"{report.sead_point_count} SEAD points, and "
            f"{report.raa_total_site_count} Swedish archaeology records in the RAÄ layer"
        )
        return 0

    if args.command == "download-aadr-anno":
        report = download_aadr_anno_files(output_root=args.output_root, version=args.version)
        print(
            f"Wrote {len(report.downloaded_files)} AADR .anno files for {report.version} to "
            f"{report.version_dir}"
        )
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
