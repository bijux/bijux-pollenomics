"""Import and signature compatibility for subcommand builders."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from contextlib import ExitStack
import inspect
from typing import cast
from unittest.mock import patch

from bijux_pollenomics.command_line.parsing import subcommands

_BUILDERS = [name for name in subcommands.__all__ if name != "register_subcommands"]
_REGISTRATION_ORDER = [
    "build_adna_archive_projects_parser",
    "build_adna_artifact_plan_parser",
    "build_adna_curation_manifest_parser",
    "build_adna_domestication_coverage_parser",
    "build_adna_layout_parser",
    "build_adna_release_bar_parser",
    "build_adna_release_readiness_parser",
    "build_adna_normalization_bundle_parser",
    "build_adna_runtime_manifest_parser",
    "build_adna_species_parser",
    "build_adna_species_review_parser",
    "build_refresh_animal_adna_foundation_parser",
    "build_report_country_parser",
    "build_multi_country_map_parser",
    "build_publish_reports_parser",
    "build_collect_data_parser",
    "build_refresh_aadr_source_accountability_parser",
    "build_refresh_data_contract_surfaces_parser",
    "build_surface_map_parser",
    "build_product_scope_parser",
    "build_ownership_map_parser",
    "build_source_support_parser",
    "build_validate_collection_summary_parser",
]


def test_export_order_covers_every_supported_builder() -> None:
    assert subcommands.__all__ == [
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


def test_builder_signatures_remain_uniform() -> None:
    expected = (
        "(subparsers: 'argparse._SubParsersAction[argparse.ArgumentParser]') "
        "-> 'argparse.ArgumentParser'"
    )
    assert len(_BUILDERS) == 23
    assert all(
        str(inspect.signature(getattr(subcommands, name))) == expected
        for name in _BUILDERS
    )
    assert str(inspect.signature(subcommands.register_subcommands)) == (
        "(subparsers: 'argparse._SubParsersAction[argparse.ArgumentParser]') -> 'None'"
    )


def test_legacy_dependency_imports_remain_reachable() -> None:
    for name in (
        "AVAILABLE_SOURCES",
        "DEFAULT_AADR_VERSION",
        "DEFAULT_CONTEXT_ROOT",
        "DEFAULT_DATA_ROOT",
        "DEFAULT_PUBLISHED_COUNTRIES",
        "Path",
        "add_aadr_root_argument",
        "add_atlas_identity_arguments",
        "add_context_root_argument",
        "add_output_root_argument",
        "add_version_argument",
        "argparse",
    ):
        assert hasattr(subcommands, name)


def test_registration_retains_facade_monkeypatch_seams_and_order() -> None:
    calls: list[str] = []
    sentinel = cast("argparse._SubParsersAction[argparse.ArgumentParser]", object())

    def replacement(
        name: str,
    ) -> Callable[
        [argparse._SubParsersAction[argparse.ArgumentParser]],
        argparse.ArgumentParser,
    ]:
        def builder(
            subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
        ) -> argparse.ArgumentParser:
            assert subparsers is sentinel
            calls.append(name)
            return cast(argparse.ArgumentParser, object())

        return builder

    with ExitStack() as patches:
        for name in _REGISTRATION_ORDER:
            patches.enter_context(patch.object(subcommands, name, replacement(name)))
        subcommands.register_subcommands(sentinel)

    assert calls == _REGISTRATION_ORDER
