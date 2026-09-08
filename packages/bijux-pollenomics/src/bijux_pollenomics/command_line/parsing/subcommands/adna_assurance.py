"""Ancient-DNA coverage, runtime, review, and release command parsers."""

from __future__ import annotations

import argparse

from ..options import add_version_argument


def build_adna_release_readiness_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the cross-surface release readiness parser."""
    parser = subparsers.add_parser(
        "adna-release-readiness",
        help=(
            "Print the medium-weight species release gate across source identity, "
            "curation integrity, normalized-record contracts, atlas summaries, "
            "and ranking provenance."
        ),
    )
    parser.add_argument(
        "--species",
        required=True,
        help="Latin name or registered alias for one species.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a table.",
    )
    return parser


def build_adna_release_bar_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the platform release-bar parser."""
    parser = subparsers.add_parser(
        "adna-release-bar",
        help=(
            "Print the platform release bar for calling bijux-pollenomics a real "
            "pollenomics app."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a table.",
    )
    return parser


def build_adna_domestication_coverage_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the cross-species domestication coverage parser."""
    parser = subparsers.add_parser(
        "adna-domestication-coverage",
        help=(
            "Print the cross-species domestication coverage report so strong, thin, "
            "and pretending support are visible."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a table.",
    )
    return parser


def build_adna_species_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the ancient-DNA species support parser."""
    parser = subparsers.add_parser(
        "adna-species",
        help=(
            "Print the canonical ancient-DNA species support matrix, including "
            "Latin-name identities, support statuses, and modality classes."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a table.",
    )
    return parser


def build_adna_runtime_manifest_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the ancient-DNA runtime manifest parser."""
    parser = subparsers.add_parser(
        "adna-runtime-manifest",
        help=(
            "Print the species-owned runtime manifest, including source bundles "
            "and analysis boundaries."
        ),
    )
    parser.add_argument(
        "--species",
        required=True,
        help="Latin name or registered alias for one species.",
    )
    add_version_argument(parser)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a table.",
    )
    return parser


def build_adna_species_review_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the ancient-DNA species review parser."""
    parser = subparsers.add_parser(
        "adna-species-review",
        help=(
            "Print the governed review for one species, including product role, "
            "assignment rule, dataset bucket, and archive integrity findings."
        ),
    )
    parser.add_argument(
        "--species",
        required=True,
        help="Latin name or registered alias for one species.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a table.",
    )
    return parser
