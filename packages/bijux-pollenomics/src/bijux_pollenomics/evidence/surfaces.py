from __future__ import annotations

from collections.abc import Iterable

from ..adna import (
    AdnaLocalitySummary,
    build_species_dataset_review,
    build_species_normalization_bundle,
    build_species_support_matrix,
)
from ..data_downloader.models import ContextPointRecord
from .models import (
    AtlasEvidenceCountryProfile,
    AtlasEvidenceLayer,
    AtlasEvidenceRefusal,
    AtlasEvidenceSpeciesRow,
    AtlasEvidenceSurface,
)

__all__ = ["build_atlas_evidence_surface"]


def build_atlas_evidence_surface(
    *,
    countries: tuple[str, ...],
    human_localities: Iterable[AdnaLocalitySummary],
    animal_localities: Iterable[AdnaLocalitySummary] = (),
    context_points: Iterable[ContextPointRecord],
) -> AtlasEvidenceSurface:
    """Build the atlas evidence contract without overstating animal locality claims."""
    human_locality_rows = tuple(human_localities)
    animal_locality_rows = tuple(animal_localities)
    context_records = tuple(context_points)
    nonhuman_rows = _build_nonhuman_species_rows(
        human_localities=human_locality_rows,
        animal_localities=animal_locality_rows,
        context_points=context_records,
    )
    layers = _build_atlas_layers(
        human_localities=human_locality_rows,
        animal_localities=animal_locality_rows,
        context_points=context_records,
        nonhuman_rows=nonhuman_rows,
    )
    country_profiles = _build_country_profiles(
        countries=countries,
        human_localities=human_locality_rows,
        animal_localities=animal_locality_rows,
        nonhuman_rows=nonhuman_rows,
    )
    refusals = _build_refusals(nonhuman_rows)
    human_row = _build_human_species_row(
        human_localities=human_locality_rows,
        context_points=context_records,
    )
    return AtlasEvidenceSurface(
        schema_version="atlas-evidence-surface.v2",
        countries=tuple(countries),
        layers=layers,
        species_rows=(human_row, *nonhuman_rows),
        country_profiles=country_profiles,
        refusals=refusals,
        north_star_boundary=(
            "Mapped Homo sapiens localities are direct atlas evidence. Non-human "
            "ancient-DNA support becomes direct atlas evidence only where tracked "
            "species-owned locality rows exist. Approximate coordinates, regional "
            "leads, comparator species, and mixed-species claims still require "
            "explicit caution."
        ),
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
        interaction_posture="increases_confidence" if context_points else "suggestive_only",
        mapped_direct_record_count=len(human_localities),
        curated_project_count=0,
        study_summary_count=0,
        chronology_posture="mapped_sample_chronology_available",
        geography_posture="mapped_locality_points",
        contextual_layer_dependencies=tuple(sorted({point.layer_key for point in context_points})),
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
) -> tuple[AtlasEvidenceSpeciesRow, ...]:
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


def _contribution_role_for(
    *, dataset_review, normalization_bundle, mapped_locality_count: int
) -> str:
    if mapped_locality_count or normalization_bundle.sample_records:
        return "direct"
    if (
        dataset_review.product_role in {"domesticated_core", "comparator"}
        and normalization_bundle.project_summaries
    ):
        if dataset_review.curated_support_project_count > 0:
            return "contextual"
        if dataset_review.dataset_bucket == "comparator_only":
            return "contextual"
    return "too_weak"


def _interaction_posture_for(
    *,
    contribution_role: str,
    dataset_review,
    normalization_bundle,
    mapped_locality_count: int,
    has_human_direct: bool,
    has_time_aware_context: bool,
) -> str:
    blocking = set(dataset_review.blocking_reasons)
    if contribution_role == "too_weak":
        return "refused"
    if contribution_role == "direct":
        if "mixed_species_rule_unresolved" in blocking:
            return "decreases_confidence"
        if "restricted_or_delayed_archive_projects" in blocking:
            return "decreases_confidence"
        if mapped_locality_count and has_time_aware_context:
            return "increases_confidence"
        if not has_human_direct:
            return "suggestive_only"
        return "increases_confidence"
    if "mixed_species_rule_unresolved" in blocking:
        return "decreases_confidence"
    if "restricted_or_delayed_archive_projects" in blocking:
        return "decreases_confidence"
    if not has_human_direct:
        return "suggestive_only"
    if not has_time_aware_context:
        return "suggestive_only"
    if any(
        summary.chronology_policy
        in {
            "manual_chronology_review_required",
            "mixed_chronology_review_required",
            "historical_interval_or_label_allowed",
            "archaeological_period_label_allowed",
        }
        for summary in normalization_bundle.project_summaries
    ):
        return "suggestive_only"
    return "suggestive_only"


def _chronology_posture_for(
    normalization_bundle,
    species_localities: tuple[AdnaLocalitySummary, ...],
) -> str:
    if species_localities:
        if all(
            locality.time_start_bp is not None and locality.time_end_bp is not None
            for locality in species_localities
        ):
            return "mapped_locality_bp_windows_available"
        return "mapped_locality_points_with_partial_chronology"
    policies = {summary.chronology_policy for summary in normalization_bundle.project_summaries}
    if not policies:
        return "no_curated_nonhuman_chronology"
    if policies == {"bp_interval_expected"}:
        return "project_level_bp_capable_but_not_locality_bound"
    if "mixed_chronology_review_required" in policies:
        return "mixed_project_level_chronology"
    return "project_level_chronology_without_locality_alignment"


def _geography_posture_for(
    normalization_bundle,
    species_localities: tuple[AdnaLocalitySummary, ...],
) -> str:
    if species_localities:
        confidences = {locality.coordinate_confidence for locality in species_localities}
        if confidences == {"exact"}:
            return "mapped_locality_points"
        return "mapped_locality_points_with_mixed_precision"
    policies = {summary.coordinate_policy for summary in normalization_bundle.project_summaries}
    if not policies:
        return "no_curated_nonhuman_geography"
    if policies == {"site_level_coordinates_expected"}:
        return "project_level_sites_known_but_not_runtime_mapped"
    if "country_only_withheld_coordinates_allowed" in policies:
        return "country_only_or_withheld_nonhuman_geography"
    return "project_level_geography_requires_manual_review"


def _rationale_for(
    *,
    species_name: str,
    contribution_role: str,
    interaction_posture: str,
    has_human_direct: bool,
    normalization_bundle,
    species_localities: tuple[AdnaLocalitySummary, ...],
) -> tuple[str, ...]:
    lines = []
    if contribution_role == "direct":
        lines.append(
            "This species now has tracked mapped locality rows and can act as direct atlas evidence with explicit locality caveats."
        )
        if any(not locality.nordic_inclusion for locality in species_localities):
            lines.append(
                "Some mapped animal leads remain non-Nordic or comparator context and should not be flattened into Nordic domestication claims."
            )
    elif contribution_role == "contextual":
        lines.append(
            "This species contributes as contextual review evidence because the runtime owns curated projects and studies, not mapped sample rows."
        )
        lines.append(
            "Atlas proximity must not be read as co-localized animal evidence until species-owned locality rows exist."
        )
    else:
        lines.append(
            "This species remains too weak for atlas contribution because curation or archive proof is still incomplete."
        )
    if not has_human_direct:
        lines.append(
            "No mapped Homo sapiens direct evidence was available, so species interaction stays suggestive at best."
        )
    if contribution_role != "direct" and any(
        summary.coordinate_policy != "site_level_coordinates_expected"
        for summary in normalization_bundle.project_summaries
    ):
        lines.append(
            "Non-human geography is still project-level or withheld, so map-level locality claims would overstate the data."
        )
    if interaction_posture == "decreases_confidence":
        lines.append(
            "Current blocking reasons reduce confidence rather than strengthening the atlas narrative."
        )
    if species_name == "Bos taurus":
        lines.append(
            "Cattle remains under a mixed-species rule, so wild or progenitor context cannot be flattened into domesticated-core support."
        )
    return tuple(lines)


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
            rationale=(
                "This is the mapped Homo sapiens direct ancient-DNA layer.",
            ),
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


def _build_country_profiles(
    *,
    countries: tuple[str, ...],
    human_localities: tuple[AdnaLocalitySummary, ...],
    animal_localities: tuple[AdnaLocalitySummary, ...],
    nonhuman_rows: tuple[AtlasEvidenceSpeciesRow, ...],
) -> tuple[AtlasEvidenceCountryProfile, ...]:
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
    profiles: list[AtlasEvidenceCountryProfile] = []
    for country in countries:
        country_localities = tuple(
            locality
            for locality in human_localities
            if (locality.identity.political_entity or "").strip() == country
        )
        animal_country_localities = tuple(
            locality
            for locality in animal_localities
            if (locality.identity.political_entity or "").strip() == country
        )
        mapped_animal_species = tuple(
            sorted({locality.species_latin_name for locality in animal_country_localities})
        )
        human_sample_count = sum(locality.sample_count for locality in country_localities)
        if country_localities and mapped_animal_species:
            evidence_posture = "human_direct_plus_mapped_animal_direct"
        elif mapped_animal_species:
            evidence_posture = "mapped_animal_direct_only"
        elif country_localities and contextual_species:
            evidence_posture = "human_direct_plus_unmapped_animal_context"
        elif country_localities:
            evidence_posture = "human_only_direct"
        elif contextual_species:
            evidence_posture = "animal_only_unmapped_context"
        elif too_weak_species:
            evidence_posture = "too_weak_only"
        else:
            evidence_posture = "no_curated_evidence"
        profiles.append(
            AtlasEvidenceCountryProfile(
                country=country,
                mapped_direct_species=(
                    ("Homo sapiens", *mapped_animal_species)
                    if country_localities
                    else mapped_animal_species
                ),
                mapped_animal_direct_species=mapped_animal_species,
                unmapped_animal_context_species=contextual_species,
                too_weak_animal_species=too_weak_species,
                human_locality_count=len(country_localities),
                human_sample_count=human_sample_count,
                mapped_animal_locality_count=len(animal_country_localities),
                evidence_posture=evidence_posture,
                caution_note=(
                    "Mapped animal localities can now appear in the atlas, but many remain approximate, regional, comparator-only, or not country-resolved. "
                    "Do not read this profile as excavation-grade support without the popup caveats."
                    if mapped_animal_species
                    else "Animal aDNA remains atlas-wide unmapped context unless species-owned locality rows exist. "
                    "This country profile must not be read as country-assigned animal support."
                ),
            )
        )
    return tuple(profiles)


def _build_refusals(
    rows: tuple[AtlasEvidenceSpeciesRow, ...],
) -> tuple[AtlasEvidenceRefusal, ...]:
    refusals: list[AtlasEvidenceRefusal] = []
    for row in rows:
        if row.contribution_role == "contextual":
            refusals.append(
                AtlasEvidenceRefusal(
                    subject=row.species_latin_name,
                    reason="atlas_proximity_is_not_locality_evidence",
                    detail=(
                        "Curated animal project support cannot be promoted to mapped locality evidence "
                        "without species-owned sample or locality records."
                    ),
                )
            )
        if (
            row.contribution_role == "direct"
            and row.chronology_posture != "mapped_locality_bp_windows_available"
        ):
            refusals.append(
                AtlasEvidenceRefusal(
                    subject=row.species_latin_name,
                    reason="mapped_animal_chronology_requires_caution",
                    detail=(
                        "Mapped animal localities exist, but their chronology remains too partial or mixed to support strong time-alignment claims."
                    ),
                )
            )
        if (
            row.contribution_role == "direct"
            and row.geography_posture != "mapped_locality_points"
        ):
            refusals.append(
                AtlasEvidenceRefusal(
                    subject=row.species_latin_name,
                    reason="mapped_animal_geography_requires_caution",
                    detail=(
                        "Mapped animal localities remain approximate, inferred, or regional and must keep their visible caveat warnings."
                    ),
                )
            )
        if row.contribution_role == "too_weak":
            refusals.append(
                AtlasEvidenceRefusal(
                    subject=row.species_latin_name,
                    reason="species_support_too_thin_for_atlas_promotion",
                    detail="Current curation and archive evidence are not strong enough to count as atlas support.",
                )
            )
    return tuple(refusals)
