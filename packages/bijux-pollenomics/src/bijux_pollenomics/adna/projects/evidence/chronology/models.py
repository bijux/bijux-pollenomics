from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdnaProjectSampleChronologyRow:
    species_latin_name: str
    species_common_name: str
    project_accession: str
    repo_stable_sample_id: str
    preferred_sample_label: str
    sample_basis: str
    sample_evidence_status: str
    sample_identity_resolution: str
    sample_ambiguity_note: str
    chronology_text: str
    chronology_strength: str
    chronology_evidence_class: str
    chronology_precision_posture: str
    chronology_provenance_path: str
    chronology_provenance_kind: str
    chronology_provenance_locator: str
    chronology_provenance_text: str
    chronology_normalization_status: str
    time_start_bp: int | None
    time_end_bp: int | None
    time_mean_bp: int | None
    dating_basis: str
    chronology_conflict_note: str
    review_note: str

    def as_dict(self) -> dict[str, object]:
        return {
            "species_latin_name": self.species_latin_name,
            "species_common_name": self.species_common_name,
            "project_accession": self.project_accession,
            "repo_stable_sample_id": self.repo_stable_sample_id,
            "preferred_sample_label": self.preferred_sample_label,
            "sample_basis": self.sample_basis,
            "sample_evidence_status": self.sample_evidence_status,
            "sample_identity_resolution": self.sample_identity_resolution,
            "sample_ambiguity_note": self.sample_ambiguity_note,
            "chronology_text": self.chronology_text,
            "chronology_strength": self.chronology_strength,
            "chronology_evidence_class": self.chronology_evidence_class,
            "chronology_precision_posture": self.chronology_precision_posture,
            "chronology_provenance_path": self.chronology_provenance_path,
            "chronology_provenance_kind": self.chronology_provenance_kind,
            "chronology_provenance_locator": self.chronology_provenance_locator,
            "chronology_provenance_text": self.chronology_provenance_text,
            "chronology_normalization_status": self.chronology_normalization_status,
            "time_start_bp": self.time_start_bp,
            "time_end_bp": self.time_end_bp,
            "time_mean_bp": self.time_mean_bp,
            "dating_basis": self.dating_basis,
            "chronology_conflict_note": self.chronology_conflict_note,
            "review_note": self.review_note,
        }


@dataclass(frozen=True)
class _ResolvedChronologySource:
    chronology_text: str
    chronology_strength: str
    chronology_evidence_class: str
    chronology_precision_posture: str
    chronology_provenance_path: str
    chronology_provenance_kind: str
    chronology_provenance_locator: str
    chronology_provenance_text: str
    chronology_normalization_status: str
    time_start_bp: int | None
    time_end_bp: int | None
    time_mean_bp: int | None
    chronology_conflict_note: str
    review_note: str
