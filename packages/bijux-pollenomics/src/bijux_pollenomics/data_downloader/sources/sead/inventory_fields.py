from __future__ import annotations

from collections.abc import Callable
import re

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


def parse_required_int(value: object) -> int:
    """Parse one required SEAD integer-like field or fall back to zero."""
    return parse_optional_int(value) or 0


def populate_sead_site_inventory_fields(
    rows: list[dict[str, object]],
    *,
    fetch_json_fn: Callable[..., object],
) -> dict[str, int]:
    """Attach linked sample, dataset, and reference counts to SEAD site rows."""
    site_ids = [
        site_id
        for row in rows
        if (site_id := parse_optional_int(row.get("site_id"))) is not None
    ]
    sample_groups = fetch_sead_rows_by_ids(
        "tbl_sample_groups",
        fetch_json_fn=fetch_json_fn,
        select="sample_group_id,site_id,sample_group_name",
        filter_field="site_id",
        ids=site_ids,
        order_by=("site_id", "sample_group_id"),
    )
    sample_group_by_id = {
        parse_required_int(row["sample_group_id"]): parse_required_int(row["site_id"])
        for row in sample_groups
        if row.get("sample_group_id") is not None and row.get("site_id") is not None
    }
    physical_samples = (
        fetch_sead_rows_by_ids(
            "tbl_physical_samples",
            fetch_json_fn=fetch_json_fn,
            select="physical_sample_id,sample_group_id",
            filter_field="sample_group_id",
            ids=sample_group_by_id,
            order_by=("sample_group_id", "physical_sample_id"),
        )
        if sample_group_by_id
        else []
    )
    site_id_by_physical_sample_id = {
        parse_required_int(row["physical_sample_id"]): sample_group_by_id.get(
            parse_required_int(row["sample_group_id"]), 0
        )
        for row in physical_samples
        if row.get("physical_sample_id") is not None
        and row.get("sample_group_id") is not None
    }
    analysis_entities = (
        fetch_sead_rows_by_ids(
            "tbl_analysis_entities",
            fetch_json_fn=fetch_json_fn,
            select="analysis_entity_id,physical_sample_id,dataset_id",
            filter_field="physical_sample_id",
            ids=site_id_by_physical_sample_id,
            order_by=("physical_sample_id", "analysis_entity_id"),
        )
        if site_id_by_physical_sample_id
        else []
    )
    analysis_entity_ids = [
        parse_required_int(row["analysis_entity_id"])
        for row in analysis_entities
        if row.get("analysis_entity_id") is not None
    ]
    analysis_values = (
        fetch_sead_rows_by_ids(
            "tbl_analysis_values",
            fetch_json_fn=fetch_json_fn,
            select="analysis_value_id,analysis_entity_id",
            filter_field="analysis_entity_id",
            ids=analysis_entity_ids,
            order_by=("analysis_entity_id", "analysis_value_id"),
        )
        if analysis_entity_ids
        else []
    )
    analysis_entity_id_by_analysis_value_id = {
        parse_required_int(row["analysis_value_id"]): parse_required_int(
            row["analysis_entity_id"]
        )
        for row in analysis_values
        if row.get("analysis_value_id") is not None
        and row.get("analysis_entity_id") is not None
    }
    dating_ranges = (
        fetch_sead_rows_by_ids(
            "tbl_analysis_dating_ranges",
            fetch_json_fn=fetch_json_fn,
            select=(
                "analysis_dating_range_id,analysis_value_id,low_value,high_value,"
                "age_type_id,dating_uncertainty_id,low_qualifier,high_qualifier,"
                "low_is_uncertain,high_is_uncertain"
            ),
            filter_field="analysis_value_id",
            ids=analysis_entity_id_by_analysis_value_id,
            order_by=("analysis_value_id",),
        )
        if analysis_entity_id_by_analysis_value_id
        else []
    )
    age_type_ids = [
        parse_required_int(row["age_type_id"])
        for row in dating_ranges
        if row.get("age_type_id") is not None
    ]
    age_types = (
        fetch_sead_rows_by_ids(
            "tbl_age_types",
            fetch_json_fn=fetch_json_fn,
            select="age_type_id,age_type,description",
            filter_field="age_type_id",
            ids=age_type_ids,
            order_by=("age_type_id",),
        )
        if age_type_ids
        else []
    )
    relative_dates = (
        fetch_sead_rows_by_ids(
            "tbl_relative_dates",
            fetch_json_fn=fetch_json_fn,
            select=(
                "relative_date_id,analysis_entity_id,relative_age_id,"
                "dating_uncertainty_id,method_id,notes"
            ),
            filter_field="analysis_entity_id",
            ids=analysis_entity_ids,
            order_by=("analysis_entity_id", "relative_date_id"),
        )
        if analysis_entity_ids
        else []
    )
    dating_uncertainty_ids = sorted(
        {
            parse_required_int(row["dating_uncertainty_id"])
            for row in dating_ranges
            if row.get("dating_uncertainty_id") is not None
        }
    )
    dating_uncertainty_ids.extend(
        sorted(
            {
                parse_required_int(row["dating_uncertainty_id"])
                for row in relative_dates
                if row.get("dating_uncertainty_id") is not None
            }
        )
    )
    dating_uncertainties = (
        fetch_sead_rows_by_ids(
            "tbl_dating_uncertainty",
            fetch_json_fn=fetch_json_fn,
            select="dating_uncertainty_id,uncertainty,description",
            filter_field="dating_uncertainty_id",
            ids=sorted(set(dating_uncertainty_ids)),
            order_by=("dating_uncertainty_id",),
        )
        if dating_uncertainty_ids
        else []
    )
    age_type_by_id = {
        parse_required_int(row["age_type_id"]): clean_optional_text(row.get("age_type"))
        for row in age_types
        if row.get("age_type_id") is not None
    }
    relative_age_ids = [
        parse_required_int(row["relative_age_id"])
        for row in relative_dates
        if row.get("relative_age_id") is not None
    ]
    relative_ages = (
        fetch_sead_rows_by_ids(
            "tbl_relative_ages",
            fetch_json_fn=fetch_json_fn,
            select=(
                "relative_age_id,relative_age_name,description,abbreviation,"
                "cal_age_older,cal_age_younger,c14_age_older,c14_age_younger"
            ),
            filter_field="relative_age_id",
            ids=relative_age_ids,
            order_by=("relative_age_id",),
        )
        if relative_age_ids
        else []
    )
    method_ids = [
        parse_required_int(row["method_id"])
        for row in relative_dates
        if row.get("method_id") is not None
    ]
    methods = (
        fetch_sead_rows_by_ids(
            "tbl_methods",
            fetch_json_fn=fetch_json_fn,
            select="method_id,method_name,method_abbrev_or_alt_name,description",
            filter_field="method_id",
            ids=method_ids,
            order_by=("method_id",),
        )
        if method_ids
        else []
    )
    dataset_ids = [
        parse_required_int(row["dataset_id"])
        for row in analysis_entities
        if row.get("dataset_id") is not None
    ]
    datasets = (
        fetch_sead_rows_by_ids(
            "tbl_datasets",
            fetch_json_fn=fetch_json_fn,
            select="dataset_id,dataset_name,biblio_id",
            filter_field="dataset_id",
            ids=dataset_ids,
            order_by=("dataset_id",),
        )
        if dataset_ids
        else []
    )
    dataset_name_by_id = {
        parse_required_int(row["dataset_id"]): clean_optional_text(
            row.get("dataset_name")
        )
        for row in datasets
        if row.get("dataset_id") is not None
    }
    site_references = (
        fetch_sead_rows_by_ids(
            "tbl_site_references",
            fetch_json_fn=fetch_json_fn,
            select="site_reference_id,site_id,biblio_id",
            filter_field="site_id",
            ids=site_ids,
            order_by=("site_id", "site_reference_id"),
        )
        if site_ids
        else []
    )
    biblio_ids = sorted(
        {
            parse_required_int(row["biblio_id"])
            for row in (*datasets, *site_references)
            if row.get("biblio_id") is not None
        }
    )
    bibliography_rows = (
        fetch_sead_rows_by_ids(
            "tbl_biblio",
            fetch_json_fn=fetch_json_fn,
            select="biblio_id,title,full_reference,year,doi,url",
            filter_field="biblio_id",
            ids=biblio_ids,
            order_by=("biblio_id",),
        )
        if biblio_ids
        else []
    )
    uncertainty_by_id = {
        parse_required_int(row["dating_uncertainty_id"]): {
            "label": clean_optional_text(row.get("uncertainty")),
            "description": clean_optional_text(row.get("description")),
        }
        for row in dating_uncertainties
        if row.get("dating_uncertainty_id") is not None
    }
    relative_age_by_id = {
        parse_required_int(row["relative_age_id"]): {
            "label": clean_optional_text(row.get("relative_age_name")),
            "description": clean_optional_text(row.get("description")),
            "abbreviation": clean_optional_text(row.get("abbreviation")),
            "cal_age_older": parse_optional_int(row.get("cal_age_older")),
            "cal_age_younger": parse_optional_int(row.get("cal_age_younger")),
            "c14_age_older": parse_optional_int(row.get("c14_age_older")),
            "c14_age_younger": parse_optional_int(row.get("c14_age_younger")),
        }
        for row in relative_ages
        if row.get("relative_age_id") is not None
    }
    method_by_id = {
        parse_required_int(row["method_id"]): {
            "name": clean_optional_text(row.get("method_name")),
            "alternate_name": clean_optional_text(row.get("method_abbrev_or_alt_name")),
            "description": clean_optional_text(row.get("description")),
        }
        for row in methods
        if row.get("method_id") is not None
    }
    bibliography_by_id = {
        parse_required_int(row["biblio_id"]): {
            "title": clean_optional_text(row.get("title")),
            "full_reference": clean_optional_text(row.get("full_reference")),
            "year": clean_optional_text(row.get("year")),
            "doi": clean_optional_text(row.get("doi")),
            "url": clean_optional_text(row.get("url")),
        }
        for row in bibliography_rows
        if row.get("biblio_id") is not None
    }
    dataset_reference_by_id = {
        parse_required_int(row["dataset_id"]): bibliography_by_id.get(
            parse_required_int(row.get("biblio_id")),
            {},
        )
        for row in datasets
        if row.get("dataset_id") is not None
    }

    sample_group_ids_by_site: dict[int, set[int]] = {}
    site_id_by_sample_group_id: dict[int, int] = {}
    physical_sample_ids_by_site: dict[int, set[int]] = {}
    analysis_entity_ids_by_site: dict[int, set[int]] = {}
    dataset_ids_by_site: dict[int, set[int]] = {}
    reference_ids_by_site: dict[int, set[int]] = {}
    relative_date_ids_by_site: dict[int, set[int]] = {}
    dating_range_counts_by_site: dict[int, int] = {}
    numeric_dating_intervals_by_site: dict[int, list[tuple[int, int]]] = {}
    contextual_period_intervals_by_site: dict[int, list[tuple[int, int]]] = {}
    relative_period_rows_by_site: dict[int, list[dict[str, object]]] = {}
    dating_range_rows_by_site: dict[int, list[dict[str, object]]] = {}
    bibliography_rows_by_site: dict[int, list[dict[str, object]]] = {}

    for sample_group in sample_groups:
        site_id = parse_required_int(sample_group.get("site_id"))
        sample_group_id = parse_required_int(sample_group.get("sample_group_id"))
        if site_id and sample_group_id:
            sample_group_ids_by_site.setdefault(site_id, set()).add(sample_group_id)
            site_id_by_sample_group_id[sample_group_id] = site_id
    for physical_sample_id, site_id in site_id_by_physical_sample_id.items():
        if site_id:
            physical_sample_ids_by_site.setdefault(site_id, set()).add(
                physical_sample_id
            )
    for entity in analysis_entities:
        physical_sample_id = parse_required_int(entity.get("physical_sample_id"))
        analysis_entity_id = parse_required_int(entity.get("analysis_entity_id"))
        dataset_id = parse_required_int(entity.get("dataset_id"))
        site_id = site_id_by_physical_sample_id.get(physical_sample_id, 0)
        if not site_id:
            continue
        if analysis_entity_id:
            analysis_entity_ids_by_site.setdefault(site_id, set()).add(
                analysis_entity_id
            )
        if dataset_id:
            dataset_ids_by_site.setdefault(site_id, set()).add(dataset_id)
    site_id_by_analysis_entity_id = {
        analysis_entity_id: site_id
        for site_id, analysis_entity_ids in analysis_entity_ids_by_site.items()
        for analysis_entity_id in analysis_entity_ids
    }
    for relative_date in relative_dates:
        analysis_entity_id = parse_required_int(relative_date.get("analysis_entity_id"))
        relative_date_id = parse_required_int(relative_date.get("relative_date_id"))
        site_id = site_id_by_analysis_entity_id.get(analysis_entity_id, 0)
        if site_id and relative_date_id:
            relative_date_ids_by_site.setdefault(site_id, set()).add(relative_date_id)
            relative_period_rows_by_site.setdefault(site_id, []).append(
                _build_relative_period_row(
                    relative_date,
                    site_id=site_id,
                    relative_age=relative_age_by_id.get(
                        parse_required_int(relative_date.get("relative_age_id")),
                        {},
                    ),
                    method=method_by_id.get(
                        parse_required_int(relative_date.get("method_id")),
                        {},
                    ),
                    uncertainty=uncertainty_by_id.get(
                        parse_required_int(relative_date.get("dating_uncertainty_id")),
                        {},
                    ),
                )
            )
    for dating_range in dating_ranges:
        analysis_value_id = parse_required_int(dating_range.get("analysis_value_id"))
        analysis_entity_id = analysis_entity_id_by_analysis_value_id.get(
            analysis_value_id, 0
        )
        site_id = site_id_by_analysis_entity_id.get(analysis_entity_id, 0)
        age_type = age_type_by_id.get(
            parse_required_int(dating_range.get("age_type_id")), ""
        )
        interval = sead_dating_interval(dating_range, age_type=age_type)
        if not site_id or interval is None:
            interval = _relative_interval_from_range(
                dating_range,
                age_type=age_type,
            )
        if site_id:
            dating_range_rows_by_site.setdefault(site_id, []).append(
                _build_dating_range_row(
                    dating_range,
                    age_type=age_type,
                    age_type_description=clean_optional_text(
                        next(
                            (
                                row.get("description")
                                for row in age_types
                                if parse_required_int(row.get("age_type_id"))
                                == parse_required_int(dating_range.get("age_type_id"))
                            ),
                            "",
                        )
                    ),
                    uncertainty=uncertainty_by_id.get(
                        parse_required_int(dating_range.get("dating_uncertainty_id")),
                        {},
                    ),
                )
            )
        if site_id and interval is not None:
            numeric_dating_intervals_by_site.setdefault(site_id, []).append(interval)
        if site_id:
            dating_range_counts_by_site[site_id] = (
                dating_range_counts_by_site.get(site_id, 0) + 1
            )
    for relative_rows in relative_period_rows_by_site.values():
        for row in relative_rows:
            interval = normalize_bp_interval(
                parse_optional_int(row.get("time_start_bp")),
                parse_optional_int(row.get("time_end_bp")),
            )
            site_id = parse_required_int(row.get("site_id"))
            if site_id and interval is not None:
                contextual_period_intervals_by_site.setdefault(site_id, []).append(
                    interval
                )
    for reference in site_references:
        site_id = parse_required_int(reference.get("site_id"))
        reference_id = parse_required_int(reference.get("site_reference_id"))
        if site_id and reference_id:
            reference_ids_by_site.setdefault(site_id, set()).add(reference_id)
            biblio = bibliography_by_id.get(parse_required_int(reference.get("biblio_id")), {})
            if biblio:
                bibliography_rows_by_site.setdefault(site_id, []).append(
                    _build_bibliography_row(
                        biblio_id=parse_required_int(reference.get("biblio_id")),
                        source_kind="site_reference",
                        biblio=biblio,
                    )
                )
    for entity in analysis_entities:
        dataset_id = parse_required_int(entity.get("dataset_id"))
        physical_sample_id = parse_required_int(entity.get("physical_sample_id"))
        site_id = site_id_by_physical_sample_id.get(physical_sample_id, 0)
        if site_id and dataset_id:
            biblio = dataset_reference_by_id.get(dataset_id, {})
            if biblio:
                bibliography_rows_by_site.setdefault(site_id, []).append(
                    _build_bibliography_row(
                        biblio_id=parse_required_int(
                            next(
                                (
                                    row.get("biblio_id")
                                    for row in datasets
                                    if parse_required_int(row.get("dataset_id")) == dataset_id
                                ),
                                0,
                            )
                        ),
                        source_kind="dataset_reference",
                        biblio=biblio,
                    )
                )
    for site_rows in bibliography_rows_by_site.values():
        site_rows.sort(
            key=lambda row: (
                str(row.get("source_kind", "")),
                str(row.get("title", "")),
                str(row.get("doi", "")),
            )
        )

    for row in rows:
        site_id = parse_required_int(row.get("site_id"))
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
        row["physical_sample_count"] = len(
            physical_sample_ids_by_site.get(site_id, set())
        )
        row["analysis_entity_count"] = len(
            analysis_entity_ids_by_site.get(site_id, set())
        )
        row["dataset_count"] = len(dataset_ids_by_site.get(site_id, set()))
        row["dataset_names"] = dataset_names
        row["reference_count"] = len(reference_ids_by_site.get(site_id, set()))
        row["relative_date_count"] = len(relative_date_ids_by_site.get(site_id, set()))
        row["dating_range_count"] = dating_range_counts_by_site.get(site_id, 0)
        numeric_time_interval = merge_sead_intervals(
            numeric_dating_intervals_by_site.get(site_id, [])
        )
        contextual_time_interval = merge_sead_intervals(
            contextual_period_intervals_by_site.get(site_id, [])
        )
        time_interval = numeric_time_interval or contextual_time_interval
        row["time_start_bp"] = time_interval[0] if time_interval is not None else None
        row["time_end_bp"] = time_interval[1] if time_interval is not None else None
        row["numeric_time_start_bp"] = (
            numeric_time_interval[0] if numeric_time_interval is not None else None
        )
        row["numeric_time_end_bp"] = (
            numeric_time_interval[1] if numeric_time_interval is not None else None
        )
        row["contextual_time_start_bp"] = (
            contextual_time_interval[0]
            if contextual_time_interval is not None
            else None
        )
        row["contextual_time_end_bp"] = (
            contextual_time_interval[1]
            if contextual_time_interval is not None
            else None
        )
        row["relative_period_rows"] = relative_period_rows_by_site.get(site_id, [])
        row["dating_range_rows"] = dating_range_rows_by_site.get(site_id, [])
        row["bibliography_rows"] = bibliography_rows_by_site.get(site_id, [])
        row["temporal_summary"] = {
            "relative_period_count": len(relative_period_rows_by_site.get(site_id, [])),
            "dating_range_count": dating_range_counts_by_site.get(site_id, 0),
            "bibliography_count": len(bibliography_rows_by_site.get(site_id, [])),
            "time_start_bp": row["time_start_bp"],
            "time_end_bp": row["time_end_bp"],
            "numeric_time_start_bp": row["numeric_time_start_bp"],
            "numeric_time_end_bp": row["numeric_time_end_bp"],
            "contextual_time_start_bp": row["contextual_time_start_bp"],
            "contextual_time_end_bp": row["contextual_time_end_bp"],
            "normalized_period_labels": _normalized_period_labels(
                relative_period_rows_by_site.get(site_id, [])
            ),
            "uncertainty_labels": _uncertainty_labels(
                relative_period_rows_by_site.get(site_id, []),
                dating_range_rows_by_site.get(site_id, []),
            ),
        }
    return {
        "site_row_count": len(rows),
        "sample_group_row_count": len(sample_groups),
        "physical_sample_row_count": len(physical_samples),
        "analysis_entity_row_count": len(analysis_entities),
        "analysis_value_row_count": len(analysis_values),
        "dating_range_row_count": len(dating_ranges),
        "age_type_row_count": len(age_types),
        "relative_date_row_count": len(relative_dates),
        "relative_age_row_count": len(relative_ages),
        "dating_uncertainty_row_count": len(dating_uncertainties),
        "method_row_count": len(methods),
        "dataset_row_count": len(datasets),
        "site_reference_row_count": len(site_references),
        "bibliography_row_count": len(bibliography_rows),
    }


__all__ = [
    "merge_sead_intervals",
    "parse_optional_int",
    "parse_required_int",
    "populate_sead_site_inventory_fields",
    "sead_dating_interval",
]


_PERIOD_LABEL_PATTERNS = (
    (re.compile(r"\bquaternary\b", re.IGNORECASE), "quaternary"),
    (re.compile(r"\bholocene\b", re.IGNORECASE), "holocene"),
    (re.compile(r"\bmesolithic\b", re.IGNORECASE), "mesolithic"),
    (re.compile(r"\bneolithic\b", re.IGNORECASE), "neolithic"),
    (re.compile(r"\bbronze\b", re.IGNORECASE), "bronze_age"),
    (re.compile(r"\biron\b", re.IGNORECASE), "iron_age"),
    (re.compile(r"\broman\b", re.IGNORECASE), "roman_period"),
    (re.compile(r"\bviking\b", re.IGNORECASE), "viking_age"),
    (re.compile(r"\bmedieval\b", re.IGNORECASE), "medieval"),
    (re.compile(r"\bhistoric|modern|present\b", re.IGNORECASE), "historic_or_modern"),
)


def _build_relative_period_row(
    relative_date: dict[str, object],
    *,
    site_id: int,
    relative_age: dict[str, object],
    method: dict[str, object],
    uncertainty: dict[str, object],
) -> dict[str, object]:
    label = str(relative_age.get("label", "")).strip()
    description = str(relative_age.get("description", "")).strip()
    interval = normalize_bp_interval(
        parse_optional_int(relative_age.get("cal_age_younger"))
        or parse_optional_int(relative_age.get("c14_age_younger")),
        parse_optional_int(relative_age.get("cal_age_older"))
        or parse_optional_int(relative_age.get("c14_age_older")),
    )
    return {
        "site_id": site_id,
        "relative_date_id": parse_required_int(relative_date.get("relative_date_id")),
        "relative_age_label": label,
        "relative_age_description": description,
        "relative_age_abbreviation": str(relative_age.get("abbreviation", "")).strip(),
        "normalized_period_label": _normalized_period_label(label, description),
        "method_name": str(method.get("name", "")).strip()
        or str(method.get("alternate_name", "")).strip(),
        "uncertainty_label": str(uncertainty.get("label", "")).strip(),
        "uncertainty_description": str(uncertainty.get("description", "")).strip(),
        "notes": clean_optional_text(relative_date.get("notes")),
        "time_start_bp": interval[0] if interval is not None else None,
        "time_end_bp": interval[1] if interval is not None else None,
    }


def _build_dating_range_row(
    dating_range: dict[str, object],
    *,
    age_type: str,
    age_type_description: str,
    uncertainty: dict[str, object],
) -> dict[str, object]:
    interval = normalize_bp_interval(
        parse_optional_int(dating_range.get("low_value")),
        parse_optional_int(dating_range.get("high_value")),
    )
    return {
        "analysis_dating_range_id": parse_required_int(
            dating_range.get("analysis_dating_range_id")
        ),
        "analysis_value_id": parse_required_int(dating_range.get("analysis_value_id")),
        "age_type": age_type,
        "age_type_description": age_type_description,
        "low_value": parse_optional_int(dating_range.get("low_value")),
        "high_value": parse_optional_int(dating_range.get("high_value")),
        "low_qualifier": clean_optional_text(dating_range.get("low_qualifier")),
        "high_qualifier": clean_optional_text(dating_range.get("high_qualifier")),
        "low_is_uncertain": bool(dating_range.get("low_is_uncertain")),
        "high_is_uncertain": bool(dating_range.get("high_is_uncertain")),
        "uncertainty_label": str(uncertainty.get("label", "")).strip(),
        "uncertainty_description": str(uncertainty.get("description", "")).strip(),
        "time_start_bp": interval[0] if interval is not None else None,
        "time_end_bp": interval[1] if interval is not None else None,
    }


def _build_bibliography_row(
    *,
    biblio_id: int,
    source_kind: str,
    biblio: dict[str, object],
) -> dict[str, object]:
    return {
        "biblio_id": biblio_id,
        "source_kind": source_kind,
        "title": str(biblio.get("title", "")).strip(),
        "full_reference": str(biblio.get("full_reference", "")).strip(),
        "year": str(biblio.get("year", "")).strip(),
        "doi": str(biblio.get("doi", "")).strip(),
        "url": str(biblio.get("url", "")).strip(),
    }


def _relative_interval_from_range(
    dating_range: dict[str, object],
    *,
    age_type: str,
) -> tuple[int, int] | None:
    text = age_type.casefold()
    if "cal" not in text and "c14" not in text:
        return None
    return normalize_bp_interval(
        parse_optional_int(dating_range.get("low_value")),
        parse_optional_int(dating_range.get("high_value")),
    )


def _normalized_period_label(label: str, description: str) -> str:
    text = " ".join(part for part in (label, description) if part).strip()
    for pattern, normalized_label in _PERIOD_LABEL_PATTERNS:
        if pattern.search(text):
            return normalized_label
    return "unmapped_period_label"


def _normalized_period_labels(rows: list[dict[str, object]]) -> list[str]:
    labels = []
    for row in rows:
        label = str(row.get("normalized_period_label", "")).strip()
        if label and label not in labels:
            labels.append(label)
    return labels


def _uncertainty_labels(
    relative_rows: list[dict[str, object]],
    dating_rows: list[dict[str, object]],
) -> list[str]:
    labels: list[str] = []
    for row in (*relative_rows, *dating_rows):
        label = str(row.get("uncertainty_label", "")).strip()
        if label and label not in labels:
            labels.append(label)
    return labels
