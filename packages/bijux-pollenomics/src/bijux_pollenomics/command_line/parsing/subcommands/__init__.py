"""Command-family parser builders for the bijux-pollenomics CLI."""

from __future__ import annotations

import argparse as argparse
from pathlib import Path as Path

from ....collection import AVAILABLE_SOURCES as AVAILABLE_SOURCES
from ....config import DEFAULT_AADR_VERSION as DEFAULT_AADR_VERSION
from ....config import DEFAULT_CONTEXT_ROOT as DEFAULT_CONTEXT_ROOT
from ....config import DEFAULT_DATA_ROOT as DEFAULT_DATA_ROOT
from ....config import DEFAULT_PUBLISHED_COUNTRIES as DEFAULT_PUBLISHED_COUNTRIES
from ..options import add_aadr_root_argument as add_aadr_root_argument
from ..options import add_atlas_identity_arguments as add_atlas_identity_arguments
from ..options import add_context_root_argument as add_context_root_argument
from ..options import add_output_root_argument as add_output_root_argument
from ..options import add_version_argument as add_version_argument
from .adna_assurance import (
    build_adna_domestication_coverage_parser,
    build_adna_release_bar_parser,
    build_adna_release_readiness_parser,
    build_adna_runtime_manifest_parser,
    build_adna_species_parser,
    build_adna_species_review_parser,
)
from .adna_inventory import (
    build_adna_archive_projects_parser,
    build_adna_artifact_plan_parser,
    build_adna_curation_manifest_parser,
    build_adna_layout_parser,
    build_adna_normalization_bundle_parser,
)
from .animal_refresh import build_refresh_animal_adna_foundation_parser
from .collection_contracts import (
    build_collect_data_parser,
    build_refresh_aadr_source_accountability_parser,
    build_refresh_data_contract_surfaces_parser,
    build_validate_collection_summary_parser,
)
from .orientation import (
    build_ownership_map_parser,
    build_product_scope_parser,
    build_source_support_parser,
    build_surface_map_parser,
)
from .reporting import (
    build_multi_country_map_parser,
    build_publish_reports_parser,
    build_report_country_parser,
)

__all__ = [
    "build_adna_archive_projects_parser",
    "build_adna_artifact_plan_parser",
    "build_adna_curation_manifest_parser",
    "build_adna_domestication_coverage_parser",
    "build_adna_layout_parser",
    "build_adna_normalization_bundle_parser",
    "build_adna_release_bar_parser",
    "build_adna_release_readiness_parser",
    "build_adna_runtime_manifest_parser",
    "build_adna_species_parser",
    "build_adna_species_review_parser",
    "build_collect_data_parser",
    "build_multi_country_map_parser",
    "build_ownership_map_parser",
    "build_product_scope_parser",
    "build_publish_reports_parser",
    "build_refresh_animal_adna_foundation_parser",
    "build_refresh_aadr_source_accountability_parser",
    "build_refresh_data_contract_surfaces_parser",
    "build_report_country_parser",
    "build_source_support_parser",
    "build_surface_map_parser",
    "build_validate_collection_summary_parser",
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
    build_refresh_aadr_source_accountability_parser(subparsers)
    build_refresh_data_contract_surfaces_parser(subparsers)
    build_surface_map_parser(subparsers)
    build_product_scope_parser(subparsers)
    build_ownership_map_parser(subparsers)
    build_source_support_parser(subparsers)
    build_validate_collection_summary_parser(subparsers)
