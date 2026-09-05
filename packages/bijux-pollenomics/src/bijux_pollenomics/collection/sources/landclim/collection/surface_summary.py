"""Stable summary documents for normalized LandClim surfaces."""

from __future__ import annotations

from .....core.geospatial.geojson import feature_list
from ....contracts.models import ContextPointRecord
from ..catalog import LANDCLIM_DATASET_METADATA
from ..grid import LANDCLIM_GRID_LAYER_KEY
from ..sites import LANDCLIM_SITE_LAYER_KEY
from ..time_windows import LANDCLIM_TEMPORAL_GRID_LAYER_KEY


def build_surface_summary(
    site_records: list[ContextPointRecord],
    grid_geojson: dict[str, object],
    temporal_grid_geojson: dict[str, object],
    *,
    generated_on: str,
    repository_paths: bool,
) -> dict[str, object]:
    numeric_intervals = sum(
        1
        for record in site_records
        if record.time_start_bp is not None and record.time_end_bp is not None
    )
    summary: dict[str, object] = {
        "generated_on": generated_on,
        "source": "LandClim",
        "site_count": len(site_records),
    }
    if repository_paths:
        summary["numeric_site_interval_count"] = numeric_intervals
    summary["grid_cell_count"] = len(feature_list(grid_geojson))
    summary["temporal_grid_feature_count"] = len(feature_list(temporal_grid_geojson))
    if not repository_paths:
        summary["numeric_site_interval_count"] = numeric_intervals
    summary.update(
        {
            "bibliography_dataset_count": len(LANDCLIM_DATASET_METADATA),
            "site_layer_key": LANDCLIM_SITE_LAYER_KEY,
            "grid_layer_key": LANDCLIM_GRID_LAYER_KEY,
            "temporal_grid_layer_key": LANDCLIM_TEMPORAL_GRID_LAYER_KEY,
        }
    )
    return summary
