from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class SeadSiteFetchResult:
    rows: list[dict[str, object]]
    inventory_summary: dict[str, int]


def build_sead_site_inventory(
    *,
    bbox: tuple[float, float, float, float],
    fetch_sead_rows_fn: Callable[..., list[dict[str, object]]],
    populate_inventory_fields_fn: Callable[[list[dict[str, object]]], dict[str, int]],
) -> SeadSiteFetchResult:
    """Download SEAD site rows plus an audit summary of linked table coverage."""
    min_longitude, min_latitude, max_longitude, max_latitude = bbox
    rows = fetch_sead_rows_fn(
        "tbl_sites",
        select="site_id,site_name,national_site_identifier,latitude_dd,longitude_dd,altitude,site_description,site_uuid",
        filters=(
            ("latitude_dd", f"gte.{min_latitude}"),
            ("latitude_dd", f"lte.{max_latitude}"),
            ("longitude_dd", f"gte.{min_longitude}"),
            ("longitude_dd", f"lte.{max_longitude}"),
        ),
        order_by=("site_id",),
    )
    deduplicated: dict[str, dict[str, object]] = {}
    for row in rows:
        deduplicated[str(row.get("site_id", ""))] = row
    deduplicated_rows = sorted(deduplicated.values(), key=lambda item: int(item.get("site_id", 0)))
    inventory_summary = populate_inventory_fields_fn(deduplicated_rows)
    return SeadSiteFetchResult(rows=deduplicated_rows, inventory_summary=inventory_summary)
