"""Dependency-scoped acquisition of the declared SEAD chronology relation graph.

This module deliberately has no live entry point.  Callers supply transport, clock,
sleep, country decisions, and immutable build identities explicitly.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
import math
from pathlib import Path
import re
import time

from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    NORDIC_COUNTRY_CODES,
    SeadTableAcquisition,
    acquire_sead_table,
    assert_sead_join_complete,
    materialize_sead_acquisition,
    reconcile_sead_countries,
    reconcile_sead_join,
)
from bijux_pollenomics.collection.sources.sead.acquisition.client import (
    SEAD_FILTER_BATCH_SIZE,
    SEAD_LIMIT,
    build_sead_in_filter,
)
from bijux_pollenomics.collection.sources.sead.acquisition.archive import (
    SEAD_FULL_EVIDENCE_SOURCE_TABLES,
    SEAD_LINKED_SOURCE_TABLES,
)

SCOPED_RECEIPT_SCHEMA_VERSION = "sead-scoped-acquisition-receipt.v1"
SCOPED_RESULT_SCHEMA_VERSION = "sead-scoped-acquisition-result.v1"
SCOPED_ORCHESTRATOR_VERSION = "sead-scoped-relation-acquisition.v1"
FULL_EVIDENCE_ORCHESTRATOR_VERSION = "sead-full-evidence-acquisition.v1"
NORDIC_TARGET_COUNTRIES = tuple(NORDIC_COUNTRY_CODES[:-1])

_SAFE_RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


@dataclass(frozen=True)
class SeadDependency:
    """One upstream field whose values define a downstream query scope."""

    table: str
    field: str


@dataclass(frozen=True)
class SeadScopedTablePlan:
    """Projection and dependency filter for one SEAD table."""

    table: str
    primary_key: str
    projection: str
    filter_field: str
    dependencies: tuple[SeadDependency, ...]


@dataclass(frozen=True)
class SeadJoinPlan:
    """One relation edge to reconcile after scoped acquisition."""

    edge: str
    parent_table: str
    child_table: str
    parent_key: str
    child_key: str
    child_foreign_key: str
    reference_required: bool


@dataclass(frozen=True)
class SeadScopedAcquisitionResult:
    """In-memory result plus the immutable manifest path."""

    schema_version: str
    scope_id: str
    run_id: str
    parent_run_id: str
    build_id: str
    manifest_path: Path
    acquisitions: tuple[SeadTableAcquisition, ...]
    country_reconciliation: dict[str, object]
    join_reconciliations: tuple[dict[str, object], ...]


_SITE_PROJECTION = (
    "site_id,site_name,national_site_identifier,latitude_dd,longitude_dd,"
    "altitude,site_description,site_uuid"
)

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

SEAD_FULL_EVIDENCE_JOIN_PLANS = (
    *_CORE_JOIN_PLANS,
    *_LOOKUP_JOIN_PLANS,
    SeadJoinPlan(
        "analysis_entities.abundances",
        "tbl_analysis_entities",
        "tbl_abundances",
        "analysis_entity_id",
        "abundance_id",
        "analysis_entity_id",
        True,
    ),
    SeadJoinPlan(
        "analysis_values.analysis_taxon_counts",
        "tbl_analysis_values",
        "tbl_analysis_taxon_counts",
        "analysis_value_id",
        "analysis_taxon_count_id",
        "analysis_value_id",
        True,
    ),
    *(
        SeadJoinPlan(
            f"analysis_values.{table.removeprefix('tbl_')}",
            "tbl_analysis_values",
            table,
            "analysis_value_id",
            primary_key,
            "analysis_value_id",
            True,
        )
        for table, primary_key in (
            ("tbl_analysis_numerical_values", "analysis_numerical_value_id"),
            ("tbl_analysis_integer_values", "analysis_integer_value_id"),
            ("tbl_analysis_categorical_values", "analysis_categorical_value_id"),
            ("tbl_analysis_boolean_values", "analysis_boolean_value_id"),
            ("tbl_analysis_value_dimensions", "analysis_value_dimension_id"),
        )
    ),
    SeadJoinPlan(
        "analysis_entities.measured_values",
        "tbl_analysis_entities",
        "tbl_measured_values",
        "analysis_entity_id",
        "measured_value_id",
        "analysis_entity_id",
        True,
    ),
    SeadJoinPlan(
        "measured_values.dimensions",
        "tbl_measured_values",
        "tbl_measured_value_dimensions",
        "measured_value_id",
        "measured_value_dimension_id",
        "measured_value_id",
        True,
    ),
    SeadJoinPlan(
        "analysis_entities.dimensions",
        "tbl_analysis_entities",
        "tbl_analysis_entity_dimensions",
        "analysis_entity_id",
        "analysis_entity_dimension_id",
        "analysis_entity_id",
        True,
    ),
    SeadJoinPlan(
        "physical_samples.dimensions",
        "tbl_physical_samples",
        "tbl_sample_dimensions",
        "physical_sample_id",
        "sample_dimension_id",
        "physical_sample_id",
        True,
    ),
    SeadJoinPlan(
        "sample_groups.dimensions",
        "tbl_sample_groups",
        "tbl_sample_group_dimensions",
        "sample_group_id",
        "sample_group_dimension_id",
        "sample_group_id",
        True,
    ),
    SeadJoinPlan(
        "value_qualifiers.sample_dimensions",
        "tbl_value_qualifiers",
        "tbl_sample_dimensions",
        "qualifier_id",
        "sample_dimension_id",
        "qualifier_id",
        False,
    ),
    SeadJoinPlan(
        "value_qualifiers.sample_group_dimensions",
        "tbl_value_qualifiers",
        "tbl_sample_group_dimensions",
        "qualifier_id",
        "sample_group_dimension_id",
        "qualifier_id",
        False,
    ),
    *(
        SeadJoinPlan(
            f"abundances.{table.removeprefix('tbl_abundance_')}",
            "tbl_abundances",
            table,
            "abundance_id",
            primary_key,
            "abundance_id",
            True,
        )
        for table, primary_key in (
            ("tbl_abundance_ident_levels", "abundance_ident_level_id"),
            ("tbl_abundance_modifications", "abundance_modification_id"),
            ("tbl_abundance_properties", "abundance_property_id"),
        )
    ),
    SeadJoinPlan(
        "abundance_elements.abundances",
        "tbl_abundance_elements",
        "tbl_abundances",
        "abundance_element_id",
        "abundance_id",
        "abundance_element_id",
        False,
    ),
    SeadJoinPlan(
        "identification_levels.abundance_ident_levels",
        "tbl_identification_levels",
        "tbl_abundance_ident_levels",
        "identification_level_id",
        "abundance_ident_level_id",
        "identification_level_id",
        False,
    ),
    SeadJoinPlan(
        "modification_types.abundance_modifications",
        "tbl_modification_types",
        "tbl_abundance_modifications",
        "modification_type_id",
        "abundance_modification_id",
        "modification_type_id",
        False,
    ),
    SeadJoinPlan(
        "property_types.abundance_properties",
        "tbl_property_types",
        "tbl_abundance_properties",
        "property_type_id",
        "abundance_property_id",
        "property_type_id",
        False,
    ),
    SeadJoinPlan(
        "taxa.abundances",
        "tbl_taxa_tree_master",
        "tbl_abundances",
        "taxon_id",
        "abundance_id",
        "taxon_id",
        False,
    ),
    SeadJoinPlan(
        "taxa.analysis_taxon_counts",
        "tbl_taxa_tree_master",
        "tbl_analysis_taxon_counts",
        "taxon_id",
        "analysis_taxon_count_id",
        "taxon_id",
        False,
    ),
    SeadJoinPlan(
        "taxon_authors.taxa",
        "tbl_taxa_tree_authors",
        "tbl_taxa_tree_master",
        "author_id",
        "taxon_id",
        "author_id",
        False,
    ),
    SeadJoinPlan(
        "taxon_genera.taxa",
        "tbl_taxa_tree_genera",
        "tbl_taxa_tree_master",
        "genus_id",
        "taxon_id",
        "genus_id",
        False,
    ),
    SeadJoinPlan(
        "taxon_families.genera",
        "tbl_taxa_tree_families",
        "tbl_taxa_tree_genera",
        "family_id",
        "genus_id",
        "family_id",
        False,
    ),
    SeadJoinPlan(
        "taxon_orders.families",
        "tbl_taxa_tree_orders",
        "tbl_taxa_tree_families",
        "order_id",
        "family_id",
        "order_id",
        False,
    ),
    SeadJoinPlan(
        "record_types.taxon_orders",
        "tbl_record_types",
        "tbl_taxa_tree_orders",
        "record_type_id",
        "order_id",
        "record_type_id",
        False,
    ),
    SeadJoinPlan(
        "record_types.abundance_elements",
        "tbl_record_types",
        "tbl_abundance_elements",
        "record_type_id",
        "abundance_element_id",
        "record_type_id",
        False,
    ),
    SeadJoinPlan(
        "taxa.ecocodes",
        "tbl_taxa_tree_master",
        "tbl_ecocodes",
        "taxon_id",
        "ecocode_id",
        "taxon_id",
        True,
    ),
    SeadJoinPlan(
        "ecocode_definitions.ecocodes",
        "tbl_ecocode_definitions",
        "tbl_ecocodes",
        "ecocode_definition_id",
        "ecocode_id",
        "ecocode_definition_id",
        False,
    ),
    SeadJoinPlan(
        "ecocode_groups.definitions",
        "tbl_ecocode_groups",
        "tbl_ecocode_definitions",
        "ecocode_group_id",
        "ecocode_definition_id",
        "ecocode_group_id",
        False,
    ),
    SeadJoinPlan(
        "ecocode_systems.groups",
        "tbl_ecocode_systems",
        "tbl_ecocode_groups",
        "ecocode_system_id",
        "ecocode_group_id",
        "ecocode_system_id",
        False,
    ),
    SeadJoinPlan(
        "value_classes.analysis_values",
        "tbl_value_classes",
        "tbl_analysis_values",
        "value_class_id",
        "analysis_value_id",
        "value_class_id",
        False,
    ),
    SeadJoinPlan(
        "value_classes.property_types",
        "tbl_value_classes",
        "tbl_property_types",
        "value_class_id",
        "property_type_id",
        "value_class_id",
        False,
    ),
    SeadJoinPlan(
        "value_types.value_classes",
        "tbl_value_types",
        "tbl_value_classes",
        "value_type_id",
        "value_class_id",
        "value_type_id",
        False,
    ),
    SeadJoinPlan(
        "value_types.property_types",
        "tbl_value_types",
        "tbl_property_types",
        "value_type_id",
        "property_type_id",
        "value_type_id",
        False,
    ),
    SeadJoinPlan(
        "value_types.items",
        "tbl_value_types",
        "tbl_value_type_items",
        "value_type_id",
        "value_type_item_id",
        "value_type_id",
        True,
    ),
    SeadJoinPlan(
        "value_type_items.categorical_values",
        "tbl_value_type_items",
        "tbl_analysis_categorical_values",
        "value_type_item_id",
        "analysis_categorical_value_id",
        "value_type_item_id",
        False,
    ),
    SeadJoinPlan(
        "dimensions.analysis_value_dimensions",
        "tbl_dimensions",
        "tbl_analysis_value_dimensions",
        "dimension_id",
        "analysis_value_dimension_id",
        "dimension_id",
        False,
    ),
    SeadJoinPlan(
        "dimensions.measured_value_dimensions",
        "tbl_dimensions",
        "tbl_measured_value_dimensions",
        "dimension_id",
        "measured_value_dimension_id",
        "dimension_id",
        False,
    ),
    SeadJoinPlan(
        "dimensions.analysis_entity_dimensions",
        "tbl_dimensions",
        "tbl_analysis_entity_dimensions",
        "dimension_id",
        "analysis_entity_dimension_id",
        "dimension_id",
        False,
    ),
    SeadJoinPlan(
        "dimensions.sample_dimensions",
        "tbl_dimensions",
        "tbl_sample_dimensions",
        "dimension_id",
        "sample_dimension_id",
        "dimension_id",
        False,
    ),
    SeadJoinPlan(
        "dimensions.sample_group_dimensions",
        "tbl_dimensions",
        "tbl_sample_group_dimensions",
        "dimension_id",
        "sample_group_dimension_id",
        "dimension_id",
        False,
    ),
    SeadJoinPlan(
        "units.value_types",
        "tbl_units",
        "tbl_value_types",
        "unit_id",
        "value_type_id",
        "unit_id",
        False,
    ),
    SeadJoinPlan(
        "units.dimensions",
        "tbl_units",
        "tbl_dimensions",
        "unit_id",
        "dimension_id",
        "unit_id",
        False,
    ),
    SeadJoinPlan(
        "data_types.datasets",
        "tbl_data_types",
        "tbl_datasets",
        "data_type_id",
        "dataset_id",
        "data_type_id",
        False,
    ),
    SeadJoinPlan(
        "data_types.value_types",
        "tbl_data_types",
        "tbl_value_types",
        "data_type_id",
        "value_type_id",
        "data_type_id",
        False,
    ),
    SeadJoinPlan(
        "data_type_groups.data_types",
        "tbl_data_type_groups",
        "tbl_data_types",
        "data_type_group_id",
        "data_type_id",
        "data_type_group_id",
        False,
    ),
    SeadJoinPlan(
        "datasets.dataset_methods",
        "tbl_datasets",
        "tbl_dataset_methods",
        "dataset_id",
        "dataset_method_id",
        "dataset_id",
        True,
    ),
    SeadJoinPlan(
        "dataset_masters.datasets",
        "tbl_dataset_masters",
        "tbl_datasets",
        "master_set_id",
        "dataset_id",
        "master_set_id",
        False,
    ),
    SeadJoinPlan(
        "datasets.dataset_contacts",
        "tbl_datasets",
        "tbl_dataset_contacts",
        "dataset_id",
        "dataset_contact_id",
        "dataset_id",
        True,
    ),
    SeadJoinPlan(
        "contacts.dataset_contacts",
        "tbl_contacts",
        "tbl_dataset_contacts",
        "contact_id",
        "dataset_contact_id",
        "contact_id",
        False,
    ),
    SeadJoinPlan(
        "contacts.dataset_masters",
        "tbl_contacts",
        "tbl_dataset_masters",
        "contact_id",
        "master_set_id",
        "contact_id",
        False,
    ),
    SeadJoinPlan(
        "contact_types.dataset_contacts",
        "tbl_contact_types",
        "tbl_dataset_contacts",
        "contact_type_id",
        "dataset_contact_id",
        "contact_type_id",
        False,
    ),
    SeadJoinPlan(
        "methods.datasets",
        "tbl_methods",
        "tbl_datasets",
        "method_id",
        "dataset_id",
        "method_id",
        False,
    ),
    SeadJoinPlan(
        "methods.dataset_methods",
        "tbl_methods",
        "tbl_dataset_methods",
        "method_id",
        "dataset_method_id",
        "method_id",
        False,
    ),
    SeadJoinPlan(
        "methods.value_classes",
        "tbl_methods",
        "tbl_value_classes",
        "method_id",
        "value_class_id",
        "method_id",
        False,
    ),
    SeadJoinPlan(
        "methods.sample_dimensions",
        "tbl_methods",
        "tbl_sample_dimensions",
        "method_id",
        "sample_dimension_id",
        "method_id",
        False,
    ),
    SeadJoinPlan(
        "biblio.dataset_masters",
        "tbl_biblio",
        "tbl_dataset_masters",
        "biblio_id",
        "master_set_id",
        "biblio_id",
        False,
    ),
    SeadJoinPlan(
        "biblio.ecocode_systems",
        "tbl_biblio",
        "tbl_ecocode_systems",
        "biblio_id",
        "ecocode_system_id",
        "biblio_id",
        False,
    ),
)


def acquire_scoped_sead_relations(
    output_root: Path,
    *,
    bbox: tuple[float, float, float, float],
    governed_country_by_site_id: Mapping[object, str],
    country_assignment_id: str,
    scope_id: str,
    run_id: str,
    parent_run_id: str,
    build_id: str,
    fetch_json_fn: Callable[..., object],
    clock: Callable[[], datetime] | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    id_batch_size: int = SEAD_FILTER_BATCH_SIZE,
    page_size: int = SEAD_LIMIT,
    max_pages: int = 10_000,
    request_retries: int = 5,
    request_timeout_seconds: float = 60.0,
) -> SeadScopedAcquisitionResult:
    """Acquire and atomically materialize the declared chronology relation graph."""
    return _acquire_sead_relations(
        output_root,
        bbox=bbox,
        governed_country_by_site_id=governed_country_by_site_id,
        country_assignment_id=country_assignment_id,
        scope_id=scope_id,
        run_id=run_id,
        parent_run_id=parent_run_id,
        build_id=build_id,
        fetch_json_fn=fetch_json_fn,
        clock=clock,
        sleep_fn=sleep_fn,
        id_batch_size=id_batch_size,
        page_size=page_size,
        max_pages=max_pages,
        request_retries=request_retries,
        request_timeout_seconds=request_timeout_seconds,
        relation_scope="chronology_relations",
        table_plans=SEAD_SCOPED_TABLE_PLANS,
        join_plans=(*_CORE_JOIN_PLANS, *_LOOKUP_JOIN_PLANS),
        required_tables=SEAD_LINKED_SOURCE_TABLES,
        orchestrator_version=SCOPED_ORCHESTRATOR_VERSION,
    )


def acquire_full_evidence_sead_relations(
    output_root: Path,
    *,
    bbox: tuple[float, float, float, float],
    governed_country_by_site_id: Mapping[object, str],
    country_assignment_id: str,
    scope_id: str,
    run_id: str,
    parent_run_id: str,
    build_id: str,
    fetch_json_fn: Callable[..., object],
    clock: Callable[[], datetime] | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    id_batch_size: int = SEAD_FILTER_BATCH_SIZE,
    page_size: int = SEAD_LIMIT,
    max_pages: int = 10_000,
    request_retries: int = 5,
    request_timeout_seconds: float = 60.0,
) -> SeadScopedAcquisitionResult:
    """Acquire source-native chronology and observation evidence relations."""
    return _acquire_sead_relations(
        output_root,
        bbox=bbox,
        governed_country_by_site_id=governed_country_by_site_id,
        country_assignment_id=country_assignment_id,
        scope_id=scope_id,
        run_id=run_id,
        parent_run_id=parent_run_id,
        build_id=build_id,
        fetch_json_fn=fetch_json_fn,
        clock=clock,
        sleep_fn=sleep_fn,
        id_batch_size=id_batch_size,
        page_size=page_size,
        max_pages=max_pages,
        request_retries=request_retries,
        request_timeout_seconds=request_timeout_seconds,
        relation_scope="full_evidence_relations",
        table_plans=SEAD_FULL_EVIDENCE_TABLE_PLANS,
        join_plans=SEAD_FULL_EVIDENCE_JOIN_PLANS,
        required_tables=SEAD_FULL_EVIDENCE_SOURCE_TABLES,
        orchestrator_version=FULL_EVIDENCE_ORCHESTRATOR_VERSION,
    )


def _acquire_sead_relations(
    output_root: Path,
    *,
    bbox: tuple[float, float, float, float],
    governed_country_by_site_id: Mapping[object, str],
    country_assignment_id: str,
    scope_id: str,
    run_id: str,
    parent_run_id: str,
    build_id: str,
    fetch_json_fn: Callable[..., object],
    clock: Callable[[], datetime] | None,
    sleep_fn: Callable[[float], None],
    id_batch_size: int,
    page_size: int,
    max_pages: int,
    request_retries: int,
    request_timeout_seconds: float,
    relation_scope: str,
    table_plans: Sequence[SeadScopedTablePlan],
    join_plans: Sequence[SeadJoinPlan],
    required_tables: Sequence[str],
    orchestrator_version: str,
) -> SeadScopedAcquisitionResult:
    _validate_declared_table_coverage(table_plans, required_tables, relation_scope)
    _validate_bbox(bbox)
    _validate_identity(scope_id, "scope_id")
    _validate_identity(run_id, "run_id", path_segment=True)
    _validate_identity(parent_run_id, "parent_run_id")
    _validate_identity(build_id, "build_id")
    _validate_identity(country_assignment_id, "country_assignment_id")
    if id_batch_size < 1:
        raise ValueError("SEAD dependency ID batch size must be positive")

    resolved_clock = clock or _current_utc
    assignments = _normalize_country_assignments(governed_country_by_site_id)
    assignment_payload = [
        {"site_id": site_id, "country_code": code}
        for site_id, code in sorted(assignments.items())
    ]
    assignment_sha256 = hashlib.sha256(_canonical_bytes(assignment_payload)).hexdigest()
    scope = {
        "scope_id": scope_id,
        "relation_scope": relation_scope,
        "countries": list(NORDIC_TARGET_COUNTRIES),
        "bbox": list(bbox),
        "country_assignment_id": country_assignment_id,
        "country_assignment_sha256": assignment_sha256,
        "orchestration_run_id": run_id,
        "parent_run_id": parent_run_id,
        "build_id": build_id,
    }
    bbox_filters = _bbox_filters(bbox)
    bbox_sites = acquire_sead_table(
        "tbl_sites",
        fetch_json_fn=fetch_json_fn,
        select=_SITE_PROJECTION,
        filters=bbox_filters,
        order_by=("site_id",),
        country_scope=NORDIC_TARGET_COUNTRIES,
        spatial_scope={**scope, "kind": "governed_bbox"},
        parent_run_id=parent_run_id,
        build_id=build_id,
        page_size=page_size,
        max_pages=max_pages,
        request_retries=request_retries,
        request_timeout_seconds=request_timeout_seconds,
        clock=resolved_clock,
        sleep_fn=sleep_fn,
    )
    bbox_rows = _validated_rows(
        "tbl_sites", bbox_sites.rows, "site_id", _SITE_PROJECTION
    )
    _validate_site_uuids(bbox_rows)
    bbox_site_ids = {_required_source_id(row, "site_id") for row in bbox_rows}
    if bbox_site_ids != set(assignments):
        missing_decisions = sorted(bbox_site_ids - set(assignments))
        stale_decisions = sorted(set(assignments) - bbox_site_ids)
        raise ValueError(
            "Governed SEAD country decisions must exactly cover bbox sites; "
            f"missing={missing_decisions}, stale={stale_decisions}"
        )
    scoped_site_rows = tuple(
        row
        for row in bbox_rows
        if assignments[_required_source_id(row, "site_id")] in NORDIC_TARGET_COUNTRIES
    )
    excluded_site_ids = sorted(
        site_id for site_id, code in assignments.items() if code == "UNASSIGNED"
    )
    site_acquisition = _aggregate_table_acquisition(
        table="tbl_sites",
        rows=scoped_site_rows,
        primary_key="site_id",
        projection=_SITE_PROJECTION,
        filter_field="site_id",
        requested_ids=sorted(bbox_site_ids),
        query_acquisitions=(bbox_sites,),
        scope=scope,
        run_id=run_id,
        parent_run_id=parent_run_id,
        build_id=build_id,
        completion_basis="governed_bbox_filter",
        extra_receipt_fields={
            "bbox_row_count": len(bbox_rows),
            "governed_row_count": len(scoped_site_rows),
            "scope_excluded_site_ids": excluded_site_ids,
            "scope_exclusion_reason": "country_assignment_unassigned",
            "governed_country_assignments": assignment_payload,
        },
        orchestrator_version=orchestrator_version,
        clock=resolved_clock,
    )

    acquisitions = [site_acquisition]
    rows_by_table: dict[str, tuple[dict[str, object], ...]] = {
        "tbl_sites": site_acquisition.rows
    }
    for plan in table_plans:
        requested_ids = _dependency_ids(plan.dependencies, rows_by_table)
        acquisition = _acquire_dependency_scoped_table(
            plan,
            requested_ids=requested_ids,
            fetch_json_fn=fetch_json_fn,
            scope=scope,
            run_id=run_id,
            parent_run_id=parent_run_id,
            build_id=build_id,
            clock=resolved_clock,
            sleep_fn=sleep_fn,
            id_batch_size=id_batch_size,
            page_size=page_size,
            max_pages=max_pages,
            request_retries=request_retries,
            request_timeout_seconds=request_timeout_seconds,
            orchestrator_version=orchestrator_version,
        )
        acquisitions.append(acquisition)
        rows_by_table[plan.table] = acquisition.rows

    country_reconciliation = reconcile_sead_countries(
        site_acquisition.rows,
        country_by_site_id={
            str(site_id): code
            for site_id, code in assignments.items()
            if code in NORDIC_TARGET_COUNTRIES
        },
    )
    country_reconciliation.update(
        {
            "scope_id": scope_id,
            "run_id": run_id,
            "parent_run_id": parent_run_id,
            "build_id": build_id,
            "country_assignment_id": country_assignment_id,
            "country_assignment_sha256": assignment_sha256,
            "bbox_row_count": len(bbox_rows),
            "scope_excluded_count": len(excluded_site_ids),
            "scope_excluded_site_ids": excluded_site_ids,
        }
    )
    if (
        country_reconciliation.get("reconciles") is not True
        or country_reconciliation.get("unassigned_count") != 0
    ):
        raise ValueError("Governed four-country SEAD site reconciliation failed")

    join_reconciliations = tuple(
        _reconcile_join(
            plan,
            rows_by_table=rows_by_table,
            scope_id=scope_id,
            run_id=run_id,
            parent_run_id=parent_run_id,
            build_id=build_id,
        )
        for plan in join_plans
    )
    for reconciliation in join_reconciliations:
        assert_sead_join_complete(reconciliation)

    manifest_path = materialize_sead_acquisition(
        Path(output_root) / run_id,
        acquisitions=acquisitions,
        required_tables=required_tables,
        country_reconciliation=country_reconciliation,
        join_reconciliations=join_reconciliations,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("status") != "complete":
        raise ValueError("Scoped SEAD acquisition manifest is not complete")
    return SeadScopedAcquisitionResult(
        schema_version=SCOPED_RESULT_SCHEMA_VERSION,
        scope_id=scope_id,
        run_id=run_id,
        parent_run_id=parent_run_id,
        build_id=build_id,
        manifest_path=manifest_path,
        acquisitions=tuple(acquisitions),
        country_reconciliation=country_reconciliation,
        join_reconciliations=join_reconciliations,
    )


def _acquire_dependency_scoped_table(
    plan: SeadScopedTablePlan,
    *,
    requested_ids: tuple[int, ...],
    fetch_json_fn: Callable[..., object],
    scope: Mapping[str, object],
    run_id: str,
    parent_run_id: str,
    build_id: str,
    clock: Callable[[], datetime],
    sleep_fn: Callable[[float], None],
    id_batch_size: int,
    page_size: int,
    max_pages: int,
    request_retries: int,
    request_timeout_seconds: float,
    orchestrator_version: str,
) -> SeadTableAcquisition:
    query_acquisitions: list[SeadTableAcquisition] = []
    rows: list[dict[str, object]] = []
    for start in range(0, len(requested_ids), id_batch_size):
        batch = requested_ids[start : start + id_batch_size]
        acquisition = acquire_sead_table(
            plan.table,
            fetch_json_fn=fetch_json_fn,
            select=plan.projection,
            filters=((plan.filter_field, build_sead_in_filter(list(batch))),),
            order_by=(plan.filter_field, plan.primary_key),
            country_scope=NORDIC_TARGET_COUNTRIES,
            spatial_scope={
                **scope,
                "kind": "dependency_identity_filter",
                "filter_field": plan.filter_field,
                "filter_ids": list(batch),
            },
            parent_run_id=parent_run_id,
            build_id=build_id,
            page_size=page_size,
            max_pages=max_pages,
            request_retries=request_retries,
            request_timeout_seconds=request_timeout_seconds,
            clock=clock,
            sleep_fn=sleep_fn,
        )
        allowed = set(batch)
        for row in acquisition.rows:
            observed = _required_source_id(row, plan.filter_field)
            if observed not in allowed:
                raise ValueError(
                    f"SEAD source ignored dependency filter for {plan.table}: "
                    f"{plan.filter_field}={observed}"
                )
        query_acquisitions.append(acquisition)
        rows.extend(dict(row) for row in acquisition.rows)
    validated = _validated_rows(plan.table, rows, plan.primary_key, plan.projection)
    return _aggregate_table_acquisition(
        table=plan.table,
        rows=validated,
        primary_key=plan.primary_key,
        projection=plan.projection,
        filter_field=plan.filter_field,
        requested_ids=requested_ids,
        query_acquisitions=tuple(query_acquisitions),
        scope=scope,
        run_id=run_id,
        parent_run_id=parent_run_id,
        build_id=build_id,
        completion_basis=(
            "all_dependency_batches_complete"
            if requested_ids
            else "empty_dependency_identity_set"
        ),
        extra_receipt_fields={},
        orchestrator_version=orchestrator_version,
        clock=clock,
    )


def _aggregate_table_acquisition(
    *,
    table: str,
    rows: Iterable[Mapping[str, object]],
    primary_key: str,
    projection: str,
    filter_field: str,
    requested_ids: Sequence[int],
    query_acquisitions: Sequence[SeadTableAcquisition],
    scope: Mapping[str, object],
    run_id: str,
    parent_run_id: str,
    build_id: str,
    completion_basis: str,
    extra_receipt_fields: Mapping[str, object],
    orchestrator_version: str,
    clock: Callable[[], datetime],
) -> SeadTableAcquisition:
    if any(item.receipt.get("status") != "complete" for item in query_acquisitions):
        raise ValueError(f"Cannot aggregate incomplete SEAD queries for {table}")
    materialized_rows = tuple(dict(row) for row in rows)
    payload = _table_payload_bytes(table, materialized_rows)
    schema = _observed_schema(materialized_rows)
    if query_acquisitions:
        started_at = str(query_acquisitions[0].receipt["started_at"])
        completed_at = str(query_acquisitions[-1].receipt["completed_at"])
    else:
        started_at = _utc_text(clock())
        completed_at = _utc_text(clock())
    receipt: dict[str, object] = {
        "schema_version": SCOPED_RECEIPT_SCHEMA_VERSION,
        "source": "SEAD",
        "route": "postgrest_dependency_scoped",
        "table": table,
        "primary_key": primary_key,
        "projection": projection,
        "filter_field": filter_field,
        "requested_identity_count": len(requested_ids),
        "requested_identities": list(requested_ids),
        "query_count": len(query_acquisitions),
        "query_receipts": [dict(item.receipt) for item in query_acquisitions],
        "completion_basis": completion_basis,
        "country_scope": list(NORDIC_TARGET_COUNTRIES),
        "spatial_scope": dict(scope),
        "scope_id": scope["scope_id"],
        "run_id": run_id,
        "parent_run_id": parent_run_id,
        "build_id": build_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "row_count": len(materialized_rows),
        "canonical_schema": schema,
        "canonical_schema_sha256": hashlib.sha256(_canonical_bytes(schema)).hexdigest(),
        "content_sha256": hashlib.sha256(payload).hexdigest(),
        "tool_version": orchestrator_version,
        "status": "complete",
        "failure_reason": None,
        **dict(extra_receipt_fields),
    }
    receipt["receipt_id"] = (
        "sead-scoped-receipt:" + hashlib.sha256(_canonical_bytes(receipt)).hexdigest()
    )
    return SeadTableAcquisition(table=table, rows=materialized_rows, receipt=receipt)


def _reconcile_join(
    plan: SeadJoinPlan,
    *,
    rows_by_table: Mapping[str, Sequence[Mapping[str, object]]],
    scope_id: str,
    run_id: str,
    parent_run_id: str,
    build_id: str,
) -> dict[str, object]:
    parent_rows = rows_by_table[plan.parent_table]
    all_child_rows = rows_by_table[plan.child_table]
    referenced_child_rows = tuple(
        row
        for row in all_child_rows
        if plan.reference_required or row.get(plan.child_foreign_key) is not None
    )
    reconciliation = reconcile_sead_join(
        edge=plan.edge,
        parent_rows=parent_rows,
        child_rows=referenced_child_rows,
        parent_key=plan.parent_key,
        child_key=plan.child_key,
        child_foreign_key=plan.child_foreign_key,
    )
    parent_ids = {
        str(row[plan.parent_key])
        for row in parent_rows
        if row.get(plan.parent_key) is not None
    }
    child_counts = Counter(
        str(row[plan.child_foreign_key])
        for row in referenced_child_rows
        if row.get(plan.child_foreign_key) is not None
    )
    matched_parent_ids = sorted(parent_ids & set(child_counts))
    unmatched_parent_ids = sorted(parent_ids - set(child_counts))
    null_reference_child_ids = sorted(
        _row_identity(row, index, plan.child_key)
        for index, row in enumerate(all_child_rows)
        if row.get(plan.child_foreign_key) is None
    )
    reconciliation.update(
        {
            "scope_id": scope_id,
            "run_id": run_id,
            "parent_run_id": parent_run_id,
            "build_id": build_id,
            "reference_required": plan.reference_required,
            "total_child_row_count": len(all_child_rows),
            "referenced_child_row_count": len(referenced_child_rows),
            "null_reference_child_count": len(null_reference_child_ids),
            "null_reference_child_ids": null_reference_child_ids,
            "matched_parent_count": len(matched_parent_ids),
            "matched_parent_ids": matched_parent_ids,
            "zero_child_parent_count": len(unmatched_parent_ids),
            "zero_child_parent_ids": unmatched_parent_ids,
            "one_child_parent_count": sum(
                child_counts[parent_id] == 1 for parent_id in parent_ids
            ),
            "many_child_parent_count": sum(
                child_counts[parent_id] > 1 for parent_id in parent_ids
            ),
        }
    )
    return reconciliation


def _dependency_ids(
    dependencies: Sequence[SeadDependency],
    rows_by_table: Mapping[str, Sequence[Mapping[str, object]]],
) -> tuple[int, ...]:
    values: set[int] = set()
    for dependency in dependencies:
        if dependency.table not in rows_by_table:
            raise ValueError(
                f"SEAD acquisition dependency is not available: {dependency.table}"
            )
        for row in rows_by_table[dependency.table]:
            value = row.get(dependency.field)
            if value is not None:
                values.add(_required_source_id(row, dependency.field))
    return tuple(sorted(values))


def _validated_rows(
    table: str,
    rows: Iterable[Mapping[str, object]],
    primary_key: str,
    projection: str,
) -> tuple[dict[str, object], ...]:
    projected_fields = set(projection.split(","))
    materialized: list[dict[str, object]] = []
    identities: list[int] = []
    for index, row in enumerate(rows):
        missing = sorted(projected_fields - set(row))
        if missing:
            raise ValueError(
                f"SEAD {table} row {index} is missing projected fields: {missing}"
            )
        identities.append(_required_source_id(row, primary_key))
        materialized.append(dict(row))
    duplicates = sorted(
        identity for identity, count in Counter(identities).items() if count > 1
    )
    if duplicates:
        raise ValueError(f"SEAD {table} contains duplicate source keys: {duplicates}")
    materialized.sort(key=lambda row: _required_source_id(row, primary_key))
    return tuple(materialized)


def _required_source_id(row: Mapping[str, object], field: str) -> int:
    value = row.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(
            f"SEAD source key must be a positive integer: {field}={value!r}"
        )
    return value


def _validate_site_uuids(rows: Sequence[Mapping[str, object]]) -> None:
    uuids: list[str] = []
    for row in rows:
        value = row.get("site_uuid")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"SEAD site_uuid is required for site_id={row.get('site_id')!r}"
            )
        uuids.append(value)
    duplicates = sorted(value for value, count in Counter(uuids).items() if count > 1)
    if duplicates:
        raise ValueError(f"SEAD site_uuid values are not unique: {duplicates}")


def _normalize_country_assignments(
    values: Mapping[object, str],
) -> dict[int, str]:
    normalized: dict[int, str] = {}
    for raw_site_id, raw_code in values.items():
        site_id = _mapping_site_id(raw_site_id)
        if site_id in normalized:
            raise ValueError(f"Duplicate normalized SEAD country site ID: {site_id}")
        if not isinstance(raw_code, str):
            raise ValueError(f"Invalid governed SEAD country code: {raw_code!r}")
        code = raw_code.strip().upper()
        if code not in NORDIC_COUNTRY_CODES:
            raise ValueError(f"Invalid governed SEAD country code: {raw_code!r}")
        normalized[site_id] = code
    return normalized


def _mapping_site_id(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError(f"Invalid governed SEAD site ID: {value!r}")
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, str) and value.strip().isdigit():
        parsed = int(value.strip())
        if parsed > 0:
            return parsed
    raise ValueError(f"Invalid governed SEAD site ID: {value!r}")


def _validate_declared_table_coverage(
    table_plans: Sequence[SeadScopedTablePlan],
    required_tables: Sequence[str],
    relation_scope: str,
) -> None:
    planned = ("tbl_sites", *(plan.table for plan in table_plans))
    if len(planned) != len(set(planned)) or set(planned) != set(required_tables):
        raise RuntimeError(
            f"SEAD {relation_scope} acquisition plans do not exactly cover "
            "declared source tables"
        )


def _validate_bbox(bbox: tuple[float, float, float, float]) -> None:
    if len(bbox) != 4 or any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        for value in bbox
    ):
        raise ValueError("SEAD bbox must contain four finite numeric values")
    minimum_longitude, minimum_latitude, maximum_longitude, maximum_latitude = bbox
    if not (
        -180 <= minimum_longitude < maximum_longitude <= 180
        and -90 <= minimum_latitude < maximum_latitude <= 90
    ):
        raise ValueError("SEAD bbox is outside valid longitude/latitude bounds")


def _bbox_filters(
    bbox: tuple[float, float, float, float],
) -> tuple[tuple[str, str], ...]:
    minimum_longitude, minimum_latitude, maximum_longitude, maximum_latitude = bbox
    return (
        ("latitude_dd", f"gte.{minimum_latitude}"),
        ("latitude_dd", f"lte.{maximum_latitude}"),
        ("longitude_dd", f"gte.{minimum_longitude}"),
        ("longitude_dd", f"lte.{maximum_longitude}"),
    )


def _validate_identity(value: str, field: str, *, path_segment: bool = False) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"SEAD acquisition requires a stable {field}")
    if path_segment and not _SAFE_RUN_ID.fullmatch(value):
        raise ValueError("SEAD acquisition run_id is not a safe path segment")


def _table_payload_bytes(table: str, rows: Iterable[Mapping[str, object]]) -> bytes:
    return _canonical_bytes(
        {
            "schema_version": "sead-table-payload.v1",
            "table": table,
            "rows": list(rows),
        }
    )


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _observed_schema(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    fields = sorted({field for row in rows for field in row})
    return {
        "row_count": len(rows),
        "fields": [
            {
                "name": field,
                "presence_count": sum(field in row for row in rows),
                "null_count": sum(
                    row.get(field) is None for row in rows if field in row
                ),
                "json_types": sorted(
                    {_json_type(row[field]) for row in rows if field in row}
                ),
            }
            for field in fields
        ],
    }


def _json_type(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return "object"


def _row_identity(row: Mapping[str, object], index: int, primary_key: str) -> str:
    value = row.get(primary_key)
    return f"{primary_key}:{value}" if value is not None else f"row:{index}"


def _current_utc() -> datetime:
    return datetime.now(UTC)


def _utc_text(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("SEAD acquisition timestamps must be timezone-aware")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


__all__ = [
    "FULL_EVIDENCE_ORCHESTRATOR_VERSION",
    "NORDIC_TARGET_COUNTRIES",
    "SCOPED_ORCHESTRATOR_VERSION",
    "SCOPED_RECEIPT_SCHEMA_VERSION",
    "SCOPED_RESULT_SCHEMA_VERSION",
    "SEAD_FULL_EVIDENCE_TABLE_PLANS",
    "SEAD_FULL_EVIDENCE_JOIN_PLANS",
    "SEAD_SCOPED_TABLE_PLANS",
    "SeadScopedAcquisitionResult",
    "acquire_full_evidence_sead_relations",
    "acquire_scoped_sead_relations",
]
