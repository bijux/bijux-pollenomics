"""Build source-keyed SEAD site inventories from declared discovery queries."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from bijux_pollenomics.collection.sources.sead.acquisition.identifiers import (
    required_sead_identifier,
)

__all__ = ["SeadSiteFetchResult", "build_sead_site_inventory"]


@dataclass(frozen=True)
class SeadSiteFetchResult:
    """Retain discovered site rows and their linked-source inventory account."""

    rows: list[dict[str, object]]
    inventory_summary: dict[str, int | str]


def build_sead_site_inventory(
    *,
    bbox: tuple[float, float, float, float],
    fetch_sead_rows_fn: Callable[..., list[dict[str, object]]],
    populate_inventory_fields_fn: Callable[
        [list[dict[str, object]]], dict[str, int | str]
    ],
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
    deduplicated: dict[int, dict[str, object]] = {}
    for row in rows:
        deduplicated[required_sead_identifier(row.get("site_id"))] = row
    deduplicated_rows = sorted(
        deduplicated.values(),
        key=lambda item: required_sead_identifier(item.get("site_id")),
    )
    inventory_summary = populate_inventory_fields_fn(deduplicated_rows)
    return SeadSiteFetchResult(
        rows=deduplicated_rows, inventory_summary=inventory_summary
    )
