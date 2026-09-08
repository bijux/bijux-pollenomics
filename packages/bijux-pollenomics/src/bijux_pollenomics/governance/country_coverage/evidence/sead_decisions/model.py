"""Typed SEAD country-decision evidence."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SeadDecisionEvidence:
    """Reconciled counts and assignment digest from governed SEAD decisions."""

    decisions: list[Mapping[str, object]]
    governed: Counter[str]
    statuses: Counter[str]
    methods: Counter[str]
    country_codes: Counter[str]
    country_assignment_sha256: str


@dataclass(frozen=True, slots=True)
class ParsedSeadCountryDecision:
    """Validated fields needed for country-decision accounting."""

    site_id: int
    site_uuid: str
    latitude: float
    longitude: float
    status: str
    method: str
    country_code: str
    refusal_reason: object
