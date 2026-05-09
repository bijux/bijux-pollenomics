from __future__ import annotations

from dataclasses import dataclass

from ..curation import build_species_curation_manifest
from ..governance import build_species_dataset_review
from ..reviews import build_species_project_manifest
from .definitions import resolve_species_definition

__all__ = [
    "BovineCombinedClaimRule",
    "BovineSpeciesSupportRow",
    "BovineSupportProgram",
    "build_bovine_support_program",
]


@dataclass(frozen=True)
class BovineSpeciesSupportRow:
    """Species-specific bovine support row for split-versus-combined governance."""

    species_latin_name: str
    common_name: str
    curated_core_project_count: int
    pending_project_count: int
    release_gate_satisfied: bool
    wild_or_progenitor_context_count: int
    combined_with_other_bovines_allowed: bool
    blocking_reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "species_latin_name": self.species_latin_name,
            "common_name": self.common_name,
            "curated_core_project_count": self.curated_core_project_count,
            "pending_project_count": self.pending_project_count,
            "release_gate_satisfied": self.release_gate_satisfied,
            "wild_or_progenitor_context_count": self.wild_or_progenitor_context_count,
            "combined_with_other_bovines_allowed": self.combined_with_other_bovines_allowed,
            "blocking_reasons": list(self.blocking_reasons),
        }


@dataclass(frozen=True)
class BovineCombinedClaimRule:
    """Explicit rule for when taurine and indicine support can be merged."""

    split_default: bool
    combined_claim_allowed: bool
    decision_reason: str
    allowed_only_when: tuple[str, ...]
    currently_blocked_by: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "split_default": self.split_default,
            "combined_claim_allowed": self.combined_claim_allowed,
            "decision_reason": self.decision_reason,
            "allowed_only_when": list(self.allowed_only_when),
            "currently_blocked_by": list(self.currently_blocked_by),
        }


@dataclass(frozen=True)
class BovineSupportProgram:
    """Governed bovine support program spanning taurine and indicine cattle."""

    schema_version: str
    species_rows: tuple[BovineSpeciesSupportRow, ...]
    combined_claim_rule: BovineCombinedClaimRule
    north_star_boundary: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "species_rows": [row.as_dict() for row in self.species_rows],
            "combined_claim_rule": self.combined_claim_rule.as_dict(),
            "north_star_boundary": self.north_star_boundary,
        }


def build_bovine_support_program() -> BovineSupportProgram:
    """Build the explicit taurine-versus-indicine support program."""
    taurine_manifest = build_species_project_manifest("Bos taurus")
    taurine_review = build_species_dataset_review("Bos taurus")
    taurine_curation = build_species_curation_manifest("Bos taurus")
    indicine_review = build_species_dataset_review("Bos indicus")
    indicine_curation = build_species_curation_manifest("Bos indicus")

    taurine_wild_context_count = sum(
        1
        for row in taurine_manifest.projects
        if row.domestication_scope == "wild_or_progenitor_context"
    )
    blocking_reasons = (
        "species_split_default",
        "wild_or_progenitor_context_present",
        "no_explicit_joint_taurine_indicine_project_manifest",
    )
    combined_claim_rule = BovineCombinedClaimRule(
        split_default=True,
        combined_claim_allowed=False,
        decision_reason=(
            "Bos taurus and Bos indicus stay split by default because the current "
            "curated evidence does not justify one merged domesticated-cattle claim."
        ),
        allowed_only_when=(
            "a project is explicitly curated as shared taurine-indicine domesticated evidence",
            "wild or progenitor context is kept separate from domesticated-core support",
            "species-specific chronology and geography remain inspectable after merge",
        ),
        currently_blocked_by=blocking_reasons,
    )
    return BovineSupportProgram(
        schema_version="bovine-support-program.v1",
        species_rows=(
            BovineSpeciesSupportRow(
                species_latin_name="Bos taurus",
                common_name=resolve_species_definition("Bos taurus").common_name,
                curated_core_project_count=len(taurine_curation.curated_projects),
                pending_project_count=len(taurine_curation.pending_projects),
                release_gate_satisfied=taurine_review.release_gate_satisfied,
                wild_or_progenitor_context_count=taurine_wild_context_count,
                combined_with_other_bovines_allowed=False,
                blocking_reasons=tuple(
                    dict.fromkeys(
                        (
                            *taurine_review.blocking_reasons,
                            *blocking_reasons,
                        )
                    )
                ),
            ),
            BovineSpeciesSupportRow(
                species_latin_name="Bos indicus",
                common_name=resolve_species_definition("Bos indicus").common_name,
                curated_core_project_count=len(indicine_curation.curated_projects),
                pending_project_count=len(indicine_curation.pending_projects),
                release_gate_satisfied=indicine_review.release_gate_satisfied,
                wild_or_progenitor_context_count=0,
                combined_with_other_bovines_allowed=False,
                blocking_reasons=tuple(
                    dict.fromkeys(
                        (
                            *indicine_review.blocking_reasons,
                            "missing_species_specific_core_projects",
                            *blocking_reasons,
                        )
                    )
                ),
            ),
        ),
        combined_claim_rule=combined_claim_rule,
        north_star_boundary=(
            "Taurine and indicine cattle remain separate support surfaces until "
            "species-specific domestication evidence is explicit enough to merge "
            "them without hiding ancestry, chronology, or geography uncertainty."
        ),
    )
