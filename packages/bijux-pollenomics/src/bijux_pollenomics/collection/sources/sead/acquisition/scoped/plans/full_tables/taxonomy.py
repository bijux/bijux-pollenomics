"""Abundance classification, taxonomy, and ecology table plans."""

from __future__ import annotations

from ...models import SeadDependency, SeadScopedTablePlan

_TAXONOMY_TABLE_PLANS = (
    SeadScopedTablePlan(
        "tbl_abundance_ident_levels",
        "abundance_ident_level_id",
        "abundance_ident_level_id,abundance_id,identification_level_id,date_updated",
        "abundance_id",
        (SeadDependency("tbl_abundances", "abundance_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_abundance_modifications",
        "abundance_modification_id",
        "abundance_modification_id,abundance_id,modification_type_id,date_updated",
        "abundance_id",
        (SeadDependency("tbl_abundances", "abundance_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_abundance_properties",
        "abundance_property_id",
        "abundance_property_id,abundance_id,property_type_id,property_value",
        "abundance_id",
        (SeadDependency("tbl_abundances", "abundance_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_abundance_elements",
        "abundance_element_id",
        (
            "abundance_element_id,record_type_id,element_name,"
            "element_description,date_updated"
        ),
        "abundance_element_id",
        (SeadDependency("tbl_abundances", "abundance_element_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_identification_levels",
        "identification_level_id",
        (
            "identification_level_id,identification_level_abbrev,"
            "identification_level_name,notes,date_updated"
        ),
        "identification_level_id",
        (SeadDependency("tbl_abundance_ident_levels", "identification_level_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_modification_types",
        "modification_type_id",
        (
            "modification_type_id,modification_type_name,"
            "modification_type_description,date_updated"
        ),
        "modification_type_id",
        (SeadDependency("tbl_abundance_modifications", "modification_type_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_property_types",
        "property_type_id",
        (
            "property_type_id,property_type_name,description,value_type_id,"
            "value_class_id,uuid"
        ),
        "property_type_id",
        (SeadDependency("tbl_abundance_properties", "property_type_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_taxa_tree_master",
        "taxon_id",
        "taxon_id,author_id,date_updated,genus_id,species",
        "taxon_id",
        (
            SeadDependency("tbl_abundances", "taxon_id"),
            SeadDependency("tbl_analysis_taxon_counts", "taxon_id"),
        ),
    ),
    SeadScopedTablePlan(
        "tbl_taxa_tree_authors",
        "author_id",
        "author_id,author_name,date_updated",
        "author_id",
        (SeadDependency("tbl_taxa_tree_master", "author_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_taxa_tree_genera",
        "genus_id",
        "genus_id,family_id,genus_name,date_updated",
        "genus_id",
        (SeadDependency("tbl_taxa_tree_master", "genus_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_taxa_tree_families",
        "family_id",
        "family_id,family_name,order_id,date_updated",
        "family_id",
        (SeadDependency("tbl_taxa_tree_genera", "family_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_taxa_tree_orders",
        "order_id",
        "order_id,order_name,record_type_id,sort_order,date_updated",
        "order_id",
        (SeadDependency("tbl_taxa_tree_families", "order_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_record_types",
        "record_type_id",
        "record_type_id,record_type_name,record_type_description,date_updated",
        "record_type_id",
        (
            SeadDependency("tbl_abundance_elements", "record_type_id"),
            SeadDependency("tbl_taxa_tree_orders", "record_type_id"),
        ),
    ),
    SeadScopedTablePlan(
        "tbl_ecocodes",
        "ecocode_id",
        "ecocode_id,date_updated,ecocode_definition_id,taxon_id",
        "taxon_id",
        (SeadDependency("tbl_taxa_tree_master", "taxon_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_ecocode_definitions",
        "ecocode_definition_id",
        (
            "ecocode_definition_id,abbreviation,date_updated,definition,"
            "ecocode_group_id,name,notes,sort_order"
        ),
        "ecocode_definition_id",
        (SeadDependency("tbl_ecocodes", "ecocode_definition_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_ecocode_groups",
        "ecocode_group_id",
        (
            "ecocode_group_id,date_updated,definition,ecocode_system_id,name,"
            "abbreviation"
        ),
        "ecocode_group_id",
        (SeadDependency("tbl_ecocode_definitions", "ecocode_group_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_ecocode_systems",
        "ecocode_system_id",
        (
            "ecocode_system_id,biblio_id,date_updated,definition,name,notes,"
            "ecocode_system_uuid"
        ),
        "ecocode_system_id",
        (SeadDependency("tbl_ecocode_groups", "ecocode_system_id"),),
    ),
)
