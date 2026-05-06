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
    context_points: Iterable[ContextPointRecord],
) -> AtlasEvidenceSurface:
    """Build the atlas evidence contract without overstating non-human spatial support."""
    human_locality_rows = tuple(human_localities)
    context_records = tuple(context_points)
    nonhuman_rows = _build_nonhuman_species_rows(
        human_localities=human_locality_rows,
        context_points=context_records,
    )
    layers = _build_atlas_layers(
        human_localities=human_locality_rows,
        context_points=context_records,
        nonhuman_rows=nonhuman_rows,
    )
    country_profiles = _build_country_profiles(
        countries=countries,
        human_localities=human_locality_rows,
        nonhuman_rows=nonhuman_rows,
    )
    refusals = _build_refusals(nonhuman_rows)
    human_row = _build_human_species_row(
        human_localities=human_locality_rows,
        context_points=context_records,
    )
    return AtlasEvidenceSurface(
        schema_version="atlas-evidence-surface.v1",
        countries=tuple(countries),
        layers=layers,
        species_rows=(human_row, *nonhuman_rows),
        country_profiles=country_profiles,
        refusals=refusals,
        north_star_boundary=(
            "Mapped Homo sapiens localities are direct atlas evidence. Non-human "
            "ancient-DNA support currently remains project and study review context "
            "unless species-owned sample or locality records exist with defensible "
            "geography and chronology."
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
        contribution_role = _contribution_role_for(
            dataset_review=dataset_review,
            normalization_bundle=normalization_bundle,
        )
        interaction_posture = _interaction_posture_for(
            contribution_role=contribution_role,
            dataset_review=dataset_review,
            normalization_bundle=normalization_bundle,
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
                mapped_direct_record_count=(
                    len(normalization_bundle.sample_records)
                    + len(normalization_bundle.locality_records)
                ),
                curated_project_count=dataset_review.curated_support_project_count,
                study_summary_count=len(normalization_bundle.study_summaries),
                chronology_posture=_chronology_posture_for(normalization_bundle),
                geography_posture=_geography_posture_for(normalization_bundle),
                contextual_layer_dependencies=context_layer_dependencies,
                blocking_reasons=dataset_review.blocking_reasons,
                rationale=_rationale_for(
                    species_name=species.latin_name,
                    contribution_role=contribution_role,
                    interaction_posture=interaction_posture,
                    has_human_direct=bool(human_localities),
                    normalization_bundle=normalization_bundle,
                ),
            )
        )
    return tuple(sorted(rows, key=lambda row: row.species_latin_name))


def _contribution_role_for(*, dataset_review, normalization_bundle) -> str:
    if normalization_bundle.sample_records or normalization_bundle.locality_records:
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
    has_human_direct: bool,
    has_time_aware_context: bool,
) -> str:
    if contribution_role == "too_weak":
        return "refused"
    if contribution_role == "direct":
        return "increases_confidence"
    blocking = set(dataset_review.blocking_reasons)
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


def _chronology_posture_for(normalization_bundle) -> str:
    policies = {summary.chronology_policy for summary in normalization_bundle.project_summaries}
    if not policies:
        return "no_curated_nonhuman_chronology"
    if policies == {"bp_interval_expected"}:
        return "project_level_bp_capable_but_not_locality_bound"
    if "mixed_chronology_review_required" in policies:
        return "mixed_project_level_chronology"
    return "project_level_chronology_without_locality_alignment"


def _geography_posture_for(normalization_bundle) -> str:
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
) -> tuple[str, ...]:
    lines = []
    if contribution_role == "direct":
        lines.append(
            "This species has runtime-owned sample or locality records and can act as direct atlas evidence."
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
    if any(
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
    context_points: tuple[ContextPointRecord, ...],
    nonhuman_rows: tuple[AtlasEvidenceSpeciesRow, ...],
) -> tuple[AtlasEvidenceLayer, ...]:
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
                "This is the only atlas layer that currently carries direct mapped ancient-DNA evidence.",
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
                "Animal aDNA is currently curated at project and study level and therefore remains an atlas-side review surface.",
                "No implied locality overlap is allowed until species-owned sample or locality records are published.",
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
        human_sample_count = sum(locality.sample_count for locality in country_localities)
        if country_localities and contextual_species:
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
                mapped_direct_species=("Homo sapiens",) if country_localities else (),
                unmapped_animal_context_species=contextual_species,
                too_weak_animal_species=too_weak_species,
                human_locality_count=len(country_localities),
                human_sample_count=human_sample_count,
                evidence_posture=evidence_posture,
                caution_note=(
                    "Animal aDNA remains atlas-wide unmapped context unless species-owned locality rows exist. "
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
        if row.chronology_posture != "project_level_bp_capable_but_not_locality_bound":
            refusals.append(
                AtlasEvidenceRefusal(
                    subject=row.species_latin_name,
                    reason="animal_context_cannot_be_time_aligned_to_localities",
                    detail=(
                        "Project-level chronology is not specific enough to claim temporal alignment "
                        "with atlas localities or environmental layers."
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
