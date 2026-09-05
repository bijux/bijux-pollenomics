"""Explicit refusal records for unsupported atlas claims."""

from __future__ import annotations

from ..models import AtlasEvidenceRefusal, AtlasEvidenceSpeciesRow


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
