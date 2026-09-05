"""Observation-value and physical-dimension table plans."""

from __future__ import annotations

from ...models import SeadDependency, SeadScopedTablePlan

_OBSERVATION_VALUE_TABLE_PLANS = (
    SeadScopedTablePlan(
        "tbl_abundances",
        "abundance_id",
        (
            "abundance_id,taxon_id,analysis_entity_id,abundance_element_id,"
            "abundance,date_updated"
        ),
        "analysis_entity_id",
        (SeadDependency("tbl_analysis_entities", "analysis_entity_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_analysis_taxon_counts",
        "analysis_taxon_count_id",
        "analysis_taxon_count_id,analysis_value_id,taxon_id,value",
        "analysis_value_id",
        (SeadDependency("tbl_analysis_values", "analysis_value_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_analysis_numerical_values",
        "analysis_numerical_value_id",
        "analysis_numerical_value_id,analysis_value_id,qualifier,value,is_variant",
        "analysis_value_id",
        (SeadDependency("tbl_analysis_values", "analysis_value_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_analysis_integer_values",
        "analysis_integer_value_id",
        "analysis_integer_value_id,analysis_value_id,qualifier,value,is_variant",
        "analysis_value_id",
        (SeadDependency("tbl_analysis_values", "analysis_value_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_analysis_categorical_values",
        "analysis_categorical_value_id",
        (
            "analysis_categorical_value_id,analysis_value_id,value_type_item_id,"
            "value,is_variant"
        ),
        "analysis_value_id",
        (SeadDependency("tbl_analysis_values", "analysis_value_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_analysis_boolean_values",
        "analysis_boolean_value_id",
        "analysis_boolean_value_id,analysis_value_id,qualifier,value",
        "analysis_value_id",
        (SeadDependency("tbl_analysis_values", "analysis_value_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_analysis_value_dimensions",
        "analysis_value_dimension_id",
        "analysis_value_dimension_id,analysis_value_id,dimension_id,value",
        "analysis_value_id",
        (SeadDependency("tbl_analysis_values", "analysis_value_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_measured_values",
        "measured_value_id",
        "measured_value_id,analysis_entity_id,measured_value,date_updated",
        "analysis_entity_id",
        (SeadDependency("tbl_analysis_entities", "analysis_entity_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_measured_value_dimensions",
        "measured_value_dimension_id",
        (
            "measured_value_dimension_id,measured_value_id,dimension_id,"
            "dimension_value,date_updated"
        ),
        "measured_value_id",
        (SeadDependency("tbl_measured_values", "measured_value_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_analysis_entity_dimensions",
        "analysis_entity_dimension_id",
        (
            "analysis_entity_dimension_id,analysis_entity_id,dimension_id,"
            "dimension_value,date_updated"
        ),
        "analysis_entity_id",
        (SeadDependency("tbl_analysis_entities", "analysis_entity_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_sample_dimensions",
        "sample_dimension_id",
        (
            "sample_dimension_id,physical_sample_id,dimension_id,dimension_value,"
            "method_id,qualifier_id,date_updated"
        ),
        "physical_sample_id",
        (SeadDependency("tbl_physical_samples", "physical_sample_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_sample_group_dimensions",
        "sample_group_dimension_id",
        (
            "sample_group_dimension_id,sample_group_id,dimension_id,"
            "dimension_value,qualifier_id,date_updated"
        ),
        "sample_group_id",
        (SeadDependency("tbl_sample_groups", "sample_group_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_value_qualifiers",
        "qualifier_id",
        "qualifier_id,qualifier_uuid,symbol,description",
        "qualifier_id",
        (
            SeadDependency("tbl_sample_dimensions", "qualifier_id"),
            SeadDependency("tbl_sample_group_dimensions", "qualifier_id"),
        ),
    ),
)
