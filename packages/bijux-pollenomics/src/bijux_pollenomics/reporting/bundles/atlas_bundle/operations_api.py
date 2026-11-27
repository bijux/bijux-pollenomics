"""Historical atlas-bundle API routed through the package surface."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
import importlib
from pathlib import Path
from types import ModuleType
from typing import TypedDict, cast

from bijux_pollenomics.adna.governance.atlas_candidates.point_inputs import (
    AnimalPointInputs,
)
from bijux_pollenomics.reporting.adna.sample_chronology_context.captured_inputs import (
    AnimalChronologyInputs,
)
from bijux_pollenomics.reporting.context.points.fieldwork_inputs import (
    FieldworkMediaInputs,
)

from ....adna import AdnaLocalitySummary
from ....adna.species.homo_sapiens.map_snapshot import AadrMapSnapshot
from ....collection.contracts.models import ContextPointRecord
from ....core.geospatial.geojson import JsonObject
from ....evidence import AnimalCoordinateVisibilityReview
from ...context.nordic_point_inputs import NordicPointInputs
from ...context.nordic_polygon_inputs import NordicPolygonInputs
from ...geography import GeographicScope
from ...map_document.evidence_projection import HistoricalChronologyRequest
from ...map_document.source_resources import AtlasResourceCatalogueInput
from ...models import MultiCountryMapReport, SampleRecord
from ..paths import AtlasBundlePaths
from ..sweden_lake_inputs import SwedenLakeInputs
from .context import (
    as_optional_int,
    attach_traceability_surfaces,
    build_animal_atlas_summary,
    extract_context_points,
    layer_features,
)
from .workflow import publish_bundle


class _OptionalInputs(TypedDict, total=False):
    source_resource_catalogue: AtlasResourceCatalogueInput
    historical_chronology: HistoricalChronologyRequest
    lake_inputs: SwedenLakeInputs
    nordic_point_inputs: NordicPointInputs
    nordic_polygon_inputs: NordicPolygonInputs
    animal_point_inputs: AnimalPointInputs
    animal_chronology_inputs: AnimalChronologyInputs
    neotoma_manifest_sha256: str
    raa_status_sha256: str
    fieldwork_inputs: FieldworkMediaInputs
    aadr_map_snapshot: AadrMapSnapshot


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
    write_static_map_document_fn: Callable[..., tuple[Path, Path]],
    render_multi_country_map_markdown_fn: Callable[..., str],
    write_summary_json_fn: Callable[[Path, dict[str, object]], None],
    atlas_detail_records: Sequence[JsonObject] | None = None,
    atlas_scientific_signals: Sequence[JsonObject] | None = None,
    atlas_edge_records: Sequence[JsonObject] | None = None,
    atlas_sequence_records: Sequence[JsonObject] | None = None,
    publication_capture_root: Path | None = None,
    source_resource_catalogue: AtlasResourceCatalogueInput | None = None,
    historical_chronology: HistoricalChronologyRequest | None = None,
    lake_inputs: SwedenLakeInputs | None = None,
    nordic_point_inputs: NordicPointInputs | None = None,
    nordic_polygon_inputs: NordicPolygonInputs | None = None,
    animal_point_inputs: AnimalPointInputs | None = None,
    animal_chronology_inputs: AnimalChronologyInputs | None = None,
    neotoma_manifest_sha256: str | None = None,
    raa_status_sha256: str | None = None,
    fieldwork_inputs: FieldworkMediaInputs | None = None,
    aadr_map_snapshot: AadrMapSnapshot | None = None,
) -> None:
    """Write the full atlas bundle into one staging directory."""
    optional_inputs: _OptionalInputs = {}
    if source_resource_catalogue is not None:
        optional_inputs["source_resource_catalogue"] = source_resource_catalogue
    if historical_chronology is not None:
        optional_inputs["historical_chronology"] = historical_chronology
    if lake_inputs is not None:
        optional_inputs["lake_inputs"] = lake_inputs
    if nordic_point_inputs is not None:
        optional_inputs["nordic_point_inputs"] = nordic_point_inputs
    if nordic_polygon_inputs is not None:
        optional_inputs["nordic_polygon_inputs"] = nordic_polygon_inputs
    if animal_point_inputs is not None:
        optional_inputs["animal_point_inputs"] = animal_point_inputs
    if animal_chronology_inputs is not None:
        optional_inputs["animal_chronology_inputs"] = animal_chronology_inputs
    if neotoma_manifest_sha256 is not None:
        optional_inputs["neotoma_manifest_sha256"] = neotoma_manifest_sha256
    if raa_status_sha256 is not None:
        optional_inputs["raa_status_sha256"] = raa_status_sha256
    if fieldwork_inputs is not None:
        optional_inputs["fieldwork_inputs"] = fieldwork_inputs
    if aadr_map_snapshot is not None:
        optional_inputs["aadr_map_snapshot"] = aadr_map_snapshot
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
        write_static_map_document_fn=write_static_map_document_fn,
        render_multi_country_map_markdown_fn=render_multi_country_map_markdown_fn,
        write_summary_json_fn=write_summary_json_fn,
        atlas_detail_records=atlas_detail_records,
        atlas_scientific_signals=atlas_scientific_signals,
        atlas_edge_records=atlas_edge_records,
        atlas_sequence_records=atlas_sequence_records,
        surface=_surface(),
        publication_capture_root=publication_capture_root,
        **optional_inputs,
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
