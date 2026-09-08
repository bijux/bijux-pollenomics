"""Typed source-evidence records for pig-panel reconciliation."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PigPanelJoinAuditRow:
    """One exact supplement-to-archive identity join with raw source semantics."""

    sample_label: str
    archive_native_sample_id: str
    source_sample_kind: str
    previous_extraction_code: str
    mtdna_accession_text: str
    source_text: str
    locality_text: str
    political_entity: str
    museum_or_sample_code: str
    additional_sample_information: str
    radiocarbon_lab_number: str
    uncalibrated_date_text: str
    uncalibrated_error_text: str
    calibrated_from_bp_text: str
    calibrated_to_bp_text: str
    source_age_text: str
    source_mean_age_text: str
    source_mean_age_is_numeric: bool
    period_text: str
    source_group_text: str
    zooarchaeology_status: str
    combined_genetic_zooarchaeology_status: str
    secondary_zooarchaeology_status: str
    publication_status_text: str
    modern_population: str
    modern_breed_or_country: str
    modern_coverage_text: str
    modern_doi_text: str
    chronology_text: str
    chronology_disposition: str
    chronology_disposition_reason: str
    domestication_status: str
    disposition: str
    disposition_reason: str
    workbook_source_path: str
    workbook_source_locator: str
    archive_source_path: str
    archive_source_locators: tuple[str, ...]
    latitude_text: str = ""
    longitude_text: str = ""
    map_admission: str = "refused_missing_source_coordinates"
    coordinate_basis: str = ""
    coordinate_confidence: str = ""
    coordinate_source_url: str = ""
    coordinate_source_locator: str = ""
    coordinate_spatial_scope: str = ""

    def as_dict(self) -> dict[str, object]:
        """Return a serialization-ready audit record."""
        return asdict(self)
