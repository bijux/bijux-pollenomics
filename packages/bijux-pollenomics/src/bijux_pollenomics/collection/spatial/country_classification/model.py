"""Country-attribution decision vocabulary and immutable result."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

COUNTRY_BOUNDARY_PROXIMITY_TOLERANCE = 0.15
BOUNDARY_CONTACT_EPSILON = 1e-12

CountryDecisionStatus: TypeAlias = Literal[
    "assigned", "review", "unassigned", "refused"
]
CountryDecisionMethod: TypeAlias = Literal[
    "strict_boundary_containment",
    "point_on_boundary",
    "multiple_boundary_containment",
    "boundary_proximity",
    "no_boundary_containment",
    "coordinate_validation",
]
RawCountryComparison: TypeAlias = Literal[
    "not_supplied", "agrees", "conflicts", "unresolved"
]


@dataclass(frozen=True)
class CountryAttributionDecision:
    """Auditable country-membership decision for one point and boundary artifact."""

    derived_country: str | None
    decision_status: CountryDecisionStatus
    decision_method: CountryDecisionMethod
    ambiguity_reason: str | None
    refusal_reason: str | None
    raw_country: str | None
    raw_country_comparison: RawCountryComparison
    candidate_countries: tuple[str, ...]
    boundary_artifact_digest: str
    boundary_version: str
