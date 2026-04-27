from __future__ import annotations

from collections.abc import Callable, Iterable
import json
from pathlib import Path

from ...core.geojson import JsonObject
from ...analysis import (
    rank_localities,
    render_candidate_site_markdown,
    write_candidate_sites_csv,
)
from ...data_downloader.models import ContextPointRecord
from ..models import MultiCountryMapReport, SampleRecord
from ..aadr import summarize_localities
from .paths import AtlasBundlePaths
from .summary_builders.atlas import build_multi_country_bundle_manifest

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
        version=version,
        output_dir=staging_output_dir,
        context_root=context_root,
    )
    ranked_sites = rank_localities(
        summarize_localities(all_samples),
        _extract_context_points(point_layers),
    )
    write_candidate_sites_csv(bundle_paths.candidate_sites_csv_path, ranked_sites)
    bundle_paths.candidate_sites_markdown_path.write_text(
        render_candidate_site_markdown(ranked_sites, title=title),
        encoding="utf-8",
    )
    extra_artifacts.extend(
        [
            ("Candidate site ranking CSV", bundle_paths.candidate_sites_csv_path.name),
            (
                "Candidate site ranking markdown",
                bundle_paths.candidate_sites_markdown_path.name,
            ),
        ]
    )
    write_summary_json_fn(
        bundle_paths.bundle_manifest_path,
        build_multi_country_bundle_manifest(report, bundle_paths, extra_artifacts),
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


def _extract_context_points(
    point_layers: list[dict[str, object]],
) -> tuple[ContextPointRecord, ...]:
    records: list[ContextPointRecord] = []
    for layer in point_layers:
        raw_points = layer.get("features")
        if not isinstance(raw_points, list):
            continue
        for raw_point in raw_points:
            if not isinstance(raw_point, dict):
                continue
            latitude = raw_point.get("latitude")
            longitude = raw_point.get("longitude")
            if not isinstance(latitude, (int, float)) or not isinstance(
                longitude, (int, float)
            ):
                continue
            records.append(
                ContextPointRecord(
                    source=str(layer.get("source_name", "")),
                    layer_key=str(layer.get("key", "")),
                    layer_label=str(layer.get("label", "")),
                    category=str(raw_point.get("subtitle", "")),
                    country=str(raw_point.get("country", "")),
                    record_id=str(raw_point.get("title", "")),
                    name=str(raw_point.get("title", "")),
                    latitude=float(latitude),
                    longitude=float(longitude),
                    geometry_type="Point",
                    subtitle=str(raw_point.get("subtitle", "")),
                    description=str(layer.get("description", "")),
                    source_url=str(raw_point.get("source_url", "")),
                    record_count=int(layer.get("count", 1)),
                    popup_rows=(),
                    time_start_bp=_as_optional_int(raw_point.get("time_start_bp")),
                    time_end_bp=_as_optional_int(raw_point.get("time_end_bp")),
                    time_mean_bp=_as_optional_int(raw_point.get("time_mean_bp")),
                    time_label=str(raw_point.get("time_label", "")),
                )
            )
    return tuple(records)


def _as_optional_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    return None
