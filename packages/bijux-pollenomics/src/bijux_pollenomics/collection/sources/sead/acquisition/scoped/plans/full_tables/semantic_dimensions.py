"""Value semantics, units, and data-type table plans."""

from __future__ import annotations

from ...models import SeadDependency, SeadScopedTablePlan

_SEMANTIC_DIMENSION_TABLE_PLANS = (
    SeadScopedTablePlan(
        "tbl_value_classes",
        "value_class_id",
        "value_class_id,value_type_id,method_id,name,description,value_class_uuid",
        "value_class_id",
        (
            SeadDependency("tbl_analysis_values", "value_class_id"),
            SeadDependency("tbl_property_types", "value_class_id"),
        ),
    ),
    SeadScopedTablePlan(
        "tbl_value_types",
        "value_type_id",
        (
            "value_type_id,unit_id,data_type_id,name,base_type,precision,"
            "description,value_type_uuid"
        ),
        "value_type_id",
        (
            SeadDependency("tbl_value_classes", "value_type_id"),
            SeadDependency("tbl_property_types", "value_type_id"),
        ),
    ),
    SeadScopedTablePlan(
        "tbl_value_type_items",
        "value_type_item_id",
        "value_type_item_id,value_type_id,name,description",
        "value_type_id",
        (SeadDependency("tbl_value_types", "value_type_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_dimensions",
        "dimension_id",
        (
            "dimension_id,date_updated,dimension_abbrev,dimension_description,"
            "dimension_name,unit_id"
        ),
        "dimension_id",
        (
            SeadDependency("tbl_analysis_value_dimensions", "dimension_id"),
            SeadDependency("tbl_measured_value_dimensions", "dimension_id"),
            SeadDependency("tbl_analysis_entity_dimensions", "dimension_id"),
            SeadDependency("tbl_sample_dimensions", "dimension_id"),
            SeadDependency("tbl_sample_group_dimensions", "dimension_id"),
        ),
    ),
    SeadScopedTablePlan(
        "tbl_units",
        "unit_id",
        "unit_id,date_updated,description,unit_abbrev,unit_name",
        "unit_id",
        (
            SeadDependency("tbl_value_types", "unit_id"),
            SeadDependency("tbl_dimensions", "unit_id"),
        ),
    ),
    SeadScopedTablePlan(
        "tbl_data_types",
        "data_type_id",
        "data_type_id,data_type_group_id,data_type_name,date_updated,definition",
        "data_type_id",
        (
            SeadDependency("tbl_datasets", "data_type_id"),
            SeadDependency("tbl_value_types", "data_type_id"),
        ),
    ),
    SeadScopedTablePlan(
        "tbl_data_type_groups",
        "data_type_group_id",
        "data_type_group_id,data_type_group_name,date_updated,description",
        "data_type_group_id",
        (SeadDependency("tbl_data_types", "data_type_group_id"),),
    ),
)
