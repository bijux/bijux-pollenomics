from __future__ import annotations

from datetime import date
from pathlib import Path

from ....core.files import write_json

SEAD_LINKED_SOURCE_TABLES = (
    "tbl_sites",
    "tbl_sample_groups",
    "tbl_physical_samples",
    "tbl_analysis_entities",
    "tbl_analysis_entity_ages",
    "tbl_geochronology",
    "tbl_dendro_dates",
    "tbl_analysis_values",
    "tbl_analysis_dating_ranges",
    "tbl_age_types",
    "tbl_relative_dates",
    "tbl_relative_ages",
    "tbl_relative_age_refs",
    "tbl_dating_uncertainty",
    "tbl_methods",
    "tbl_datasets",
    "tbl_site_references",
    "tbl_sample_group_references",
    "tbl_biblio",
)

__all__ = ["SEAD_LINKED_SOURCE_TABLES", "write_sead_site_archive"]


def write_sead_site_archive(
    raw_dir: Path,
    *,
    bbox: tuple[float, float, float, float],
    rows: list[dict[str, object]],
    inventory_summary: dict[str, int | str],
) -> Path:
    """Write the raw SEAD site inventory archive and return its path."""
    raw_path = Path(raw_dir) / "nordic_sites.json"
    write_json(
        raw_path,
        {
            "generated_on": str(date.today()),
            "source": "SEAD",
            "endpoint": "https://browser.sead.se/postgrest/tbl_sites",
            "row_count": len(rows),
            "bbox": list(bbox),
            "source_tables": list(SEAD_LINKED_SOURCE_TABLES),
            "inventory_summary": inventory_summary,
            "rows": rows,
        },
    )
    return raw_path
