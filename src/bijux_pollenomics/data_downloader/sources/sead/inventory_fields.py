from __future__ import annotations

from collections.abc import Callable

from ....core.bp_time import normalize_bp_interval
from ....core.text import clean_optional_text
from .api_client import fetch_sead_rows_by_ids


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
    return (min(start for start, _ in intervals), max(end for _, end in intervals))


def populate_sead_site_inventory_fields(
    rows: list[dict[str, object]],
    *,
    fetch_json_fn: Callable[..., object],
) -> dict[str, int]:
    """Attach linked sample, dataset, and reference counts to SEAD site rows."""
    site_ids = [int(row.get("site_id", 0)) for row in rows if row.get("site_id")]
    sample_groups = fetch_sead_rows_by_ids(
        "tbl_sample_groups",
        fetch_json_fn=fetch_json_fn,
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
        fetch_json_fn=fetch_json_fn,
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
        fetch_json_fn=fetch_json_fn,
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
        fetch_json_fn=fetch_json_fn,
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
        fetch_json_fn=fetch_json_fn,
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
        fetch_json_fn=fetch_json_fn,
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
        fetch_json_fn=fetch_json_fn,
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
        fetch_json_fn=fetch_json_fn,
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
        fetch_json_fn=fetch_json_fn,
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


__all__ = [
    "merge_sead_intervals",
    "parse_optional_int",
    "populate_sead_site_inventory_fields",
    "sead_dating_interval",
]
