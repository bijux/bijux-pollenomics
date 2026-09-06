"""Stable identities and table ownership for SEAD admission fixtures."""

from __future__ import annotations

_RUN_ID = "sead-live-fixture"

_SCOPE_ID = "sha256:" + "1" * 64

_PARENT_RUN_ID = "JOB-SEAD-FIXTURE"

_BUILD_ID = "sha256:" + "2" * 64

_SITE_PROJECTION = (
    "site_id,site_name,national_site_identifier,latitude_dd,longitude_dd,"
    "altitude,site_description,site_uuid"
)

_TABLE_PRIMARY_KEYS = {
    "tbl_sites": "site_id",
    "tbl_sample_groups": "sample_group_id",
    "tbl_physical_samples": "physical_sample_id",
    "tbl_analysis_entities": "analysis_entity_id",
    "tbl_analysis_entity_ages": "analysis_entity_age_id",
    "tbl_geochronology": "geochron_id",
    "tbl_dendro_dates": "dendro_date_id",
    "tbl_analysis_values": "analysis_value_id",
    "tbl_analysis_dating_ranges": "analysis_dating_range_id",
    "tbl_age_types": "age_type_id",
    "tbl_relative_dates": "relative_date_id",
    "tbl_relative_ages": "relative_age_id",
    "tbl_relative_age_refs": "relative_age_ref_id",
    "tbl_dating_uncertainty": "dating_uncertainty_id",
    "tbl_methods": "method_id",
    "tbl_datasets": "dataset_id",
    "tbl_site_references": "site_reference_id",
    "tbl_sample_group_references": "sample_group_reference_id",
    "tbl_biblio": "biblio_id",
}

_JOIN_TABLES = {
    "sites.sample_groups": ("tbl_sites", "tbl_sample_groups"),
    "sample_groups.physical_samples": (
        "tbl_sample_groups",
        "tbl_physical_samples",
    ),
    "physical_samples.analysis_entities": (
        "tbl_physical_samples",
        "tbl_analysis_entities",
    ),
    "analysis_entities.analysis_entity_ages": (
        "tbl_analysis_entities",
        "tbl_analysis_entity_ages",
    ),
    "analysis_entities.geochronology": (
        "tbl_analysis_entities",
        "tbl_geochronology",
    ),
    "analysis_entities.dendro_dates": (
        "tbl_analysis_entities",
        "tbl_dendro_dates",
    ),
    "analysis_entities.analysis_values": (
        "tbl_analysis_entities",
        "tbl_analysis_values",
    ),
    "analysis_values.analysis_dating_ranges": (
        "tbl_analysis_values",
        "tbl_analysis_dating_ranges",
    ),
    "analysis_entities.relative_dates": (
        "tbl_analysis_entities",
        "tbl_relative_dates",
    ),
    "relative_ages.relative_age_refs": (
        "tbl_relative_ages",
        "tbl_relative_age_refs",
    ),
    "sites.site_references": ("tbl_sites", "tbl_site_references"),
    "sample_groups.sample_group_references": (
        "tbl_sample_groups",
        "tbl_sample_group_references",
    ),
    "age_types.analysis_dating_ranges": (
        "tbl_age_types",
        "tbl_analysis_dating_ranges",
    ),
    "age_types.dendro_dates": ("tbl_age_types", "tbl_dendro_dates"),
    "relative_ages.relative_dates": ("tbl_relative_ages", "tbl_relative_dates"),
    "dating_uncertainty.analysis_dating_ranges": (
        "tbl_dating_uncertainty",
        "tbl_analysis_dating_ranges",
    ),
    "dating_uncertainty.geochronology": (
        "tbl_dating_uncertainty",
        "tbl_geochronology",
    ),
    "dating_uncertainty.dendro_dates": (
        "tbl_dating_uncertainty",
        "tbl_dendro_dates",
    ),
    "dating_uncertainty.relative_dates": (
        "tbl_dating_uncertainty",
        "tbl_relative_dates",
    ),
    "methods.relative_dates": ("tbl_methods", "tbl_relative_dates"),
    "datasets.analysis_entities": ("tbl_datasets", "tbl_analysis_entities"),
    "biblio.datasets": ("tbl_biblio", "tbl_datasets"),
    "biblio.site_references": ("tbl_biblio", "tbl_site_references"),
    "biblio.sample_group_references": (
        "tbl_biblio",
        "tbl_sample_group_references",
    ),
    "biblio.relative_age_refs": ("tbl_biblio", "tbl_relative_age_refs"),
}
