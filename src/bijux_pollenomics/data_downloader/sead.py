from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

from .common import clean_optional_text, fetch_json, write_json
from .contracts import SEAD_POINT_CSV, SEAD_POINT_GEOJSON
from .geometry import classify_country
from .models import ContextPointRecord
from .writers import write_context_points_csv, write_context_points_geojson
from ..temporal import build_bp_interval_label, mean_bp_year_from_interval, normalize_bp_interval


SEAD_LIMIT = 1000
SEAD_FILTER_BATCH_SIZE = 100
SEAD_POSTGREST_ROOT = "https://browser.sead.se/postgrest"


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
    rows: list[dict[str, object]] = []
    start = 0
    params: list[tuple[str, str]] = [("select", select)]
    if filters:
        params.extend(filters)
    if order_by:
        params.append(("order", ",".join(order_by)))
    while True:
        chunk = fetch_json(
            f"{SEAD_POSTGREST_ROOT}/{table_name}",
            params=params,
            headers={
                "Range-Unit": "items",
                "Range": f"{start}-{start + SEAD_LIMIT - 1}",
            },
        )
        if not isinstance(chunk, list) or not chunk:
            break
        rows.extend(item for item in chunk if isinstance(item, dict))
        if len(chunk) < SEAD_LIMIT:
            break
        start += SEAD_LIMIT
    return rows


def fetch_sead_rows_by_ids(
    table_name: str,
    *,
    select: str,
    filter_field: str,
    ids: Iterable[int],
    order_by: tuple[str, ...] = (),
) -> list[dict[str, object]]:
    """Fetch SEAD rows in manageable `in.(...)` batches."""
    unique_ids = sorted({int(value) for value in ids})
    rows: list[dict[str, object]] = []
    for start in range(0, len(unique_ids), SEAD_FILTER_BATCH_SIZE):
        batch = unique_ids[start:start + SEAD_FILTER_BATCH_SIZE]
        rows.extend(
            fetch_sead_rows(
                table_name,
                select=select,
                filters=((filter_field, build_sead_in_filter(batch)),),
                order_by=order_by,
            )
        )
    return rows


def build_sead_in_filter(values: list[int]) -> str:
    """Render a PostgREST `in.(...)` filter from integer identifiers."""
    return f"in.({','.join(str(value) for value in values)})"


def parse_optional_int(value: object) -> int | None:
    """Parse one optional integer-like SEAD field."""
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(round(value))
    text = clean_optional_text(value)
    if not text:
        return None
    try:
        return int(round(float(text)))
    except ValueError:
        return None


def sead_dating_interval(
    dating_range: dict[str, object],
    *,
    age_type: str,
) -> tuple[int, int] | None:
    """Normalize one SEAD dating range when the age type is expressed in BP."""
    if "bp" not in age_type.casefold():
        return None
    return normalize_bp_interval(
        parse_optional_int(dating_range.get("low_value")),
        parse_optional_int(dating_range.get("high_value")),
    )


def merge_sead_intervals(intervals: list[tuple[int, int]]) -> tuple[int, int] | None:
    """Merge multiple SEAD BP intervals into one site span."""
    if not intervals:
        return None
    return (
        min(start for start, _ in intervals),
        max(end for _, end in intervals),
    )


def populate_sead_site_inventory_fields(rows: list[dict[str, object]]) -> dict[str, int]:
    """Attach linked sample, dataset, and reference counts to SEAD site rows."""
    site_ids = [int(row.get("site_id", 0)) for row in rows if row.get("site_id")]
    sample_groups = fetch_sead_rows_by_ids(
        "tbl_sample_groups",
        select="sample_group_id,site_id,sample_group_name",
        filter_field="site_id",
        ids=site_ids,
        order_by=("site_id", "sample_group_id"),
    )
    sample_group_by_id = {
        int(row["sample_group_id"]): int(row["site_id"])
        for row in sample_groups
        if row.get("sample_group_id") is not None and row.get("site_id") is not None
    }
    physical_samples = fetch_sead_rows_by_ids(
        "tbl_physical_samples",
        select="physical_sample_id,sample_group_id",
        filter_field="sample_group_id",
        ids=sample_group_by_id,
        order_by=("sample_group_id", "physical_sample_id"),
    ) if sample_group_by_id else []
    site_id_by_physical_sample_id = {
        int(row["physical_sample_id"]): sample_group_by_id.get(int(row["sample_group_id"]), 0)
        for row in physical_samples
        if row.get("physical_sample_id") is not None and row.get("sample_group_id") is not None
    }
    analysis_entities = fetch_sead_rows_by_ids(
        "tbl_analysis_entities",
        select="analysis_entity_id,physical_sample_id,dataset_id",
        filter_field="physical_sample_id",
        ids=site_id_by_physical_sample_id,
        order_by=("physical_sample_id", "analysis_entity_id"),
    ) if site_id_by_physical_sample_id else []
    analysis_entity_ids = [
        int(row["analysis_entity_id"])
        for row in analysis_entities
        if row.get("analysis_entity_id") is not None
    ]
    analysis_values = fetch_sead_rows_by_ids(
        "tbl_analysis_values",
        select="analysis_value_id,analysis_entity_id",
        filter_field="analysis_entity_id",
        ids=analysis_entity_ids,
        order_by=("analysis_entity_id", "analysis_value_id"),
    ) if analysis_entity_ids else []
    analysis_entity_id_by_analysis_value_id = {
        int(row["analysis_value_id"]): int(row["analysis_entity_id"])
        for row in analysis_values
        if row.get("analysis_value_id") is not None and row.get("analysis_entity_id") is not None
    }
    dating_ranges = fetch_sead_rows_by_ids(
        "tbl_analysis_dating_ranges",
        select="analysis_value_id,low_value,high_value,age_type_id",
        filter_field="analysis_value_id",
        ids=analysis_entity_id_by_analysis_value_id,
        order_by=("analysis_value_id",),
    ) if analysis_entity_id_by_analysis_value_id else []
    age_type_ids = [
        int(row["age_type_id"])
        for row in dating_ranges
        if row.get("age_type_id") is not None
    ]
    age_types = fetch_sead_rows_by_ids(
        "tbl_age_types",
        select="age_type_id,age_type",
        filter_field="age_type_id",
        ids=age_type_ids,
        order_by=("age_type_id",),
    ) if age_type_ids else []
    age_type_by_id = {
        int(row["age_type_id"]): clean_optional_text(row.get("age_type"))
        for row in age_types
        if row.get("age_type_id") is not None
    }
    relative_dates = fetch_sead_rows_by_ids(
        "tbl_relative_dates",
        select="relative_date_id,analysis_entity_id",
        filter_field="analysis_entity_id",
        ids=analysis_entity_ids,
        order_by=("analysis_entity_id", "relative_date_id"),
    ) if analysis_entity_ids else []
    dataset_ids = [
        int(row["dataset_id"])
        for row in analysis_entities
        if row.get("dataset_id") is not None
    ]
    datasets = fetch_sead_rows_by_ids(
        "tbl_datasets",
        select="dataset_id,dataset_name",
        filter_field="dataset_id",
        ids=dataset_ids,
        order_by=("dataset_id",),
    ) if dataset_ids else []
    dataset_name_by_id = {
        int(row["dataset_id"]): clean_optional_text(row.get("dataset_name"))
        for row in datasets
        if row.get("dataset_id") is not None
    }
    site_references = fetch_sead_rows_by_ids(
        "tbl_site_references",
        select="site_reference_id,site_id,biblio_id",
        filter_field="site_id",
        ids=site_ids,
        order_by=("site_id", "site_reference_id"),
    ) if site_ids else []

    sample_group_ids_by_site: dict[int, set[int]] = {}
    site_id_by_sample_group_id: dict[int, int] = {}
    physical_sample_ids_by_site: dict[int, set[int]] = {}
    analysis_entity_ids_by_site: dict[int, set[int]] = {}
    dataset_ids_by_site: dict[int, set[int]] = {}
    reference_ids_by_site: dict[int, set[int]] = {}
    relative_date_ids_by_site: dict[int, set[int]] = {}
    dating_range_counts_by_site: dict[int, int] = {}
    dating_intervals_by_site: dict[int, list[tuple[int, int]]] = {}

    for sample_group in sample_groups:
        site_id = int(sample_group.get("site_id") or 0)
        sample_group_id = int(sample_group.get("sample_group_id") or 0)
        if site_id and sample_group_id:
            sample_group_ids_by_site.setdefault(site_id, set()).add(sample_group_id)
            site_id_by_sample_group_id[sample_group_id] = site_id
    for physical_sample_id, site_id in site_id_by_physical_sample_id.items():
        if site_id:
            physical_sample_ids_by_site.setdefault(site_id, set()).add(physical_sample_id)
    for entity in analysis_entities:
        physical_sample_id = int(entity.get("physical_sample_id") or 0)
        analysis_entity_id = int(entity.get("analysis_entity_id") or 0)
        dataset_id = int(entity.get("dataset_id") or 0)
        site_id = site_id_by_physical_sample_id.get(physical_sample_id, 0)
        if not site_id:
            continue
        if analysis_entity_id:
            analysis_entity_ids_by_site.setdefault(site_id, set()).add(analysis_entity_id)
        if dataset_id:
            dataset_ids_by_site.setdefault(site_id, set()).add(dataset_id)
    site_id_by_analysis_entity_id = {
        analysis_entity_id: site_id
        for site_id, analysis_entity_ids in analysis_entity_ids_by_site.items()
        for analysis_entity_id in analysis_entity_ids
    }
    for relative_date in relative_dates:
        analysis_entity_id = int(relative_date.get("analysis_entity_id") or 0)
        relative_date_id = int(relative_date.get("relative_date_id") or 0)
        site_id = site_id_by_analysis_entity_id.get(analysis_entity_id, 0)
        if site_id and relative_date_id:
            relative_date_ids_by_site.setdefault(site_id, set()).add(relative_date_id)
    for dating_range in dating_ranges:
        analysis_value_id = int(dating_range.get("analysis_value_id") or 0)
        analysis_entity_id = analysis_entity_id_by_analysis_value_id.get(analysis_value_id, 0)
        site_id = site_id_by_analysis_entity_id.get(analysis_entity_id, 0)
        age_type = age_type_by_id.get(int(dating_range.get("age_type_id") or 0), "")
        interval = sead_dating_interval(dating_range, age_type=age_type)
        if not site_id or interval is None:
            continue
        dating_intervals_by_site.setdefault(site_id, []).append(interval)
        dating_range_counts_by_site[site_id] = dating_range_counts_by_site.get(site_id, 0) + 1
    for reference in site_references:
        site_id = int(reference.get("site_id") or 0)
        reference_id = int(reference.get("site_reference_id") or 0)
        if site_id and reference_id:
            reference_ids_by_site.setdefault(site_id, set()).add(reference_id)

    for row in rows:
        site_id = int(row.get("site_id") or 0)
        dataset_names = [
            name
            for name in sorted(
                {
                    dataset_name_by_id.get(dataset_id, "")
                    for dataset_id in dataset_ids_by_site.get(site_id, set())
                }
            )
            if name
        ]
        row["sample_group_count"] = len(sample_group_ids_by_site.get(site_id, set()))
        row["physical_sample_count"] = len(physical_sample_ids_by_site.get(site_id, set()))
        row["analysis_entity_count"] = len(analysis_entity_ids_by_site.get(site_id, set()))
        row["dataset_count"] = len(dataset_ids_by_site.get(site_id, set()))
        row["dataset_names"] = dataset_names
        row["reference_count"] = len(reference_ids_by_site.get(site_id, set()))
        row["relative_date_count"] = len(relative_date_ids_by_site.get(site_id, set()))
        row["dating_range_count"] = dating_range_counts_by_site.get(site_id, 0)
        time_interval = merge_sead_intervals(dating_intervals_by_site.get(site_id, []))
        row["time_start_bp"] = time_interval[0] if time_interval is not None else None
        row["time_end_bp"] = time_interval[1] if time_interval is not None else None
    return {
        "site_row_count": len(rows),
        "sample_group_row_count": len(sample_groups),
        "physical_sample_row_count": len(physical_samples),
        "analysis_entity_row_count": len(analysis_entities),
        "analysis_value_row_count": len(analysis_values),
        "dating_range_row_count": len(dating_ranges),
        "age_type_row_count": len(age_types),
        "relative_date_row_count": len(relative_dates),
        "dataset_row_count": len(datasets),
        "site_reference_row_count": len(site_references),
    }


def normalize_sead_rows(
    rows: Iterable[dict[str, object]],
    country_boundaries: dict[str, dict[str, object]],
) -> list[ContextPointRecord]:
    """Convert SEAD site rows into compact environmental archaeology records."""
    records: list[ContextPointRecord] = []
    for row in rows:
        latitude = row.get("latitude_dd")
        longitude = row.get("longitude_dd")
        if latitude is None or longitude is None:
            continue
        country = classify_country(float(longitude), float(latitude), country_boundaries)
        if not country:
            continue
        site_id = str(row.get("site_id", "")).strip()
        site_name = str(row.get("site_name", "")).strip() or f"SEAD site {site_id}"
        national_identifier = str(row.get("national_site_identifier", "") or "").strip()
        altitude = clean_optional_text(row.get("altitude"))
        description = str(row.get("site_description", "") or "").strip()
        source_url = f"https://browser.sead.se/site/{site_id}"
        sample_group_count = int(row.get("sample_group_count") or 0)
        physical_sample_count = int(row.get("physical_sample_count") or 0)
        analysis_entity_count = int(row.get("analysis_entity_count") or 0)
        dataset_count = int(row.get("dataset_count") or 0)
        reference_count = int(row.get("reference_count") or 0)
        relative_date_count = int(row.get("relative_date_count") or 0)
        dating_range_count = int(row.get("dating_range_count") or 0)
        dataset_names = row.get("dataset_names")
        if not isinstance(dataset_names, list):
            dataset_names = []
        time_interval = normalize_bp_interval(
            parse_optional_int(row.get("time_start_bp")),
            parse_optional_int(row.get("time_end_bp")),
        )

        popup_rows = [
            ("Site ID", site_id),
            ("Category", "Environmental archaeology"),
            ("Source", "SEAD"),
            ("Country", country),
        ]
        if sample_group_count:
            popup_rows.append(("Sample groups", str(sample_group_count)))
        if physical_sample_count:
            popup_rows.append(("Physical samples", str(physical_sample_count)))
        if analysis_entity_count:
            popup_rows.append(("Analysis entities", str(analysis_entity_count)))
        if dataset_count:
            popup_rows.append(("Datasets", str(dataset_count)))
        if dataset_names:
            popup_rows.append(("Dataset names", ", ".join(dataset_names)))
        if reference_count:
            popup_rows.append(("References", str(reference_count)))
        if relative_date_count:
            popup_rows.append(("Relative dates", str(relative_date_count)))
        if dating_range_count:
            popup_rows.append(("Dating ranges", str(dating_range_count)))
        if time_interval is not None:
            popup_rows.append(("Date coverage", build_bp_interval_label(time_interval[0], time_interval[1])))
        if national_identifier:
            popup_rows.append(("National identifier", national_identifier))
        if altitude:
            popup_rows.append(("Altitude", altitude))
        if description:
            popup_rows.append(("Description", description))

        records.append(
            ContextPointRecord(
                source="SEAD",
                layer_key="sead-sites",
                layer_label="SEAD sites",
                category="Environmental archaeology",
                country=country,
                record_id=site_id,
                name=site_name,
                latitude=float(latitude),
                longitude=float(longitude),
                geometry_type="Point",
                subtitle="Nordic environmental archaeology sites",
                description=description,
                source_url=source_url,
                record_count=max(dataset_count, analysis_entity_count, dating_range_count, 1),
                popup_rows=tuple(popup_rows),
                time_start_bp=time_interval[0] if time_interval is not None else None,
                time_end_bp=time_interval[1] if time_interval is not None else None,
                time_mean_bp=mean_bp_year_from_interval(time_interval),
                time_label=build_bp_interval_label(time_interval[0], time_interval[1]) if time_interval is not None else "",
            )
        )

    return sorted(records, key=lambda item: (item.name.casefold(), item.record_id))


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
    raw_path = raw_dir / "nordic_sites.json"
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
            "inventory_summary": fetch_result.inventory_summary,
            "rows": rows,
        },
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
