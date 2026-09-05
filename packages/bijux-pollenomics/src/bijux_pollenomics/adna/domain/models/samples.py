"""Species-aware normalized aDNA sample records."""

from __future__ import annotations

from dataclasses import dataclass

from .chronology import AdnaChronology, AdnaCoordinate
from .identity import AdnaLocalityIdentity, AdnaSampleIdentity


@dataclass(frozen=True)
class AdnaSampleRecord:
    """Species-aware normalized ancient-DNA sample record."""

    identity: AdnaSampleIdentity
    locality_identity: AdnaLocalityIdentity
    species_latin_name: str
    species_common_name: str
    source_family: str
    source_release: str
    record_modality: str
    review_strength: str
    provenance_quality: str
    master_id: str
    group_id: str
    locality: str | None
    political_entity: str | None
    coordinates: AdnaCoordinate
    publication: str
    year_first_published: str
    full_date: str
    chronology: AdnaChronology
    data_type: str
    molecular_sex: str
    datasets: tuple[str, ...]
    project_accession: str = ""
    paper_doi: str = ""
    paper_url: str = ""
    supplementary_source: str = ""
    inclusion_status: str = "included"
    inclusion_note: str = ""
    chronology_strength: str = ""
    chronology_normalization_status: str = ""
    chronology_provenance_path: str = ""
    chronology_provenance_kind: str = ""
    chronology_provenance_locator: str = ""
    chronology_provenance_text: str = ""
    chronology_conflict_note: str = ""
    sample_basis: str = ""
    archive_native_sample_id: str = ""
    paper_native_sample_label: str = ""
    supplementary_table_sample_label: str = ""
    sample_evidence_status: str = ""
    sample_lineage_path: str = ""
    sample_lineage_locator: str = ""
    sample_lineage_excerpt: str = ""
    sample_identity_resolution: str = ""
    sample_ambiguity_note: str = ""
    source_native_tax_id: str = ""
    source_native_scientific_name: str = ""
    taxon_alignment_status: str = "not_reported"
    archive_native_experiment_id: str = ""
    source_native_identity_kind: str = "biological_sample"

    @property
    def genetic_id(self) -> str:
        return self.identity.stable_token

    @property
    def sample_namespace(self) -> str:
        return self.identity.namespace

    @property
    def accession_lineage(self) -> tuple[str, ...]:
        return self.identity.accession_lineage

    @property
    def locality_namespace(self) -> str:
        return self.locality_identity.namespace

    @property
    def locality_token(self) -> str:
        return self.locality_identity.stable_token

    @property
    def latitude(self) -> float | None:
        return self.coordinates.latitude

    @property
    def longitude(self) -> float | None:
        return self.coordinates.longitude

    @property
    def latitude_text(self) -> str:
        return self.coordinates.latitude_text

    @property
    def longitude_text(self) -> str:
        return self.coordinates.longitude_text

    @property
    def coordinate_confidence(self) -> str:
        return self.coordinates.confidence

    @property
    def date_mean_bp(self) -> str:
        return (
            str(self.chronology.time_mean_bp)
            if self.chronology.time_mean_bp is not None
            else ""
        )

    @property
    def date_stddev_bp(self) -> str:
        return self.chronology.date_stddev_bp

    @property
    def time_start_bp(self) -> int | None:
        return self.chronology.time_start_bp

    @property
    def time_end_bp(self) -> int | None:
        return self.chronology.time_end_bp

    @property
    def time_mean_bp(self) -> int | None:
        return self.chronology.time_mean_bp

    @property
    def time_label(self) -> str:
        return self.chronology.original_text

    @property
    def dating_basis(self) -> str:
        return self.chronology.dating_basis

    def as_dict(self) -> dict[str, object]:
        return {
            "identity": self.identity.__dict__,
            "locality_identity": self.locality_identity.as_dict(),
            "species_latin_name": self.species_latin_name,
            "species_common_name": self.species_common_name,
            "source_family": self.source_family,
            "source_release": self.source_release,
            "record_modality": self.record_modality,
            "review_strength": self.review_strength,
            "provenance_quality": self.provenance_quality,
            "master_id": self.master_id,
            "group_id": self.group_id,
            "locality": self.locality,
            "political_entity": self.political_entity,
            "coordinates": self.coordinates.as_dict(),
            "publication": self.publication,
            "year_first_published": self.year_first_published,
            "full_date": self.full_date,
            "chronology": self.chronology.as_dict(),
            "data_type": self.data_type,
            "molecular_sex": self.molecular_sex,
            "datasets": list(self.datasets),
            "project_accession": self.project_accession,
            "paper_doi": self.paper_doi,
            "paper_url": self.paper_url,
            "supplementary_source": self.supplementary_source,
            "inclusion_status": self.inclusion_status,
            "inclusion_note": self.inclusion_note,
            "chronology_strength": self.chronology_strength,
            "chronology_normalization_status": self.chronology_normalization_status,
            "chronology_provenance_path": self.chronology_provenance_path,
            "chronology_provenance_kind": self.chronology_provenance_kind,
            "chronology_provenance_locator": self.chronology_provenance_locator,
            "chronology_provenance_text": self.chronology_provenance_text,
            "chronology_conflict_note": self.chronology_conflict_note,
            "sample_basis": self.sample_basis,
            "archive_native_sample_id": self.archive_native_sample_id,
            "paper_native_sample_label": self.paper_native_sample_label,
            "supplementary_table_sample_label": self.supplementary_table_sample_label,
            "sample_evidence_status": self.sample_evidence_status,
            "sample_lineage_path": self.sample_lineage_path,
            "sample_lineage_locator": self.sample_lineage_locator,
            "sample_lineage_excerpt": self.sample_lineage_excerpt,
            "sample_identity_resolution": self.sample_identity_resolution,
            "sample_ambiguity_note": self.sample_ambiguity_note,
            "source_native_tax_id": self.source_native_tax_id,
            "source_native_scientific_name": self.source_native_scientific_name,
            "taxon_alignment_status": self.taxon_alignment_status,
            "archive_native_experiment_id": self.archive_native_experiment_id,
            "source_native_identity_kind": self.source_native_identity_kind,
        }
