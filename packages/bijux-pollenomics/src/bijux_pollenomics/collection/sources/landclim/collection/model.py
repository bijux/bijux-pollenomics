"""LandClim collection result and refusal types."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class LandClimRawReceiptError(ValueError):
    """Raised when the governed LandClim raw receipt does not match its assets."""


@dataclass(frozen=True)
class LandClimDataReport:
    output_dir: Path
    site_count: int
    grid_cell_count: int
    temporal_grid_feature_count: int
    raw_manifest_path: Path
    normalized_sites_csv_path: Path
    normalized_sites_geojson_path: Path
    normalized_grid_geojson_path: Path
    normalized_temporal_grid_geojson_path: Path
    bibliography_path: Path
    review_path: Path
    summary_path: Path
