from __future__ import annotations

from dataclasses import dataclass, field
from statistics import fmean
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..reporting.models import LocalitySummary

__all__ = [
    "CandidateRankingProfile",
    "CandidateSiteContext",
    "CandidateSiteScore",
    "ScoringWeights",
    "build_ranking_profiles",
    "resolve_ranking_profile",
    "score_candidate_site",
]


@dataclass(frozen=True)
class CandidateSiteContext:
    """One rankable locality anchor plus direct and contextual evidence around it."""

    locality: LocalitySummary
    direct_evidence: tuple[LocalitySummary, ...] = field(default_factory=tuple)
    nearby_context_points: int = 0
    nearby_context_layer_count: int = 0
    time_aware_context_points: int = 0
    temporal_overlap_points: int = 0
    nearest_context_distance_km: float | None = None

    def __post_init__(self) -> None:
        if not self.direct_evidence:
            object.__setattr__(self, "direct_evidence", (self.locality,))

    @property
    def direct_sample_count(self) -> int:
        return sum(locality.sample_count for locality in self.direct_evidence)

    @property
    def distinct_species_count(self) -> int:
        return len({locality.species_latin_name for locality in self.direct_evidence})

    @property
    def record_modalities(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    modality
                    for locality in self.direct_evidence
                    for modality in locality.record_modalities
                }
            )
        )

    @property
    def review_strengths(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    strength
                    for locality in self.direct_evidence
                    for strength in locality.review_strengths
                }
            )
        )

    @property
    def provenance_qualities(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    quality
                    for locality in self.direct_evidence
                    for quality in locality.provenance_qualities
                }
            )
        )


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


@dataclass(frozen=True)
class CandidateSiteScore:
    """Profile-aware candidate ranking result with explicit evidence boundaries."""

    locality: str
    locality_token: str
    profile_name: str
    ranking_status: str
    total_score: float
    evidence_density_signal: float
    chronology_alignment_signal: float
    species_diversity_signal: float
    contextual_support_signal: float
    missingness_penalty: float
    direct_sample_count: int
    distinct_species_count: int
    nearby_context_points: int
    nearby_context_layer_count: int
    time_aware_context_points: int
    temporal_overlap_points: int
    sampling_recommendation_ready: bool
    recommendation_posture: str
    ranking_blockers: tuple[str, ...]
    recommendation_blockers: tuple[str, ...]
    warning_flags: tuple[str, ...]
    rationale: tuple[str, ...]


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


def score_candidate_site(
    candidate: CandidateSiteContext,
    *,
    profile: CandidateRankingProfile | None = None,
) -> CandidateSiteScore:
    """Score one candidate locality with explicit profile and evidence boundaries."""
    active_profile = (
        resolve_ranking_profile("atlas_exploration") if profile is None else profile
    )
    evidence_density_signal = _round_signal(_build_evidence_density_signal(candidate))
    chronology_alignment_signal = _round_signal(
        _build_chronology_alignment_signal(candidate)
    )
    species_diversity_signal = _round_signal(_build_species_diversity_signal(candidate))
    contextual_support_signal = _round_signal(
        _build_contextual_support_signal(candidate)
    )
    warning_flags = _build_warning_flags(candidate)
    ranking_blockers = _build_ranking_blockers(candidate)
    recommendation_blockers = _build_recommendation_blockers(
        candidate,
        profile=active_profile,
        ranking_blockers=ranking_blockers,
    )
    missingness_penalty = _round_signal(
        _build_missingness_penalty(candidate, warning_flags, profile=active_profile)
    )

    if ranking_blockers:
        total_score = 0.0
        ranking_status = "refused"
    else:
        weighted_total = (
            evidence_density_signal * active_profile.weights.evidence_density
            + chronology_alignment_signal * active_profile.weights.chronology_alignment
            + species_diversity_signal * active_profile.weights.species_diversity
            + contextual_support_signal * active_profile.weights.contextual_support
        )
        total_score = max(0.0, weighted_total - missingness_penalty)
        ranking_status = (
            "downgraded"
            if any(
                flag
                in {
                    "missing_direct_chronology",
                    "no_time_aware_context",
                    "no_temporal_context_overlap",
                    "no_nearby_context",
                }
                for flag in warning_flags
            )
            else "ranked"
        )

    sampling_recommendation_ready = not recommendation_blockers and total_score >= 0.65
    recommendation_posture = (
        "fieldwork_triage_ready"
        if sampling_recommendation_ready
        else "exploratory_only"
    )
    rationale = _build_rationale(
        candidate,
        active_profile,
        evidence_density_signal=evidence_density_signal,
        chronology_alignment_signal=chronology_alignment_signal,
        species_diversity_signal=species_diversity_signal,
        contextual_support_signal=contextual_support_signal,
        missingness_penalty=missingness_penalty,
        ranking_status=ranking_status,
        recommendation_posture=recommendation_posture,
    )
    return CandidateSiteScore(
        locality=candidate.locality.locality or "Unspecified locality",
        locality_token=candidate.locality.locality_token,
        profile_name=active_profile.profile_name,
        ranking_status=ranking_status,
        total_score=round(total_score, 4),
        evidence_density_signal=evidence_density_signal,
        chronology_alignment_signal=chronology_alignment_signal,
        species_diversity_signal=species_diversity_signal,
        contextual_support_signal=contextual_support_signal,
        missingness_penalty=missingness_penalty,
        direct_sample_count=candidate.direct_sample_count,
        distinct_species_count=candidate.distinct_species_count,
        nearby_context_points=candidate.nearby_context_points,
        nearby_context_layer_count=candidate.nearby_context_layer_count,
        time_aware_context_points=candidate.time_aware_context_points,
        temporal_overlap_points=candidate.temporal_overlap_points,
        sampling_recommendation_ready=sampling_recommendation_ready,
        recommendation_posture=recommendation_posture,
        ranking_blockers=ranking_blockers,
        recommendation_blockers=recommendation_blockers,
        warning_flags=warning_flags,
        rationale=rationale,
    )


def _build_evidence_density_signal(candidate: CandidateSiteContext) -> float:
    sample_signal = min(1.0, candidate.direct_sample_count / 6.0)
    review_signal = _mean_or_zero(
        max(_review_strength_weight(strength) for strength in locality.review_strengths)
        for locality in candidate.direct_evidence
    )
    provenance_signal = _mean_or_zero(
        max(
            _provenance_quality_weight(quality)
            for quality in locality.provenance_qualities
        )
        for locality in candidate.direct_evidence
    )
    modality_signal = _mean_or_zero(
        max(
            _record_modality_weight(modality) for modality in locality.record_modalities
        )
        for locality in candidate.direct_evidence
    )
    return (
        sample_signal * 0.5
        + review_signal * 0.2
        + provenance_signal * 0.15
        + modality_signal * 0.15
    )


def _build_chronology_alignment_signal(candidate: CandidateSiteContext) -> float:
    chronology_rows = [
        locality
        for locality in candidate.direct_evidence
        if locality.time_start_bp is not None and locality.time_end_bp is not None
    ]
    direct_signal = 1.0 if chronology_rows else 0.0
    cross_species_signal = 0.0
    if len(chronology_rows) >= 2:
        pairwise_checks: list[float] = []
        for index, left in enumerate(chronology_rows):
            for right in chronology_rows[index + 1 :]:
                pairwise_checks.append(1.0 if _windows_overlap(left, right) else 0.0)
        cross_species_signal = _mean_or_zero(pairwise_checks)
    context_signal = (
        candidate.temporal_overlap_points / candidate.time_aware_context_points
        if candidate.time_aware_context_points
        else 0.0
    )
    components = [direct_signal]
    if len(chronology_rows) >= 2:
        components.append(cross_species_signal)
    if candidate.time_aware_context_points:
        components.append(context_signal)
    return _mean_or_zero(components)


def _build_species_diversity_signal(candidate: CandidateSiteContext) -> float:
    distinct_species = candidate.distinct_species_count
    if distinct_species <= 0:
        species_signal = 0.0
    elif distinct_species == 1:
        species_signal = 0.35
    elif distinct_species == 2:
        species_signal = 0.7
    else:
        species_signal = 1.0
    modality_signal = min(1.0, len(candidate.record_modalities) / 3.0)
    return species_signal * 0.8 + modality_signal * 0.2


def _build_contextual_support_signal(candidate: CandidateSiteContext) -> float:
    density_signal = min(1.0, candidate.nearby_context_points / 8.0)
    layer_signal = min(1.0, candidate.nearby_context_layer_count / 4.0)
    if candidate.nearest_context_distance_km is None:
        distance_signal = 0.0
    else:
        distance_signal = max(
            0.0,
            min(1.0, (25.0 - candidate.nearest_context_distance_km) / 25.0),
        )
    return density_signal * 0.45 + layer_signal * 0.35 + distance_signal * 0.2


def _build_warning_flags(candidate: CandidateSiteContext) -> tuple[str, ...]:
    flags: list[str] = []
    if all(
        locality.time_start_bp is None or locality.time_end_bp is None
        for locality in candidate.direct_evidence
    ):
        flags.append("missing_direct_chronology")
    if candidate.time_aware_context_points == 0:
        flags.append("no_time_aware_context")
    if candidate.temporal_overlap_points == 0:
        flags.append("no_temporal_context_overlap")
    if candidate.nearby_context_points == 0:
        flags.append("no_nearby_context")
    if candidate.distinct_species_count < 2:
        flags.append("single_species_direct_evidence")
    if candidate.record_modalities and all(
        modality == "metadata_only" for modality in candidate.record_modalities
    ):
        flags.append("metadata_only_direct_evidence")
    return tuple(flags)


def _build_ranking_blockers(candidate: CandidateSiteContext) -> tuple[str, ...]:
    blockers: list[str] = []
    if candidate.direct_sample_count <= 0:
        blockers.append("direct_evidence_required")
    if candidate.locality.latitude is None or candidate.locality.longitude is None:
        blockers.append("coordinates_required_for_ranking")
    return tuple(blockers)


def _build_recommendation_blockers(
    candidate: CandidateSiteContext,
    *,
    profile: CandidateRankingProfile,
    ranking_blockers: tuple[str, ...],
) -> tuple[str, ...]:
    blockers = list(ranking_blockers)
    if profile.profile_name != "fieldwork_triage":
        blockers.append("profile_is_not_fieldwork_triage")
    if profile.requires_direct_chronology and all(
        locality.time_start_bp is None or locality.time_end_bp is None
        for locality in candidate.direct_evidence
    ):
        blockers.append("direct_chronology_required_for_fieldwork")
    if (
        profile.requires_temporal_context
        and candidate.temporal_overlap_points < profile.minimum_temporal_overlap_points
    ):
        blockers.append("temporal_context_overlap_required_for_fieldwork")
    if profile.requires_cross_species_evidence and candidate.distinct_species_count < 2:
        blockers.append("cross_species_direct_evidence_required_for_fieldwork")
    if profile.requires_non_metadata_direct_evidence and (
        not candidate.record_modalities
        or all(modality == "metadata_only" for modality in candidate.record_modalities)
    ):
        blockers.append("non_metadata_direct_evidence_required_for_fieldwork")
    return tuple(blockers)


def _build_missingness_penalty(
    candidate: CandidateSiteContext,
    warning_flags: tuple[str, ...],
    *,
    profile: CandidateRankingProfile,
) -> float:
    serious_flags = {
        "missing_direct_chronology",
        "no_time_aware_context",
        "no_temporal_context_overlap",
        "no_nearby_context",
    }
    moderate_flags = {
        "single_species_direct_evidence",
        "metadata_only_direct_evidence",
    }
    base_penalty = 0.0
    for flag in warning_flags:
        if flag in serious_flags:
            base_penalty += 0.12
        elif flag in moderate_flags:
            base_penalty += 0.05
    if candidate.direct_sample_count <= 1:
        base_penalty += 0.04
    return min(
        profile.max_missingness_penalty,
        base_penalty * profile.missingness_penalty_scale,
    )


def _build_rationale(
    candidate: CandidateSiteContext,
    profile: CandidateRankingProfile,
    *,
    evidence_density_signal: float,
    chronology_alignment_signal: float,
    species_diversity_signal: float,
    contextual_support_signal: float,
    missingness_penalty: float,
    ranking_status: str,
    recommendation_posture: str,
) -> tuple[str, ...]:
    rationale = [
        (
            f"profile `{profile.profile_name}` weights evidence density, chronology, "
            "species diversity, and contextual support explicitly"
        ),
        (
            f"{candidate.direct_sample_count} direct ancient-DNA samples support "
            f"{candidate.distinct_species_count} species at this locality anchor"
        ),
        (
            f"{candidate.nearby_context_points} nearby context points across "
            f"{candidate.nearby_context_layer_count} context layers shape the support surface"
        ),
        (
            f"score families: evidence={evidence_density_signal:.4f}; "
            f"chronology={chronology_alignment_signal:.4f}; "
            f"species={species_diversity_signal:.4f}; "
            f"context={contextual_support_signal:.4f}"
        ),
        f"missingness penalty={missingness_penalty:.4f}; ranking status={ranking_status}",
        f"recommendation posture={recommendation_posture}",
    ]
    return tuple(rationale)


def _windows_overlap(left: LocalitySummary, right: LocalitySummary) -> bool:
    return not (
        left.time_end_bp is None
        or left.time_start_bp is None
        or right.time_end_bp is None
        or right.time_start_bp is None
        or left.time_end_bp > right.time_start_bp
        or left.time_start_bp < right.time_end_bp
    )


def _review_strength_weight(value: str) -> float:
    weights = {
        "primary_paper_pinned": 1.0,
        "curated_release_metadata": 0.85,
        "archive_verified_needs_paper_pinning": 0.7,
        "comparator_only": 0.5,
        "manual_review_required": 0.3,
    }
    return weights.get(value, 0.25)


def _provenance_quality_weight(value: str) -> float:
    weights = {
        "release_manifest_pinned": 1.0,
        "archive_project_catalog": 0.8,
        "manual_curation_only": 0.45,
    }
    return weights.get(value, 0.35)


def _record_modality_weight(value: str) -> float:
    weights = {
        "genotypes": 1.0,
        "archive_reads": 0.9,
        "metadata_only": 0.55,
        "mitogenome_only": 0.6,
        "paper_only": 0.35,
    }
    return weights.get(value, 0.4)


def _mean_or_zero(values) -> float:
    collected = tuple(values)
    return fmean(collected) if collected else 0.0


def _round_signal(value: float) -> float:
    return round(value, 4)
