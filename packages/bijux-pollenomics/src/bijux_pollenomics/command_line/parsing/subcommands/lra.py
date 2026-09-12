"""Landscape reconstruction commands over governed request files."""

from __future__ import annotations

import argparse
from pathlib import Path


def _request_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("request", type=Path, help="lra-request.v1 JSON file.")
    parser.add_argument(
        "--input-root",
        type=Path,
        required=True,
        help="Root for the request's relative evidence paths.",
    )


def build_validate_lra_input_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build input validation with explicit evidence-root ownership."""
    parser = subparsers.add_parser(
        "validate-lra-input",
        help="Validate an LRA request, source hashes and numerical configuration.",
    )
    _request_arguments(parser)
    return parser


def build_run_lra_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build exploratory reconstruction into a new local product directory."""
    parser = subparsers.add_parser(
        "run-lra", help="Run an exploratory REVEALS, LOVE or paired series request."
    )
    _request_arguments(parser)
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New local product directory; existing outputs are never overwritten.",
    )
    return parser
