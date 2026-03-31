from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ..core.http import fetch_json
from .contracts import SEAD_POINT_CSV, SEAD_POINT_GEOJSON
from .sead_archive import write_sead_site_archive
from .sead_fetch import (
    build_sead_in_filter as build_sead_in_filter_value,
    fetch_sead_rows as fetch_sead_rows_from_api,
    fetch_sead_rows_by_ids as fetch_sead_rows_by_ids_from_api,
    merge_sead_intervals as merge_sead_intervals_value,
    parse_optional_int as parse_optional_int_value,
    populate_sead_site_inventory_fields as populate_sead_site_inventory_fields_from_api,
    sead_dating_interval as sead_dating_interval_value,
)
from .sead_normalization import normalize_sead_rows
from .writers import write_context_points_csv, write_context_points_geojson


@dataclass(frozen=True)
class SeadDataReport:
    output_dir: Path
    point_count: int
    raw_path: Path
    normalized_csv_path: Path
    normalized_geojson_path: Path


@dataclass(frozen=True)
class SeadSiteFetchResult:
    rows: list[dict[str, object]]
    inventory_summary: dict[str, int]


def fetch_sead_site_rows(bbox: tuple[float, float, float, float]) -> list[dict[str, object]]:
    """Download SEAD site rows inside the Nordic bounding box."""
    return fetch_sead_site_inventory(bbox).rows


def fetch_sead_site_inventory(bbox: tuple[float, float, float, float]) -> SeadSiteFetchResult:
    """Download SEAD site rows plus an audit summary of linked table coverage."""
    min_longitude, min_latitude, max_longitude, max_latitude = bbox
    rows = fetch_sead_rows(
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
    inventory_summary = populate_sead_site_inventory_fields(deduplicated_rows)
    return SeadSiteFetchResult(rows=deduplicated_rows, inventory_summary=inventory_summary)


def fetch_sead_rows(
    table_name: str,
    *,
    select: str,
    filters: tuple[tuple[str, str], ...] | None = None,
    order_by: tuple[str, ...] = (),
) -> list[dict[str, object]]:
    """Fetch every row from one SEAD PostgREST table for a selected projection."""
    return fetch_sead_rows_from_api(
        table_name,
        fetch_json_fn=fetch_json,
        select=select,
        filters=filters,
        order_by=order_by,
    )


def fetch_sead_rows_by_ids(
    table_name: str,
    *,
    select: str,
    filter_field: str,
    ids: Iterable[int],
    order_by: tuple[str, ...] = (),
) -> list[dict[str, object]]:
    """Fetch SEAD rows in manageable `in.(...)` batches."""
    return fetch_sead_rows_by_ids_from_api(
        table_name,
        fetch_json_fn=fetch_json,
        select=select,
        filter_field=filter_field,
        ids=ids,
        order_by=order_by,
    )


def build_sead_in_filter(values: list[int]) -> str:
    """Render a PostgREST `in.(...)` filter from integer identifiers."""
    return build_sead_in_filter_value(values)


def parse_optional_int(value: object) -> int | None:
    """Parse one optional integer-like SEAD field."""
    return parse_optional_int_value(value)


def sead_dating_interval(
    dating_range: dict[str, object],
    *,
    age_type: str,
) -> tuple[int, int] | None:
    """Normalize one SEAD dating range when the age type is expressed in BP."""
    return sead_dating_interval_value(dating_range, age_type=age_type)


def merge_sead_intervals(intervals: list[tuple[int, int]]) -> tuple[int, int] | None:
    """Merge multiple SEAD BP intervals into one site span."""
    return merge_sead_intervals_value(intervals)


def populate_sead_site_inventory_fields(rows: list[dict[str, object]]) -> dict[str, int]:
    """Attach linked sample, dataset, and reference counts to SEAD site rows."""
    return populate_sead_site_inventory_fields_from_api(rows, fetch_json_fn=fetch_json)


def collect_sead_data(
    output_root: Path,
    country_boundaries: dict[str, dict[str, object]],
    bbox: tuple[float, float, float, float],
) -> SeadDataReport:
    """Download and write the SEAD dataset under data/sead."""
    output_root = Path(output_root)
    raw_dir = output_root / "raw"
    normalized_dir = output_root / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    fetch_result = fetch_sead_site_inventory(bbox=bbox)
    rows = fetch_result.rows
    raw_path = write_sead_site_archive(
        raw_dir,
        bbox=bbox,
        rows=rows,
        inventory_summary=fetch_result.inventory_summary,
    )
    records = normalize_sead_rows(rows, country_boundaries=country_boundaries)
    normalized_csv_path = SEAD_POINT_CSV.source_path_under(output_root)
    normalized_geojson_path = SEAD_POINT_GEOJSON.source_path_under(output_root)
    write_context_points_csv(normalized_csv_path, records)
    write_context_points_geojson(normalized_geojson_path, records)

    return SeadDataReport(
        output_dir=output_root,
        point_count=len(records),
        raw_path=raw_path,
        normalized_csv_path=normalized_csv_path,
        normalized_geojson_path=normalized_geojson_path,
    )
