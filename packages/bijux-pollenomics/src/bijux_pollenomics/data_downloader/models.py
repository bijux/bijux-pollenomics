from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceAcquisitionMetadata:
    source: str
    version: str
    license: str
    retrieved_on: str
    acquisition_method: str


@dataclass(frozen=True)
class SourceProvenanceRecord:
    source: str
    display_name: str
    evidence_family: str
    version: str
    license: str
    retrieved_on: str
    acquisition_method: str
    snapshot_root: str
    normalized_root: str
    snapshot_sha256: str
    normalized_sha256: str


@dataclass(frozen=True)
class SourceReplacementRule:
    source: str
    refresh_mode: str
    final_output_root: str
    staging_output_root: str
    destructive_refresh: bool
    preserves_previous_on_failure: bool


@dataclass(frozen=True)
class SourceTraceabilityRecord:
    source: str
    source_identity: str
    source_version: str
    snapshot_sha256: str
    normalized_sha256: str
    dispute_token: str


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
    source_metadata: dict[str, SourceAcquisitionMetadata]
    source_hashes: dict[str, dict[str, str]]
    source_provenance: dict[str, SourceProvenanceRecord]
    source_replacement_rules: dict[str, SourceReplacementRule]
    source_traceability: dict[str, SourceTraceabilityRecord]
    boundary_source: str | None
    aadr_file_count: int
    landclim_site_count: int
    landclim_grid_cell_count: int
    neotoma_point_count: int
    sead_point_count: int
    raa_total_site_count: int
    raa_heritage_site_count: int
    summary_path: Path


@dataclass(frozen=True)
class DataCollectionReport:
    generated_on: str
    output_root: Path
    version: str
    collected_sources: tuple[str, ...]
    source_output_roots: dict[str, str]
    source_metadata: dict[str, SourceAcquisitionMetadata]
    source_hashes: dict[str, dict[str, str]]
    source_provenance: dict[str, SourceProvenanceRecord]
    source_replacement_rules: dict[str, SourceReplacementRule]
    source_traceability: dict[str, SourceTraceabilityRecord]
    aadr_file_count: int
    landclim_site_count: int
    landclim_grid_cell_count: int
    neotoma_point_count: int
    sead_point_count: int
    raa_total_site_count: int
    raa_heritage_site_count: int
    boundary_source: str | None
    summary_path: Path
