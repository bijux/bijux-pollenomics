"""Repository orientation and product-scope command parsers."""

from __future__ import annotations

import argparse


def build_surface_map_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the foundation surface-map subcommand parser."""
    parser = subparsers.add_parser(
        "surface-map",
        help=(
            "Print current runtime surfaces and planned engine surfaces "
            "for repository orientation."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a table.",
    )
    return parser


def build_product_scope_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the product-scope subcommand parser."""
    parser = subparsers.add_parser(
        "product-scope",
        help=(
            "Print an explicit scope statement showing current atlas-builder "
            "capabilities versus planned engine claims."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a table.",
    )
    return parser


def build_ownership_map_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the ownership-map subcommand parser."""
    parser = subparsers.add_parser(
        "ownership-map",
        help=(
            "Print where source data, ranking, and publication logic live "
            "inside the runtime package."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a table.",
    )
    return parser


def build_source_support_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the source-support subcommand parser."""
    parser = subparsers.add_parser(
        "source-support",
        help=(
            "Print support-status and country-coverage rows for tracked source "
            "families."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a table.",
    )
    return parser
