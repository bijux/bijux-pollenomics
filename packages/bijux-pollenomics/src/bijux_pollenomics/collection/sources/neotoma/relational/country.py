"""Country evidence and propagation posture for relational Neotoma rows."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import TypeAlias

from .....core.text import clean_optional_text
from ....spatial import CountryAttributionDecision
from .contracts import COUNTRY_NAMES_TO_CODES

CountryAttributionInput: TypeAlias = CountryAttributionDecision | str


@dataclass(frozen=True)
class NeotomaCountryAttribution:
    raw_country: str | None
    derived_country: str | None
    final_country_code: str
    decision_status: str
    decision_method: str
    candidate_countries: tuple[str, ...]
    ambiguity_reason: str | None
    refusal_reason: str | None
    boundary_artifact_digest: str | None
    boundary_version: str | None
    source_vs_derived_comparison: str
    propagation_eligible: bool


def country_code(value: str) -> str:
    cleaned = clean_optional_text(value)
    normalized_code = cleaned.upper()
    if normalized_code in {"SE", "DK", "NO", "FI"}:
        return normalized_code
    normalized_name = cleaned.casefold()
    return next(
        (
            code
            for name, code in COUNTRY_NAMES_TO_CODES.items()
            if name.casefold() == normalized_name
        ),
        "UNASSIGNED",
    )


def country_attribution(value: CountryAttributionInput) -> NeotomaCountryAttribution:
    if isinstance(value, str):
        legacy_country = clean_optional_text(value)
        return NeotomaCountryAttribution(
            raw_country=None,
            derived_country=legacy_country or None,
            final_country_code="UNASSIGNED",
            decision_status="review",
            decision_method="legacy_unproven_country_string",
            candidate_countries=(legacy_country,) if legacy_country else (),
            ambiguity_reason="legacy_country_string_without_boundary_provenance",
            refusal_reason=None if legacy_country else "empty_legacy_country_string",
            boundary_artifact_digest=None,
            boundary_version=None,
            source_vs_derived_comparison="unresolved",
            propagation_eligible=False,
        )
    if not isinstance(value, CountryAttributionDecision):
        raise TypeError(
            "country_by_site_id values must be CountryAttributionDecision or str"
        )
    derived_code = country_code(value.derived_country or "")
    propagation_eligible = (
        value.decision_status == "assigned"
        and value.decision_method == "strict_boundary_containment"
        and value.raw_country_comparison != "conflicts"
        and derived_code != "UNASSIGNED"
    )
    return NeotomaCountryAttribution(
        raw_country=value.raw_country,
        derived_country=value.derived_country,
        final_country_code=derived_code if propagation_eligible else "UNASSIGNED",
        decision_status=value.decision_status,
        decision_method=value.decision_method,
        candidate_countries=value.candidate_countries,
        ambiguity_reason=value.ambiguity_reason,
        refusal_reason=value.refusal_reason,
        boundary_artifact_digest=value.boundary_artifact_digest,
        boundary_version=value.boundary_version,
        source_vs_derived_comparison=value.raw_country_comparison,
        propagation_eligible=propagation_eligible,
    )


def missing_country_attribution(
    site: Mapping[str, object],
) -> NeotomaCountryAttribution:
    return NeotomaCountryAttribution(
        raw_country=source_country(site),
        derived_country=None,
        final_country_code="UNASSIGNED",
        decision_status="unassigned",
        decision_method="missing_country_decision",
        candidate_countries=(),
        ambiguity_reason=None,
        refusal_reason="missing_country_decision",
        boundary_artifact_digest=None,
        boundary_version=None,
        source_vs_derived_comparison="unresolved",
        propagation_eligible=False,
    )


def with_source_country(
    attribution: NeotomaCountryAttribution,
    site: Mapping[str, object],
) -> NeotomaCountryAttribution:
    observed_country = source_country(site)
    if observed_country is None:
        return attribution
    if attribution.raw_country is not None and country_code(
        attribution.raw_country
    ) != country_code(observed_country):
        raise ValueError("Country decision raw country conflicts with Neotoma source")
    return replace(attribution, raw_country=observed_country)


def source_country(site: Mapping[str, object]) -> str | None:
    geopolitical = site.get("geopolitical")
    if not isinstance(geopolitical, list):
        return None
    candidates: set[str] = set()
    for value in geopolitical:
        if isinstance(value, Mapping):
            candidate = clean_optional_text(value.get("country"))
        else:
            candidate = clean_optional_text(value)
        if country_code(candidate) != "UNASSIGNED":
            candidates.add(candidate)
    if len(candidates) != 1:
        return None
    return candidates.pop()


def country_attribution_counts(
    sites: list[dict[str, object]],
) -> dict[str, dict[str, int]]:
    raw_country_values: Counter[str] = Counter()
    derived_country_values: Counter[str] = Counter()
    raw_countries: Counter[str] = Counter()
    derived_countries: Counter[str] = Counter()
    final_countries: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    methods: Counter[str] = Counter()
    comparisons: Counter[str] = Counter()
    eligibility: Counter[str] = Counter()
    for site in sites:
        raw_country_values[str(site.get("raw_country") or "UNASSIGNED")] += 1
        derived_country_values[str(site.get("derived_country") or "UNASSIGNED")] += 1
        raw_countries[country_code(str(site.get("raw_country") or ""))] += 1
        derived_countries[country_code(str(site.get("derived_country") or ""))] += 1
        final_countries[str(site.get("country_code", "UNASSIGNED"))] += 1
        statuses[str(site.get("country_decision_status", "unassigned"))] += 1
        methods[str(site.get("country_decision_method", "unknown"))] += 1
        comparisons[str(site.get("source_vs_derived_comparison", "unresolved"))] += 1
        eligibility[
            "eligible"
            if site.get("country_propagation_eligible") is True
            else "blocked"
        ] += 1
    return {
        "raw_country_values": dict(sorted(raw_country_values.items())),
        "derived_country_values": dict(sorted(derived_country_values.items())),
        "raw_country_codes": dict(sorted(raw_countries.items())),
        "derived_country_codes": dict(sorted(derived_countries.items())),
        "final_country_codes": dict(sorted(final_countries.items())),
        "decision_statuses": dict(sorted(statuses.items())),
        "decision_methods": dict(sorted(methods.items())),
        "source_vs_derived_comparisons": dict(sorted(comparisons.items())),
        "propagation_eligibility": dict(sorted(eligibility.items())),
    }
