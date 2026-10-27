"""Bundle manifest, summary, HTML, and README finalization."""

from __future__ import annotations

from typing import Any

from ...map_document.render import static_map_optional_controller_paths


def finalize_bundle(
    *,
    staging_output_dir: Any,
    report: Any,
    title: str,
    version: str,
    generated_on: str,
    countries: tuple[str, ...],
    country_sample_counts: dict[str, int],
    asset_base_path: str,
    bundle_paths: Any,
    point_layers: list[dict[str, object]],
    polygon_layers: list[dict[str, object]],
    extra_artifacts: list[tuple[str, str]],
    map_policy: Any,
    map_publication_contract: dict[str, object],
    animal_atlas_summary: dict[str, object],
    static_assets: Any,
    build_multi_country_map_summary_fn: Any,
    copy_map_assets_fn: Any,
    write_static_map_document_fn: Any,
    render_multi_country_map_markdown_fn: Any,
    write_summary_json_fn: Any,
    surface: Any,
) -> None:
    """Write the atlas document, inventory its runtime, and finalize bundle reports."""
    copy_map_assets_fn(staging_output_dir)
    _, runtime_path = write_static_map_document_fn(
        output_path=bundle_paths.map_html_path,
        title=title,
        version=version,
        generated_on=generated_on,
        countries=countries,
        policy=map_policy,
        point_layers=point_layers,
        polygon_layers=polygon_layers,
        asset_base_path=asset_base_path,
        static_assets=static_assets,
    )
    extra_artifacts.append(("Static atlas runtime", runtime_path.name))
    extra_artifacts.extend(
        (
            "Static atlas index transport"
            if path.name.rsplit(".", 3)[-3] == "atlas-index-transport"
            else "Interactive evidence tools",
            path.name,
        )
        for path in static_map_optional_controller_paths(bundle_paths.map_html_path)
    )
    write_summary_json_fn(
        bundle_paths.bundle_manifest_path,
        surface.build_multi_country_bundle_manifest(
            report,
            bundle_paths,
            extra_artifacts,
            map_publication_contract=map_publication_contract,
            animal_atlas_summary=animal_atlas_summary,
        ),
    )
    write_summary_json_fn(
        bundle_paths.summary_json_path,
        build_multi_country_map_summary_fn(
            report,
            bundle_paths,
            extra_artifacts,
            map_publication_contract=map_publication_contract,
            animal_atlas_summary=animal_atlas_summary,
        ),
    )
    bundle_paths.readme_path.write_text(
        render_multi_country_map_markdown_fn(
            title=title,
            version=version,
            generated_on=generated_on,
            countries=countries,
            country_sample_counts=country_sample_counts,
            map_html_name=bundle_paths.map_html_path.name,
            geojson_name=bundle_paths.samples_geojson_path.name,
            summary_json_name=bundle_paths.summary_json_path.name,
            map_publication_contract_json_name=(
                bundle_paths.map_publication_contract_json_path.name
            ),
            map_publication_contract_markdown_name=(
                bundle_paths.map_publication_contract_markdown_path.name
            ),
            point_traceability_json_name=(
                bundle_paths.map_point_traceability_json_path.name
            ),
            point_traceability_markdown_name=(
                bundle_paths.map_point_traceability_markdown_path.name
            ),
            extra_artifacts=extra_artifacts,
            map_publication_contract=map_publication_contract,
            animal_atlas_summary=animal_atlas_summary,
        ),
        encoding="utf-8",
    )
