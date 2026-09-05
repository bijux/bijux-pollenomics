"""Admission identities, profiles, and immutable result models."""

from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
import re
from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    NORDIC_COUNTRY_CODES,
)
from bijux_pollenomics.collection.sources.sead.acquisition.archive import (
    SEAD_FULL_EVIDENCE_SOURCE_TABLES,
    SEAD_LINKED_SOURCE_TABLES,
)
from bijux_pollenomics.collection.sources.sead.acquisition.scoped import (
    FULL_EVIDENCE_ORCHESTRATOR_VERSION,
    SCOPED_ORCHESTRATOR_VERSION,
    SEAD_FULL_EVIDENCE_JOIN_PLANS,
    SEAD_FULL_EVIDENCE_TABLE_PLANS,
    SEAD_SCOPED_TABLE_PLANS,
    SeadJoinPlan,
    SeadScopedTablePlan,
)


ADMISSION_SCHEMA_VERSION = "sead-acquisition-admission.v1"
ADMISSION_SCOPE = "declared_chronology_relations"
FULL_EVIDENCE_ADMISSION_SCOPE = "full_evidence_relations"

_SAFE_RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SHA256_ID = re.compile(r"sha256:[0-9a-f]{64}\Z")
_TARGET_COUNTRY_CODES = NORDIC_COUNTRY_CODES[:-1]
_COUNTRY_SCOPE = list(_TARGET_COUNTRY_CODES)
_SITE_PRIMARY_KEY = "site_id"
_SITE_PROJECTION = (
    "site_id,site_name,national_site_identifier,latitude_dd,longitude_dd,"
    "altitude,site_description,site_uuid"
)
_AGGREGATE_ROUTE = "postgrest_dependency_scoped"
_QUERY_ROUTE = "postgrest"
_QUERY_TOOL_VERSION = "sead-postgrest-acquisition.v1"
_QUERY_MAX_PAGES = 10_000
_PREFLIGHT_MAX_PAGES = 100
_COUNTRY_NAMES = {
    "SE": "Sweden",
    "DK": "Denmark",
    "NO": "Norway",
    "FI": "Finland",
}
_COUNTRY_DECISIONS_SCHEMA_VERSION = "sead-live-country-decisions.v1"
_COUNTRY_RECONCILIATION_SCHEMA_VERSION = "sead-country-reconciliation.v1"
_JOIN_RECONCILIATIONS_SCHEMA_VERSION = "sead-join-reconciliations.v1"
_EXPECTED_JOIN_SPECS = {
    "sites.sample_groups": (
        "tbl_sites",
        "tbl_sample_groups",
        "site_id",
        "sample_group_id",
        "site_id",
        True,
    ),
    "sample_groups.physical_samples": (
        "tbl_sample_groups",
        "tbl_physical_samples",
        "sample_group_id",
        "physical_sample_id",
        "sample_group_id",
        True,
    ),
    "physical_samples.analysis_entities": (
        "tbl_physical_samples",
        "tbl_analysis_entities",
        "physical_sample_id",
        "analysis_entity_id",
        "physical_sample_id",
        True,
    ),
    "analysis_entities.analysis_entity_ages": (
        "tbl_analysis_entities",
        "tbl_analysis_entity_ages",
        "analysis_entity_id",
        "analysis_entity_age_id",
        "analysis_entity_id",
        True,
    ),
    "analysis_entities.geochronology": (
        "tbl_analysis_entities",
        "tbl_geochronology",
        "analysis_entity_id",
        "geochron_id",
        "analysis_entity_id",
        True,
    ),
    "analysis_entities.dendro_dates": (
        "tbl_analysis_entities",
        "tbl_dendro_dates",
        "analysis_entity_id",
        "dendro_date_id",
        "analysis_entity_id",
        True,
    ),
    "analysis_entities.analysis_values": (
        "tbl_analysis_entities",
        "tbl_analysis_values",
        "analysis_entity_id",
        "analysis_value_id",
        "analysis_entity_id",
        True,
    ),
    "analysis_values.analysis_dating_ranges": (
        "tbl_analysis_values",
        "tbl_analysis_dating_ranges",
        "analysis_value_id",
        "analysis_dating_range_id",
        "analysis_value_id",
        True,
    ),
    "analysis_entities.relative_dates": (
        "tbl_analysis_entities",
        "tbl_relative_dates",
        "analysis_entity_id",
        "relative_date_id",
        "analysis_entity_id",
        True,
    ),
    "relative_ages.relative_age_refs": (
        "tbl_relative_ages",
        "tbl_relative_age_refs",
        "relative_age_id",
        "relative_age_ref_id",
        "relative_age_id",
        True,
    ),
    "sites.site_references": (
        "tbl_sites",
        "tbl_site_references",
        "site_id",
        "site_reference_id",
        "site_id",
        True,
    ),
    "sample_groups.sample_group_references": (
        "tbl_sample_groups",
        "tbl_sample_group_references",
        "sample_group_id",
        "sample_group_reference_id",
        "sample_group_id",
        True,
    ),
    "age_types.analysis_dating_ranges": (
        "tbl_age_types",
        "tbl_analysis_dating_ranges",
        "age_type_id",
        "analysis_dating_range_id",
        "age_type_id",
        False,
    ),
    "age_types.dendro_dates": (
        "tbl_age_types",
        "tbl_dendro_dates",
        "age_type_id",
        "dendro_date_id",
        "age_type_id",
        False,
    ),
    "relative_ages.relative_dates": (
        "tbl_relative_ages",
        "tbl_relative_dates",
        "relative_age_id",
        "relative_date_id",
        "relative_age_id",
        False,
    ),
    "dating_uncertainty.analysis_dating_ranges": (
        "tbl_dating_uncertainty",
        "tbl_analysis_dating_ranges",
        "dating_uncertainty_id",
        "analysis_dating_range_id",
        "dating_uncertainty_id",
        False,
    ),
    "dating_uncertainty.geochronology": (
        "tbl_dating_uncertainty",
        "tbl_geochronology",
        "dating_uncertainty_id",
        "geochron_id",
        "dating_uncertainty_id",
        False,
    ),
    "dating_uncertainty.dendro_dates": (
        "tbl_dating_uncertainty",
        "tbl_dendro_dates",
        "dating_uncertainty_id",
        "dendro_date_id",
        "dating_uncertainty_id",
        False,
    ),
    "dating_uncertainty.relative_dates": (
        "tbl_dating_uncertainty",
        "tbl_relative_dates",
        "dating_uncertainty_id",
        "relative_date_id",
        "dating_uncertainty_id",
        False,
    ),
    "methods.relative_dates": (
        "tbl_methods",
        "tbl_relative_dates",
        "method_id",
        "relative_date_id",
        "method_id",
        False,
    ),
    "datasets.analysis_entities": (
        "tbl_datasets",
        "tbl_analysis_entities",
        "dataset_id",
        "analysis_entity_id",
        "dataset_id",
        False,
    ),
    "biblio.datasets": (
        "tbl_biblio",
        "tbl_datasets",
        "biblio_id",
        "dataset_id",
        "biblio_id",
        False,
    ),
    "biblio.site_references": (
        "tbl_biblio",
        "tbl_site_references",
        "biblio_id",
        "site_reference_id",
        "biblio_id",
        False,
    ),
    "biblio.sample_group_references": (
        "tbl_biblio",
        "tbl_sample_group_references",
        "biblio_id",
        "sample_group_reference_id",
        "biblio_id",
        False,
    ),
    "biblio.relative_age_refs": (
        "tbl_biblio",
        "tbl_relative_age_refs",
        "biblio_id",
        "relative_age_ref_id",
        "biblio_id",
        False,
    ),
}
_DOWNSTREAM_REFUSALS = {
    "chronology_claims": "typed_chronology_claims_not_materialized",
    "evidence_events": "observation_relations_not_captured",
    "propagation_events": "propagation_events_not_materialized",
}


@dataclass(frozen=True)
class _AdmissionProfile:
    scope_key: str
    relation_scope: str
    tables: tuple[str, ...]
    table_plans: tuple[SeadScopedTablePlan, ...]
    join_plans: tuple[SeadJoinPlan, ...]
    orchestrator_version: str
    wp01_complete: bool


_SCOPED_PROFILE = _AdmissionProfile(
    scope_key=ADMISSION_SCOPE,
    relation_scope="chronology_relations",
    tables=SEAD_LINKED_SOURCE_TABLES,
    table_plans=SEAD_SCOPED_TABLE_PLANS,
    join_plans=tuple(
        SeadJoinPlan(edge, *spec) for edge, spec in _EXPECTED_JOIN_SPECS.items()
    ),
    orchestrator_version=SCOPED_ORCHESTRATOR_VERSION,
    wp01_complete=False,
)
_FULL_EVIDENCE_PROFILE = _AdmissionProfile(
    scope_key=FULL_EVIDENCE_ADMISSION_SCOPE,
    relation_scope="full_evidence_relations",
    tables=SEAD_FULL_EVIDENCE_SOURCE_TABLES,
    table_plans=SEAD_FULL_EVIDENCE_TABLE_PLANS,
    join_plans=SEAD_FULL_EVIDENCE_JOIN_PLANS,
    orchestrator_version=FULL_EVIDENCE_ORCHESTRATOR_VERSION,
    wp01_complete=False,
)


@dataclass(frozen=True)
class SeadAcquisitionAdmission:
    """One validated immutable acquisition admission."""

    run_id: str
    output_root: Path
    admission_path: Path
    admission: dict[str, object]


@dataclass(frozen=True)
class SeadAdmissionExpectedIdentity:
    """Caller-pinned identities required before an acquisition can be admitted."""

    scope_id: str
    run_id: str
    parent_run_id: str
    build_id: str
    country_authority_id: str
    country_authority_artifact_digest: str
    country_authority_root: Path
    bbox_payload_sha256: str
    acquisition_manifest_sha256: str
    country_decisions_sha256: str
    parent_admission_sha256: str | None = None


@dataclass(frozen=True)
class SeadMaterializedAdmissionSnapshot:
    """Admission metadata and the exact bytes verified in one validation pass."""

    admission: Mapping[str, object]
    copied_files: Mapping[str, bytes]


@dataclass(frozen=True)
class _ValidatedAdmission:
    source_root: Path
    decisions_path: Path
    admission: dict[str, object]
    copied_files: dict[str, bytes]


@dataclass(frozen=True)
class _BoundaryAuthority:
    boundaries: dict[str, dict[str, object]]
    artifact_digest: str
    version: str
    source_version: str
    authority_id: str
    manifest_sha256: str
    source_asset_sha256: str
    country_artifact_sha256: dict[str, str]
