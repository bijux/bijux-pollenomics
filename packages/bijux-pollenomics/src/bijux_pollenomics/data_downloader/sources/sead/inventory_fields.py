from __future__ import annotations

from collections.abc import Callable
import re

from ....core.bp_time import normalize_bp_interval
from ....core.text import clean_optional_text
from .api_client import fetch_sead_rows, fetch_sead_rows_by_ids

BP_REFERENCE_YEAR = 1950


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
    """Normalize one SEAD dating range into the shared BP interval convention."""
    low_value = parse_optional_int(dating_range.get("low_value"))
    high_value = parse_optional_int(dating_range.get("high_value"))
    age_type_text = age_type.casefold()
    if "bp" in age_type_text:
        return _normalize_optional_interval(low_value, high_value)
    if _is_before_common_era_age_type(age_type_text):
        return _calendar_year_interval_to_bp(
            low_value,
            high_value,
            treat_as_bce=True,
        )
    if _is_common_era_age_type(age_type_text):
        return _calendar_year_interval_to_bp(
            low_value,
            high_value,
            treat_as_bce=False,
        )
    return None


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
) -> dict[str, int | str]:
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
    analysis_entity_id_set = set(analysis_entity_ids)
    analysis_entity_ages = [
        row
        for row in (
            fetch_sead_rows(
                "tbl_analysis_entity_ages",
                fetch_json_fn=fetch_json_fn,
                select=(
                    "analysis_entity_age_id,analysis_entity_id,age,age_older,"
                    "age_younger,chronology_id,dating_specifier,age_range"
                ),
                order_by=("analysis_entity_id", "analysis_entity_age_id"),
            )
            if analysis_entity_id_set
            else []
        )
        if parse_required_int(row.get("analysis_entity_id")) in analysis_entity_id_set
    ]
    geochronology_rows = [
        row
        for row in (
            fetch_sead_rows(
                "tbl_geochronology",
                fetch_json_fn=fetch_json_fn,
                select=(
                    "geochron_id,analysis_entity_id,dating_lab_id,lab_number,age,"
                    "error_older,error_younger,notes,dating_uncertainty_id"
                ),
                order_by=("analysis_entity_id", "geochron_id"),
            )
            if analysis_entity_id_set
            else []
        )
        if parse_required_int(row.get("analysis_entity_id")) in analysis_entity_id_set
    ]
    dendro_dates = [
        row
        for row in (
            fetch_sead_rows(
                "tbl_dendro_dates",
                fetch_json_fn=fetch_json_fn,
                select=(
                    "dendro_date_id,analysis_entity_id,age_older,age_younger,"
                    "age_type_id,dating_uncertainty_id,dendro_lookup_id,season_id,"
                    "age_range"
                ),
                order_by=("analysis_entity_id", "dendro_date_id"),
            )
            if analysis_entity_id_set
            else []
        )
        if parse_required_int(row.get("analysis_entity_id")) in analysis_entity_id_set
    ]
    all_dating_ranges = fetch_sead_rows(
        "tbl_analysis_dating_ranges",
        fetch_json_fn=fetch_json_fn,
        select=(
            "analysis_dating_range_id,analysis_value_id,low_value,high_value,"
            "age_type_id,dating_uncertainty_id,low_qualifier,high_qualifier,"
            "low_is_uncertain,high_is_uncertain"
        ),
        order_by=("analysis_value_id",),
    )
    dating_analysis_value_ids = {
        analysis_value_id
        for row in all_dating_ranges
        if (analysis_value_id := parse_optional_int(row.get("analysis_value_id")))
        is not None
    }
    analysis_values = (
        fetch_sead_rows_by_ids(
            "tbl_analysis_values",
            fetch_json_fn=fetch_json_fn,
            select="analysis_value_id,analysis_entity_id",
            filter_field="analysis_value_id",
            ids=dating_analysis_value_ids,
            order_by=("analysis_entity_id", "analysis_value_id"),
        )
        if dating_analysis_value_ids
        else []
    )
    analysis_entity_id_by_analysis_value_id = {
        parse_required_int(row["analysis_value_id"]): parse_required_int(
            row["analysis_entity_id"]
        )
        for row in analysis_values
        if row.get("analysis_value_id") is not None
        and row.get("analysis_entity_id") is not None
        and parse_required_int(row["analysis_entity_id"]) in analysis_entity_id_set
    }
    dating_ranges = [
        row
        for row in all_dating_ranges
        if parse_required_int(row.get("analysis_value_id"))
        in analysis_entity_id_by_analysis_value_id
    ]
    age_type_ids = [
        parse_required_int(row["age_type_id"])
        for row in (*dating_ranges, *dendro_dates)
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
    relative_dates = [
        row
        for row in (
            fetch_sead_rows(
                "tbl_relative_dates",
                fetch_json_fn=fetch_json_fn,
                select=(
                    "relative_date_id,analysis_entity_id,relative_age_id,"
                    "dating_uncertainty_id,method_id,notes"
                ),
                order_by=("analysis_entity_id", "relative_date_id"),
            )
            if analysis_entity_id_set
            else []
        )
        if parse_required_int(row.get("analysis_entity_id")) in analysis_entity_id_set
    ]
    dating_uncertainty_ids = sorted(
        {
            parse_required_int(row["dating_uncertainty_id"])
            for row in (*dating_ranges, *geochronology_rows, *dendro_dates)
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
    sample_group_references = (
        fetch_sead_rows_by_ids(
            "tbl_sample_group_references",
            fetch_json_fn=fetch_json_fn,
            select="sample_group_reference_id,sample_group_id,biblio_id",
            filter_field="sample_group_id",
            ids=sample_group_by_id,
            order_by=("sample_group_id", "sample_group_reference_id"),
        )
        if sample_group_by_id
        else []
    )
    relative_age_references = (
        fetch_sead_rows_by_ids(
            "tbl_relative_age_refs",
            fetch_json_fn=fetch_json_fn,
            select="relative_age_ref_id,relative_age_id,biblio_id",
            filter_field="relative_age_id",
            ids=relative_age_ids,
            order_by=("relative_age_id", "relative_age_ref_id"),
        )
        if relative_age_ids
        else []
    )
    biblio_ids = sorted(
        {
            parse_required_int(row["biblio_id"])
            for row in (
                *datasets,
                *site_references,
                *sample_group_references,
                *relative_age_references,
            )
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
    site_ids_by_relative_age_id: dict[int, set[int]] = {}
    dating_range_counts_by_site: dict[int, int] = {}
    numeric_dating_intervals_by_site: dict[int, list[tuple[int, int]]] = {}
    contextual_period_intervals_by_site: dict[int, list[tuple[int, int]]] = {}
    relative_period_rows_by_site: dict[int, list[dict[str, object]]] = {}
    dating_range_rows_by_site: dict[int, list[dict[str, object]]] = {}
    bibliography_rows_by_site: dict[int, list[dict[str, object]]] = {}
    analysis_entity_age_rows_by_site: dict[int, list[dict[str, object]]] = {}
    geochronology_rows_by_site: dict[int, list[dict[str, object]]] = {}
    dendro_date_rows_by_site: dict[int, list[dict[str, object]]] = {}

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
    for entity_age in analysis_entity_ages:
        analysis_entity_id = parse_required_int(entity_age.get("analysis_entity_id"))
        site_id = site_id_by_analysis_entity_id.get(analysis_entity_id, 0)
        interval = _analysis_entity_age_interval(entity_age)
        if not site_id:
            continue
        analysis_entity_age_rows_by_site.setdefault(site_id, []).append(
            _build_analysis_entity_age_row(entity_age, interval=interval)
        )
        if interval is not None:
            numeric_dating_intervals_by_site.setdefault(site_id, []).append(interval)
    for geochronology_row in geochronology_rows:
        analysis_entity_id = parse_required_int(
            geochronology_row.get("analysis_entity_id")
        )
        site_id = site_id_by_analysis_entity_id.get(analysis_entity_id, 0)
        interval = _geochronology_interval(geochronology_row)
        if not site_id:
            continue
        geochronology_rows_by_site.setdefault(site_id, []).append(
            _build_geochronology_row(
                geochronology_row,
                interval=interval,
                uncertainty=uncertainty_by_id.get(
                    parse_required_int(
                        geochronology_row.get("dating_uncertainty_id")
                    ),
                    {},
                ),
            )
        )
        if interval is not None:
            numeric_dating_intervals_by_site.setdefault(site_id, []).append(interval)
    for dendro_date in dendro_dates:
        analysis_entity_id = parse_required_int(dendro_date.get("analysis_entity_id"))
        site_id = site_id_by_analysis_entity_id.get(analysis_entity_id, 0)
        age_type = age_type_by_id.get(
            parse_required_int(dendro_date.get("age_type_id")), ""
        )
        interval = _dendro_date_interval(dendro_date, age_type=age_type)
        if not site_id:
            continue
        dendro_date_rows_by_site.setdefault(site_id, []).append(
            _build_dendro_date_row(
                dendro_date,
                age_type=age_type,
                interval=interval,
                uncertainty=uncertainty_by_id.get(
                    parse_required_int(dendro_date.get("dating_uncertainty_id")),
                    {},
                ),
            )
        )
        if interval is not None:
            numeric_dating_intervals_by_site.setdefault(site_id, []).append(interval)
    for relative_date in relative_dates:
        analysis_entity_id = parse_required_int(relative_date.get("analysis_entity_id"))
        relative_date_id = parse_required_int(relative_date.get("relative_date_id"))
        site_id = site_id_by_analysis_entity_id.get(analysis_entity_id, 0)
        if site_id and relative_date_id:
            relative_date_ids_by_site.setdefault(site_id, set()).add(relative_date_id)
            relative_age_id = parse_required_int(relative_date.get("relative_age_id"))
            if relative_age_id:
                site_ids_by_relative_age_id.setdefault(relative_age_id, set()).add(
                    site_id
                )
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
            biblio = bibliography_by_id.get(
                parse_required_int(reference.get("biblio_id")), {}
            )
            if biblio:
                bibliography_rows_by_site.setdefault(site_id, []).append(
                    _build_bibliography_row(
                        biblio_id=parse_required_int(reference.get("biblio_id")),
                        source_kind="site_reference",
                        source_record_id=reference_id,
                        source_record_label="",
                        biblio=biblio,
                    )
                )
    for site_id, dataset_ids_for_site in dataset_ids_by_site.items():
        for dataset_id in dataset_ids_for_site:
            biblio = dataset_reference_by_id.get(dataset_id, {})
            if biblio:
                bibliography_rows_by_site.setdefault(site_id, []).append(
                    _build_bibliography_row(
                        biblio_id=parse_required_int(
                            next(
                                (
                                    row.get("biblio_id")
                                    for row in datasets
                                    if parse_required_int(row.get("dataset_id"))
                                    == dataset_id
                                ),
                                0,
                            )
                        ),
                        source_kind="dataset_reference",
                        source_record_id=dataset_id,
                        source_record_label=dataset_name_by_id.get(dataset_id, ""),
                        biblio=biblio,
                    )
                )
    for reference in sample_group_references:
        sample_group_id = parse_required_int(reference.get("sample_group_id"))
        site_id = sample_group_by_id.get(sample_group_id, 0)
        biblio_id = parse_required_int(reference.get("biblio_id"))
        biblio = bibliography_by_id.get(biblio_id, {})
        if site_id and biblio:
            bibliography_rows_by_site.setdefault(site_id, []).append(
                _build_bibliography_row(
                    biblio_id=biblio_id,
                    source_kind="sample_group_reference",
                    source_record_id=sample_group_id,
                    source_record_label="",
                    biblio=biblio,
                )
            )
    for reference in relative_age_references:
        relative_age_id = parse_required_int(reference.get("relative_age_id"))
        biblio_id = parse_required_int(reference.get("biblio_id"))
        biblio = bibliography_by_id.get(biblio_id, {})
        relative_age = relative_age_by_id.get(relative_age_id, {})
        for site_id in site_ids_by_relative_age_id.get(relative_age_id, set()):
            if biblio:
                bibliography_rows_by_site.setdefault(site_id, []).append(
                    _build_bibliography_row(
                        biblio_id=biblio_id,
                        source_kind="relative_age_definition",
                        source_record_id=relative_age_id,
                        source_record_label=clean_optional_text(
                            relative_age.get("label")
                        ),
                        biblio=biblio,
                    )
                )
    for site_id, site_rows in bibliography_rows_by_site.items():
        bibliography_rows_by_site[site_id] = _deduplicate_bibliography_rows(site_rows)
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
        row["site_reference_count"] = len(reference_ids_by_site.get(site_id, set()))
        row["reference_count"] = len(bibliography_rows_by_site.get(site_id, []))
        row["relative_date_count"] = len(relative_date_ids_by_site.get(site_id, set()))
        row["dating_range_count"] = dating_range_counts_by_site.get(site_id, 0)
        row["analysis_entity_age_count"] = len(
            analysis_entity_age_rows_by_site.get(site_id, [])
        )
        row["geochronology_count"] = len(
            geochronology_rows_by_site.get(site_id, [])
        )
        row["dendro_date_count"] = len(dendro_date_rows_by_site.get(site_id, []))
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
        row["analysis_entity_age_rows"] = analysis_entity_age_rows_by_site.get(
            site_id, []
        )
        row["geochronology_rows"] = geochronology_rows_by_site.get(site_id, [])
        row["dendro_date_rows"] = dendro_date_rows_by_site.get(site_id, [])
        row["bibliography_rows"] = bibliography_rows_by_site.get(site_id, [])
        row["temporal_summary"] = {
            "relative_period_count": len(relative_period_rows_by_site.get(site_id, [])),
            "dating_range_count": dating_range_counts_by_site.get(site_id, 0),
            "analysis_entity_age_count": row["analysis_entity_age_count"],
            "geochronology_count": row["geochronology_count"],
            "dendro_date_count": row["dendro_date_count"],
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
                analysis_entity_age_rows_by_site.get(site_id, []),
                geochronology_rows_by_site.get(site_id, []),
                dendro_date_rows_by_site.get(site_id, []),
            ),
        }
    numeric_interval_site_count = sum(
        1
        for row in rows
        if row.get("time_start_bp") is not None and row.get("time_end_bp") is not None
    )
    return {
        "site_row_count": len(rows),
        "sample_group_row_count": len(sample_groups),
        "physical_sample_row_count": len(physical_samples),
        "analysis_entity_row_count": len(analysis_entities),
        "analysis_entity_age_row_count": len(analysis_entity_ages),
        "geochronology_row_count": len(geochronology_rows),
        "dendro_date_row_count": len(dendro_dates),
        "analysis_value_row_count": len(analysis_values),
        "dating_range_row_count": len(dating_ranges),
        "age_type_row_count": len(age_types),
        "relative_date_row_count": len(relative_dates),
        "relative_age_row_count": len(relative_ages),
        "dating_uncertainty_row_count": len(dating_uncertainties),
        "method_row_count": len(methods),
        "dataset_row_count": len(datasets),
        "site_reference_row_count": len(site_references),
        "sample_group_reference_row_count": len(sample_group_references),
        "relative_age_reference_row_count": len(relative_age_references),
        "bibliography_source_row_count": len(bibliography_rows),
        "bibliography_row_count": sum(
            len(site_rows) for site_rows in bibliography_rows_by_site.values()
        ),
        "bibliography_site_count": len(bibliography_rows_by_site),
        "dating_range_site_count": len(dating_range_rows_by_site),
        "relative_period_site_count": len(relative_period_rows_by_site),
        "analysis_entity_age_site_count": len(analysis_entity_age_rows_by_site),
        "geochronology_site_count": len(geochronology_rows_by_site),
        "dendro_date_site_count": len(dendro_date_rows_by_site),
        "numeric_interval_row_count": numeric_interval_site_count,
        "site_inventory_only_row_count": len(rows) - numeric_interval_site_count,
        "temporal_capture_posture": "linked_chronology_captured",
    }


__all__ = [
    "merge_sead_intervals",
    "parse_optional_int",
    "parse_required_int",
    "refresh_sead_repository_rows",
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
    cal_younger = parse_optional_int(relative_age.get("cal_age_younger"))
    cal_older = parse_optional_int(relative_age.get("cal_age_older"))
    c14_younger = parse_optional_int(relative_age.get("c14_age_younger"))
    c14_older = parse_optional_int(relative_age.get("c14_age_older"))
    interval = _normalize_optional_interval(
        cal_younger if cal_younger is not None else c14_younger,
        cal_older if cal_older is not None else c14_older,
    )
    interval_source = "relative_age_bounds"
    if interval is None:
        interval = _interval_from_relative_age_label(label)
        interval_source = "encoded_relative_age_label" if interval else "unresolved"
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
        "interval_source": interval_source,
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
    interval = sead_dating_interval(dating_range, age_type=age_type) or (
        _relative_interval_from_range(dating_range, age_type=age_type)
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


def _analysis_entity_age_interval(
    entity_age: dict[str, object],
) -> tuple[int, int] | None:
    age = parse_optional_int(entity_age.get("age"))
    younger = parse_optional_int(entity_age.get("age_younger"))
    older = parse_optional_int(entity_age.get("age_older"))
    return _normalize_optional_interval(
        younger if younger is not None else age,
        older if older is not None else age,
    )


def _build_analysis_entity_age_row(
    entity_age: dict[str, object],
    *,
    interval: tuple[int, int] | None,
) -> dict[str, object]:
    return {
        "analysis_entity_age_id": parse_required_int(
            entity_age.get("analysis_entity_age_id")
        ),
        "analysis_entity_id": parse_required_int(
            entity_age.get("analysis_entity_id")
        ),
        "chronology_id": parse_optional_int(entity_age.get("chronology_id")),
        "dating_specifier": clean_optional_text(entity_age.get("dating_specifier")),
        "age": parse_optional_int(entity_age.get("age")),
        "age_older": parse_optional_int(entity_age.get("age_older")),
        "age_younger": parse_optional_int(entity_age.get("age_younger")),
        "age_range": clean_optional_text(entity_age.get("age_range")),
        "time_start_bp": interval[0] if interval is not None else None,
        "time_end_bp": interval[1] if interval is not None else None,
    }


def _geochronology_interval(
    geochronology_row: dict[str, object],
) -> tuple[int, int] | None:
    age = parse_optional_int(geochronology_row.get("age"))
    if age is None:
        return None
    error_older = parse_optional_int(geochronology_row.get("error_older")) or 0
    error_younger = parse_optional_int(geochronology_row.get("error_younger")) or 0
    return normalize_bp_interval(max(0, age - error_younger), age + error_older)


def _build_geochronology_row(
    geochronology_row: dict[str, object],
    *,
    interval: tuple[int, int] | None,
    uncertainty: dict[str, object],
) -> dict[str, object]:
    return {
        "geochron_id": parse_required_int(geochronology_row.get("geochron_id")),
        "analysis_entity_id": parse_required_int(
            geochronology_row.get("analysis_entity_id")
        ),
        "dating_lab_id": parse_optional_int(geochronology_row.get("dating_lab_id")),
        "lab_number": clean_optional_text(geochronology_row.get("lab_number")),
        "age": parse_optional_int(geochronology_row.get("age")),
        "error_older": parse_optional_int(geochronology_row.get("error_older")),
        "error_younger": parse_optional_int(geochronology_row.get("error_younger")),
        "notes": clean_optional_text(geochronology_row.get("notes")),
        "uncertainty_label": clean_optional_text(uncertainty.get("label")),
        "uncertainty_description": clean_optional_text(
            uncertainty.get("description")
        ),
        "time_start_bp": interval[0] if interval is not None else None,
        "time_end_bp": interval[1] if interval is not None else None,
    }


def _dendro_date_interval(
    dendro_date: dict[str, object],
    *,
    age_type: str,
) -> tuple[int, int] | None:
    return sead_dating_interval(
        {
            "low_value": dendro_date.get("age_younger"),
            "high_value": dendro_date.get("age_older"),
        },
        age_type=age_type,
    )


def _build_dendro_date_row(
    dendro_date: dict[str, object],
    *,
    age_type: str,
    interval: tuple[int, int] | None,
    uncertainty: dict[str, object],
) -> dict[str, object]:
    return {
        "dendro_date_id": parse_required_int(dendro_date.get("dendro_date_id")),
        "analysis_entity_id": parse_required_int(
            dendro_date.get("analysis_entity_id")
        ),
        "age_type": age_type,
        "age_older": parse_optional_int(dendro_date.get("age_older")),
        "age_younger": parse_optional_int(dendro_date.get("age_younger")),
        "age_range": clean_optional_text(dendro_date.get("age_range")),
        "dendro_lookup_id": parse_optional_int(dendro_date.get("dendro_lookup_id")),
        "season_id": parse_optional_int(dendro_date.get("season_id")),
        "uncertainty_label": clean_optional_text(uncertainty.get("label")),
        "uncertainty_description": clean_optional_text(
            uncertainty.get("description")
        ),
        "time_start_bp": interval[0] if interval is not None else None,
        "time_end_bp": interval[1] if interval is not None else None,
    }


def _build_bibliography_row(
    *,
    biblio_id: int,
    source_kind: str,
    source_record_id: int,
    source_record_label: str,
    biblio: dict[str, object],
) -> dict[str, object]:
    return {
        "biblio_id": biblio_id,
        "source_kind": source_kind,
        "source_record_id": source_record_id,
        "source_record_label": source_record_label,
        "title": str(biblio.get("title", "")).strip(),
        "full_reference": str(biblio.get("full_reference", "")).strip(),
        "year": str(biblio.get("year", "")).strip(),
        "doi": str(biblio.get("doi", "")).strip(),
        "url": str(biblio.get("url", "")).strip(),
    }


def _deduplicate_bibliography_rows(
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    unique_rows: dict[tuple[int, str, int], dict[str, object]] = {}
    for row in rows:
        key = (
            parse_required_int(row.get("biblio_id")),
            clean_optional_text(row.get("source_kind")),
            parse_required_int(row.get("source_record_id")),
        )
        unique_rows.setdefault(key, row)
    return list(unique_rows.values())


def _relative_interval_from_range(
    dating_range: dict[str, object],
    *,
    age_type: str,
) -> tuple[int, int] | None:
    text = age_type.casefold()
    if "cal" not in text and "c14" not in text:
        return None
    return _normalize_optional_interval(
        parse_optional_int(dating_range.get("low_value")),
        parse_optional_int(dating_range.get("high_value")),
    )


_RELATIVE_BP_LABEL_PATTERN = re.compile(
    r"^CAL_PERIOD_(?P<older>\d+)[_-](?P<younger>\d+)_BP$",
    re.IGNORECASE,
)
_RELATIVE_CALENDAR_LABEL_PATTERN = re.compile(
    r"^CAL_(?P<start>-?\d+)(?:-(?P<end>-?\d+))?_(?P<era>AD|BC)(?P<open>-)?$",
    re.IGNORECASE,
)


def _interval_from_relative_age_label(label: str) -> tuple[int, int] | None:
    bp_match = _RELATIVE_BP_LABEL_PATTERN.fullmatch(label.strip())
    if bp_match:
        return normalize_bp_interval(
            int(bp_match.group("younger")),
            int(bp_match.group("older")),
        )
    calendar_match = _RELATIVE_CALENDAR_LABEL_PATTERN.fullmatch(label.strip())
    if not calendar_match:
        return None
    era = calendar_match.group("era").upper()
    start_year = int(calendar_match.group("start"))
    end_text = calendar_match.group("end")
    end_year = int(end_text) if end_text is not None else start_year
    if calendar_match.group("open"):
        end_year = BP_REFERENCE_YEAR
    return normalize_bp_interval(
        _historical_year_to_bp(start_year, era=era),
        _historical_year_to_bp(end_year, era=era),
    )


def _historical_year_to_bp(year: int, *, era: str) -> int:
    if era == "BC" or year < 0:
        return _bce_year_to_bp(abs(year)) or 0
    return _ce_year_to_bp(year) or 0


def _normalize_optional_interval(
    start_value: int | None,
    end_value: int | None,
) -> tuple[int, int] | None:
    if start_value is None and end_value is None:
        return None
    if start_value is None:
        start_value = end_value
    if end_value is None:
        end_value = start_value
    return normalize_bp_interval(start_value, end_value)


def _calendar_year_interval_to_bp(
    start_year: int | None,
    end_year: int | None,
    *,
    treat_as_bce: bool,
) -> tuple[int, int] | None:
    if treat_as_bce:
        return _normalize_optional_interval(
            _bce_year_to_bp(start_year),
            _bce_year_to_bp(end_year),
        )
    return _normalize_optional_interval(
        _ce_year_to_bp(start_year),
        _ce_year_to_bp(end_year),
    )


def _ce_year_to_bp(year_ce: int | None) -> int | None:
    if year_ce is None:
        return None
    return max(0, BP_REFERENCE_YEAR - year_ce)


def _bce_year_to_bp(year_bce: int | None) -> int | None:
    if year_bce is None:
        return None
    return year_bce + (BP_REFERENCE_YEAR - 1)


def _is_common_era_age_type(age_type_text: str) -> bool:
    common_era_tokens = (" ad", " ce", "anno domini", "common era")
    normalized_text = f" {age_type_text} "
    return any(token in normalized_text for token in common_era_tokens)


def _is_before_common_era_age_type(age_type_text: str) -> bool:
    before_common_era_tokens = (
        " bc",
        " bce",
        "before christ",
        "before common era",
    )
    normalized_text = f" {age_type_text} "
    return any(token in normalized_text for token in before_common_era_tokens)


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
    *row_groups: list[dict[str, object]],
) -> list[str]:
    labels: list[str] = []
    for rows in row_groups:
        for row in rows:
            label = str(row.get("uncertainty_label", "")).strip()
            if label and label not in labels:
                labels.append(label)
    return labels


def refresh_sead_repository_rows(rows: list[dict[str, object]]) -> None:
    """Backfill repository-owned derived SEAD fields from checked-in linked rows."""
    for row in rows:
        relative_rows = [
            item for item in row.get("relative_period_rows", []) if isinstance(item, dict)
        ]
        dating_rows = [
            item for item in row.get("dating_range_rows", []) if isinstance(item, dict)
        ]
        entity_age_rows = [
            item
            for item in row.get("analysis_entity_age_rows", [])
            if isinstance(item, dict)
        ]
        geochronology_rows = [
            item
            for item in row.get("geochronology_rows", [])
            if isinstance(item, dict)
        ]
        dendro_date_rows = [
            item for item in row.get("dendro_date_rows", []) if isinstance(item, dict)
        ]
        bibliography_rows = [
            item for item in row.get("bibliography_rows", []) if isinstance(item, dict)
        ]
        numeric_intervals: list[tuple[int, int]] = []
        for dating_row in dating_rows:
            interval = sead_dating_interval(
                dating_row,
                age_type=clean_optional_text(dating_row.get("age_type")),
            ) or _relative_interval_from_range(
                dating_row,
                age_type=clean_optional_text(dating_row.get("age_type")),
            )
            dating_row["time_start_bp"] = interval[0] if interval is not None else None
            dating_row["time_end_bp"] = interval[1] if interval is not None else None
            if interval is not None:
                numeric_intervals.append(interval)
        for entity_age_row in entity_age_rows:
            interval = _analysis_entity_age_interval(entity_age_row)
            entity_age_row["time_start_bp"] = (
                interval[0] if interval is not None else None
            )
            entity_age_row["time_end_bp"] = (
                interval[1] if interval is not None else None
            )
            if interval is not None:
                numeric_intervals.append(interval)
        for geochronology_row in geochronology_rows:
            interval = _geochronology_interval(geochronology_row)
            geochronology_row["time_start_bp"] = (
                interval[0] if interval is not None else None
            )
            geochronology_row["time_end_bp"] = (
                interval[1] if interval is not None else None
            )
            if interval is not None:
                numeric_intervals.append(interval)
        for dendro_date_row in dendro_date_rows:
            interval = _dendro_date_interval(
                dendro_date_row,
                age_type=clean_optional_text(dendro_date_row.get("age_type")),
            )
            dendro_date_row["time_start_bp"] = (
                interval[0] if interval is not None else None
            )
            dendro_date_row["time_end_bp"] = (
                interval[1] if interval is not None else None
            )
            if interval is not None:
                numeric_intervals.append(interval)
        contextual_intervals: list[tuple[int, int]] = []
        for relative_row in relative_rows:
            interval = _normalize_optional_interval(
                parse_optional_int(relative_row.get("time_start_bp")),
                parse_optional_int(relative_row.get("time_end_bp")),
            )
            if interval is None:
                interval = _interval_from_relative_age_label(
                    clean_optional_text(relative_row.get("relative_age_label"))
                )
                if interval is not None:
                    relative_row["interval_source"] = "encoded_relative_age_label"
            relative_row["time_start_bp"] = interval[0] if interval is not None else None
            relative_row["time_end_bp"] = interval[1] if interval is not None else None
            if interval is not None:
                contextual_intervals.append(interval)
        numeric_time_interval = merge_sead_intervals(numeric_intervals)
        contextual_time_interval = merge_sead_intervals(contextual_intervals)
        time_interval = numeric_time_interval or contextual_time_interval
        row["relative_date_count"] = len(relative_rows)
        row["dating_range_count"] = len(dating_rows)
        row["analysis_entity_age_count"] = len(entity_age_rows)
        row["geochronology_count"] = len(geochronology_rows)
        row["dendro_date_count"] = len(dendro_date_rows)
        row["reference_count"] = max(
            parse_required_int(row.get("reference_count")),
            len(bibliography_rows),
        )
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
        row["temporal_summary"] = {
            "relative_period_count": len(relative_rows),
            "dating_range_count": len(dating_rows),
            "analysis_entity_age_count": len(entity_age_rows),
            "geochronology_count": len(geochronology_rows),
            "dendro_date_count": len(dendro_date_rows),
            "bibliography_count": len(bibliography_rows),
            "time_start_bp": row["time_start_bp"],
            "time_end_bp": row["time_end_bp"],
            "numeric_time_start_bp": row["numeric_time_start_bp"],
            "numeric_time_end_bp": row["numeric_time_end_bp"],
            "contextual_time_start_bp": row["contextual_time_start_bp"],
            "contextual_time_end_bp": row["contextual_time_end_bp"],
            "normalized_period_labels": _normalized_period_labels(relative_rows),
            "uncertainty_labels": _uncertainty_labels(
                relative_rows,
                dating_rows,
                entity_age_rows,
                geochronology_rows,
                dendro_date_rows,
            ),
        }
