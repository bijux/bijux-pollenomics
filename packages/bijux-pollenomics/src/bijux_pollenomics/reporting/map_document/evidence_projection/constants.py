"""Stable schema identifiers and SEAD compact-record field contracts."""

from __future__ import annotations

from typing import Final

PROJECTION_SCHEMA_VERSION: Final = "atlas-evidence-projection.v2"


_NEOTOMA_LAYER_KEY: Final = "neotoma-pollen"


_SEAD_LAYER_KEYS: Final = frozenset(
    {
        "sead-sites",
        "sead-temporal-evidence",
        "sweden-archaeology-site-discovery",
    }
)


_UNAVAILABLE_RELATION = {
    "status": "unavailable",
    "reason_code": "governed_relation_model_not_available",
}


_UNAVAILABLE_CLASSIFICATION = {
    "status": "unavailable",
    "reason_code": "accepted_scientific_classification_not_available",
}


_SEAD_CLAIM_FIELDS: Final = (
    "chronology_claim_id",
    "source_table",
    "source_record_id",
    "source_native_record_id",
    "subject_type",
    "subject_id",
    "sample_group_id",
    "physical_sample_id",
    "analysis_entity_id",
    "analysis_value_id",
    "dataset_id",
    "claim_type",
    "source_age_type",
    "source_age_value",
    "source_age_unit",
    "original_interval_orientation",
    "younger_bp",
    "older_bp",
    "calibration_status",
    "comparability_status",
    "chronology_eligibility",
    "propagation_eligibility",
    "propagation_reason_codes",
    "publication_role",
    "reason_codes",
    "transformation_id",
    "selection_status",
    "selection_rule_version",
    "observation_link_status",
    "observation_relation_id",
    "linked_source_native_observation_count",
    "source_relation_path",
    "source_payload_sha256",
)


_SEAD_CLAIM_COMMON_FIELDS: Final = (
    "source_family",
    "source_site_id",
    "site_uuid",
    "country_code",
    "latitude_dd",
    "longitude_dd",
    "country_assignment_method",
    "provenance_record_id",
    "build_id",
    "schema_version",
    "acquisition_manifest_sha256",
)


_SEAD_DICTIONARY_FIELDS: Final = frozenset(
    {
        "source_table",
        "subject_type",
        "claim_type",
        "source_age_type",
        "source_age_unit",
        "original_interval_orientation",
        "calibration_status",
        "comparability_status",
        "chronology_eligibility",
        "propagation_eligibility",
        "publication_role",
        "transformation_id",
        "selection_status",
        "selection_rule_version",
        "observation_link_status",
    }
)


_SEAD_LIST_DICTIONARY_FIELDS: Final = frozenset(
    {"propagation_reason_codes", "reason_codes"}
)


_SEAD_EVIDENCE_DOCUMENTS: Final = (
    "chronology_claims.json",
    "source_native_observations.json",
    "observation_relation_index.json",
    "evidence_events.json",
)


_SEAD_OBSERVATION_FIELDS: Final = (
    "observation_id",
    "source_table",
    "source_record_id",
    "entity_relation_id",
    "analysis_entity_id",
    "physical_sample_id",
    "sample_group_id",
    "dataset_id",
    "source_value",
    "source_value_field",
    "source_value_state",
    "source_unit_id",
    "unit_status",
    "value_semantics_id",
    "dataset_semantics_id",
    "dataset_semantics_status",
    "taxon_relation_id",
    "taxon_status",
    "dimension_relation_ids",
    "dimension_status",
    "chronology_link_status",
    "chronology_claim_count",
    "chronology_eligible_claim_count",
    "event_eligibility",
    "event_refusal_reason_codes",
    "source_payload_sha256",
)


_SEAD_OBSERVATION_DICTIONARY_FIELDS: Final = frozenset(
    {
        "source_table",
        "source_value_field",
        "source_value_state",
        "unit_status",
        "dataset_semantics_status",
        "taxon_status",
        "dimension_status",
        "chronology_link_status",
        "event_eligibility",
    }
)


_SEAD_OBSERVATION_LIST_DICTIONARY_FIELDS: Final = frozenset(
    {"event_refusal_reason_codes"}
)


_SEAD_ENTITY_FIELDS: Final = (
    "entity_relation_id",
    "analysis_entity_id",
    "physical_sample_id",
    "sample_group_id",
    "dataset_id",
    "chronology_claim_ids",
    "eligible_chronology_claim_ids",
)


_SEAD_TAXON_FIELDS: Final = (
    "taxon_relation_id",
    "taxon_id",
    "species",
    "genus_name",
    "family_name",
    "order_name",
    "author_name",
    "source_ecocodes",
    "derived_classification_status",
)


_SEAD_DIMENSION_FIELDS: Final = (
    "dimension_relation_id",
    "owner_kind",
    "owner_id",
    "source_table",
    "source_record_id",
    "dimension_semantics_id",
    "dimension_value",
    "qualifier_id",
    "unit_status",
)


_SEAD_DIMENSION_SEMANTIC_FIELDS: Final = (
    "dimension_semantics_id",
    "dimension_id",
    "dimension_name",
    "dimension_abbrev",
    "dimension_description",
    "source_unit_id",
    "unit_name",
    "unit_abbrev",
    "unit_description",
    "unit_status",
)


_SEAD_DATASET_SEMANTIC_FIELDS: Final = (
    "dataset_semantics_id",
    "dataset_id",
    "dataset_uuid",
    "dataset_name",
    "data_type_id",
    "data_type_name",
    "data_type_group_name",
)


_SEAD_VALUE_SEMANTIC_FIELDS: Final = (
    "value_semantics_id",
    "value_class_id",
    "value_class_name",
    "value_class_description",
    "value_type_id",
    "value_type_name",
    "base_type",
    "source_unit_id",
    "unit_name",
    "unit_abbrev",
    "unit_description",
)


_SEAD_SOURCE_AGE_INHERITED_FIELDS: Final = {
    "analysis_entity_id": "analysis_entity_id",
    "physical_sample_id": "physical_sample_id",
    "sample_group_id": "sample_group_id",
    "dataset_id": "dataset_id",
    "analysis_value_id": "analysis_value_id",
}


_SEAD_RELATION_VALUE_FIELDS: Final = {
    "site_id": "common_fields.source_site_id",
    "sample_group_id": "sample_group_id",
    "physical_sample_id": "physical_sample_id",
    "analysis_entity_id": "analysis_entity_id",
    "dataset_id": "dataset_id",
    "analysis_value_id": "analysis_value_id",
    "analysis_dating_range_id": "source_record_id",
    "dendro_date_id": "source_record_id",
    "relative_date_id": "source_record_id",
    "geochron_id": "source_record_id",
    "analysis_entity_age_id": "source_record_id",
}
