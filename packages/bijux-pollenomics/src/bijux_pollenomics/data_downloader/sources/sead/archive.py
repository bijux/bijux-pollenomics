from __future__ import annotations

from datetime import date
from pathlib import Path

from ....core.files import write_json

__all__ = ["write_sead_site_archive"]


def write_sead_site_archive(
    raw_dir: Path,
    *,
    bbox: tuple[float, float, float, float],
    rows: list[dict[str, object]],
    inventory_summary: dict[str, int],
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
            "source_tables": [
                "tbl_sites",
                "tbl_sample_groups",
                "tbl_physical_samples",
                "tbl_analysis_entities",
                "tbl_analysis_values",
                "tbl_analysis_dating_ranges",
                "tbl_age_types",
                "tbl_relative_dates",
                "tbl_datasets",
                "tbl_site_references",
            ],
            "inventory_summary": inventory_summary,
            "rows": rows,
        },
    )
    return raw_path
