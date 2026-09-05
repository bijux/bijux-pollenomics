"""Chronological-bin coverage for human and animal evidence."""

from __future__ import annotations

from collections import defaultdict

from ...adna import AdnaLocalitySummary
from ..models import AtlasEvidenceSpeciesRow
from .models import SpeciesPeriodCoverageRow
from .temporal import _PERIOD_BINS, _period_label_for


def _build_period_coverage(
    *,
    direct_localities: tuple[AdnaLocalitySummary, ...],
    animal_localities: tuple[AdnaLocalitySummary, ...],
    species_rows: tuple[AtlasEvidenceSpeciesRow, ...],
) -> tuple[SpeciesPeriodCoverageRow, ...]:
    rows: list[SpeciesPeriodCoverageRow] = []
    grouped: dict[str, list[AdnaLocalitySummary]] = defaultdict(list)
    for locality in direct_localities:
        grouped[_period_label_for(locality)].append(locality)
    for label, _, _ in _PERIOD_BINS:
        rows.append(
            SpeciesPeriodCoverageRow(
                species_latin_name="Homo sapiens",
                period_label=label,
                evidence_scope="mapped_direct",
                mapped_locality_count=len(grouped.get(label, [])),
                contextual_project_count=0,
                chronology_confidence="locality_level_bp_window",
                caution_note="Human period coverage remains locality-based metadata, not genotype-aware chronology.",
            )
        )
    for row in species_rows:
        if row.species_latin_name == "Homo sapiens":
            continue
        species_animal_localities = tuple(
            locality
            for locality in animal_localities
            if locality.species_latin_name == row.species_latin_name
        )
        if species_animal_localities:
            grouped_animal: dict[str, list[AdnaLocalitySummary]] = defaultdict(list)
            for locality in species_animal_localities:
                grouped_animal[_period_label_for(locality)].append(locality)
            for period_label in sorted(grouped_animal):
                rows.append(
                    SpeciesPeriodCoverageRow(
                        species_latin_name=row.species_latin_name,
                        period_label=period_label,
                        evidence_scope="mapped_direct",
                        mapped_locality_count=len(grouped_animal[period_label]),
                        contextual_project_count=row.curated_project_count,
                        chronology_confidence=row.chronology_posture,
                        caution_note="Mapped animal chronology remains bounded by locality-lead precision and support-class caveats.",
                    )
                )
            continue
        rows.append(
            SpeciesPeriodCoverageRow(
                species_latin_name=row.species_latin_name,
                period_label="project_level_or_unresolved",
                evidence_scope=row.contribution_role,
                mapped_locality_count=0,
                contextual_project_count=row.curated_project_count,
                chronology_confidence=row.chronology_posture,
                caution_note="Non-human chronology is not yet resolved to mapped locality periods.",
            )
        )
    return tuple(rows)
