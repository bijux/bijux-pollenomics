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


def build_run_lra_batch_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build bounded cache-backed execution with a fresh report for each attempt."""
    parser = subparsers.add_parser(
        "run-lra-batch",
        help="Run or resume an exploratory batch using verified cached products.",
    )
    parser.add_argument("request", type=Path, help="lra-batch-request.v1 JSON file.")
    parser.add_argument(
        "--input-root",
        type=Path,
        required=True,
        help="Root for all item requests' relative evidence paths.",
    )
    parser.add_argument(
        "--cache-root",
        type=Path,
        required=True,
        help="Local directory for verified reusable LRA products.",
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        required=True,
        help="New directory for this attempt's complete item accounting.",
    )
    parser.add_argument(
        "--max-workers", type=int, default=1, help="Maximum concurrent model calls."
    )
    parser.add_argument(
        "--max-items", type=int, default=1000, help="Maximum declared batch size."
    )
    return parser


def build_render_lra_report_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build saved-product reporting with explicitly pinned input identities."""
    parser = subparsers.add_parser(
        "render-lra-report",
        help="Render a verified saved LRA product and declared display geometry.",
    )
    parser.add_argument("product", type=Path, help="Saved LRA product directory.")
    parser.add_argument(
        "--expected-manifest-sha256",
        required=True,
        help="Expected product manifest SHA-256.",
    )
    parser.add_argument(
        "--geometry",
        type=Path,
        required=True,
        help="Evidence-bound display geometry JSON.",
    )
    parser.add_argument(
        "--expected-geometry-sha256",
        required=True,
        help="Expected geometry file SHA-256.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New directory for the exploratory report.",
    )
    parser.add_argument(
        "--temporal-profile",
        choices=["calendar-bp1950-signed.v1"],
        default=None,
        help="Explicit signed calendar BP1950 representation for synthetic paired reports.",
    )
    return parser


def build_render_joint_lra_report_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build lossless reporting for one externally pinned joint product."""
    parser = subparsers.add_parser(
        "render-joint-lra-report",
        help="Render a verified retained joint LRA product without recomputation.",
    )
    parser.add_argument("product", type=Path, help="Saved joint LRA product directory.")
    parser.add_argument(
        "--expected-manifest-sha256",
        required=True,
        help="Expected joint-product manifest SHA-256.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New directory for the exploratory retained-law report.",
    )
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


def build_run_joint_lra_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build supplied synthetic joint realizations with complete failure accounting."""
    parser = subparsers.add_parser(
        "run-joint-lra",
        help="Run a synthetic supplied joint-realization analytical LRA ensemble.",
    )
    parser.add_argument(
        "request", type=Path, help="lra-joint-realizations.v1 JSON plan."
    )
    parser.add_argument(
        "--input-root",
        type=Path,
        required=True,
        help="Root for the plan's pinned base request and evidence paths.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New directory for all draw/bin outcomes and complete-law summaries.",
    )
    parser.add_argument(
        "--cache-root",
        type=Path,
        default=None,
        help="Optional local directory for verified reusable child LRA products.",
    )
    return parser
