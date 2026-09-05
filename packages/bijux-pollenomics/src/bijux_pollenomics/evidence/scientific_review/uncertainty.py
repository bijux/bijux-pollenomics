"""Explicit uncertainty assessment for scientific evidence."""

from __future__ import annotations

from ...adna import AdnaLocalitySummary
from ..models import AtlasEvidenceSpeciesRow
from .models import EvidenceUncertaintyRow


def _build_uncertainties(
    *,
    direct_localities: tuple[AdnaLocalitySummary, ...],
    animal_localities: tuple[AdnaLocalitySummary, ...],
    species_rows: tuple[AtlasEvidenceSpeciesRow, ...],
) -> tuple[EvidenceUncertaintyRow, ...]:
    rows: list[EvidenceUncertaintyRow] = []
    for row in species_rows:
        if row.species_latin_name != "Homo sapiens":
            species_animal_localities = tuple(
                locality
                for locality in animal_localities
                if locality.species_latin_name == row.species_latin_name
            )
            rows.append(
                EvidenceUncertaintyRow(
                    subject=row.species_latin_name,
                    uncertainty_kind="species_assignment",
                    severity=(
                        "high"
                        if "mixed_species_rule_unresolved" in row.blocking_reasons
                        else "medium"
                    ),
                    reason="nonhuman support remains species-review context or mixed-species blocked",
                    impact="cross-species comparisons cannot be promoted to locality-level inference safely",
                )
            )
            rows.append(
                EvidenceUncertaintyRow(
                    subject=row.species_latin_name,
                    uncertainty_kind="locality_precision",
                    severity=("medium" if species_animal_localities else "high"),
                    reason=row.geography_posture,
                    impact=(
                        "mapped animal atlas points remain useful but must keep their coordinate and regional caveats visible"
                        if species_animal_localities
                        else "country or atlas placement for animal evidence would overstate runtime geography support"
                    ),
                )
            )
            rows.append(
                EvidenceUncertaintyRow(
                    subject=row.species_latin_name,
                    uncertainty_kind="date_precision",
                    severity="medium",
                    reason=row.chronology_posture,
                    impact=(
                        "mapped animal localities support chronology comparison only within the explicit BP and caveat bounds"
                        if species_animal_localities
                        else "animal evidence cannot yet support locality-aligned chronology claims"
                    ),
                )
            )
    if any(locality.coordinate_confidence != "exact" for locality in direct_localities):
        rows.append(
            EvidenceUncertaintyRow(
                subject="Homo sapiens",
                uncertainty_kind="locality_precision",
                severity="low",
                reason="some mapped human localities rely on approximate or inferred coordinates",
                impact="descriptive maps remain valid but should not be treated as exact site centroids automatically",
            )
        )
    return tuple(rows)
