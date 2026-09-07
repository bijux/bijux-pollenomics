"""Data collection and collection-contract command parsers."""

from __future__ import annotations

import argparse
from pathlib import Path

from ....collection import AVAILABLE_SOURCES
from ....config import DEFAULT_AADR_VERSION, DEFAULT_CONTEXT_ROOT, DEFAULT_DATA_ROOT
from ..options import add_version_argument


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


def build_validate_collection_summary_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the collection-summary schema validation parser."""
    parser = subparsers.add_parser(
        "validate-collection-summary",
        help=(
            "Validate one collection_summary.json payload without rerunning the "
            "full source collection build."
        ),
    )
    parser.add_argument(
        "--summary-path",
        type=Path,
        default=DEFAULT_CONTEXT_ROOT / "collection_summary.json",
        help="Path to collection_summary.json. Default: data/collection_summary.json",
    )
    return parser


def build_refresh_data_contract_surfaces_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the checked-in data-contract refresh parser."""
    parser = subparsers.add_parser(
        "refresh-data-contract-surfaces",
        help=(
            "Refresh collection_summary.json and the checked-in data contract "
            "surfaces from the current repository data tree."
        ),
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DEFAULT_DATA_ROOT,
        help="Path to the repository data root. Default: data",
    )
    add_version_argument(parser)
    return parser


def build_refresh_aadr_source_accountability_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the compact AADR source-accountability refresh parser."""
    parser = subparsers.add_parser(
        "refresh-aadr-source-accountability",
        help=(
            "Reconcile the tracked AADR source panels into a compact, "
            "non-admitting accountability receipt."
        ),
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DEFAULT_DATA_ROOT,
        help="Path to the repository data root. Default: data",
    )
    add_version_argument(parser)
    return parser
