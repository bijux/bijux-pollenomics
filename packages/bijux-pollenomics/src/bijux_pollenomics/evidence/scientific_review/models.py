"""Immutable contracts exposed by the scientific-review surface."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnimalCoordinateVisibilityReview:
    """Visible animal-feature counts by coordinate-basis strength."""

    direct_coordinate_feature_count: int
    named_site_geocoded_feature_count: int
    weaker_geography_feature_count: int

    def as_dict(self) -> dict[str, object]:
        return {
            "direct_coordinate_feature_count": self.direct_coordinate_feature_count,
            "named_site_geocoded_feature_count": self.named_site_geocoded_feature_count,
            "weaker_geography_feature_count": self.weaker_geography_feature_count,
        }


@dataclass(frozen=True)
class SpeciesCountryCoverageRow:
    """Species-by-country coverage row that keeps unmapped animal context explicit."""

    country: str
    species_latin_name: str
    evidence_scope: str
    mapped_locality_count: int
    contextual_project_count: int
    assignment_confidence: str
    caution_note: str

    def as_dict(self) -> dict[str, object]:
        return {
            "country": self.country,
            "species_latin_name": self.species_latin_name,
            "evidence_scope": self.evidence_scope,
            "mapped_locality_count": self.mapped_locality_count,
            "contextual_project_count": self.contextual_project_count,
            "assignment_confidence": self.assignment_confidence,
            "caution_note": self.caution_note,
        }


@dataclass(frozen=True)
class SpeciesPeriodCoverageRow:
    """Species-by-period coverage row with explicit chronology honesty."""

    species_latin_name: str
    period_label: str
    evidence_scope: str
    mapped_locality_count: int
    contextual_project_count: int
    chronology_confidence: str
    caution_note: str

    def as_dict(self) -> dict[str, object]:
        return {
            "species_latin_name": self.species_latin_name,
            "period_label": self.period_label,
            "evidence_scope": self.evidence_scope,
            "mapped_locality_count": self.mapped_locality_count,
            "contextual_project_count": self.contextual_project_count,
            "chronology_confidence": self.chronology_confidence,
            "caution_note": self.caution_note,
        }


@dataclass(frozen=True)
class ChronologyOverlapRow:
    """Comparison row between species evidence and contextual time windows."""

    species_latin_name: str
    context_layer_key: str
    overlap_status: str
    overlapping_direct_localities: int
    non_overlapping_direct_localities: int
    noncomparable_records: int
    rationale: str

    def as_dict(self) -> dict[str, object]:
        return {
            "species_latin_name": self.species_latin_name,
            "context_layer_key": self.context_layer_key,
            "overlap_status": self.overlap_status,
            "overlapping_direct_localities": self.overlapping_direct_localities,
            "non_overlapping_direct_localities": self.non_overlapping_direct_localities,
            "noncomparable_records": self.noncomparable_records,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class EvidenceUncertaintyRow:
    """Explicit uncertainty row for species identity, locality, or chronology weakness."""

    subject: str
    uncertainty_kind: str
    severity: str
    reason: str
    impact: str

    def as_dict(self) -> dict[str, object]:
        return {
            "subject": self.subject,
            "uncertainty_kind": self.uncertainty_kind,
            "severity": self.severity,
            "reason": self.reason,
            "impact": self.impact,
        }


@dataclass(frozen=True)
class NordicScenarioAssessment:
    """Assessment of one real Nordic farming-history scenario."""

    scenario_key: str
    question: str
    claim_scope: str
    usable_evidence: tuple[str, ...]
    blockers: tuple[str, ...]
    current_posture: str

    def as_dict(self) -> dict[str, object]:
        return {
            "scenario_key": self.scenario_key,
            "question": self.question,
            "claim_scope": self.claim_scope,
            "usable_evidence": list(self.usable_evidence),
            "blockers": list(self.blockers),
            "current_posture": self.current_posture,
        }


@dataclass(frozen=True)
class ScientificReviewSurface:
    """Scientist-facing summary of what the platform can claim today."""

    schema_version: str
    descriptive_scope: tuple[str, ...]
    comparative_scope: tuple[str, ...]
    exploratory_scope: tuple[str, ...]
    country_coverage: tuple[SpeciesCountryCoverageRow, ...]
    period_coverage: tuple[SpeciesPeriodCoverageRow, ...]
    chronology_overlaps: tuple[ChronologyOverlapRow, ...]
    animal_coordinate_review: AnimalCoordinateVisibilityReview
    uncertainties: tuple[EvidenceUncertaintyRow, ...]
    scenarios: tuple[NordicScenarioAssessment, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "descriptive_scope": list(self.descriptive_scope),
            "comparative_scope": list(self.comparative_scope),
            "exploratory_scope": list(self.exploratory_scope),
            "country_coverage": [row.as_dict() for row in self.country_coverage],
            "period_coverage": [row.as_dict() for row in self.period_coverage],
            "chronology_overlaps": [row.as_dict() for row in self.chronology_overlaps],
            "animal_coordinate_review": self.animal_coordinate_review.as_dict(),
            "uncertainties": [row.as_dict() for row in self.uncertainties],
            "scenarios": [row.as_dict() for row in self.scenarios],
        }
