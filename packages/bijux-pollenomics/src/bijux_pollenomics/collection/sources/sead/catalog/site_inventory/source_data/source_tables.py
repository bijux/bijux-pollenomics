"""Load the exact linked SEAD tables required for site enrichment."""

from __future__ import annotations

from dataclasses import dataclass

from ..values import parse_optional_int, parse_required_int
from .table_readers import SeadTableReader

Row = dict[str, object]


@dataclass(frozen=True, slots=True)
class SeadInventorySourceRows:
    sample_groups: list[Row]
    physical_samples: list[Row]
    analysis_entities: list[Row]
    analysis_entity_ages: list[Row]
    geochronology_rows: list[Row]
    dendro_dates: list[Row]
    analysis_values: list[Row]
    dating_ranges: list[Row]
    age_types: list[Row]
    relative_dates: list[Row]
    dating_uncertainties: list[Row]
    relative_ages: list[Row]
    methods: list[Row]
    datasets: list[Row]
    site_references: list[Row]
    sample_group_references: list[Row]
    relative_age_references: list[Row]
    bibliography_rows: list[Row]


def load_inventory_source_rows(
    site_ids: list[int], *, reader: SeadTableReader
) -> SeadInventorySourceRows:
    sample_groups = reader.rows_by_ids(
        "tbl_sample_groups",
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
        reader.rows_by_ids(
            "tbl_physical_samples",
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
        reader.rows_by_ids(
            "tbl_analysis_entities",
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
            reader.all_rows(
                "tbl_analysis_entity_ages",
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
            reader.all_rows(
                "tbl_geochronology",
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
            reader.all_rows(
                "tbl_dendro_dates",
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
    all_dating_ranges = reader.all_rows(
        "tbl_analysis_dating_ranges",
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
        reader.rows_by_ids(
            "tbl_analysis_values",
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
        reader.rows_by_ids(
            "tbl_age_types",
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
            reader.all_rows(
                "tbl_relative_dates",
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
        reader.rows_by_ids(
            "tbl_dating_uncertainty",
            select="dating_uncertainty_id,uncertainty,description",
            filter_field="dating_uncertainty_id",
            ids=sorted(set(dating_uncertainty_ids)),
            order_by=("dating_uncertainty_id",),
        )
        if dating_uncertainty_ids
        else []
    )
    relative_age_ids = [
        parse_required_int(row["relative_age_id"])
        for row in relative_dates
        if row.get("relative_age_id") is not None
    ]
    relative_ages = (
        reader.rows_by_ids(
            "tbl_relative_ages",
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
        reader.rows_by_ids(
            "tbl_methods",
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
        reader.rows_by_ids(
            "tbl_datasets",
            select="dataset_id,dataset_name,biblio_id",
            filter_field="dataset_id",
            ids=dataset_ids,
            order_by=("dataset_id",),
        )
        if dataset_ids
        else []
    )
    site_references = (
        reader.rows_by_ids(
            "tbl_site_references",
            select="site_reference_id,site_id,biblio_id",
            filter_field="site_id",
            ids=site_ids,
            order_by=("site_id", "site_reference_id"),
        )
        if site_ids
        else []
    )
    sample_group_references = (
        reader.rows_by_ids(
            "tbl_sample_group_references",
            select="sample_group_reference_id,sample_group_id,biblio_id",
            filter_field="sample_group_id",
            ids=sample_group_by_id,
            order_by=("sample_group_id", "sample_group_reference_id"),
        )
        if sample_group_by_id
        else []
    )
    relative_age_references = (
        reader.rows_by_ids(
            "tbl_relative_age_refs",
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
        reader.rows_by_ids(
            "tbl_biblio",
            select="biblio_id,title,full_reference,year,doi,url",
            filter_field="biblio_id",
            ids=biblio_ids,
            order_by=("biblio_id",),
        )
        if biblio_ids
        else []
    )
    return SeadInventorySourceRows(
        sample_groups=sample_groups,
        physical_samples=physical_samples,
        analysis_entities=analysis_entities,
        analysis_entity_ages=analysis_entity_ages,
        geochronology_rows=geochronology_rows,
        dendro_dates=dendro_dates,
        analysis_values=analysis_values,
        dating_ranges=dating_ranges,
        age_types=age_types,
        relative_dates=relative_dates,
        dating_uncertainties=dating_uncertainties,
        relative_ages=relative_ages,
        methods=methods,
        datasets=datasets,
        site_references=site_references,
        sample_group_references=sample_group_references,
        relative_age_references=relative_age_references,
        bibliography_rows=bibliography_rows,
    )


__all__ = ["SeadInventorySourceRows", "load_inventory_source_rows"]
