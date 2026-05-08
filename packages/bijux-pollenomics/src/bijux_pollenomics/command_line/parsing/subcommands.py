from __future__ import annotations

import argparse
from pathlib import Path

from ...config import (
    DEFAULT_AADR_VERSION,
    DEFAULT_CONTEXT_ROOT,
    DEFAULT_DATA_ROOT,
    DEFAULT_PUBLISHED_COUNTRIES,
)
from ...data_downloader import AVAILABLE_SOURCES
from .options import (
    add_aadr_root_argument,
    add_atlas_identity_arguments,
    add_context_root_argument,
    add_output_root_argument,
    add_version_argument,
)

__all__ = [
    "build_adna_archive_projects_parser",
    "build_adna_artifact_plan_parser",
    "build_adna_curation_manifest_parser",
    "build_adna_domestication_coverage_parser",
    "build_adna_layout_parser",
    "build_adna_release_bar_parser",
    "build_adna_release_readiness_parser",
    "build_adna_normalization_bundle_parser",
    "build_adna_runtime_manifest_parser",
    "build_adna_species_review_parser",
    "build_adna_species_parser",
    "build_refresh_animal_adna_foundation_parser",
    "build_collect_data_parser",
    "build_refresh_data_contract_surfaces_parser",
    "build_multi_country_map_parser",
    "build_publish_reports_parser",
    "build_ownership_map_parser",
    "build_report_country_parser",
    "build_product_scope_parser",
    "build_validate_collection_summary_parser",
    "build_source_support_parser",
    "build_surface_map_parser",
    "register_subcommands",
]


def register_subcommands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register every supported subcommand on the root parser."""
    build_adna_archive_projects_parser(subparsers)
    build_adna_artifact_plan_parser(subparsers)
    build_adna_curation_manifest_parser(subparsers)
    build_adna_domestication_coverage_parser(subparsers)
    build_adna_layout_parser(subparsers)
    build_adna_release_bar_parser(subparsers)
    build_adna_release_readiness_parser(subparsers)
    build_adna_normalization_bundle_parser(subparsers)
    build_adna_runtime_manifest_parser(subparsers)
    build_adna_species_parser(subparsers)
    build_adna_species_review_parser(subparsers)
    build_refresh_animal_adna_foundation_parser(subparsers)
    build_report_country_parser(subparsers)
    build_multi_country_map_parser(subparsers)
    build_publish_reports_parser(subparsers)
    build_collect_data_parser(subparsers)
    build_refresh_data_contract_surfaces_parser(subparsers)
    build_surface_map_parser(subparsers)
    build_product_scope_parser(subparsers)
    build_ownership_map_parser(subparsers)
    build_source_support_parser(subparsers)
    build_validate_collection_summary_parser(subparsers)


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


def build_report_country_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the country-report subcommand parser."""
    parser = subparsers.add_parser(
        "report-country",
        help="Filter AADR anno files by country and write a report bundle.",
    )
    parser.add_argument(
        "country", help="Political Entity value to filter, for example Sweden."
    )
    add_aadr_root_argument(parser)
    add_version_argument(parser)
    add_output_root_argument(
        parser,
        help_text="Directory where country report folders should be written. Default: docs/report",
    )
    parser.add_argument(
        "--shared-map-label",
        default=None,
        help="Optional label for a shared interactive map link shown in the country README.",
    )
    parser.add_argument(
        "--shared-map-path",
        default=None,
        help="Optional relative path to a shared interactive map shown in the country README.",
    )
    return parser


def build_multi_country_map_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the shared multi-country atlas subcommand parser."""
    parser = subparsers.add_parser(
        "report-multi-country-map",
        help="Build the Nordic Evidence Atlas for multiple countries with country toggles.",
    )
    parser.add_argument(
        "countries",
        nargs="+",
        help="Political Entity values to include, for example Sweden Norway Finland.",
    )
    add_atlas_identity_arguments(parser)
    add_aadr_root_argument(parser)
    add_version_argument(parser)
    add_output_root_argument(
        parser,
        help_text="Directory where report folders should be written. Default: docs/report",
    )
    add_context_root_argument(parser)
    return parser


def build_publish_reports_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the checked-in publication workflow subcommand parser."""
    parser = subparsers.add_parser(
        "publish-reports",
        help="Regenerate the current published Nordic Evidence Atlas bundle and country report bundles.",
    )
    parser.add_argument(
        "--countries",
        nargs="+",
        default=DEFAULT_PUBLISHED_COUNTRIES,
        help="Countries to publish. Default: " + " ".join(DEFAULT_PUBLISHED_COUNTRIES),
    )
    add_atlas_identity_arguments(parser)
    add_aadr_root_argument(parser)
    add_version_argument(parser)
    add_output_root_argument(
        parser,
        help_text="Directory where published report bundles should be written. Default: docs/report",
    )
    add_context_root_argument(parser)
    return parser


def build_refresh_animal_adna_foundation_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Build the end-to-end animal foundation refresh parser."""
    parser = subparsers.add_parser(
        "refresh-animal-adna-foundation",
        help=(
            "Refresh tracked animal source capture, normalized data roots, and "
            "published Nordic animal report outputs in one run."
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
        help="Countries to include in the published Nordic report refresh.",
    )
    parser.add_argument(
        "--species",
        nargs="+",
        default=[],
        help="Optional species names or aliases to refresh. Default: all tracked animal species.",
    )
    return parser


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
