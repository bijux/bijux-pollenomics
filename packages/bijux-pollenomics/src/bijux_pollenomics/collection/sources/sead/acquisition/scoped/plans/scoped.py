"""Chronology-scoped SEAD table acquisition plans."""

from __future__ import annotations

from ..models import SeadDependency, SeadScopedTablePlan

SEAD_SCOPED_TABLE_PLANS = (
    SeadScopedTablePlan(
        "tbl_sample_groups",
        "sample_group_id",
        "sample_group_id,site_id,sample_group_name",
        "site_id",
        (SeadDependency("tbl_sites", "site_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_physical_samples",
        "physical_sample_id",
        "physical_sample_id,sample_group_id",
        "sample_group_id",
        (SeadDependency("tbl_sample_groups", "sample_group_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_analysis_entities",
        "analysis_entity_id",
        "analysis_entity_id,physical_sample_id,dataset_id",
        "physical_sample_id",
        (SeadDependency("tbl_physical_samples", "physical_sample_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_analysis_entity_ages",
        "analysis_entity_age_id",
        (
            "analysis_entity_age_id,analysis_entity_id,age,age_older,age_younger,"
            "chronology_id,dating_specifier,age_range"
        ),
        "analysis_entity_id",
        (SeadDependency("tbl_analysis_entities", "analysis_entity_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_geochronology",
        "geochron_id",
        (
            "geochron_id,analysis_entity_id,dating_lab_id,lab_number,age,"
            "error_older,error_younger,notes,dating_uncertainty_id"
        ),
        "analysis_entity_id",
        (SeadDependency("tbl_analysis_entities", "analysis_entity_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_dendro_dates",
        "dendro_date_id",
        (
            "dendro_date_id,analysis_entity_id,age_older,age_younger,age_type_id,"
            "dating_uncertainty_id,dendro_lookup_id,season_id,age_range"
        ),
        "analysis_entity_id",
        (SeadDependency("tbl_analysis_entities", "analysis_entity_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_analysis_values",
        "analysis_value_id",
        "analysis_value_id,analysis_entity_id",
        "analysis_entity_id",
        (SeadDependency("tbl_analysis_entities", "analysis_entity_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_analysis_dating_ranges",
        "analysis_dating_range_id",
        (
            "analysis_dating_range_id,analysis_value_id,low_value,high_value,"
            "age_type_id,dating_uncertainty_id,low_qualifier,high_qualifier,"
            "low_is_uncertain,high_is_uncertain"
        ),
        "analysis_value_id",
        (SeadDependency("tbl_analysis_values", "analysis_value_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_relative_dates",
        "relative_date_id",
        (
            "relative_date_id,analysis_entity_id,relative_age_id,"
            "dating_uncertainty_id,method_id,notes"
        ),
        "analysis_entity_id",
        (SeadDependency("tbl_analysis_entities", "analysis_entity_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_age_types",
        "age_type_id",
        "age_type_id,age_type,description",
        "age_type_id",
        (
            SeadDependency("tbl_analysis_dating_ranges", "age_type_id"),
            SeadDependency("tbl_dendro_dates", "age_type_id"),
        ),
    ),
    SeadScopedTablePlan(
        "tbl_relative_ages",
        "relative_age_id",
        (
            "relative_age_id,relative_age_name,description,abbreviation,"
            "cal_age_older,cal_age_younger,c14_age_older,c14_age_younger"
        ),
        "relative_age_id",
        (SeadDependency("tbl_relative_dates", "relative_age_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_relative_age_refs",
        "relative_age_ref_id",
        "relative_age_ref_id,relative_age_id,biblio_id",
        "relative_age_id",
        (SeadDependency("tbl_relative_ages", "relative_age_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_dating_uncertainty",
        "dating_uncertainty_id",
        "dating_uncertainty_id,uncertainty,description",
        "dating_uncertainty_id",
        (
            SeadDependency("tbl_analysis_dating_ranges", "dating_uncertainty_id"),
            SeadDependency("tbl_geochronology", "dating_uncertainty_id"),
            SeadDependency("tbl_dendro_dates", "dating_uncertainty_id"),
            SeadDependency("tbl_relative_dates", "dating_uncertainty_id"),
        ),
    ),
    SeadScopedTablePlan(
        "tbl_methods",
        "method_id",
        "method_id,method_name,method_abbrev_or_alt_name,description",
        "method_id",
        (SeadDependency("tbl_relative_dates", "method_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_datasets",
        "dataset_id",
        "dataset_id,dataset_name,biblio_id",
        "dataset_id",
        (SeadDependency("tbl_analysis_entities", "dataset_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_site_references",
        "site_reference_id",
        "site_reference_id,site_id,biblio_id",
        "site_id",
        (SeadDependency("tbl_sites", "site_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_sample_group_references",
        "sample_group_reference_id",
        "sample_group_reference_id,sample_group_id,biblio_id",
        "sample_group_id",
        (SeadDependency("tbl_sample_groups", "sample_group_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_biblio",
        "biblio_id",
        "biblio_id,title,full_reference,year,doi,url",
        "biblio_id",
        (
            SeadDependency("tbl_datasets", "biblio_id"),
            SeadDependency("tbl_site_references", "biblio_id"),
            SeadDependency("tbl_sample_group_references", "biblio_id"),
            SeadDependency("tbl_relative_age_refs", "biblio_id"),
        ),
    ),
)

_SCOPED_PLAN_BY_TABLE = {plan.table: plan for plan in SEAD_SCOPED_TABLE_PLANS}


def _scoped_plan(table: str) -> SeadScopedTablePlan:
    return _SCOPED_PLAN_BY_TABLE[table]
