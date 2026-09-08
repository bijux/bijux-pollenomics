"""Candidate propagation rules and evidence-aware site ranking."""

from .context import CandidateSiteContext
from .profiles import (
    CandidateRankingProfile,
    ScoringWeights,
    build_ranking_profiles,
    resolve_ranking_profile,
)
from .rules import (
    DEFAULT_PROPAGATION_SCENARIO,
    CandidatePairRefusalError,
    CandidatePropagationAssessment,
    CandidatePropagationScenario,
    PropagationStatusDecision,
    assess_candidate_propagation,
    classify_candidate_propagation,
)
from .scoring import CandidateSiteScore, score_candidate_site

__all__ = [
    "DEFAULT_PROPAGATION_SCENARIO",
    "CandidatePairRefusalError",
    "CandidatePropagationAssessment",
    "CandidatePropagationScenario",
    "CandidateRankingProfile",
    "CandidateSiteContext",
    "CandidateSiteScore",
    "PropagationStatusDecision",
    "ScoringWeights",
    "assess_candidate_propagation",
    "build_ranking_profiles",
    "classify_candidate_propagation",
    "resolve_ranking_profile",
    "score_candidate_site",
]
