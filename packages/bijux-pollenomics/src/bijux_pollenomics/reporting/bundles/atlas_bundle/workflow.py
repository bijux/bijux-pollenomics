"""Ordered orchestration of atlas bundle publication."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import publish_contracts
from .evidence import publish_evidence_and_rankings
from .finalization import finalize_bundle
from .layers import prepare_layers


def publish_bundle(
    staging_output_dir: Path,
    *,
    report: Any,
    title: str,
    version: str,
    generated_on: str,
    countries: tuple[str, ...],
    country_sample_counts: dict[str, int],
    all_samples: Any,
    context_root: Path | None,
    geography_scope: Any,
    asset_base_path: str,
    build_atlas_bundle_paths_fn: Any,
    build_context_layers_fn: Any,
    build_multi_country_map_summary_fn: Any,
    build_samples_geojson_fn: Any,
    copy_map_assets_fn: Any,
    render_multi_country_map_html_fn: Any,
    render_multi_country_map_markdown_fn: Any,
    write_summary_json_fn: Any,
    atlas_detail_records: Any,
    atlas_scientific_signals: Any,
    atlas_edge_records: Any,
    atlas_sequence_records: Any,
    surface: Any,
) -> None:
    (
        bundle_paths,
        point_layers,
        polygon_layers,
        extra_artifacts,
        animal_localities,
        animal_coordinate_review,
        detail_projection_reconciliation,
        static_assets,
    ) = prepare_layers(
        staging_output_dir,
        report=report,
        version=version,
        all_samples=all_samples,
        context_root=context_root,
        geography_scope=geography_scope,
        build_atlas_bundle_paths_fn=build_atlas_bundle_paths_fn,
        build_context_layers_fn=build_context_layers_fn,
        build_samples_geojson_fn=build_samples_geojson_fn,
        atlas_detail_records=atlas_detail_records,
        atlas_scientific_signals=atlas_scientific_signals,
        atlas_edge_records=atlas_edge_records,
        atlas_sequence_records=atlas_sequence_records,
        surface=surface,
    )
    animal_atlas_summary = surface._build_animal_atlas_summary(
        point_layers,
        animal_localities,
        animal_coordinate_review,
    )
    map_policy, map_publication_contract = publish_contracts(
        report=report,
        geography_scope=geography_scope,
        countries=countries,
        point_layers=point_layers,
        polygon_layers=polygon_layers,
        bundle_paths=bundle_paths,
        detail_projection_reconciliation=detail_projection_reconciliation,
        static_assets=static_assets,
        write_summary_json_fn=write_summary_json_fn,
        surface=surface,
    )
    publish_evidence_and_rankings(
        title=title,
        countries=countries,
        all_samples=all_samples,
        context_root=context_root,
        bundle_paths=bundle_paths,
        point_layers=point_layers,
        animal_localities=animal_localities,
        animal_coordinate_review=animal_coordinate_review,
        extra_artifacts=extra_artifacts,
        surface=surface,
    )
    finalize_bundle(
        staging_output_dir=staging_output_dir,
        report=report,
        title=title,
        version=version,
        generated_on=generated_on,
        countries=countries,
        country_sample_counts=country_sample_counts,
        asset_base_path=asset_base_path,
        bundle_paths=bundle_paths,
        point_layers=point_layers,
        polygon_layers=polygon_layers,
        extra_artifacts=extra_artifacts,
        map_policy=map_policy,
        map_publication_contract=map_publication_contract,
        animal_atlas_summary=animal_atlas_summary,
        static_assets=static_assets,
        build_multi_country_map_summary_fn=build_multi_country_map_summary_fn,
        copy_map_assets_fn=copy_map_assets_fn,
        render_multi_country_map_html_fn=render_multi_country_map_html_fn,
        render_multi_country_map_markdown_fn=render_multi_country_map_markdown_fn,
        write_summary_json_fn=write_summary_json_fn,
        surface=surface,
    )
