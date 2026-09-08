"""Published animal-atlas evidence and coordinate-review records."""

from __future__ import annotations

from dataclasses import dataclass

from ...domain.models.chronology import AdnaChronology


@dataclass(frozen=True)
class AnimalAtlasEvidenceRow:
    """One traceable animal atlas evidence row eligible for point publication."""

    feature_id: str
    evidence_row_id: str
    site_record_id: str
    species_latin_name: str
    species_common_name: str
    animal_scope: str
    support_class: str
    support_note: str
    locality: str
    political_entity: str
    latitude: float
    longitude: float
    latitude_text: str
    longitude_text: str
    coordinate_basis: str
    coordinate_confidence: str
    geocoding_method: str
    geocoder_or_gazetteer: str
    confidence_rationale: str
    original_place_text: str
    resolved_place_text: str
    coordinate_source_artifact_path: str
    coordinate_source_locator: str
    coordinate_supplementary_source: str
    coordinate_support_gap_note: str
    chronology: AdnaChronology
    project_accessions: tuple[str, ...]
    primary_project_accession: str
    sample_record_ids: tuple[str, ...]
    sample_group_ids: tuple[str, ...]
    source_native_taxon_labels: tuple[str, ...]
    source_native_tax_ids: tuple[str, ...]
    source_native_scientific_names: tuple[str, ...]
    taxon_alignment_statuses: tuple[str, ...]
    sample_count: int
    sample_namespace: str
    inclusion_statuses: tuple[str, ...]
    inclusion_notes: tuple[str, ...]
    paper_title: str
    paper_doi: str
    publication_year: str
    journal_title: str
    paper_url: str
    supplementary_sources: tuple[str, ...]
    source_artifact_path: str
    source_artifact_kind: str
    source_locator: str
    source_support_status: str
    exact_source_text: str
    nordic_inclusion: bool
    nordic_inclusion_reason: str
    interpretation_note: str

    def as_dict(self) -> dict[str, object]:
        return {
            "feature_id": self.feature_id,
            "evidence_row_id": self.evidence_row_id,
            "site_record_id": self.site_record_id,
            "species_latin_name": self.species_latin_name,
            "species_common_name": self.species_common_name,
            "animal_scope": self.animal_scope,
            "support_class": self.support_class,
            "support_note": self.support_note,
            "locality": self.locality,
            "political_entity": self.political_entity,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "latitude_text": self.latitude_text,
            "longitude_text": self.longitude_text,
            "coordinate_basis": self.coordinate_basis,
            "coordinate_confidence": self.coordinate_confidence,
            "geocoding_method": self.geocoding_method,
            "geocoder_or_gazetteer": self.geocoder_or_gazetteer,
            "confidence_rationale": self.confidence_rationale,
            "original_place_text": self.original_place_text,
            "resolved_place_text": self.resolved_place_text,
            "coordinate_source_artifact_path": self.coordinate_source_artifact_path,
            "coordinate_source_locator": self.coordinate_source_locator,
            "coordinate_supplementary_source": self.coordinate_supplementary_source,
            "coordinate_support_gap_note": self.coordinate_support_gap_note,
            "chronology": self.chronology.as_dict(),
            "project_accessions": list(self.project_accessions),
            "primary_project_accession": self.primary_project_accession,
            "sample_record_ids": list(self.sample_record_ids),
            "sample_group_ids": list(self.sample_group_ids),
            "source_native_taxon_labels": list(self.source_native_taxon_labels),
            "source_native_tax_ids": list(self.source_native_tax_ids),
            "source_native_scientific_names": list(self.source_native_scientific_names),
            "taxon_alignment_statuses": list(self.taxon_alignment_statuses),
            "sample_count": self.sample_count,
            "sample_namespace": self.sample_namespace,
            "inclusion_statuses": list(self.inclusion_statuses),
            "inclusion_notes": list(self.inclusion_notes),
            "paper_title": self.paper_title,
            "paper_doi": self.paper_doi,
            "publication_year": self.publication_year,
            "journal_title": self.journal_title,
            "paper_url": self.paper_url,
            "supplementary_sources": list(self.supplementary_sources),
            "source_artifact_path": self.source_artifact_path,
            "source_artifact_kind": self.source_artifact_kind,
            "source_locator": self.source_locator,
            "source_support_status": self.source_support_status,
            "exact_source_text": self.exact_source_text,
            "nordic_inclusion": self.nordic_inclusion,
            "nordic_inclusion_reason": self.nordic_inclusion_reason,
            "interpretation_note": self.interpretation_note,
        }


@dataclass(frozen=True)
class AnimalAtlasCoordinateReview:
    """Visible coordinate-basis counts for one animal atlas bundle."""

    direct_coordinate_feature_count: int
    named_site_geocoded_feature_count: int
    weaker_geography_feature_count: int

    def as_dict(self) -> dict[str, object]:
        return {
            "direct_coordinate_feature_count": self.direct_coordinate_feature_count,
            "named_site_geocoded_feature_count": self.named_site_geocoded_feature_count,
            "weaker_geography_feature_count": self.weaker_geography_feature_count,
        }


# Preserve the established public pickle path.
AnimalAtlasEvidenceRow.__module__ = (
    "bijux_pollenomics.reporting.adna.atlas_evidence_rows.models"
)
AnimalAtlasCoordinateReview.__module__ = (
    "bijux_pollenomics.reporting.adna.atlas_evidence_rows.models"
)
