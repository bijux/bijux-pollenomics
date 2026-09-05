from __future__ import annotations

from .models import SourceFamilyContract, SourceFamilyLayerContract


def build_dna_source_family_contracts() -> tuple[SourceFamilyContract, ...]:
    return (
        SourceFamilyContract(
            source_key="aadr",
            display_name="AADR human ancient DNA",
            domain_group="human_ancient_dna",
            evidence_role="direct_evidence_domain",
            primary_question=(
                "Which tracked human ancient-DNA inputs and normalized records exist "
                "under the governed AADR program?"
            ),
            raw_layer=SourceFamilyLayerContract(
                layer_key="raw",
                repository_path="data/aadr",
                required=True,
                purpose="tracked AADR versioned source files",
                example_artifacts=("data/aadr/v66",),
            ),
            normalized_layer=SourceFamilyLayerContract(
                layer_key="normalized",
                repository_path="data/adna/species/homo_sapiens/normalized",
                required=True,
                purpose="tracked governed Homo sapiens normalized outputs",
                example_artifacts=("data/adna/species/homo_sapiens/normalized",),
            ),
            reviewed_layer=SourceFamilyLayerContract(
                layer_key="reviewed",
                repository_path="data/adna/species/homo_sapiens/review",
                required=True,
                purpose="review-ready Homo sapiens package artifacts",
                example_artifacts=("data/adna/species/homo_sapiens/review",),
            ),
            published_layer=SourceFamilyLayerContract(
                layer_key="published",
                repository_path="docs/report",
                required=True,
                purpose="country and atlas outputs that consume governed AADR records",
                example_artifacts=("docs/report/published_reports_summary.json",),
            ),
            coverage_metric_keys=("aadr_file_count",),
        ),
        SourceFamilyContract(
            source_key="animal_adna",
            display_name="Animal ancient DNA recovery",
            domain_group="animal_ancient_dna",
            evidence_role="sample_owned_evidence_domain",
            primary_question=(
                "Which animal ancient-DNA records are only captured, which are "
                "normalized, and which are safe for public publication?"
            ),
            raw_layer=SourceFamilyLayerContract(
                layer_key="raw",
                repository_path="data/adna/governance/source_library",
                required=True,
                purpose=(
                    "tracked project, paper, archive, and supplement capture for the "
                    "animal recovery program"
                ),
                example_artifacts=(
                    "data/adna/governance/source_library/project_registry.json",
                ),
            ),
            normalized_layer=SourceFamilyLayerContract(
                layer_key="normalized",
                repository_path="data/adna/species",
                required=True,
                purpose=(
                    "species-owned normalized sample, locality, chronology, and "
                    "coordinate evidence"
                ),
                example_artifacts=(
                    "data/adna/species/equus_caballus/normalized/sample_records.json",
                ),
            ),
            reviewed_layer=SourceFamilyLayerContract(
                layer_key="reviewed",
                repository_path="data/adna/governance",
                required=True,
                purpose="cross-species review, curation, and evidence-honesty artifacts",
                example_artifacts=(
                    "data/adna/governance/animal_sample_foundation_truth.json",
                ),
            ),
            published_layer=SourceFamilyLayerContract(
                layer_key="published",
                repository_path="data/adna/final",
                required=True,
                purpose="shared publication-ready animal bundles and atlas candidate surfaces",
                example_artifacts=(
                    "data/adna/final/atlas/animal_atlas_point_candidates.json",
                ),
            ),
            coverage_metric_keys=(
                "animal_species_count",
                "animal_project_count",
                "animal_sample_count",
            ),
        ),
    )
