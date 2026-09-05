"""Full-evidence SEAD table acquisition plans."""

from __future__ import annotations

from ..models import SeadDependency, SeadJoinPlan, SeadScopedTablePlan
from .scoped import _scoped_plan

SEAD_FULL_EVIDENCE_TABLE_PLANS = (
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
    SeadScopedTablePlan(
        "tbl_abundance_ident_levels",
        "abundance_ident_level_id",
        ("abundance_ident_level_id,abundance_id,identification_level_id,date_updated"),
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
        ("record_type_id,record_type_name,record_type_description,date_updated"),
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
    SeadScopedTablePlan(
        "tbl_value_classes",
        "value_class_id",
        ("value_class_id,value_type_id,method_id,name,description,value_class_uuid"),
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
        ("data_type_id,data_type_group_id,data_type_name,date_updated,definition"),
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
    SeadScopedTablePlan(
        "tbl_dataset_methods",
        "dataset_method_id",
        "dataset_method_id,dataset_id,method_id,date_updated",
        "dataset_id",
        (SeadDependency("tbl_datasets", "dataset_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_dataset_masters",
        "master_set_id",
        (
            "master_set_id,master_set_uuid,master_name,master_notes,biblio_id,"
            "contact_id,url,date_updated"
        ),
        "master_set_id",
        (SeadDependency("tbl_datasets", "master_set_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_dataset_contacts",
        "dataset_contact_id",
        "dataset_contact_id,dataset_id,contact_id,contact_type_id,date_updated",
        "dataset_id",
        (SeadDependency("tbl_datasets", "dataset_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_contacts",
        "contact_id",
        (
            "contact_id,first_name,last_name,address_1,address_2,"
            "phone_number,email,url,date_updated"
        ),
        "contact_id",
        (
            SeadDependency("tbl_dataset_contacts", "contact_id"),
            SeadDependency("tbl_dataset_masters", "contact_id"),
        ),
    ),
    SeadScopedTablePlan(
        "tbl_contact_types",
        "contact_type_id",
        "contact_type_id,contact_type_name,description,date_updated",
        "contact_type_id",
        (SeadDependency("tbl_dataset_contacts", "contact_type_id"),),
    ),
    SeadScopedTablePlan(
        "tbl_methods",
        "method_id",
        "method_id,method_name,method_abbrev_or_alt_name,description",
        "method_id",
        (
            SeadDependency("tbl_relative_dates", "method_id"),
            SeadDependency("tbl_datasets", "method_id"),
            SeadDependency("tbl_dataset_methods", "method_id"),
            SeadDependency("tbl_value_classes", "method_id"),
            SeadDependency("tbl_sample_dimensions", "method_id"),
        ),
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
            SeadDependency("tbl_dataset_masters", "biblio_id"),
            SeadDependency("tbl_ecocode_systems", "biblio_id"),
        ),
    ),
)

_CORE_JOIN_PLANS = (
    SeadJoinPlan(
        "sites.sample_groups",
        "tbl_sites",
        "tbl_sample_groups",
        "site_id",
        "sample_group_id",
        "site_id",
        True,
    ),
    SeadJoinPlan(
        "sample_groups.physical_samples",
        "tbl_sample_groups",
        "tbl_physical_samples",
        "sample_group_id",
        "physical_sample_id",
        "sample_group_id",
        True,
    ),
    SeadJoinPlan(
        "physical_samples.analysis_entities",
        "tbl_physical_samples",
        "tbl_analysis_entities",
        "physical_sample_id",
        "analysis_entity_id",
        "physical_sample_id",
        True,
    ),
    SeadJoinPlan(
        "analysis_entities.analysis_entity_ages",
        "tbl_analysis_entities",
        "tbl_analysis_entity_ages",
        "analysis_entity_id",
        "analysis_entity_age_id",
        "analysis_entity_id",
        True,
    ),
    SeadJoinPlan(
        "analysis_entities.geochronology",
        "tbl_analysis_entities",
        "tbl_geochronology",
        "analysis_entity_id",
        "geochron_id",
        "analysis_entity_id",
        True,
    ),
    SeadJoinPlan(
        "analysis_entities.dendro_dates",
        "tbl_analysis_entities",
        "tbl_dendro_dates",
        "analysis_entity_id",
        "dendro_date_id",
        "analysis_entity_id",
        True,
    ),
    SeadJoinPlan(
        "analysis_entities.analysis_values",
        "tbl_analysis_entities",
        "tbl_analysis_values",
        "analysis_entity_id",
        "analysis_value_id",
        "analysis_entity_id",
        True,
    ),
    SeadJoinPlan(
        "analysis_values.analysis_dating_ranges",
        "tbl_analysis_values",
        "tbl_analysis_dating_ranges",
        "analysis_value_id",
        "analysis_dating_range_id",
        "analysis_value_id",
        True,
    ),
    SeadJoinPlan(
        "analysis_entities.relative_dates",
        "tbl_analysis_entities",
        "tbl_relative_dates",
        "analysis_entity_id",
        "relative_date_id",
        "analysis_entity_id",
        True,
    ),
    SeadJoinPlan(
        "relative_ages.relative_age_refs",
        "tbl_relative_ages",
        "tbl_relative_age_refs",
        "relative_age_id",
        "relative_age_ref_id",
        "relative_age_id",
        True,
    ),
    SeadJoinPlan(
        "sites.site_references",
        "tbl_sites",
        "tbl_site_references",
        "site_id",
        "site_reference_id",
        "site_id",
        True,
    ),
    SeadJoinPlan(
        "sample_groups.sample_group_references",
        "tbl_sample_groups",
        "tbl_sample_group_references",
        "sample_group_id",
        "sample_group_reference_id",
        "sample_group_id",
        True,
    ),
)

_LOOKUP_JOIN_PLANS = (
    SeadJoinPlan(
        "age_types.analysis_dating_ranges",
        "tbl_age_types",
        "tbl_analysis_dating_ranges",
        "age_type_id",
        "analysis_dating_range_id",
        "age_type_id",
        False,
    ),
    SeadJoinPlan(
        "age_types.dendro_dates",
        "tbl_age_types",
        "tbl_dendro_dates",
        "age_type_id",
        "dendro_date_id",
        "age_type_id",
        False,
    ),
    SeadJoinPlan(
        "relative_ages.relative_dates",
        "tbl_relative_ages",
        "tbl_relative_dates",
        "relative_age_id",
        "relative_date_id",
        "relative_age_id",
        False,
    ),
    SeadJoinPlan(
        "dating_uncertainty.analysis_dating_ranges",
        "tbl_dating_uncertainty",
        "tbl_analysis_dating_ranges",
        "dating_uncertainty_id",
        "analysis_dating_range_id",
        "dating_uncertainty_id",
        False,
    ),
    SeadJoinPlan(
        "dating_uncertainty.geochronology",
        "tbl_dating_uncertainty",
        "tbl_geochronology",
        "dating_uncertainty_id",
        "geochron_id",
        "dating_uncertainty_id",
        False,
    ),
    SeadJoinPlan(
        "dating_uncertainty.dendro_dates",
        "tbl_dating_uncertainty",
        "tbl_dendro_dates",
        "dating_uncertainty_id",
        "dendro_date_id",
        "dating_uncertainty_id",
        False,
    ),
    SeadJoinPlan(
        "dating_uncertainty.relative_dates",
        "tbl_dating_uncertainty",
        "tbl_relative_dates",
        "dating_uncertainty_id",
        "relative_date_id",
        "dating_uncertainty_id",
        False,
    ),
    SeadJoinPlan(
        "methods.relative_dates",
        "tbl_methods",
        "tbl_relative_dates",
        "method_id",
        "relative_date_id",
        "method_id",
        False,
    ),
    SeadJoinPlan(
        "datasets.analysis_entities",
        "tbl_datasets",
        "tbl_analysis_entities",
        "dataset_id",
        "analysis_entity_id",
        "dataset_id",
        False,
    ),
    SeadJoinPlan(
        "biblio.datasets",
        "tbl_biblio",
        "tbl_datasets",
        "biblio_id",
        "dataset_id",
        "biblio_id",
        False,
    ),
    SeadJoinPlan(
        "biblio.site_references",
        "tbl_biblio",
        "tbl_site_references",
        "biblio_id",
        "site_reference_id",
        "biblio_id",
        False,
    ),
    SeadJoinPlan(
        "biblio.sample_group_references",
        "tbl_biblio",
        "tbl_sample_group_references",
        "biblio_id",
        "sample_group_reference_id",
        "biblio_id",
        False,
    ),
    SeadJoinPlan(
        "biblio.relative_age_refs",
        "tbl_biblio",
        "tbl_relative_age_refs",
        "biblio_id",
        "relative_age_ref_id",
        "biblio_id",
        False,
    ),
)
