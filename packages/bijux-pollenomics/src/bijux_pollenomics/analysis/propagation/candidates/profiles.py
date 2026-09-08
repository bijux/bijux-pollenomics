"""Named candidate-ranking policies and their explicit weights."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoringWeights:
    """Explicit signal families for candidate ranking."""

    evidence_density: float
    chronology_alignment: float
    species_diversity: float
    contextual_support: float


@dataclass(frozen=True)
class CandidateRankingProfile:
    """Named ranking profile with durable purpose and explicit warnings."""

    profile_name: str
    purpose: str
    warning: str
    weights: ScoringWeights
    missingness_penalty_scale: float
    max_missingness_penalty: float
    requires_direct_chronology: bool = False
    requires_temporal_context: bool = False
    requires_cross_species_evidence: bool = False
    requires_non_metadata_direct_evidence: bool = False
    minimum_temporal_overlap_points: int = 0

    def as_dict(self) -> dict[str, object]:
        return {
            "profile_name": self.profile_name,
            "purpose": self.purpose,
            "warning": self.warning,
            "weights": {
                "evidence_density": self.weights.evidence_density,
                "chronology_alignment": self.weights.chronology_alignment,
                "species_diversity": self.weights.species_diversity,
                "contextual_support": self.weights.contextual_support,
            },
            "missingness_penalty_scale": self.missingness_penalty_scale,
            "max_missingness_penalty": self.max_missingness_penalty,
            "requires_direct_chronology": self.requires_direct_chronology,
            "requires_temporal_context": self.requires_temporal_context,
            "requires_cross_species_evidence": self.requires_cross_species_evidence,
            "requires_non_metadata_direct_evidence": self.requires_non_metadata_direct_evidence,
            "minimum_temporal_overlap_points": self.minimum_temporal_overlap_points,
        }


def build_ranking_profiles() -> tuple[CandidateRankingProfile, ...]:
    """Return every supported ranking profile in stable order."""
    return (
        CandidateRankingProfile(
            profile_name="atlas_exploration",
            purpose=(
                "Compare current locality anchors for descriptive atlas exploration "
                "without pretending the result is a fieldwork recommendation."
            ),
            warning=(
                "Exploratory atlas ordering remains heuristic and can elevate "
                "metadata-rich human localities over scientifically stronger "
                "multi-evidence candidates."
            ),
            weights=ScoringWeights(
                evidence_density=0.35,
                chronology_alignment=0.2,
                species_diversity=0.1,
                contextual_support=0.35,
            ),
            missingness_penalty_scale=0.75,
            max_missingness_penalty=0.35,
        ),
        CandidateRankingProfile(
            profile_name="chronology_first",
            purpose=(
                "Stress chronology agreement over context density to expose which "
                "localities remain coherent under date-aware comparison."
            ),
            warning=(
                "Chronology-first ordering still depends on current metadata "
                "coverage and should not be treated as a recommendation surface."
            ),
            weights=ScoringWeights(
                evidence_density=0.25,
                chronology_alignment=0.45,
                species_diversity=0.1,
                contextual_support=0.2,
            ),
            missingness_penalty_scale=0.95,
            max_missingness_penalty=0.4,
            requires_direct_chronology=True,
        ),
        CandidateRankingProfile(
            profile_name="context_first",
            purpose=(
                "Stress nearby cross-layer support over direct sample density to "
                "show how much the atlas depends on surrounding context."
            ),
            warning=(
                "Context-first ordering can reward busy neighborhoods even when "
                "direct ancient-DNA evidence is still thin."
            ),
            weights=ScoringWeights(
                evidence_density=0.2,
                chronology_alignment=0.15,
                species_diversity=0.1,
                contextual_support=0.55,
            ),
            missingness_penalty_scale=0.85,
            max_missingness_penalty=0.4,
        ),
        CandidateRankingProfile(
            profile_name="fieldwork_triage",
            purpose=(
                "Hold candidates against a stricter pre-recommendation bar for "
                "future lake-selection workflows."
            ),
            warning=(
                "Fieldwork triage is stricter than atlas exploration and should be "
                "read as a refusal-prone readiness screen, not a final sampling plan."
            ),
            weights=ScoringWeights(
                evidence_density=0.3,
                chronology_alignment=0.3,
                species_diversity=0.2,
                contextual_support=0.2,
            ),
            missingness_penalty_scale=1.15,
            max_missingness_penalty=0.55,
            requires_direct_chronology=True,
            requires_temporal_context=True,
            requires_cross_species_evidence=True,
            requires_non_metadata_direct_evidence=True,
            minimum_temporal_overlap_points=1,
        ),
    )


def resolve_ranking_profile(profile_name: str) -> CandidateRankingProfile:
    """Resolve one supported ranking profile by stable name."""
    for profile in build_ranking_profiles():
        if profile.profile_name == profile_name:
            return profile
    raise ValueError(f"Unsupported ranking profile: {profile_name}")
