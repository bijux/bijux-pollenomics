from __future__ import annotations

import argparse

from ... import __version__
from .subcommands import register_subcommands

__all__ = ["build_parser"]


def build_parser() -> argparse.ArgumentParser:
    """Build the canonical command-line parser."""
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
    register_subcommands(subparsers)
    return parser
