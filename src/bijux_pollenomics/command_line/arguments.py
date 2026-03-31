from __future__ import annotations

import argparse
from pathlib import Path

from .. import __version__
from ..data_downloader import AVAILABLE_SOURCES
from ..settings import (
    DEFAULT_AADR_ROOT,
    DEFAULT_AADR_VERSION,
    DEFAULT_ATLAS_SLUG,
    DEFAULT_ATLAS_TITLE,
    DEFAULT_CONTEXT_ROOT,
    DEFAULT_PUBLISHED_COUNTRIES,
    DEFAULT_REPORT_ROOT,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface."""
    parser = argparse.ArgumentParser(
        prog="bijux-pollenomics",
        description="Generate Nordic country reports and the Nordic Evidence Atlas from tracked data sources.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    report_parser = subparsers.add_parser(
        "report-country",
        help="Filter AADR anno files by country and write a report bundle.",
    )
    report_parser.add_argument("country", help="Political Entity value to filter, for example Sweden.")
    add_aadr_root_argument(report_parser)
    add_version_argument(report_parser)
    add_output_root_argument(
        report_parser,
        help_text="Directory where country report folders should be written. Default: docs/report",
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
    add_atlas_identity_arguments(multi_map_parser)
    add_aadr_root_argument(multi_map_parser)
    add_version_argument(multi_map_parser)
    add_output_root_argument(
        multi_map_parser,
        help_text="Directory where report folders should be written. Default: docs/report",
    )
    add_context_root_argument(multi_map_parser)

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
    add_atlas_identity_arguments(publish_parser)
    add_aadr_root_argument(publish_parser)
    add_version_argument(publish_parser)
    add_output_root_argument(
        publish_parser,
        help_text="Directory where published report bundles should be written. Default: docs/report",
    )
    add_context_root_argument(publish_parser)

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
    add_version_argument(
        collect_parser,
        help_text=f"AADR version to download when `aadr` is selected. Default: {DEFAULT_AADR_VERSION}",
    )
    collect_parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_CONTEXT_ROOT,
        help="Directory where tracked data should be written. Default: data",
    )
    return parser


def add_aadr_root_argument(parser: argparse.ArgumentParser) -> None:
    """Add the shared AADR root option."""
    parser.add_argument(
        "--aadr-root",
        type=Path,
        default=DEFAULT_AADR_ROOT,
        help="Root directory containing AADR versions. Default: data/aadr",
    )


def add_version_argument(parser: argparse.ArgumentParser, *, help_text: str | None = None) -> None:
    """Add the shared version option."""
    parser.add_argument(
        "--version",
        default=DEFAULT_AADR_VERSION,
        help=help_text or f"AADR version directory under the AADR root. Default: {DEFAULT_AADR_VERSION}",
    )


def add_output_root_argument(parser: argparse.ArgumentParser, *, help_text: str) -> None:
    """Add the shared output root option."""
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_REPORT_ROOT,
        help=help_text,
    )


def add_context_root_argument(parser: argparse.ArgumentParser) -> None:
    """Add the shared normalized-context root option."""
    parser.add_argument(
        "--context-root",
        type=Path,
        default=DEFAULT_CONTEXT_ROOT,
        help="Directory containing normalized context datasets. Default: data",
    )


def add_atlas_identity_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the shared atlas slug and title options."""
    parser.add_argument(
        "--name",
        default=DEFAULT_ATLAS_SLUG,
        help=f"Stable output directory and file slug. Default: {DEFAULT_ATLAS_SLUG}",
    )
    parser.add_argument(
        "--title",
        default=DEFAULT_ATLAS_TITLE,
        help=f"Human-readable title shown in the shared map. Default: {DEFAULT_ATLAS_TITLE}",
    )
