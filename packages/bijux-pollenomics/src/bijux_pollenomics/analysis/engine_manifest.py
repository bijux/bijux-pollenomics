from __future__ import annotations

from dataclasses import dataclass

from .site_candidates import CandidateRankingProfile, build_ranking_profiles

__all__ = [
    "LakeSelectionRequirement",
    "RankingEngineManifest",
    "build_ranking_engine_manifest",
]


@dataclass(frozen=True)
class LakeSelectionRequirement:
    """One requirement that must exist before ranking becomes a serious field workflow."""

    requirement: str
    why_it_matters: str
    currently_satisfied: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "requirement": self.requirement,
            "why_it_matters": self.why_it_matters,
            "currently_satisfied": self.currently_satisfied,
        }


@dataclass(frozen=True)
class RankingEngineManifest:
    """Bridge current atlas ranking outputs to future pollenomics engine work."""

    schema_version: str
    engine_name: str
    current_mode: str
    bridge_statement: str
    default_profile: str
    supported_profiles: tuple[CandidateRankingProfile, ...]
    current_artifacts: tuple[str, ...]
    recommendation_gate_statement: str
    future_lake_selection_requirements: tuple[LakeSelectionRequirement, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "engine_name": self.engine_name,
            "current_mode": self.current_mode,
            "bridge_statement": self.bridge_statement,
            "default_profile": self.default_profile,
            "supported_profiles": [profile.as_dict() for profile in self.supported_profiles],
            "current_artifacts": list(self.current_artifacts),
            "recommendation_gate_statement": self.recommendation_gate_statement,
            "future_lake_selection_requirements": [
                requirement.as_dict()
                for requirement in self.future_lake_selection_requirements
            ],
        }


def build_ranking_engine_manifest() -> RankingEngineManifest:
    """Build the governed engine manifest for candidate-site ranking."""
    return RankingEngineManifest(
        schema_version="candidate-ranking-engine-manifest.v1",
        engine_name="candidate_site_ranking",
        current_mode="profiled_atlas_heuristic",
        bridge_statement=(
            "The current engine ranks locality anchors with explicit evidence "
            "families and refusal behavior, but it remains an atlas-adjacent "
            "heuristic until stronger multi-evidence contracts are satisfied."
        ),
        default_profile="atlas_exploration",
        supported_profiles=build_ranking_profiles(),
        current_artifacts=(
            "candidate_sites_csv",
            "candidate_sites_json",
            "candidate_sites_markdown",
            "candidate_site_sensitivity_json",
            "candidate_site_sensitivity_markdown",
            "candidate_ranking_engine_manifest_json",
            "atlas_evidence_surface_json",
            "atlas_evidence_surface_markdown",
        ),
        recommendation_gate_statement=(
            "No output counts as a sampling recommendation unless the "
            "`fieldwork_triage` profile clears cross-species, chronology, "
            "context-overlap, and non-metadata direct-evidence gates."
        ),
        future_lake_selection_requirements=(
            LakeSelectionRequirement(
                requirement="cross-species direct evidence at the same locality anchor",
                why_it_matters=(
                    "single-species metadata can describe presence but cannot support "
                    "serious pollenomics inference on its own"
                ),
                currently_satisfied=False,
            ),
            LakeSelectionRequirement(
                requirement="non-metadata direct evidence such as archive reads or genotypes",
                why_it_matters=(
                    "field sampling should not be prioritized from metadata-only "
                    "human locality inventories"
                ),
                currently_satisfied=False,
            ),
            LakeSelectionRequirement(
                requirement="chronology overlap between direct evidence and contextual layers",
                why_it_matters=(
                    "distance without temporal agreement can create false confidence"
                ),
                currently_satisfied=False,
            ),
            LakeSelectionRequirement(
                requirement="evidence contracts that reconcile human, animal, pollen, and archaeology layers",
                why_it_matters=(
                    "future site selection must combine evidence types without "
                    "pretending they mean the same thing"
                ),
                currently_satisfied=False,
            ),
        ),
    )
