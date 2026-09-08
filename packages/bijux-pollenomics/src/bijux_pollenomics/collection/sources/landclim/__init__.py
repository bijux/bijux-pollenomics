"""LANDCLIM source collectors for grid and site evidence."""

from .catalog import (
    LANDCLIM_DATASET_METADATA,
    LandClimRawAssets,
    build_landclim_bibliography,
    build_landclim_raw_asset_summaries,
    inspect_landclim_ii_archive,
    resolve_landclim_asset_urls,
    resolve_landclim_marquer_asset_urls,
    resolve_landclim_tabular_asset_urls,
    validate_landclim_raw_asset,
)
from .grid import (
    LANDCLIM_GRID_LAYER_KEY,
    build_landclim_grid_geojson,
    feature_key_from_center,
    feature_key_from_geometry,
    grid_geometry_from_nw_cell_label,
)
from .review import (
    build_landclim_spatiotemporal_review,
    render_landclim_spatiotemporal_review_markdown,
    write_landclim_review_outputs,
)
from .sites import (
    LANDCLIM_SITE_LAYER_KEY,
    build_landclim_site_records,
    landclim_i_site_records,
    landclim_ii_site_records,
    parse_coordinate,
)
from .time_windows import (
    LANDCLIM_TEMPORAL_GRID_LAYER_KEY,
    build_landclim_temporal_grid_geojson,
)

__all__ = [
    "LANDCLIM_DATASET_METADATA",
    "LANDCLIM_GRID_LAYER_KEY",
    "LANDCLIM_SITE_LAYER_KEY",
    "LANDCLIM_TEMPORAL_GRID_LAYER_KEY",
    "LandClimRawAssets",
    "build_landclim_bibliography",
    "build_landclim_grid_geojson",
    "build_landclim_raw_asset_summaries",
    "build_landclim_site_records",
    "build_landclim_spatiotemporal_review",
    "build_landclim_temporal_grid_geojson",
    "feature_key_from_center",
    "feature_key_from_geometry",
    "grid_geometry_from_nw_cell_label",
    "inspect_landclim_ii_archive",
    "landclim_i_site_records",
    "landclim_ii_site_records",
    "parse_coordinate",
    "render_landclim_spatiotemporal_review_markdown",
    "resolve_landclim_asset_urls",
    "resolve_landclim_marquer_asset_urls",
    "resolve_landclim_tabular_asset_urls",
    "validate_landclim_raw_asset",
    "write_landclim_review_outputs",
]
