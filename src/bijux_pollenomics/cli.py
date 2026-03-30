from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .data_downloader import AVAILABLE_SOURCES, collect_data
from .reporting import generate_country_report, generate_multi_country_map, generate_published_reports, slugify
from .settings import DEFAULT_AADR_VERSION, DEFAULT_ATLAS_SLUG, DEFAULT_ATLAS_TITLE, DEFAULT_PUBLISHED_COUNTRIES


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface."""
    parser = argparse.ArgumentParser(
        prog="bijux-pollenomics",
        description="Generate Nordic country reports and the Nordic Evidence Atlas from tracked data sources.",
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
        default=DEFAULT_AADR_VERSION,
        help=f"AADR version directory under the AADR root. Default: {DEFAULT_AADR_VERSION}",
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
        help="Build the Nordic Evidence Atlas for multiple countries with country toggles.",
    )
    multi_map_parser.add_argument(
        "countries",
        nargs="+",
        help="Political Entity values to include, for example Sweden Norway Finland.",
    )
    multi_map_parser.add_argument(
        "--name",
        default=DEFAULT_ATLAS_SLUG,
        help=f"Stable output directory and file slug. Default: {DEFAULT_ATLAS_SLUG}",
    )
    multi_map_parser.add_argument(
        "--title",
        default=DEFAULT_ATLAS_TITLE,
        help=f"Human-readable title shown in the shared map. Default: {DEFAULT_ATLAS_TITLE}",
    )
    multi_map_parser.add_argument(
        "--aadr-root",
        type=Path,
        default=Path("data/aadr"),
        help="Root directory containing AADR versions. Default: data/aadr",
    )
    multi_map_parser.add_argument(
        "--version",
        default=DEFAULT_AADR_VERSION,
        help=f"AADR version directory under the AADR root. Default: {DEFAULT_AADR_VERSION}",
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
        help="Regenerate the current published Nordic Evidence Atlas bundle and country report bundles.",
    )
    publish_parser.add_argument(
        "--countries",
        nargs="+",
        default=DEFAULT_PUBLISHED_COUNTRIES,
        help="Countries to publish. Default: " + " ".join(DEFAULT_PUBLISHED_COUNTRIES),
    )
    publish_parser.add_argument(
        "--name",
        default=DEFAULT_ATLAS_SLUG,
        help=f"Stable shared-map output directory and file slug. Default: {DEFAULT_ATLAS_SLUG}",
    )
    publish_parser.add_argument(
        "--title",
        default=DEFAULT_ATLAS_TITLE,
        help=f"Human-readable shared map title. Default: {DEFAULT_ATLAS_TITLE}",
    )
    publish_parser.add_argument(
        "--aadr-root",
        type=Path,
        default=Path("data/aadr"),
        help="Root directory containing AADR versions. Default: data/aadr",
    )
    publish_parser.add_argument(
        "--version",
        default=DEFAULT_AADR_VERSION,
        help=f"AADR version directory under the AADR root. Default: {DEFAULT_AADR_VERSION}",
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
        default=DEFAULT_AADR_VERSION,
        help=f"AADR version to download when `aadr` is selected. Default: {DEFAULT_AADR_VERSION}",
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
    return run_command(args, parser=parser)

def run_command(args: argparse.Namespace, *, parser: argparse.ArgumentParser) -> int:
    """Dispatch one parsed command to its handler."""
    if args.command == "report-country":
        return run_report_country(args, parser=parser)
    if args.command == "report-multi-country-map":
        return run_report_multi_country_map(args)
    if args.command == "collect-data":
        return run_collect_data(args)
    if args.command == "publish-reports":
        return run_publish_reports(args)
    parser.error(f"Unsupported command: {args.command}")
    return 2


def run_report_country(args: argparse.Namespace, *, parser: argparse.ArgumentParser) -> int:
    """Run the country-report command."""
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


def run_report_multi_country_map(args: argparse.Namespace) -> int:
    """Run the shared multi-country atlas command."""
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
        f"Wrote {report.title} with "
        f"{report.total_unique_samples} unique samples to {output_dir}"
    )
    return 0


def run_collect_data(args: argparse.Namespace) -> int:
    """Run the data-collection command."""
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


def run_publish_reports(args: argparse.Namespace) -> int:
    """Run the checked-in publication workflow."""
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


if __name__ == "__main__":
    raise SystemExit(main())
