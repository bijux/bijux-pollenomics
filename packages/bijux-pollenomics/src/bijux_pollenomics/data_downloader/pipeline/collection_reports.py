from __future__ import annotations

from datetime import date
from pathlib import Path

from ..models import DataCollectionReport, DataCollectionSummary

__all__ = [
    "build_data_collection_report",
    "build_data_collection_summary",
    "initialize_source_counts",
]


def initialize_source_counts() -> dict[str, int]:
    """Create a zeroed count mapping for every tracked source metric."""
    return {
        "aadr_file_count": 0,
        "landclim_site_count": 0,
        "landclim_grid_cell_count": 0,
        "neotoma_point_count": 0,
        "sead_point_count": 0,
        "raa_total_site_count": 0,
        "raa_heritage_site_count": 0,
    }


def build_data_collection_summary(
    *,
    output_root: Path,
    version: str,
    collected_sources: tuple[str, ...],
    source_output_roots: dict[str, str],
    boundary_source: str | None,
    counts: dict[str, int],
) -> DataCollectionSummary:
    """Build the machine-readable collection summary from collected source counts."""
    summary_path = output_root / "collection_summary.json"
    return DataCollectionSummary(
        generated_on=str(date.today()),
        output_root=output_root,
        version=version,
        collected_sources=collected_sources,
        source_output_roots=source_output_roots,
        boundary_source=boundary_source,
        aadr_file_count=counts["aadr_file_count"],
        landclim_site_count=counts["landclim_site_count"],
        landclim_grid_cell_count=counts["landclim_grid_cell_count"],
        neotoma_point_count=counts["neotoma_point_count"],
        sead_point_count=counts["sead_point_count"],
        raa_total_site_count=counts["raa_total_site_count"],
        raa_heritage_site_count=counts["raa_heritage_site_count"],
        summary_path=summary_path,
    )


def build_data_collection_report(
    summary: DataCollectionSummary,
) -> DataCollectionReport:
    """Build the public collection report from the persisted summary contract."""
    return DataCollectionReport(
        generated_on=summary.generated_on,
        output_root=summary.output_root,
        version=summary.version,
        collected_sources=summary.collected_sources,
        source_output_roots=summary.source_output_roots,
        aadr_file_count=summary.aadr_file_count,
        landclim_site_count=summary.landclim_site_count,
        landclim_grid_cell_count=summary.landclim_grid_cell_count,
        neotoma_point_count=summary.neotoma_point_count,
        sead_point_count=summary.sead_point_count,
        raa_total_site_count=summary.raa_total_site_count,
        raa_heritage_site_count=summary.raa_heritage_site_count,
        boundary_source=summary.boundary_source,
        summary_path=summary.summary_path,
    )
