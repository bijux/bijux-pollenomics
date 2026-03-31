from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..core.files import write_json
from ..core.http import fetch_binary
from .contracts import LANDCLIM_GRID_GEOJSON, LANDCLIM_SITE_CSV, LANDCLIM_SITE_GEOJSON
from .sources.landclim.catalog import (
    LANDCLIM_DATASET_METADATA,
    LandClimRawAssets,
    build_landclim_raw_asset_summaries,
    inspect_landclim_ii_archive,
    resolve_landclim_asset_urls as _resolve_landclim_asset_urls,
    resolve_landclim_marquer_asset_urls,
    resolve_landclim_tabular_asset_urls,
    validate_landclim_raw_asset,
)
from .sources.landclim.grid import (
    LANDCLIM_GRID_LAYER_KEY,
    build_landclim_grid_geojson,
    feature_key_from_center,
    feature_key_from_geometry,
    grid_geometry_from_nw_cell_label,
)
from .sources.landclim.sites import (
    LANDCLIM_SITE_LAYER_KEY,
    build_landclim_site_records,
    landclim_i_site_records,
    landclim_ii_site_records,
    parse_coordinate,
)
from .writers import write_context_points_csv, write_context_points_geojson


@dataclass(frozen=True)
class LandClimDataReport:
    output_dir: Path
    site_count: int
    grid_cell_count: int
    raw_manifest_path: Path
    normalized_sites_csv_path: Path
    normalized_sites_geojson_path: Path
    normalized_grid_geojson_path: Path
    summary_path: Path


def collect_landclim_data(
    output_root: Path,
    country_boundaries: dict[str, dict[str, object]],
    bbox: tuple[float, float, float, float],
) -> LandClimDataReport:
    """Download and normalize LandClim PANGAEA datasets under data/landclim."""
    output_root = Path(output_root)
    raw_dir = output_root / "raw"
    normalized_dir = output_root / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    raw_assets = download_landclim_raw_assets(raw_dir)
    raw_paths = raw_assets.paths
    landclim_ii_archive_summary = inspect_landclim_ii_archive(raw_paths["landclim_ii_reveals_results.zip"])
    site_records = build_landclim_site_records(raw_paths, bbox=bbox, country_boundaries=country_boundaries)
    grid_geojson = build_landclim_grid_geojson(raw_paths, bbox=bbox, country_boundaries=country_boundaries)

    raw_manifest_path = raw_dir / "landclim_sources.json"
    write_json(
        raw_manifest_path,
        {
            "generated_on": str(date.today()),
            "source": "LandClim",
            "datasets": [
                {
                    "doi": LANDCLIM_DATASET_METADATA["900966"]["doi"],
                    "label": LANDCLIM_DATASET_METADATA["900966"]["label"],
                    "files": ["marquer_2017_reveals_taxa_grid_cells.xlsx"],
                },
                {
                    "doi": LANDCLIM_DATASET_METADATA["897303"]["doi"],
                    "label": LANDCLIM_DATASET_METADATA["897303"]["label"],
                    "files": [
                        "landclim_i_land_cover_types.xlsx",
                        "landclim_i_plant_functional_types.xlsx",
                    ],
                },
                {
                    "doi": LANDCLIM_DATASET_METADATA["937075"]["doi"],
                    "label": LANDCLIM_DATASET_METADATA["937075"]["label"],
                    "files": [
                        "landclim_ii_reveals_results.zip",
                        "landclim_ii_grid_cell_quality.xlsx",
                        "landclim_ii_contributors.xlsx",
                        "landclim_ii_site_metadata.xlsx",
                        "landclim_ii_taxa_pft_ppe_fsp_values.csv",
                    ],
                    "archive_summary": landclim_ii_archive_summary,
                },
            ],
            "assets": build_landclim_raw_asset_summaries(raw_paths, raw_assets.asset_urls),
        },
    )

    normalized_sites_csv_path = LANDCLIM_SITE_CSV.source_path_under(output_root)
    normalized_sites_geojson_path = LANDCLIM_SITE_GEOJSON.source_path_under(output_root)
    normalized_grid_geojson_path = LANDCLIM_GRID_GEOJSON.source_path_under(output_root)
    summary_path = normalized_dir / "landclim_summary.json"
    write_context_points_csv(normalized_sites_csv_path, site_records)
    write_context_points_geojson(normalized_sites_geojson_path, site_records)
    write_json(normalized_grid_geojson_path, grid_geojson)
    write_json(
        summary_path,
        {
            "generated_on": str(date.today()),
            "source": "LandClim",
            "site_count": len(site_records),
            "grid_cell_count": len(grid_geojson.get("features", [])),
            "site_layer_key": LANDCLIM_SITE_LAYER_KEY,
            "grid_layer_key": LANDCLIM_GRID_LAYER_KEY,
        },
    )

    return LandClimDataReport(
        output_dir=output_root,
        site_count=len(site_records),
        grid_cell_count=len(grid_geojson.get("features", [])),
        raw_manifest_path=raw_manifest_path,
        normalized_sites_csv_path=normalized_sites_csv_path,
        normalized_sites_geojson_path=normalized_sites_geojson_path,
        normalized_grid_geojson_path=normalized_grid_geojson_path,
        summary_path=summary_path,
    )


def resolve_landclim_asset_urls() -> dict[str, str]:
    """Backward-compatible access to the LandClim source catalog resolver."""
    return _resolve_landclim_asset_urls()


def download_landclim_raw_assets(raw_dir: Path) -> LandClimRawAssets:
    """Download the LandClim raw upstream assets used for normalization."""
    asset_urls = resolve_landclim_asset_urls()
    raw_paths: dict[str, Path] = {}
    for filename, url in asset_urls.items():
        path = Path(raw_dir) / filename
        payload = fetch_binary(url)
        validate_landclim_raw_asset(filename, payload)
        path.write_bytes(payload)
        raw_paths[filename] = path
    return LandClimRawAssets(paths=raw_paths, asset_urls=asset_urls)


__all__ = [
    "LandClimDataReport",
    "build_landclim_grid_geojson",
    "build_landclim_raw_asset_summaries",
    "build_landclim_site_records",
    "collect_landclim_data",
    "download_landclim_raw_assets",
    "feature_key_from_center",
    "feature_key_from_geometry",
    "grid_geometry_from_nw_cell_label",
    "inspect_landclim_ii_archive",
    "landclim_i_site_records",
    "landclim_ii_site_records",
    "parse_coordinate",
    "resolve_landclim_asset_urls",
    "resolve_landclim_marquer_asset_urls",
    "resolve_landclim_tabular_asset_urls",
]
