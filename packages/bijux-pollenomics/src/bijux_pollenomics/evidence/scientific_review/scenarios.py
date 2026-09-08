"""Claim-scoped Nordic interpretation scenarios."""

from __future__ import annotations

from ...adna import AdnaLocalitySummary, build_bovine_support_program
from ..models import AtlasEvidenceSpeciesRow
from .models import ChronologyOverlapRow, NordicScenarioAssessment


def _build_scenarios(
    *,
    direct_localities: tuple[AdnaLocalitySummary, ...],
    animal_localities: tuple[AdnaLocalitySummary, ...],
    species_rows: tuple[AtlasEvidenceSpeciesRow, ...],
    chronology_overlaps: tuple[ChronologyOverlapRow, ...],
) -> tuple[NordicScenarioAssessment, ...]:
    animal_context_species = tuple(
        row.species_latin_name
        for row in species_rows
        if row.species_latin_name != "Homo sapiens"
        and row.contribution_role == "contextual"
    )
    mapped_animal_species = tuple(
        sorted({locality.species_latin_name for locality in animal_localities})
    )
    has_human_direct = bool(direct_localities)
    has_human_overlap = any(
        row.species_latin_name == "Homo sapiens"
        and row.overlapping_direct_localities > 0
        for row in chronology_overlaps
    )
    bovine_program = build_bovine_support_program()
    return (
        NordicScenarioAssessment(
            scenario_key="nordic_farming_arrival",
            question="Can the platform compare early human presence with domesticated-animal context and landscape change in one honest review surface?",
            claim_scope="exploratory",
            usable_evidence=(
                "mapped_homo_sapiens_localities"
                if has_human_direct
                else "no_human_direct_localities",
                *(
                    mapped_animal_species
                    or animal_context_species
                    or ("no_contextual_animal_species",)
                ),
            ),
            blockers=(
                "animal_evidence_mapped_with_precision_caveats",
                "nonhuman_chronology_not_uniformly_country_resolved",
            ),
            current_posture="exploratory_only",
        ),
        NordicScenarioAssessment(
            scenario_key="pastoral_species_turnover",
            question="Can the platform compare animal-management turnover signals across species without flattening their support classes?",
            claim_scope="comparative",
            usable_evidence=mapped_animal_species
            or animal_context_species
            or ("no_contextual_animal_species",),
            blockers=("species_support_asymmetry", "mapped_animal_precision_caveats"),
            current_posture="comparative_with_locality_caveats",
        ),
        NordicScenarioAssessment(
            scenario_key="cattle_management_split",
            question="Can the platform distinguish taurine and indicine cattle support without collapsing them into one cattle story?",
            claim_scope="descriptive",
            usable_evidence=("bovine_support_program",),
            blockers=bovine_program.combined_claim_rule.currently_blocked_by,
            current_posture="descriptive_only",
        ),
        NordicScenarioAssessment(
            scenario_key="lake_selection_for_domestication_signal",
            question="Can the platform recommend lake targets for domestication-focused fieldwork today?",
            claim_scope="exploratory",
            usable_evidence=(
                "human_context_overlap"
                if has_human_overlap
                else "limited_human_context_overlap",
            ),
            blockers=(
                "field_sampling_gate_not_cleared",
                "animal_evidence_not_yet_dense_enough_for_fieldwork_recommendation",
            ),
            current_posture="exploratory_only",
        ),
    )
