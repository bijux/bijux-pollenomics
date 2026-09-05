"""Dispatch and derive governed country reconciliation postures."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import cast

from ...release_evidence.models import _COUNTRIES, _RequiredReconciliation
from .chronology import sead_chronology_claim_values
from .classification import classification_country_values
from .json_object import optional_json_object
from .model import DerivedCount


def governed_country_values(
    root: Path, requirement: _RequiredReconciliation
) -> dict[str, DerivedCount] | None:
    """Dispatch a country reconciliation to its governed source adapter."""
    if requirement.derivation_adapter == "classification_observation_memberships":
        return classification_country_values(root, requirement.derivation_metric)
    if requirement.derivation_adapter == "sead_chronology_claims":
        return sead_chronology_claim_values(root, requirement.derivation_metric)
    if requirement.derivation_adapter == "unavailable":
        return None
    if requirement.derivation_adapter == "neotoma_relational_reconciliation":
        document = optional_json_object(
            root, "data/neotoma/relational/reconciliation.json"
        )
        reconciliation = document.get("reconciliation") if document else None
        country_counts = (
            reconciliation.get("country_counts")
            if isinstance(reconciliation, Mapping)
            else None
        )
        if isinstance(country_counts, Mapping):
            values: dict[str, DerivedCount] = {}
            for country in _COUNTRIES:
                if country == "OUTSIDE":
                    values[country] = partition_posture(country, 0, ())
                    continue
                record = country_counts.get(country)
                value = (
                    record.get(requirement.derivation_metric)
                    if isinstance(record, Mapping)
                    else None
                )
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    return None
                values[country] = partition_posture(country, value, ())
            return values
    if requirement.derivation_adapter != "country_coverage":
        return None
    ledger = optional_json_object(root, "data/country_dimension_coverage.json")
    cells = ledger.get("cells") if ledger else None
    if not isinstance(cells, list):
        return None
    values = {}
    for country in _COUNTRIES:
        matches = [
            cell
            for cell in cells
            if isinstance(cell, Mapping)
            and cell.get("source_family") == requirement.source
            and cell.get("country_dimension") == "governed_assignment"
            and cell.get("resolution") == "source"
            and cell.get("country_code") == country
        ]
        if len(matches) != 1:
            return None
        cell = matches[0]
        counts = cell.get("counts")
        value = (
            counts.get(requirement.derivation_metric)
            if isinstance(counts, Mapping)
            else None
        )
        reason_codes = cell.get("reason_codes")
        if (
            value is None
            and isinstance(counts, Mapping)
            and counts.get("sites") == 0
            and reason_codes == ["explicit_empty_partition"]
        ):
            value = 0
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return None
        if not isinstance(reason_codes, list) or any(
            not isinstance(item, str) for item in reason_codes
        ):
            return None
        values[country] = partition_posture(
            country, value, tuple(sorted(cast(list[str], reason_codes)))
        )
    return values


def partition_posture(
    country: str, value: int, reason_codes: tuple[str, ...]
) -> DerivedCount:
    """Map governed partition identity to its terminal count posture."""
    if country == "UNASSIGNED":
        return DerivedCount(value, 0, 0, value, 0, 0, reason_codes)
    if country == "OUTSIDE":
        return DerivedCount(value, 0, 0, 0, value, 0, reason_codes)
    return DerivedCount(value, value, value, 0, 0, 0, reason_codes)
