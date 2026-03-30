from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .data_downloader import AVAILABLE_SOURCES, collect_data
from .reporting import generate_country_report, generate_multi_country_map, generate_published_reports, slugify


PUBLISHED_COUNTRIES = ("Sweden", "Norway", "Finland", "Denmark")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface."""
    parser = argparse.ArgumentParser(
        prog="bijux-pollenomics",
        description="Generate Nordic country reports and shared research maps from tracked data sources.",
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
        help="Build one interactive research map for multiple countries with country toggles.",
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

    publish_parser = subparsers.add_parser(
        "publish-reports",
        help="Regenerate the current published shared map and country report bundles.",
    )
    publish_parser.add_argument(
        "--countries",
        nargs="+",
        default=PUBLISHED_COUNTRIES,
        help="Countries to publish. Default: Sweden Norway Finland Denmark",
    )
    publish_parser.add_argument(
        "--name",
        default="nordic",
        help="Stable shared-map output directory and file slug. Default: nordic",
    )
    publish_parser.add_argument(
        "--title",
        default="Nordic Countries",
        help="Human-readable shared map title. Default: Nordic Countries",
    )
    publish_parser.add_argument(
        "--aadr-root",
        type=Path,
        default=Path("data/aadr"),
        help="Root directory containing AADR versions. Default: data/aadr",
    )
    publish_parser.add_argument(
        "--version",
        default="v62.0",
        help="AADR version directory under the AADR root. Default: v62.0",
    )
    publish_parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("docs/report"),
        help="Directory where published report bundles should be written. Default: docs/report",
    )
    publish_parser.add_argument(
        "--context-root",
        type=Path,
        default=Path("data"),
        help="Directory containing normalized context datasets. Default: data",
    )

    collect_parser = subparsers.add_parser(
        "collect-data",
        help="Collect one or more tracked data sources into data/.",
    )
    collect_parser.add_argument(
        "sources",
        nargs="+",
        choices=("all", *AVAILABLE_SOURCES),
        help="One or more data sources to collect, or `all`.",
    )
    collect_parser.add_argument(
        "--version",
        default="v62.0",
        help="AADR version to download when `aadr` is selected. Default: v62.0",
    )
    collect_parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data"),
        help="Directory where tracked data should be written. Default: data",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "report-country":
        if bool(args.shared_map_label) != bool(args.shared_map_path):
            parser.error("--shared-map-label and --shared-map-path must be provided together")
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
            f"Wrote {report.title} research map with "
            f"{report.total_unique_samples} unique samples to {output_dir}"
        )
        return 0

    if args.command == "collect-data":
        report = collect_data(output_root=args.output_root, sources=args.sources, version=args.version)
        print(
            f"Wrote data sources {', '.join(report.collected_sources)} to {report.output_root} with "
            f"{report.aadr_file_count} AADR .anno files, "
            f"{report.landclim_site_count} LandClim pollen sequences, "
            f"{report.landclim_grid_cell_count} LandClim REVEALS grid cells, "
            f"{report.neotoma_point_count} Neotoma points, "
            f"{report.sead_point_count} SEAD points, and "
            f"{report.raa_total_site_count} Swedish archaeology records in the RAÄ layer"
        )
        return 0

    if args.command == "publish-reports":
        version_dir = args.aadr_root / args.version
        report = generate_published_reports(
            version_dir=version_dir,
            countries=args.countries,
            output_root=args.output_root,
            title=args.title,
            slug=args.name,
            context_root=args.context_root,
        )
        print(
            f"Wrote published report bundles for {', '.join(report.countries)} to {args.output_root} "
            f"with shared map under {report.shared_map_dir.name}"
        )
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
