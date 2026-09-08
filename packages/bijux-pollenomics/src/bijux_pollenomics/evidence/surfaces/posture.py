"""Scientific posture derivation for species evidence."""

from __future__ import annotations

from ...adna import (
    AdnaLocalitySummary,
    AdnaSpeciesDatasetReview,
    AdnaSpeciesNormalizationBundle,
)


def _contribution_role_for(
    *,
    dataset_review: AdnaSpeciesDatasetReview,
    normalization_bundle: AdnaSpeciesNormalizationBundle,
    mapped_locality_count: int,
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
    dataset_review: AdnaSpeciesDatasetReview,
    normalization_bundle: AdnaSpeciesNormalizationBundle,
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
    normalization_bundle: AdnaSpeciesNormalizationBundle,
    species_localities: tuple[AdnaLocalitySummary, ...],
) -> str:
    if species_localities:
        if all(
            locality.time_start_bp is not None and locality.time_end_bp is not None
            for locality in species_localities
        ):
            return "mapped_locality_bp_windows_available"
        return "mapped_locality_points_with_partial_chronology"
    policies = {
        summary.chronology_policy for summary in normalization_bundle.project_summaries
    }
    if not policies:
        return "no_curated_nonhuman_chronology"
    if policies == {"bp_interval_expected"}:
        return "project_level_bp_capable_but_not_locality_bound"
    if "mixed_chronology_review_required" in policies:
        return "mixed_project_level_chronology"
    return "project_level_chronology_without_locality_alignment"


def _geography_posture_for(
    normalization_bundle: AdnaSpeciesNormalizationBundle,
    species_localities: tuple[AdnaLocalitySummary, ...],
) -> str:
    if species_localities:
        confidences = {
            locality.coordinate_confidence for locality in species_localities
        }
        if confidences == {"exact"}:
            return "mapped_locality_points"
        return "mapped_locality_points_with_mixed_precision"
    policies = {
        summary.coordinate_policy for summary in normalization_bundle.project_summaries
    }
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
    normalization_bundle: AdnaSpeciesNormalizationBundle,
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
