from __future__ import annotations

from dataclasses import dataclass

from ..adna import (
    build_bovine_support_program,
    build_domestication_coverage_report,
    build_homo_sapiens_genotype_contract,
    build_species_support_matrix,
)

__all__ = ["PollenomicsReleaseBar", "build_release_bar"]


@dataclass(frozen=True)
class PollenomicsReleaseBar:
    """Platform-level bar for calling bijux-pollenomics a real pollenomics app."""

    schema_version: str
    species_aware_adna_support_defined: bool
    bovine_split_rule_defined: bool
    homo_sapiens_genotype_boundary_defined: bool
    nonhuman_domestication_program_defined: bool
    scientific_review_surface_defined: bool
    ranking_boundary_defined: bool
    current_posture: str
    blockers: tuple[str, ...]
    north_star_requirements: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "species_aware_adna_support_defined": self.species_aware_adna_support_defined,
            "bovine_split_rule_defined": self.bovine_split_rule_defined,
            "homo_sapiens_genotype_boundary_defined": self.homo_sapiens_genotype_boundary_defined,
            "nonhuman_domestication_program_defined": self.nonhuman_domestication_program_defined,
            "scientific_review_surface_defined": self.scientific_review_surface_defined,
            "ranking_boundary_defined": self.ranking_boundary_defined,
            "current_posture": self.current_posture,
            "blockers": list(self.blockers),
            "north_star_requirements": list(self.north_star_requirements),
        }


def build_release_bar() -> PollenomicsReleaseBar:
    """Build the governed release bar for the current pollenomics platform."""
    from ..analysis import build_ranking_engine_manifest
    from ..evidence import build_scientific_review_surface

    support_matrix = build_species_support_matrix()
    bovine_program = build_bovine_support_program()
    genotype_contract = build_homo_sapiens_genotype_contract()
    coverage_report = build_domestication_coverage_report()
    scientific_review = build_scientific_review_surface(
        countries=("Sweden",),
        human_localities=(),
        context_points=(),
    )
    ranking_engine_manifest = build_ranking_engine_manifest()

    species_aware_adna_support_defined = any(
        row.latin_name == "Homo sapiens" for row in support_matrix
    ) and any(row.latin_name != "Homo sapiens" for row in support_matrix)
    bovine_split_rule_defined = (
        bovine_program.combined_claim_rule.split_default
        and len(bovine_program.species_rows) == 2
        and not bovine_program.combined_claim_rule.combined_claim_allowed
    )
    homo_sapiens_genotype_boundary_defined = (
        genotype_contract.schema_version == "homo-sapiens-genotype-contract.v1"
        and genotype_contract.nonhuman_boundary.startswith("These genotype artifacts belong only")
        and len(genotype_contract.required_artifacts) == 3
    )
    nonhuman_domestication_program_defined = any(
        row.coverage_posture == "strong" for row in coverage_report.rows
    ) and any(row.coverage_posture in {"thin", "pretending"} for row in coverage_report.rows)
    scientific_review_surface_defined = (
        scientific_review.schema_version == "scientific-review-surface.v3"
        and bool(scientific_review.descriptive_scope)
        and bool(scientific_review.comparative_scope)
        and bool(scientific_review.exploratory_scope)
        and any(
            row.current_posture == "exploratory_only"
            for row in scientific_review.scenarios
        )
    )
    ranking_boundary_defined = (
        ranking_engine_manifest.schema_version == "candidate-ranking-engine-manifest.v1"
        and "atlas_scientific_review_json" in ranking_engine_manifest.current_artifacts
        and "Sampling recommendation" not in ranking_engine_manifest.recommendation_gate_statement
        and "No output counts as a sampling recommendation"
        in ranking_engine_manifest.recommendation_gate_statement
    )

    blockers = []
    if genotype_contract.ingestion_blockers:
        blockers.append("homo_sapiens_genotype_ingestion_not_ready")
    if any(
        row.blocking_reasons for row in bovine_program.species_rows if not row.release_gate_satisfied
    ):
        blockers.append("bovine_species_support_still_split_or_blocked")
    if any(
        row.current_posture == "exploratory_only" for row in scientific_review.scenarios
    ):
        blockers.append("nordic_farming_history_inference_still_exploratory")
    blockers.append("nonhuman_sample_and_locality_runtime_rows_not_implemented")

    current_posture = (
        "reference_grade_release_bar_ready"
        if not blockers
        else "governed_exploratory_not_release_bar_ready"
    )
    return PollenomicsReleaseBar(
        schema_version="pollenomics-release-bar.v1",
        species_aware_adna_support_defined=species_aware_adna_support_defined,
        bovine_split_rule_defined=bovine_split_rule_defined,
        homo_sapiens_genotype_boundary_defined=homo_sapiens_genotype_boundary_defined,
        nonhuman_domestication_program_defined=nonhuman_domestication_program_defined,
        scientific_review_surface_defined=scientific_review_surface_defined,
        ranking_boundary_defined=ranking_boundary_defined,
        current_posture=current_posture,
        blockers=tuple(dict.fromkeys(blockers)),
        north_star_requirements=(
            "species-aware aDNA support with explicit human and non-human ownership",
            "honest evidence contracts that refuse locality and chronology overclaiming",
            "domesticated-animal curation that stays species-specific where the science is split",
            "ranking outputs that remain review aids until stronger direct multi-evidence support exists",
        ),
    )
