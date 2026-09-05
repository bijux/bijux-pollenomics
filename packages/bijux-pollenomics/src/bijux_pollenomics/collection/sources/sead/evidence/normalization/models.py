"""Typed records shared by SEAD chronology normalization."""

from __future__ import annotations

from typing import TypedDict


class _TemporalRowGroup(TypedDict):
    """One group of equivalent source chronology rows."""

    kind: str
    interval: tuple[int, int]
    label: str
    uncertainty_notes: tuple[str, ...]
    source_record_ids: tuple[int, ...]


class SeadRelationStep(TypedDict):
    """One source-table link in a chronology claim's lineage."""

    table: str
    key: str
    value: str | int | None


class SeadChronologyClaim(TypedDict):
    """A source-owned SEAD chronology claim with explicit eligibility."""

    chronology_claim_id: str
    source_family: str
    source_table: str
    source_record_id: str
    source_native_record_id: str | None
    site_uuid: str | None
    source_site_id: str | None
    country_code: str | None
    latitude_dd: float | None
    longitude_dd: float | None
    country_assignment_method: str | None
    subject_type: str
    subject_id: str
    sample_group_id: int | None
    physical_sample_id: int | None
    analysis_entity_id: int | None
    analysis_value_id: int | None
    dataset_id: int | None
    claim_type: str
    source_age_type: str
    source_age_value: dict[str, object]
    source_age_unit: str
    calibration_status: str
    younger_bp: int | None
    older_bp: int | None
    comparability_status: str
    chronology_eligibility: str
    propagation_eligibility: str
    propagation_reason_codes: list[str]
    publication_role: str
    reason_codes: list[str]
    transformation_id: str | None
    original_interval_orientation: str
    selection_status: str
    selection_rule_version: str
    provenance_record_id: str
    build_id: str
    source_relation_path: list[SeadRelationStep]


class _SeadAgePolicy(TypedDict):
    """Governed interpretation of one source-native age value."""

    source_age_type: str
    source_age_unit: str
    calibration_status: str
    comparability_status: str
    younger_bp: int | None
    older_bp: int | None
    reason_codes: tuple[str, ...]
    transformation_id: str | None


TemporalRowGroup = _TemporalRowGroup
SeadAgePolicy = _SeadAgePolicy
