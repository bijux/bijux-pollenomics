from __future__ import annotations

from ....geography import (
    REGIONAL_COUNTRY_ASSIGNMENTS,
    TERRITORY_COUNTRY_ASSIGNMENTS,
)
from ...atlas_evidence_rows import AnimalAtlasEvidenceRow


def assign_evidence_row_to_country(
    row: AnimalAtlasEvidenceRow,
    country: str,
) -> dict[str, str] | None:
    political_entity = row.political_entity.strip()
    if not row.nordic_inclusion:
        return None
    if political_entity == country:
        return {
            "confidence": "exact_country",
            "reason": f"The tracked locality lead is already labeled `{country}`.",
        }
    territory_owner = TERRITORY_COUNTRY_ASSIGNMENTS.get(political_entity)
    if territory_owner == country:
        return {
            "confidence": "territory_projection",
            "reason": (
                f"The tracked locality lead is labeled `{political_entity}` and is "
                f"published under `{country}` as an explicit territorial projection."
            ),
        }
    regional_countries = REGIONAL_COUNTRY_ASSIGNMENTS.get(political_entity, ())
    if country in regional_countries:
        return {
            "confidence": "regional_projection",
            "reason": (
                f"The tracked locality lead is labeled `{political_entity}` and is "
                f"published under `{country}` as a regional Baltic projection, not "
                "a country-exact excavation."
            ),
        }
    return None


def assignment_sort_key(confidence: str) -> int:
    order = {
        "exact_country": 0,
        "territory_projection": 1,
        "regional_projection": 2,
    }
    return order.get(confidence, 9)
