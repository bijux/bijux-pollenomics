"""Exact count eligibility without replacing missing values or source units."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math

from bijux_pollenomics.collection.sources.neotoma.relational.variables import (
    unit_family,
)
from bijux_pollenomics.core.text import clean_optional_text

from .models import canonical_bytes


@dataclass(frozen=True)
class CountAssessment:
    """Count semantics are necessary but not sufficient for LRA admission."""

    status: str
    reason: str | None
    exact_count: int | None
    source_value_status: str


def assess_count(row: Mapping[str, object]) -> CountAssessment:
    """Refuse noncounts, fractions, booleans and inconsistent source projections."""
    payload = row.get("source_payload")
    if not isinstance(payload, Mapping):
        return CountAssessment(
            "refused", "missing_source_payload", None, "unverifiable"
        )
    status = (
        "not_provided_by_source"
        if "value" not in payload
        else "source_null"
        if payload["value"] is None
        else "reported_value"
    )
    if (
        row.get("detection_status") != status
        or canonical_bytes(row.get("source_value"))
        != canonical_bytes(payload.get("value"))
        or canonical_bytes(row.get("source_unit"))
        != canonical_bytes(payload.get("units"))
    ):
        return CountAssessment(
            "refused", "inconsistent_source_projection", None, status
        )
    if status != "reported_value":
        return CountAssessment("refused", status, None, status)
    declared_unit = unit_family(clean_optional_text(row.get("source_unit")))
    if declared_unit != row.get("unit_family"):
        return CountAssessment("refused", "inconsistent_unit_family", None, status)
    if declared_unit != "count":
        return CountAssessment("refused", "source_unit_is_not_count", None, status)
    value = row.get("source_value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return CountAssessment("refused", "count_is_not_numeric", None, status)
    if isinstance(value, float) and (
        not math.isfinite(value) or not value.is_integer()
    ):
        return CountAssessment("refused", "count_is_not_finite_integer", None, status)
    if value < 0:
        return CountAssessment("refused", "negative_count", None, status)
    return CountAssessment("count_candidate", None, int(value), status)
