"""Human and non-human species evidence rows."""

from __future__ import annotations

from ...adna import (
    AdnaLocalitySummary,
    build_species_dataset_review,
    build_species_normalization_bundle,
    build_species_support_matrix,
)
from ...collection.contracts.models import ContextPointRecord
from ..models import AtlasEvidenceSpeciesRow
from .posture import (
    _chronology_posture_for,
    _contribution_role_for,
    _geography_posture_for,
    _interaction_posture_for,
    _rationale_for,
)


def _build_human_species_row(
    *,
    human_localities: tuple[AdnaLocalitySummary, ...],
    context_points: tuple[ContextPointRecord, ...],
) -> AtlasEvidenceSpeciesRow:
    return AtlasEvidenceSpeciesRow(
        species_latin_name="Homo sapiens",
        species_common_name="human",
        support_status="supported",
        product_role="human_reference",
        dataset_bucket="paper_pinned_core",
        contribution_role="direct",
        interaction_posture="increases_confidence"
        if context_points
        else "suggestive_only",
        mapped_direct_record_count=len(human_localities),
        curated_project_count=0,
        study_summary_count=0,
        chronology_posture="mapped_sample_chronology_available",
        geography_posture="mapped_locality_points",
        contextual_layer_dependencies=tuple(
            sorted({point.layer_key for point in context_points})
        ),
        blocking_reasons=(),
        rationale=(
            "Homo sapiens atlas evidence is direct because the runtime owns mapped sample and locality metadata.",
            "The current human layer remains metadata-only and does not imply genotype-aware interpretation.",
        ),
    )


def _build_nonhuman_species_rows(
    *,
    human_localities: tuple[AdnaLocalitySummary, ...],
    animal_localities: tuple[AdnaLocalitySummary, ...],
    context_points: tuple[ContextPointRecord, ...],
    include_tracked_nonhuman_review: bool,
) -> tuple[AtlasEvidenceSpeciesRow, ...]:
    if not include_tracked_nonhuman_review:
        return ()
    rows: list[AtlasEvidenceSpeciesRow] = []
    context_layer_dependencies = tuple(
        sorted({point.layer_key for point in context_points})
    )
    for species in build_species_support_matrix():
        if species.latin_name == "Homo sapiens":
            continue
        dataset_review = build_species_dataset_review(species.latin_name)
        normalization_bundle = build_species_normalization_bundle(species.latin_name)
        species_localities = tuple(
            locality
            for locality in animal_localities
            if locality.species_latin_name == species.latin_name
        )
        contribution_role = _contribution_role_for(
            dataset_review=dataset_review,
            normalization_bundle=normalization_bundle,
            mapped_locality_count=len(species_localities),
        )
        interaction_posture = _interaction_posture_for(
            contribution_role=contribution_role,
            dataset_review=dataset_review,
            normalization_bundle=normalization_bundle,
            mapped_locality_count=len(species_localities),
            has_human_direct=bool(human_localities),
            has_time_aware_context=any(
                point.time_start_bp is not None and point.time_end_bp is not None
                for point in context_points
            ),
        )
        rows.append(
            AtlasEvidenceSpeciesRow(
                species_latin_name=species.latin_name,
                species_common_name=species.common_name,
                support_status=species.support_status,
                product_role=dataset_review.product_role,
                dataset_bucket=dataset_review.dataset_bucket,
                contribution_role=contribution_role,
                interaction_posture=interaction_posture,
                mapped_direct_record_count=len(species_localities),
                curated_project_count=dataset_review.curated_support_project_count,
                study_summary_count=len(normalization_bundle.study_summaries),
                chronology_posture=_chronology_posture_for(
                    normalization_bundle, species_localities
                ),
                geography_posture=_geography_posture_for(
                    normalization_bundle, species_localities
                ),
                contextual_layer_dependencies=context_layer_dependencies,
                blocking_reasons=dataset_review.blocking_reasons,
                rationale=_rationale_for(
                    species_name=species.latin_name,
                    contribution_role=contribution_role,
                    interaction_posture=interaction_posture,
                    has_human_direct=bool(human_localities),
                    normalization_bundle=normalization_bundle,
                    species_localities=species_localities,
                ),
            )
        )
    return tuple(sorted(rows, key=lambda row: row.species_latin_name))
