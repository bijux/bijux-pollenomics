"""Reconcile governed classification concepts by country."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import cast

from ...release_evidence.models import _COUNTRIES
from .json_object import optional_json_object
from .model import DerivedCount


def classification_country_values(
    root: Path, metric: str
) -> dict[str, DerivedCount] | None:
    """Derive distinct classification-concept posture for each country."""
    bundle = "artifacts/execution-control/classification/neotoma-audit-dde3936c"
    document = optional_json_object(root, f"{bundle}/observation_memberships.json")
    records = document.get("records") if document else None
    if not isinstance(records, list):
        return None
    concept_memberships: dict[str, dict[str, set[str]]] = {
        country: {
            "accepted": set(),
            "unresolved": set(),
            "excluded": set(),
            "refused": set(),
        }
        for country in _COUNTRIES
    }
    for record in records:
        if not isinstance(record, Mapping):
            return None
        country = record.get("governed_country_code")
        concept = record.get("classification_concept_id")
        status = record.get("mapping_status")
        if country not in concept_memberships or not isinstance(concept, str):
            return None
        bucket: str | None
        if status in {"accepted", "accepted_qualified"}:
            bucket = "accepted"
        elif status == "unmapped" or status == "contested":
            bucket = "unresolved"
        elif status == "not_applicable":
            bucket = "excluded"
        elif status == "refused":
            bucket = "refused"
        else:
            return None
        selected = (
            metric == "distinct_concepts"
            or (metric == "mapped_concepts" and bucket == "accepted")
            or (metric == "unmapped_concepts" and status == "unmapped")
            or (metric == "ambiguous_concepts" and status in {"contested", "refused"})
        )
        if selected:
            concept_memberships[cast(str, country)][bucket].add(concept)
    return {
        country: DerivedCount(
            candidate=sum(len(concepts) for concepts in parts.values()),
            eligible=len(parts["accepted"]) + len(parts["refused"]),
            accepted=len(parts["accepted"]),
            unresolved=len(parts["unresolved"]),
            excluded=len(parts["excluded"]),
            refused=len(parts["refused"]),
        )
        for country, parts in concept_memberships.items()
    }
