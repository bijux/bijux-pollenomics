"""Site, chronology, dataset, and reference table plans."""

from __future__ import annotations

from ...models import SeadDependency, SeadScopedTablePlan
from ..scoped import _scoped_plan

_FOUNDATION_TABLE_PLANS = (
    _scoped_plan("tbl_sample_groups"),
    _scoped_plan("tbl_physical_samples"),
    _scoped_plan("tbl_analysis_entities"),
    _scoped_plan("tbl_analysis_entity_ages"),
    _scoped_plan("tbl_geochronology"),
    _scoped_plan("tbl_dendro_dates"),
    SeadScopedTablePlan(
        "tbl_analysis_values",
        "analysis_value_id",
        (
            "analysis_value_id,analysis_entity_id,value_class_id,analysis_value,"
            "boolean_value,is_boolean,is_uncertain,is_undefined,is_not_analyzed,"
            "is_indeterminable,is_anomaly"
        ),
        "analysis_entity_id",
        (SeadDependency("tbl_analysis_entities", "analysis_entity_id"),),
    ),
    _scoped_plan("tbl_analysis_dating_ranges"),
    _scoped_plan("tbl_relative_dates"),
    _scoped_plan("tbl_age_types"),
    _scoped_plan("tbl_relative_ages"),
    _scoped_plan("tbl_relative_age_refs"),
    _scoped_plan("tbl_dating_uncertainty"),
    SeadScopedTablePlan(
        "tbl_datasets",
        "dataset_id",
        (
            "dataset_id,master_set_id,data_type_id,method_id,biblio_id,"
            "dataset_name,date_updated,dataset_uuid"
        ),
        "dataset_id",
        (SeadDependency("tbl_analysis_entities", "dataset_id"),),
    ),
    _scoped_plan("tbl_site_references"),
    _scoped_plan("tbl_sample_group_references"),
)
