from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ContextPointRecord:
    source: str
    layer_key: str
    layer_label: str
    category: str
    country: str
    record_id: str
    name: str
    latitude: float
    longitude: float
    geometry_type: str
    subtitle: str
    description: str
    source_url: str
    record_count: int
    popup_rows: tuple[tuple[str, str], ...]
    time_start_bp: int | None = None
    time_end_bp: int | None = None
    time_mean_bp: int | None = None
    time_label: str = ""


@dataclass(frozen=True)
class ContextDataReport:
    generated_on: str
    output_root: Path
    landclim_site_count: int
    landclim_grid_cell_count: int
    neotoma_point_count: int
    sead_point_count: int
    raa_total_site_count: int
    raa_heritage_site_count: int


@dataclass(frozen=True)
class DataCollectionSummary:
    generated_on: str
    output_root: Path
    version: str
    collected_sources: tuple[str, ...]
    source_output_roots: dict[str, str]
    boundary_source: str | None
    aadr_file_count: int
    landclim_site_count: int
    landclim_grid_cell_count: int
    neotoma_point_count: int
    sead_point_count: int
    raa_total_site_count: int
    raa_heritage_site_count: int
    summary_path: Path
