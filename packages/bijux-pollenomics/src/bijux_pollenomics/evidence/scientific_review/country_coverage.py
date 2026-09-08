"""Country-resolved human and animal evidence coverage."""

from __future__ import annotations

from ...adna import AdnaLocalitySummary
from ..models import AtlasEvidenceSpeciesRow
from .models import SpeciesCountryCoverageRow


def _build_country_coverage(
    *,
    countries: tuple[str, ...],
    direct_localities: tuple[AdnaLocalitySummary, ...],
    animal_localities: tuple[AdnaLocalitySummary, ...],
    species_rows: tuple[AtlasEvidenceSpeciesRow, ...],
) -> tuple[SpeciesCountryCoverageRow, ...]:
    rows: list[SpeciesCountryCoverageRow] = []
    for country in countries:
        country_direct = tuple(
            locality
            for locality in direct_localities
            if (locality.identity.political_entity or "").strip() == country
        )
        country_animal_localities = tuple(
            locality
            for locality in animal_localities
            if (locality.identity.political_entity or "").strip() == country
        )
        rows.append(
            SpeciesCountryCoverageRow(
                country=country,
                species_latin_name="Homo sapiens",
                evidence_scope="mapped_direct",
                mapped_locality_count=len(country_direct),
                contextual_project_count=0,
                assignment_confidence="country_filter_from_aadr_metadata",
                caution_note="Human country assignment is metadata-derived and remains separate from non-human context.",
            )
        )
        for row in species_rows:
            if row.species_latin_name == "Homo sapiens":
                continue
            species_country_localities = tuple(
                locality
                for locality in country_animal_localities
                if locality.species_latin_name == row.species_latin_name
            )
            rows.append(
                SpeciesCountryCoverageRow(
                    country=country,
                    species_latin_name=row.species_latin_name,
                    evidence_scope=(
                        "mapped_direct"
                        if species_country_localities
                        else row.contribution_role
                    ),
                    mapped_locality_count=len(species_country_localities),
                    contextual_project_count=row.curated_project_count,
                    assignment_confidence=(
                        "country_resolved_from_mapped_locality_rows"
                        if species_country_localities
                        else "not_country_assignable_from_current_runtime"
                    ),
                    caution_note=(
                        "Mapped animal locality rows remain cautionary leads and can still be approximate, regional, or comparator-only."
                        if species_country_localities
                        else "Current non-human support is species-level review context, not country-resolved locality evidence."
                    ),
                )
            )
    return tuple(rows)
