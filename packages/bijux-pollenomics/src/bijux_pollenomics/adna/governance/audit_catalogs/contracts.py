"""Typed payload contracts for animal evidence audits."""

from __future__ import annotations

from typing import TypedDict


class BibliographyRow(TypedDict):
    paper_title: str
    paper_doi: str | None
    journal_title: str | None
    publication_year: int | None
    reference_kind: str
    species_latin_names: list[str]
    project_accessions: list[str]
    species_count: int
    project_count: int


class ArchiveInventoryRow(TypedDict):
    source_family: str
    project_accession: str
    metadata_url: str
    result_kind: str
    archive_status: str
    evidence_strength: object
    access_policy: str
    species_latin_names: list[str]
    species_count: int


class CoverageRow(TypedDict):
    species_latin_name: str
    species_common_name: str
    raw_inventory_present: bool
    raw_source_snapshot_present: bool
    citation_manifest_present: bool
    normalized_project_summary_present: bool
    coordinate_provenance_present: bool
    normalized_locality_artifact_present: bool
    review_markdown_present: bool
    review_json_present: bool
    country_output_count: int
    atlas_locality_count: int
    mappable_coordinate_count: int
    region_refused_coordinate_count: int
    unresolved_sample_count: int
    nordic_unmapped_lead_count: int


class CoverageDashboard(TypedDict):
    schema_version: str
    rows: list[CoverageRow]


class ShippedProductAudit(TypedDict):
    schema_version: str
    tracked_species_count: int
    species_with_source_snapshots: int
    species_with_coordinate_provenance: int
    species_with_locality_artifacts: int
    species_with_country_outputs: int
    species_with_atlas_localities: int
    rows: list[CoverageRow]
    missing_public_outputs: list[str]


class MapReadinessPostureRow(TypedDict):
    species_latin_name: str
    species_common_name: str
    direct_coordinate_backed: int
    indirectly_geocoded: int
    unresolved_sample_count: int
    refused_coordinate_provenance_count: int
    region_only_coordinate_refusal_count: int
    unresolved_location_coordinate_refusal_count: int


class MapReadinessRow(MapReadinessPostureRow):
    coordinate_provenance_mappable_count: int
    publication_candidate_count: int
    not_materialized_count: int


class MapReadinessTotals(TypedDict):
    direct_coordinate_backed: int
    indirectly_geocoded: int
    unresolved_sample_count: int
    refused_coordinate_provenance_count: int
    region_only_coordinate_refusal_count: int
    unresolved_location_coordinate_refusal_count: int
    coordinate_provenance_mappable_count: int
    coordinate_provenance_row_count: int
    publication_candidate_count: int
    not_materialized_count: int


class PublicationAccounting(TypedDict):
    overall_ok: bool
    coordinate_posture_definition: str
    publication_candidate_definition: str
    not_materialized_reason_definition: str
    unresolved_sample_definition: str
    coordinate_refusal_definition: str


class MapReadinessAudit(TypedDict):
    schema_version: str
    rows: list[MapReadinessRow]
    totals: MapReadinessTotals
    not_materialized_rows: list[dict[str, object]]
    publication_accounting: PublicationAccounting


class CoordinateCaveatRow(TypedDict):
    species_latin_name: object
    species_common_name: object
    project_accession: object
    site_label: object
    original_place_text: object
    resolved_place_text: object
    coordinate_basis: object
    coordinate_confidence: object
    mapping_posture: object
    confidence_rationale: object


class CoordinateCaveatSurface(TypedDict):
    schema_version: str
    direct_coordinates: list[CoordinateCaveatRow]
    place_name_resolution: list[CoordinateCaveatRow]
    still_weak_geography: list[CoordinateCaveatRow]


class HonestyRow(TypedDict):
    species_latin_name: str
    species_common_name: str
    tracked_sample_count: int
    mapped_sample_count: int
    blocked_sample_count: int
    unresolved_sample_count: int
    country_published_sample_count: int


class HonestyTotals(TypedDict):
    tracked_sample_count: int
    mapped_sample_count: int
    blocked_sample_count: int
    unresolved_sample_count: int
    country_published_sample_count: int


class AnimalOutputHonesty(TypedDict):
    schema_version: str
    totals: HonestyTotals
    rows: list[HonestyRow]


class PublicAnimalOutputAudit(TypedDict):
    schema_version: str
    report_root: str
    countries: list[str]
    atlas_bundle_present: bool
    country_bundle_count: int
    point_candidate_count: int
    candidate_rows_with_full_traceability: int
    tracked_sample_count: int
    mapped_sample_count: int
    blocked_sample_count: int
    unresolved_sample_count: int
    country_published_sample_count: int
    atlas_notes: str
    species_rows: list[CoverageRow]


class AtlasAccountabilityRow(TypedDict):
    evidence_row_id: str
    species_latin_name: str
    project_accession: str
    site_record_id: str
    sample_record_ids: list[str]
    sample_rows_present: bool
    sample_lineage_present: bool
    site_evidence_present: bool
    chronology_evidence_present: bool
    coordinate_provenance_present: bool
    sample_locality_matches_site_record: bool
    sample_lineage_paths: list[str]
    site_evidence_path: str
    site_evidence_locator: str
    chronology_provenance_paths: list[str]
    coordinate_provenance_path: str
    coordinate_provenance_locator: str
    fully_accountable: bool


class AtlasAccountability(TypedDict):
    schema_version: str
    candidate_row_count: int
    passed_row_count: int
    overall_ok: bool
    rows: list[AtlasAccountabilityRow]
