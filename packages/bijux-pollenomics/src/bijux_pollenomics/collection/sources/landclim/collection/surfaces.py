"""Publication workflows for normalized LandClim repository surfaces."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from .....config import NORDIC_BBOX
from .....core.files import write_json
from .....core.geospatial.geojson import feature_list
from ....contracts.artifacts import (
    LANDCLIM_BIBLIOGRAPHY_JSON,
    LANDCLIM_GRID_GEOJSON,
    LANDCLIM_SITE_CSV,
    LANDCLIM_SITE_GEOJSON,
    LANDCLIM_TEMPORAL_GRID_GEOJSON,
)
from ....exports.context_points import (
    write_context_points_csv,
    write_context_points_geojson,
)
from ...boundaries.store import load_repository_country_boundaries
from ..catalog import LandClimRawAssets, build_landclim_bibliography
from ..grid import build_landclim_grid_geojson
from ..review import write_landclim_review_outputs
from ..sites import build_landclim_site_records
from ..time_windows import build_landclim_temporal_grid_geojson
from .model import LandClimDataReport
from .surface_summary import build_surface_summary

RawAssetCollector = Callable[[Path], LandClimRawAssets]
RawReceiptBuilder = Callable[..., dict[str, object]]
RawReceiptValidator = Callable[[Path], dict[str, object]]
GeneratedOn = Callable[[], str]


def collect_landclim_data(
    output_root: Path,
    country_boundaries: dict[str, dict[str, object]],
    bbox: tuple[float, float, float, float],
    *,
    raw_asset_collector: RawAssetCollector,
    raw_receipt_builder: RawReceiptBuilder,
    raw_receipt_validator: RawReceiptValidator,
    generated_on: GeneratedOn,
) -> LandClimDataReport:
    """Download and normalize LandClim PANGAEA datasets under data/landclim."""
    output_root = Path(output_root)
    raw_dir = output_root / "raw"
    normalized_dir = output_root / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    raw_assets = raw_asset_collector(raw_dir)
    raw_manifest_path = raw_dir / "landclim_sources.json"

    def publish_receipt() -> None:
        write_json(
            raw_manifest_path,
            raw_receipt_builder(
                raw_assets.paths,
                raw_assets.asset_urls,
                generated_on=generated_on(),
            ),
        )
        raw_receipt_validator(raw_dir)

    return _publish_surfaces(
        output_root,
        raw_assets.paths,
        country_boundaries=country_boundaries,
        bbox=bbox,
        raw_manifest_path=raw_manifest_path,
        repository_paths=False,
        generated_on=generated_on,
        before_publication=publish_receipt,
    )


def materialize_landclim_repository_surfaces(
    data_root: Path,
    *,
    raw_receipt_validator: RawReceiptValidator,
    generated_on: GeneratedOn,
) -> LandClimDataReport:
    """Refresh normalized LandClim surfaces from the checked-in raw capture."""
    data_root = Path(data_root)
    output_root = data_root / "landclim"
    raw_dir = output_root / "raw"
    raw_receipt_validator(raw_dir)
    (output_root / "normalized").mkdir(parents=True, exist_ok=True)
    raw_paths = {
        path.name: path
        for path in raw_dir.iterdir()
        if path.is_file() and path.name != "landclim_sources.json"
    }
    return _publish_surfaces(
        output_root,
        raw_paths,
        country_boundaries=load_repository_country_boundaries(data_root),
        bbox=NORDIC_BBOX,
        raw_manifest_path=raw_dir / "landclim_sources.json",
        repository_paths=True,
        generated_on=generated_on,
        before_publication=lambda: None,
    )


def _publish_surfaces(
    output_root: Path,
    raw_paths: dict[str, Path],
    *,
    country_boundaries: dict[str, dict[str, object]],
    bbox: tuple[float, float, float, float],
    raw_manifest_path: Path,
    repository_paths: bool,
    generated_on: GeneratedOn,
    before_publication: Callable[[], None],
) -> LandClimDataReport:
    site_records = build_landclim_site_records(
        raw_paths, bbox=bbox, country_boundaries=country_boundaries
    )
    grid_geojson = build_landclim_grid_geojson(
        raw_paths, bbox=bbox, country_boundaries=country_boundaries
    )
    temporal_grid_geojson = build_landclim_temporal_grid_geojson(
        raw_paths, bbox=bbox, country_boundaries=country_boundaries
    )
    before_publication()
    data_root = output_root.parent
    paths = (
        (
            LANDCLIM_SITE_CSV.path_under(data_root),
            LANDCLIM_SITE_GEOJSON.path_under(data_root),
            LANDCLIM_GRID_GEOJSON.path_under(data_root),
            LANDCLIM_TEMPORAL_GRID_GEOJSON.path_under(data_root),
            LANDCLIM_BIBLIOGRAPHY_JSON.path_under(data_root),
        )
        if repository_paths
        else (
            LANDCLIM_SITE_CSV.source_path_under(output_root),
            LANDCLIM_SITE_GEOJSON.source_path_under(output_root),
            LANDCLIM_GRID_GEOJSON.source_path_under(output_root),
            LANDCLIM_TEMPORAL_GRID_GEOJSON.source_path_under(output_root),
            LANDCLIM_BIBLIOGRAPHY_JSON.source_path_under(output_root),
        )
    )
    sites_csv, sites_geojson, grid_path, temporal_path, bibliography_path = paths
    write_context_points_csv(sites_csv, site_records)
    write_context_points_geojson(sites_geojson, site_records)
    write_json(grid_path, grid_geojson)
    write_json(temporal_path, temporal_grid_geojson)
    bibliography = build_landclim_bibliography()
    write_json(bibliography_path, bibliography)
    review_path = write_landclim_review_outputs(
        output_root,
        records=site_records,
        temporal_grid_geojson=temporal_grid_geojson,
        bibliography=bibliography,
    )
    summary_path = output_root / "normalized" / "landclim_summary.json"
    write_json(
        summary_path,
        build_surface_summary(
            site_records,
            grid_geojson,
            temporal_grid_geojson,
            generated_on=generated_on(),
            repository_paths=repository_paths,
        ),
    )
    return LandClimDataReport(
        output_dir=output_root,
        site_count=len(site_records),
        grid_cell_count=len(feature_list(grid_geojson)),
        temporal_grid_feature_count=len(feature_list(temporal_grid_geojson)),
        raw_manifest_path=raw_manifest_path,
        normalized_sites_csv_path=sites_csv,
        normalized_sites_geojson_path=sites_geojson,
        normalized_grid_geojson_path=grid_path,
        normalized_temporal_grid_geojson_path=temporal_path,
        bibliography_path=bibliography_path,
        review_path=review_path,
        summary_path=summary_path,
    )
