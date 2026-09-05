"""Ancient-DNA source inventory and normalization command parsers."""

from __future__ import annotations

import argparse


def build_adna_archive_projects_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the ancient-DNA archive project inventory parser."""
    parser = subparsers.add_parser(
        "adna-archive-projects",
        help=(
            "Print the curated ENA project inventory for domesticated-animal "
            "ancient-DNA support."
        ),
    )
    parser.add_argument(
        "--species",
        default=None,
        help="Optional Latin name or registered alias to filter one species.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a table.",
    )
    return parser


def build_adna_artifact_plan_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the species artifact plan parser."""
    parser = subparsers.add_parser(
        "adna-artifact-plan",
        help=(
            "Print the deterministic species rebuild artifact plan, including "
            "governed manifest and review payload paths."
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


def build_adna_layout_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the canonical ancient-DNA layout parser."""
    parser = subparsers.add_parser(
        "adna-layout",
        help="Print the canonical `data/adna/species/<latin_name>/...` layout for one species.",
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


def build_adna_curation_manifest_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the species curation manifest parser."""
    parser = subparsers.add_parser(
        "adna-curation-manifest",
        help=(
            "Print the species-owned domesticated-animal curation manifest, "
            "including core, pending, and rejected projects."
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


def build_adna_normalization_bundle_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the non-human normalization bundle parser."""
    parser = subparsers.add_parser(
        "adna-normalization-bundle",
        help=(
            "Print the governed non-human normalization bundle, including project "
            "summaries, study summaries, lineage, and refusals."
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
