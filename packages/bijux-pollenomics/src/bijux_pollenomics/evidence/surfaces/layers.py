"""Atlas layer projections from direct and contextual evidence."""

from __future__ import annotations

from ...adna import AdnaLocalitySummary
from ...collection.contracts.models import ContextPointRecord
from ..models import AtlasEvidenceLayer, AtlasEvidenceSpeciesRow


def _build_atlas_layers(
    *,
    human_localities: tuple[AdnaLocalitySummary, ...],
    animal_localities: tuple[AdnaLocalitySummary, ...],
    context_points: tuple[ContextPointRecord, ...],
    nonhuman_rows: tuple[AtlasEvidenceSpeciesRow, ...],
) -> tuple[AtlasEvidenceLayer, ...]:
    direct_domesticated_species = tuple(
        row.species_latin_name
        for row in nonhuman_rows
        if row.contribution_role == "direct" and row.product_role != "comparator"
    )
    direct_comparator_species = tuple(
        row.species_latin_name
        for row in nonhuman_rows
        if row.contribution_role == "direct" and row.product_role == "comparator"
    )
    contextual_species = tuple(
        row.species_latin_name
        for row in nonhuman_rows
        if row.contribution_role == "contextual"
    )
    too_weak_species = tuple(
        row.species_latin_name
        for row in nonhuman_rows
        if row.contribution_role == "too_weak"
    )
    return (
        AtlasEvidenceLayer(
            layer_key="homo_sapiens_direct",
            label="Homo sapiens direct evidence",
            species_scope=("Homo sapiens",),
            layer_role="mapped_direct",
            mapped=True,
            feature_count=len(human_localities),
            evidence_posture="mapped_locality_direct_evidence",
            provenance_posture="aadr_metadata_only",
            popup_contract=(
                "Species",
                "Evidence role",
                "Source family",
                "Source release",
                "Record modality",
                "Review strength",
                "Provenance quality",
                "Coordinate confidence",
                "Dating basis",
            ),
            rationale=("This is the mapped Homo sapiens direct ancient-DNA layer.",),
        ),
        AtlasEvidenceLayer(
            layer_key="animal_domesticated_direct",
            label="Domesticated-core animal direct evidence",
            species_scope=direct_domesticated_species,
            layer_role="mapped_direct",
            mapped=True,
            feature_count=sum(
                1
                for locality in animal_localities
                if locality.species_latin_name in direct_domesticated_species
            ),
            evidence_posture="mapped_species_owned_locality_evidence",
            provenance_posture="tracked_species_locality_summaries",
            popup_contract=(
                "Species",
                "Support class",
                "Project accession",
                "Paper title",
                "Publication year",
                "Chronology",
                "Coordinate confidence",
                "Nordic relevance",
                "Interpretation",
                "Warning",
            ),
            rationale=(
                "Domesticated-core animal species now ship mapped locality leads in the atlas bundle.",
            ),
        ),
        AtlasEvidenceLayer(
            layer_key="animal_comparator_direct",
            label="Comparator animal direct evidence",
            species_scope=direct_comparator_species,
            layer_role="mapped_direct_comparator",
            mapped=True,
            feature_count=sum(
                1
                for locality in animal_localities
                if locality.species_latin_name in direct_comparator_species
            ),
            evidence_posture="mapped_comparator_locality_evidence",
            provenance_posture="tracked_species_locality_summaries",
            popup_contract=(
                "Species",
                "Support class",
                "Project accession",
                "Paper title",
                "Publication year",
                "Chronology",
                "Coordinate confidence",
                "Nordic relevance",
                "Interpretation",
                "Warning",
            ),
            rationale=(
                "Comparator species remain distinct from domesticated-core support even when mapped as localities.",
            ),
        ),
        AtlasEvidenceLayer(
            layer_key="animal_adna_species_context",
            label="Animal aDNA species context",
            species_scope=contextual_species,
            layer_role="unmapped_contextual_review",
            mapped=False,
            feature_count=0,
            evidence_posture="species_review_context_only",
            provenance_posture="project_and_study_manifests",
            popup_contract=(),
            rationale=(
                "Some animal species still remain project and study review surfaces without mapped locality rows.",
            ),
        ),
        AtlasEvidenceLayer(
            layer_key="animal_adna_refused_or_thin",
            label="Animal aDNA refused or thin evidence",
            species_scope=too_weak_species,
            layer_role="refusal_guard",
            mapped=False,
            feature_count=0,
            evidence_posture="not_publishable_as_atlas_support",
            provenance_posture="governance_and_integrity_review",
            popup_contract=(),
            rationale=(
                "This layer exists only to make weak or blocked species explicit.",
            ),
        ),
        AtlasEvidenceLayer(
            layer_key="environmental_context",
            label="Environmental and archaeology context",
            species_scope=(),
            layer_role="mapped_context",
            mapped=True,
            feature_count=len(context_points),
            evidence_posture="non_adna_context",
            provenance_posture="normalized_context_layers",
            popup_contract=("Source-specific context rows",),
            rationale=(
                "Environmental and archaeology layers help contextualize atlas localities but do not become direct ancient-DNA evidence.",
            ),
        ),
    )
