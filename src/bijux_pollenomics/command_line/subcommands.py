from __future__ import annotations

import argparse
from pathlib import Path

from ..data_downloader import AVAILABLE_SOURCES
from ..settings import DEFAULT_AADR_VERSION, DEFAULT_CONTEXT_ROOT, DEFAULT_PUBLISHED_COUNTRIES
from .options import (
    add_aadr_root_argument,
    add_atlas_identity_arguments,
    add_context_root_argument,
    add_output_root_argument,
    add_version_argument,
)


def register_subcommands(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register every supported subcommand on the root parser."""
    build_report_country_parser(subparsers)
    build_multi_country_map_parser(subparsers)
    build_publish_reports_parser(subparsers)
    build_collect_data_parser(subparsers)


def build_report_country_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the country-report subcommand parser."""
    parser = subparsers.add_parser(
        "report-country",
        help="Filter AADR anno files by country and write a report bundle.",
    )
    parser.add_argument("country", help="Political Entity value to filter, for example Sweden.")
    add_aadr_root_argument(parser)
    add_version_argument(parser)
    add_output_root_argument(
        parser,
        help_text="Directory where country report folders should be written. Default: docs/report",
    )
    parser.add_argument(
        "--shared-map-label",
        default=None,
        help="Optional label for a shared interactive map link shown in the country README.",
    )
    parser.add_argument(
        "--shared-map-path",
        default=None,
        help="Optional relative path to a shared interactive map shown in the country README.",
    )
    return parser


def build_multi_country_map_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the shared multi-country atlas subcommand parser."""
    parser = subparsers.add_parser(
        "report-multi-country-map",
        help="Build the Nordic Evidence Atlas for multiple countries with country toggles.",
    )
    parser.add_argument(
        "countries",
        nargs="+",
        help="Political Entity values to include, for example Sweden Norway Finland.",
    )
    add_atlas_identity_arguments(parser)
    add_aadr_root_argument(parser)
    add_version_argument(parser)
    add_output_root_argument(
        parser,
        help_text="Directory where report folders should be written. Default: docs/report",
    )
    add_context_root_argument(parser)
    return parser


def build_publish_reports_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the checked-in publication workflow subcommand parser."""
    parser = subparsers.add_parser(
        "publish-reports",
        help="Regenerate the current published Nordic Evidence Atlas bundle and country report bundles.",
    )
    parser.add_argument(
        "--countries",
        nargs="+",
        default=DEFAULT_PUBLISHED_COUNTRIES,
        help="Countries to publish. Default: " + " ".join(DEFAULT_PUBLISHED_COUNTRIES),
    )
    add_atlas_identity_arguments(parser)
    add_aadr_root_argument(parser)
    add_version_argument(parser)
    add_output_root_argument(
        parser,
        help_text="Directory where published report bundles should be written. Default: docs/report",
    )
    add_context_root_argument(parser)
    return parser


def build_collect_data_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the tracked data collection subcommand parser."""
    available_sources_label = ", ".join(("all", *AVAILABLE_SOURCES))
    parser = subparsers.add_parser(
        "collect-data",
        help="Collect one or more tracked data sources into data/.",
    )
    parser.add_argument(
        "sources",
        nargs="+",
        metavar="source",
        help=(
            "One or more data sources to collect. "
            f"Accepted values: {available_sources_label}. Source names are normalized case-insensitively."
        ),
    )
    add_version_argument(
        parser,
        help_text=f"AADR version to download when `aadr` is selected. Default: {DEFAULT_AADR_VERSION}",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_CONTEXT_ROOT,
        help="Directory where tracked data should be written. Default: data",
    )
    return parser
