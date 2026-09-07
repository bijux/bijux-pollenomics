"""Denominator validation for reconciled European cat evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol


class ReconciledCatRow(Protocol):
    """Fields required to validate one reconciled cat row."""

    reconciliation_status: str
    political_entity: str
    chronology_evidence_class: str
    coordinate_admission_status: str
    archive_native_sample_id: str


def validate_reconciliation(
    rows: Sequence[ReconciledCatRow],
    *,
    expected_ancient_countries: Mapping[str, int],
    expected_unresolved: frozenset[str],
) -> None:
    """Validate status, country, chronology, coordinate, and refusal counts."""
    status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row.reconciliation_status] = (
            status_counts.get(row.reconciliation_status, 0) + 1
        )
    _require(
        status_counts
        == {
            "exact_ancient": 70,
            "exact_modern_context": 14,
            "unresolved_identifier_conflict": 3,
        },
        "European cat reconciliation denominator drift",
    )
    ancient = tuple(row for row in rows if row.reconciliation_status == "exact_ancient")
    country_counts: dict[str, int] = {}
    for row in ancient:
        country_counts[row.political_entity] = (
            country_counts.get(row.political_entity, 0) + 1
        )
    _require(
        country_counts == expected_ancient_countries,
        "ancient country denominator drift",
    )
    _require(
        sum(
            row.chronology_evidence_class == "direct_radiocarbon_date"
            for row in ancient
        )
        == 37,
        "radiocarbon chronology denominator drift",
    )
    _require(
        sum(
            row.chronology_evidence_class == "archaeological_context_date"
            for row in ancient
        )
        == 33,
        "archaeological chronology denominator drift",
    )
    _require(
        sum(
            row.coordinate_admission_status == "source_reported_pair_admitted"
            for row in ancient
        )
        == 56,
        "admitted coordinate denominator drift",
    )
    _require(
        sum(
            row.coordinate_admission_status == "withheld_coordinate_order_anomaly"
            for row in ancient
        )
        == 14,
        "coordinate-order refusal denominator drift",
    )
    _require(
        {
            row.archive_native_sample_id
            for row in rows
            if row.reconciliation_status.startswith("unresolved")
        }
        == expected_unresolved,
        "identifier-conflict set drift",
    )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)
