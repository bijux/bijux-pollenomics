from __future__ import annotations

from collections.abc import Callable, Iterable
import json
from pathlib import Path

from ...core.geojson import JsonObject
from ..models import MultiCountryMapReport, SampleRecord
from .paths import AtlasBundlePaths

__all__ = ["publish_multi_country_map_bundle"]


def publish_multi_country_map_bundle(
    staging_output_dir: Path,
    *,
    report: MultiCountryMapReport,
    title: str,
    version: str,
    generated_on: str,
    countries: tuple[str, ...],
    country_sample_counts: dict[str, int],
    all_samples: tuple[SampleRecord, ...],
    context_root: Path | None,
    asset_base_path: str,
    build_atlas_bundle_paths_fn: Callable[..., AtlasBundlePaths],
    build_context_layers_fn: Callable[
        ...,
        tuple[list[dict[str, object]], list[dict[str, object]], list[tuple[str, str]]],
    ],
    build_multi_country_map_summary_fn: Callable[..., dict[str, object]],
    build_samples_geojson_fn: Callable[[Iterable[SampleRecord]], JsonObject],
    copy_map_assets_fn: Callable[[Path], Path],
    render_multi_country_map_html_fn: Callable[..., str],
    render_multi_country_map_markdown_fn: Callable[..., str],
    write_summary_json_fn: Callable[[Path, dict[str, object]], None],
) -> None:
    """Write the full atlas bundle into one staging directory."""
    bundle_paths = build_atlas_bundle_paths_fn(
        output_dir=staging_output_dir, slug=report.slug, version=version
    )
    map_geojson = build_samples_geojson_fn(all_samples)
    bundle_paths.samples_geojson_path.write_text(
        json.dumps(map_geojson, indent=2), encoding="utf-8"
    )
    point_layers, polygon_layers, extra_artifacts = build_context_layers_fn(
        samples=all_samples,
        output_dir=staging_output_dir,
        context_root=context_root,
    )
    copy_map_assets_fn(staging_output_dir)
    write_summary_json_fn(
        bundle_paths.summary_json_path,
        build_multi_country_map_summary_fn(report, bundle_paths, extra_artifacts),
    )
    bundle_paths.map_html_path.write_text(
        render_multi_country_map_html_fn(
            title=title,
            version=version,
            generated_on=generated_on,
            countries=countries,
            point_layers=point_layers,
            polygon_layers=polygon_layers,
            asset_base_path=asset_base_path,
        ),
        encoding="utf-8",
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
            extra_artifacts=extra_artifacts,
        ),
        encoding="utf-8",
    )
