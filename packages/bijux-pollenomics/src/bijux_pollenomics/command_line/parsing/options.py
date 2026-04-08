from __future__ import annotations

import argparse
from pathlib import Path

from ...config import (
    DEFAULT_AADR_ROOT,
    DEFAULT_AADR_VERSION,
    DEFAULT_ATLAS_SLUG,
    DEFAULT_ATLAS_TITLE,
    DEFAULT_CONTEXT_ROOT,
    DEFAULT_REPORT_ROOT,
)

__all__ = [
    "add_aadr_root_argument",
    "add_atlas_identity_arguments",
    "add_context_root_argument",
    "add_output_root_argument",
    "add_version_argument",
]


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
