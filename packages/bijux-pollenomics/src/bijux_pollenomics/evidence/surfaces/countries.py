"""Country-accountability projections for atlas evidence."""

from __future__ import annotations

from ...adna import AdnaLocalitySummary
from ..models import AtlasEvidenceCountryProfile, AtlasEvidenceSpeciesRow


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
            sorted(
                {locality.species_latin_name for locality in animal_country_localities}
            )
        )
        human_sample_count = sum(
            locality.sample_count for locality in country_localities
        )
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
