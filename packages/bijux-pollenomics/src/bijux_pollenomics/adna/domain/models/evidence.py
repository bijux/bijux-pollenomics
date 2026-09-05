"""Source evidence and coordinate provenance records for aDNA sites."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdnaSiteEvidenceRecord:
    """Curated site-evidence row that links one project lead to one cited source."""

    project_accession: str
    species_latin_name: str
    species_common_name: str
    site_label: str
    political_entity: str | None
    source_artifact_path: str
    source_artifact_kind: str
    source_locator: str
    exact_source_text: str
    source_support_status: str
    paper_doi: str = ""
    paper_url: str = ""
    supplementary_source: str = ""
    coordinate_basis: str = ""
    latitude_text: str = ""
    longitude_text: str = ""
    chronology_text: str = ""
    time_start_bp: int | None = None
    time_end_bp: int | None = None
    dating_basis: str = "unknown"
    comparator_context: bool = False
    domestication_context: str = ""
    interpretation_note: str = ""
    support_gap_note: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "project_accession": self.project_accession,
            "species_latin_name": self.species_latin_name,
            "species_common_name": self.species_common_name,
            "site_label": self.site_label,
            "political_entity": self.political_entity,
            "source_artifact_path": self.source_artifact_path,
            "source_artifact_kind": self.source_artifact_kind,
            "source_locator": self.source_locator,
            "exact_source_text": self.exact_source_text,
            "source_support_status": self.source_support_status,
            "paper_doi": self.paper_doi,
            "paper_url": self.paper_url,
            "supplementary_source": self.supplementary_source,
            "coordinate_basis": self.coordinate_basis,
            "latitude_text": self.latitude_text,
            "longitude_text": self.longitude_text,
            "chronology_text": self.chronology_text,
            "time_start_bp": self.time_start_bp,
            "time_end_bp": self.time_end_bp,
            "dating_basis": self.dating_basis,
            "comparator_context": self.comparator_context,
            "domestication_context": self.domestication_context,
            "interpretation_note": self.interpretation_note,
            "support_gap_note": self.support_gap_note,
        }


@dataclass(frozen=True)
class AdnaCoordinateProvenanceRecord:
    """Curated coordinate provenance row for one shipped animal aDNA site lead."""

    project_accession: str
    species_latin_name: str
    species_common_name: str
    site_label: str
    original_place_text: str
    resolved_place_text: str
    political_entity: str | None
    source_artifact_path: str
    source_locator: str
    coordinate_basis: str
    mapping_posture: str
    latitude_text: str = ""
    longitude_text: str = ""
    geocoding_method: str = ""
    geocoder_or_gazetteer: str = ""
    confidence_rationale: str = ""
    coordinate_confidence: str = "unknown"
    paper_doi: str = ""
    paper_url: str = ""
    supplementary_source: str = ""
    chronology_text: str = ""
    time_start_bp: int | None = None
    time_end_bp: int | None = None
    dating_basis: str = "unknown"
    comparator_context: bool = False
    domestication_context: str = ""
    interpretation_note: str = ""
    support_gap_note: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "project_accession": self.project_accession,
            "species_latin_name": self.species_latin_name,
            "species_common_name": self.species_common_name,
            "site_label": self.site_label,
            "original_place_text": self.original_place_text,
            "resolved_place_text": self.resolved_place_text,
            "political_entity": self.political_entity,
            "source_artifact_path": self.source_artifact_path,
            "source_locator": self.source_locator,
            "coordinate_basis": self.coordinate_basis,
            "mapping_posture": self.mapping_posture,
            "latitude_text": self.latitude_text,
            "longitude_text": self.longitude_text,
            "geocoding_method": self.geocoding_method,
            "geocoder_or_gazetteer": self.geocoder_or_gazetteer,
            "confidence_rationale": self.confidence_rationale,
            "coordinate_confidence": self.coordinate_confidence,
            "paper_doi": self.paper_doi,
            "paper_url": self.paper_url,
            "supplementary_source": self.supplementary_source,
            "chronology_text": self.chronology_text,
            "time_start_bp": self.time_start_bp,
            "time_end_bp": self.time_end_bp,
            "dating_basis": self.dating_basis,
            "comparator_context": self.comparator_context,
            "domestication_context": self.domestication_context,
            "interpretation_note": self.interpretation_note,
            "support_gap_note": self.support_gap_note,
        }
