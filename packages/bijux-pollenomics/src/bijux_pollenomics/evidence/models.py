from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "ATLAS_EVIDENCE_CONTRIBUTION_ROLES",
    "ATLAS_EVIDENCE_INTERACTION_POSTURES",
    "AtlasEvidenceCountryProfile",
    "AtlasEvidenceLayer",
    "AtlasEvidenceRefusal",
    "AtlasEvidenceSpeciesRow",
    "AtlasEvidenceSurface",
]

ATLAS_EVIDENCE_CONTRIBUTION_ROLES = (
    "direct",
    "contextual",
    "too_weak",
)
ATLAS_EVIDENCE_INTERACTION_POSTURES = (
    "increases_confidence",
    "decreases_confidence",
    "suggestive_only",
    "refused",
)


@dataclass(frozen=True)
class AtlasEvidenceSpeciesRow:
    """One species-level evidence row for atlas review and refusal logic."""

    species_latin_name: str
    species_common_name: str
    support_status: str
    product_role: str
    dataset_bucket: str
    contribution_role: str
    interaction_posture: str
    mapped_direct_record_count: int
    curated_project_count: int
    study_summary_count: int
    chronology_posture: str
    geography_posture: str
    contextual_layer_dependencies: tuple[str, ...]
    blocking_reasons: tuple[str, ...]
    rationale: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "species_latin_name": self.species_latin_name,
            "species_common_name": self.species_common_name,
            "support_status": self.support_status,
            "product_role": self.product_role,
            "dataset_bucket": self.dataset_bucket,
            "contribution_role": self.contribution_role,
            "interaction_posture": self.interaction_posture,
            "mapped_direct_record_count": self.mapped_direct_record_count,
            "curated_project_count": self.curated_project_count,
            "study_summary_count": self.study_summary_count,
            "chronology_posture": self.chronology_posture,
            "geography_posture": self.geography_posture,
            "contextual_layer_dependencies": list(self.contextual_layer_dependencies),
            "blocking_reasons": list(self.blocking_reasons),
            "rationale": list(self.rationale),
        }


@dataclass(frozen=True)
class AtlasEvidenceLayer:
    """One durable atlas evidence layer definition, even when it is unmapped."""

    layer_key: str
    label: str
    species_scope: tuple[str, ...]
    layer_role: str
    mapped: bool
    feature_count: int
    evidence_posture: str
    provenance_posture: str
    popup_contract: tuple[str, ...]
    rationale: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "layer_key": self.layer_key,
            "label": self.label,
            "species_scope": list(self.species_scope),
            "layer_role": self.layer_role,
            "mapped": self.mapped,
            "feature_count": self.feature_count,
            "evidence_posture": self.evidence_posture,
            "provenance_posture": self.provenance_posture,
            "popup_contract": list(self.popup_contract),
            "rationale": list(self.rationale),
        }


@dataclass(frozen=True)
class AtlasEvidenceCountryProfile:
    """Country-scoped evidence profile for mapped human and animal evidence."""

    country: str
    mapped_direct_species: tuple[str, ...]
    mapped_animal_direct_species: tuple[str, ...]
    unmapped_animal_context_species: tuple[str, ...]
    too_weak_animal_species: tuple[str, ...]
    human_locality_count: int
    human_sample_count: int
    mapped_animal_locality_count: int
    evidence_posture: str
    caution_note: str

    def as_dict(self) -> dict[str, object]:
        return {
            "country": self.country,
            "mapped_direct_species": list(self.mapped_direct_species),
            "mapped_animal_direct_species": list(self.mapped_animal_direct_species),
            "unmapped_animal_context_species": list(
                self.unmapped_animal_context_species
            ),
            "too_weak_animal_species": list(self.too_weak_animal_species),
            "human_locality_count": self.human_locality_count,
            "human_sample_count": self.human_sample_count,
            "mapped_animal_locality_count": self.mapped_animal_locality_count,
            "evidence_posture": self.evidence_posture,
            "caution_note": self.caution_note,
        }


@dataclass(frozen=True)
class AtlasEvidenceRefusal:
    """Explicit refusal row for scientific claims the atlas cannot support honestly."""

    subject: str
    reason: str
    detail: str

    def as_dict(self) -> dict[str, object]:
        return {
            "subject": self.subject,
            "reason": self.reason,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class AtlasEvidenceSurface:
    """Species-aware evidence contract for one published atlas bundle."""

    schema_version: str
    countries: tuple[str, ...]
    layers: tuple[AtlasEvidenceLayer, ...]
    species_rows: tuple[AtlasEvidenceSpeciesRow, ...]
    country_profiles: tuple[AtlasEvidenceCountryProfile, ...]
    refusals: tuple[AtlasEvidenceRefusal, ...]
    north_star_boundary: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "countries": list(self.countries),
            "layers": [layer.as_dict() for layer in self.layers],
            "species_rows": [row.as_dict() for row in self.species_rows],
            "country_profiles": [profile.as_dict() for profile in self.country_profiles],
            "refusals": [refusal.as_dict() for refusal in self.refusals],
            "north_star_boundary": self.north_star_boundary,
        }
