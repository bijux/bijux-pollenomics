"""aDNA project sample-master records."""

from __future__ import annotations

from dataclasses import dataclass

ADNA_SAMPLE_EVIDENCE_STATUSES = (
    "direct_table_extracted",
    "article_text_extracted",
    "appendix_extracted",
    "pdf_text_extracted",
    "archive_native",
    "experiment_level_only",
    "manual_curation_required",
    "not_yet_recoverable",
)
ADNA_SAMPLE_IDENTITY_RESOLUTIONS = (
    "final",
    "ambiguous",
    "provisional",
)
ADNA_SOURCE_NATIVE_IDENTITY_KINDS = (
    "biological_sample",
    "biological_sample_accession",
    "sequencing_experiment_accession",
    "supplementary_sample_label",
)
_XLSX_NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "p": "http://schemas.openxmlformats.org/package/2006/relationships",
}
_ARCHIVE_PROJECT_SAMPLE_ACCESSIONS = {
    "PRJEB30282",
    "PRJEB31621",
    "PRJEB41594",
    "PRJEB59481",
    "PRJEB60484",
    "PRJEB75467",
    "PRJEB81815",
    "PRJNA705960",
    "SRP073444",
}


@dataclass(frozen=True)
class AdnaProjectSampleMasterRow:
    species_latin_name: str
    species_common_name: str
    project_accession: str
    repo_stable_sample_id: str
    archive_native_sample_id: str
    paper_native_sample_label: str
    supplementary_table_sample_label: str
    preferred_sample_label: str
    sample_basis: str
    sample_evidence_status: str
    sample_lineage_path: str
    sample_lineage_locator: str
    sample_lineage_excerpt: str
    sample_identity_resolution: str
    sample_ambiguity_note: str
    locality_text: str
    political_entity: str
    latitude_text: str
    longitude_text: str
    chronology_text: str
    chronology_dating_basis: str = ""
    chronology_evidence_class: str = ""
    chronology_precision_posture: str = ""
    source_native_tax_id: str = ""
    source_native_scientific_name: str = ""
    taxon_alignment_status: str = "not_reported"
    archive_native_experiment_id: str = ""
    source_native_identity_kind: str = "biological_sample"
    chronology_time_mean_bp: int | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "species_latin_name": self.species_latin_name,
            "species_common_name": self.species_common_name,
            "project_accession": self.project_accession,
            "repo_stable_sample_id": self.repo_stable_sample_id,
            "archive_native_sample_id": self.archive_native_sample_id,
            "paper_native_sample_label": self.paper_native_sample_label,
            "supplementary_table_sample_label": self.supplementary_table_sample_label,
            "preferred_sample_label": self.preferred_sample_label,
            "sample_basis": self.sample_basis,
            "sample_evidence_status": self.sample_evidence_status,
            "sample_lineage_path": self.sample_lineage_path,
            "sample_lineage_locator": self.sample_lineage_locator,
            "sample_lineage_excerpt": self.sample_lineage_excerpt,
            "sample_identity_resolution": self.sample_identity_resolution,
            "sample_ambiguity_note": self.sample_ambiguity_note,
            "locality_text": self.locality_text,
            "political_entity": self.political_entity,
            "latitude_text": self.latitude_text,
            "longitude_text": self.longitude_text,
            "chronology_text": self.chronology_text,
            "chronology_dating_basis": self.chronology_dating_basis,
            "chronology_evidence_class": self.chronology_evidence_class,
            "chronology_precision_posture": self.chronology_precision_posture,
            "source_native_tax_id": self.source_native_tax_id,
            "source_native_scientific_name": self.source_native_scientific_name,
            "taxon_alignment_status": self.taxon_alignment_status,
            "archive_native_experiment_id": self.archive_native_experiment_id,
            "source_native_identity_kind": self.source_native_identity_kind,
            "chronology_time_mean_bp": self.chronology_time_mean_bp,
        }


@dataclass(frozen=True)
class AdnaProjectSampleMaster:
    project_accession: str
    species_latin_name: str
    species_common_name: str
    expected_sample_count: int | None
    expected_sample_count_status: str
    expected_sample_count_provenance: str
    expected_sample_count_artifact_path: str
    recovered_sample_count: int
    unresolved_sample_count: int | None
    final_sample_count: int
    ambiguity_row_count: int
    sample_identifier_status: str
    extraction_plan: str
    rows: tuple[AdnaProjectSampleMasterRow, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "project_accession": self.project_accession,
            "species_latin_name": self.species_latin_name,
            "species_common_name": self.species_common_name,
            "expected_sample_count": self.expected_sample_count,
            "expected_sample_count_status": self.expected_sample_count_status,
            "expected_sample_count_provenance": self.expected_sample_count_provenance,
            "expected_sample_count_artifact_path": self.expected_sample_count_artifact_path,
            "recovered_sample_count": self.recovered_sample_count,
            "unresolved_sample_count": self.unresolved_sample_count,
            "final_sample_count": self.final_sample_count,
            "ambiguity_row_count": self.ambiguity_row_count,
            "sample_identifier_status": self.sample_identifier_status,
            "extraction_plan": self.extraction_plan,
            "rows": [row.as_dict() for row in self.rows],
        }
