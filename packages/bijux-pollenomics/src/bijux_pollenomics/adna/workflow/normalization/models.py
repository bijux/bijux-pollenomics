"""Normalization result and summary models."""

from __future__ import annotations

from dataclasses import dataclass

from bijux_pollenomics.adna.domain.models import (
    AdnaCoordinate,
    AdnaCoordinateProvenanceRecord,
    AdnaLocalitySummary,
    AdnaSampleRecord,
    AdnaSiteEvidenceRecord,
)
from bijux_pollenomics.adna.workflow.manifests import (
    AdnaSpeciesManifest,
)

from ...species.definitions import AdnaSpeciesDefinition

ADNA_DOMESTICATION_STATUSES = (
    "domesticated_core",
    "comparator_only",
    "thin_evidence",
    "unsupported",
)


ADNA_PROJECT_SUPPORT_CLASSES = (
    "domesticated_core_curated",
    "archive_pending_paper_linkage",
    "wild_or_progenitor_context",
    "comparator_only",
    "rejected_or_out_of_scope",
)


@dataclass(frozen=True)
class AdnaCoordinateResolution:
    """Coordinate normalization result that can keep locations honestly withheld."""

    coordinate: AdnaCoordinate | None
    confidence: str
    source_basis: str
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "coordinate": None if self.coordinate is None else self.coordinate.__dict__,
            "confidence": self.confidence,
            "source_basis": self.source_basis,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class AdnaNormalizationLineage:
    """Trace one normalized output back to one governed raw-source expectation."""

    schema_version: str
    output_record_kind: str
    output_record_token: str
    source_artifact_path: str
    source_accessions: tuple[str, ...]
    lineage_tokens: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "output_record_kind": self.output_record_kind,
            "output_record_token": self.output_record_token,
            "source_artifact_path": self.source_artifact_path,
            "source_accessions": list(self.source_accessions),
            "lineage_tokens": list(self.lineage_tokens),
        }


@dataclass(frozen=True)
class AdnaNormalizationRefusal:
    """Explicit refusal row for non-human normalization that would overclaim support."""

    schema_version: str
    species_latin_name: str
    source_token: str
    record_kind: str
    reason: str
    detail: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "species_latin_name": self.species_latin_name,
            "source_token": self.source_token,
            "record_kind": self.record_kind,
            "reason": self.reason,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class AdnaProjectSummary:
    """Normalized project-level summary for non-human ancient-DNA support."""

    schema_version: str
    summary_token: str
    species_latin_name: str
    species_common_name: str
    project_accession: str
    study_token: str
    source_family: str
    source_release: str
    result_kind: str
    archive_status: str
    evidence_strength: str
    review_strength: str
    support_class: str
    record_modality: str
    domestication_status: str
    domestication_scope: str
    comparator_status: bool
    normalized_breed_label: str | None
    sequencing_target: str | None
    material_basis: str | None
    chronology_basis: str | None
    dating_basis: str | None
    geographic_basis: str | None
    coordinate_policy: str
    chronology_policy: str
    paper_title: str | None
    paper_doi: str | None
    paper_url: str | None
    nordic_relevance: str
    nordic_relevance_reason: str
    interpretation_caveat: str
    notes: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "summary_token": self.summary_token,
            "species_latin_name": self.species_latin_name,
            "species_common_name": self.species_common_name,
            "project_accession": self.project_accession,
            "study_token": self.study_token,
            "source_family": self.source_family,
            "source_release": self.source_release,
            "result_kind": self.result_kind,
            "archive_status": self.archive_status,
            "evidence_strength": self.evidence_strength,
            "review_strength": self.review_strength,
            "support_class": self.support_class,
            "record_modality": self.record_modality,
            "domestication_status": self.domestication_status,
            "domestication_scope": self.domestication_scope,
            "comparator_status": self.comparator_status,
            "normalized_breed_label": self.normalized_breed_label,
            "sequencing_target": self.sequencing_target,
            "material_basis": self.material_basis,
            "chronology_basis": self.chronology_basis,
            "dating_basis": self.dating_basis,
            "geographic_basis": self.geographic_basis,
            "coordinate_policy": self.coordinate_policy,
            "chronology_policy": self.chronology_policy,
            "paper_title": self.paper_title,
            "paper_doi": self.paper_doi,
            "paper_url": self.paper_url,
            "nordic_relevance": self.nordic_relevance,
            "nordic_relevance_reason": self.nordic_relevance_reason,
            "interpretation_caveat": self.interpretation_caveat,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class AdnaStudySummary:
    """Normalized study-level grouping across one or more project summaries."""

    schema_version: str
    summary_token: str
    species_latin_name: str
    species_common_name: str
    project_accessions: tuple[str, ...]
    source_families: tuple[str, ...]
    archive_statuses: tuple[str, ...]
    evidence_strengths: tuple[str, ...]
    domestication_status: str
    paper_title: str | None
    paper_doi: str | None
    sequencing_targets: tuple[str, ...]
    material_bases: tuple[str, ...]
    dating_bases: tuple[str, ...]
    geographic_bases: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "summary_token": self.summary_token,
            "species_latin_name": self.species_latin_name,
            "species_common_name": self.species_common_name,
            "project_accessions": list(self.project_accessions),
            "source_families": list(self.source_families),
            "archive_statuses": list(self.archive_statuses),
            "evidence_strengths": list(self.evidence_strengths),
            "domestication_status": self.domestication_status,
            "paper_title": self.paper_title,
            "paper_doi": self.paper_doi,
            "sequencing_targets": list(self.sequencing_targets),
            "material_bases": list(self.material_bases),
            "dating_bases": list(self.dating_bases),
            "geographic_bases": list(self.geographic_bases),
        }


@dataclass(frozen=True)
class AdnaSpeciesNormalizationBundle:
    """Normalized non-human aDNA bundle for project and study review."""

    schema_version: str
    species_manifest: AdnaSpeciesManifest
    sample_records: tuple[AdnaSampleRecord, ...]
    coordinate_provenance_records: tuple[AdnaCoordinateProvenanceRecord, ...]
    site_evidence_records: tuple[AdnaSiteEvidenceRecord, ...]
    locality_records: tuple[AdnaLocalitySummary, ...]
    project_summaries: tuple[AdnaProjectSummary, ...]
    study_summaries: tuple[AdnaStudySummary, ...]
    lineage_records: tuple[AdnaNormalizationLineage, ...]
    refusals: tuple[AdnaNormalizationRefusal, ...]
    normalization_scope: str

    @property
    def species(self) -> AdnaSpeciesDefinition:
        return self.species_manifest.species

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "evidence_domain": "animal_ancient_dna",
            "pollen_eligible": False,
            "pollen_propagation_eligible": False,
            "species_manifest": self.species_manifest.as_dict(),
            "sample_records": [record.as_dict() for record in self.sample_records],
            "coordinate_provenance_records": [
                record.as_dict() for record in self.coordinate_provenance_records
            ],
            "site_evidence_records": [
                record.as_dict() for record in self.site_evidence_records
            ],
            "locality_records": [record.as_dict() for record in self.locality_records],
            "project_summaries": [
                summary.as_dict() for summary in self.project_summaries
            ],
            "study_summaries": [summary.as_dict() for summary in self.study_summaries],
            "lineage_records": [row.as_dict() for row in self.lineage_records],
            "refusals": [row.as_dict() for row in self.refusals],
            "normalization_scope": self.normalization_scope,
        }
