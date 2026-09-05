"""End-to-end animal ancient-DNA refresh command parser."""

from __future__ import annotations

import argparse
from pathlib import Path

from ....config import (
    DEFAULT_AADR_VERSION,
    DEFAULT_CONTEXT_ROOT,
    DEFAULT_DATA_ROOT,
    DEFAULT_PUBLISHED_COUNTRIES,
)
from ..options import (
    add_aadr_root_argument,
    add_output_root_argument,
    add_version_argument,
)


def build_refresh_animal_adna_foundation_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the end-to-end animal foundation refresh parser."""
    parser = subparsers.add_parser(
        "refresh-animal-adna-foundation",
        help=(
            "Refresh tracked animal source capture, normalized data roots, and "
            "published world, regional, and country animal report outputs in one run."
        ),
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DEFAULT_DATA_ROOT,
        help=f"Directory containing tracked animal data roots. Default: {DEFAULT_DATA_ROOT}",
    )
    add_aadr_root_argument(parser)
    add_output_root_argument(
        parser,
        help_text="Directory where published report bundles are written. Default: docs/report",
    )
    parser.add_argument(
        "--context-root",
        type=Path,
        default=DEFAULT_CONTEXT_ROOT,
        help=f"Directory containing normalized context datasets. Default: {DEFAULT_CONTEXT_ROOT}",
    )
    add_version_argument(
        parser,
        help_text=f"AADR version directory under the AADR root. Default: {DEFAULT_AADR_VERSION}",
    )
    parser.add_argument(
        "--countries",
        nargs="+",
        default=list(DEFAULT_PUBLISHED_COUNTRIES),
        help="Countries to include in the published geography-tree refresh.",
    )
    parser.add_argument(
        "--species",
        nargs="+",
        default=[],
        help="Optional species names or aliases to refresh. Default: all tracked animal species.",
    )
    return parser
