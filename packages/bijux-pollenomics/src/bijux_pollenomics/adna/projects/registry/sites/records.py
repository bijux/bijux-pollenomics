"""Stable row schema and controlled statuses for sample-site evidence."""

from __future__ import annotations

from dataclasses import dataclass

ADNA_LOCALITY_RESOLUTION_STATUSES = (
    "direct_sample_site",
    "sample_group_site",
    "project_level_site_only",
    "named_place_inferred",
    "region_only",
    "unresolved",
)


@dataclass(frozen=True)
class AdnaProjectSampleSiteRow:
    species_latin_name: str
    species_common_name: str
    project_accession: str
    repo_stable_sample_id: str
    preferred_sample_label: str
    sample_basis: str
    sample_evidence_status: str
    sample_identity_resolution: str
    sample_ambiguity_note: str
    locality_text: str
    locality_resolution_status: str
    location_evidence_artifact_path: str
    location_evidence_artifact_kind: str
    location_evidence_locator: str
    location_evidence_text: str
    site_name: str
    municipality_name: str
    region_name: str
    country_name: str
    broader_geography: str
    coordinate_basis: str
    coordinate_mapping_posture: str
    coordinate_confidence: str
    chronology_text: str
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
            "locality_text": self.locality_text,
            "locality_resolution_status": self.locality_resolution_status,
            "location_evidence_artifact_path": self.location_evidence_artifact_path,
            "location_evidence_artifact_kind": self.location_evidence_artifact_kind,
            "location_evidence_locator": self.location_evidence_locator,
            "location_evidence_text": self.location_evidence_text,
            "site_name": self.site_name,
            "municipality_name": self.municipality_name,
            "region_name": self.region_name,
            "country_name": self.country_name,
            "broader_geography": self.broader_geography,
            "coordinate_basis": self.coordinate_basis,
            "coordinate_mapping_posture": self.coordinate_mapping_posture,
            "coordinate_confidence": self.coordinate_confidence,
            "chronology_text": self.chronology_text,
            "review_note": self.review_note,
        }
