"""Historical atlas-bundle API routed through the package surface."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
import importlib
from pathlib import Path
from types import ModuleType
from typing import cast

from ....adna import AdnaLocalitySummary
from ....collection.contracts.models import ContextPointRecord
from ....core.geospatial.geojson import JsonObject
from ....evidence import AnimalCoordinateVisibilityReview
from ...geography import GeographicScope
from ...models import MultiCountryMapReport, SampleRecord
from ..paths import AtlasBundlePaths
from .context import (
    as_optional_int,
    attach_traceability_surfaces,
    build_animal_atlas_summary,
    extract_context_points,
    layer_features,
)
from .workflow import publish_bundle


def _surface() -> ModuleType:
    return importlib.import_module(__package__ or "")


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
    geography_scope: GeographicScope | None,
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
    atlas_detail_records: Sequence[JsonObject] | None = None,
    atlas_scientific_signals: Sequence[JsonObject] | None = None,
    atlas_edge_records: Sequence[JsonObject] | None = None,
    atlas_sequence_records: Sequence[JsonObject] | None = None,
) -> None:
    """Write the full atlas bundle into one staging directory."""
    publish_bundle(
        staging_output_dir,
        report=report,
        title=title,
        version=version,
        generated_on=generated_on,
        countries=countries,
        country_sample_counts=country_sample_counts,
        all_samples=all_samples,
        context_root=context_root,
        geography_scope=geography_scope,
        asset_base_path=asset_base_path,
        build_atlas_bundle_paths_fn=build_atlas_bundle_paths_fn,
        build_context_layers_fn=build_context_layers_fn,
        build_multi_country_map_summary_fn=build_multi_country_map_summary_fn,
        build_samples_geojson_fn=build_samples_geojson_fn,
        copy_map_assets_fn=copy_map_assets_fn,
        render_multi_country_map_html_fn=render_multi_country_map_html_fn,
        render_multi_country_map_markdown_fn=render_multi_country_map_markdown_fn,
        write_summary_json_fn=write_summary_json_fn,
        atlas_detail_records=atlas_detail_records,
        atlas_scientific_signals=atlas_scientific_signals,
        atlas_edge_records=atlas_edge_records,
        atlas_sequence_records=atlas_sequence_records,
        surface=_surface(),
    )


def _extract_context_points(
    point_layers: list[dict[str, object]],
) -> tuple[ContextPointRecord, ...]:
    return cast(
        tuple[ContextPointRecord, ...],
        extract_context_points(point_layers, surface=_surface()),
    )


def _as_optional_int(value: object) -> int | None:
    return as_optional_int(value)


def _build_animal_atlas_summary(
    point_layers: list[dict[str, object]],
    animal_localities: tuple[AdnaLocalitySummary, ...],
    animal_coordinate_review: AnimalCoordinateVisibilityReview,
) -> dict[str, object]:
    return build_animal_atlas_summary(
        point_layers,
        animal_localities,
        animal_coordinate_review,
        surface=_surface(),
    )


def _layer_features(layer: dict[str, object]) -> list[dict[str, object]]:
    return layer_features(layer)


def _attach_traceability_surfaces(
    point_layers: list[dict[str, object]],
    bundle_paths: AtlasBundlePaths,
) -> None:
    attach_traceability_surfaces(point_layers, bundle_paths)
