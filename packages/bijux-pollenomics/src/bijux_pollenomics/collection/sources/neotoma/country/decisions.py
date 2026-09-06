from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable, Mapping
from dataclasses import replace

from bijux_pollenomics.collection.spatial import (
    CountryAttributionDecision,
    decide_country_attribution,
)
from bijux_pollenomics.core.text import clean_optional_text

from .site_geometry import neotoma_site_representative_point

_CONTENT_ADDRESSED_BOUNDARY_VERSION = "content-addressed-boundary-collection"


def build_neotoma_context_country_decisions(
    rows: Iterable[Mapping[str, object]],
    country_boundaries: Mapping[str, Mapping[str, object]],
    *,
    raw_country_aliases: Mapping[str, str] | None = None,
    proximity_tolerance: float = 0.15,
) -> dict[str, CountryAttributionDecision]:
    """Build governed map decisions from a content-addressed boundary collection."""
    serialized_boundaries = json.dumps(
        country_boundaries,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    boundary_digest = hashlib.sha256(serialized_boundaries).hexdigest()
    return build_neotoma_site_country_decisions(
        rows,
        country_boundaries,
        boundary_artifact_digest=f"sha256:{boundary_digest}",
        boundary_version=_CONTENT_ADDRESSED_BOUNDARY_VERSION,
        raw_country_aliases=raw_country_aliases,
        proximity_tolerance=proximity_tolerance,
    )


def build_neotoma_site_country_decisions(
    rows: Iterable[Mapping[str, object]],
    country_boundaries: Mapping[str, Mapping[str, object]],
    *,
    boundary_artifact_digest: str,
    boundary_version: str,
    raw_country_aliases: Mapping[str, str] | None = None,
    proximity_tolerance: float = 0.15,
) -> dict[str, CountryAttributionDecision]:
    """Build evidence-preserving decisions for identified Neotoma site rows."""
    decisions: dict[str, CountryAttributionDecision] = {}
    for row in rows:
        nested_site = row.get("site")
        site = nested_site if isinstance(nested_site, Mapping) else row
        site_id = clean_optional_text(site.get("siteid"))
        if not site_id:
            raise ValueError("Neotoma country attribution requires siteid")
        raw_country = neotoma_site_raw_country(
            site,
            country_boundaries=country_boundaries,
            raw_country_aliases=raw_country_aliases,
        )
        representative_point = neotoma_site_representative_point(site)
        if representative_point is None:
            invalid = decide_country_attribution(
                math.nan,
                math.nan,
                country_boundaries,
                boundary_artifact_digest=boundary_artifact_digest,
                boundary_version=boundary_version,
                raw_country=raw_country,
                raw_country_aliases=raw_country_aliases,
                proximity_tolerance=proximity_tolerance,
            )
            geography = clean_optional_text(site.get("geography"))
            decision = replace(
                invalid,
                refusal_reason=(
                    "missing_site_geometry"
                    if not geography
                    else "invalid_site_geometry"
                ),
            )
        else:
            longitude, latitude, _ = representative_point
            decision = decide_country_attribution(
                longitude,
                latitude,
                country_boundaries,
                boundary_artifact_digest=boundary_artifact_digest,
                boundary_version=boundary_version,
                raw_country=raw_country,
                raw_country_aliases=raw_country_aliases,
                proximity_tolerance=proximity_tolerance,
            )
        existing = decisions.get(site_id)
        if existing is not None and existing != decision:
            raise ValueError(
                f"Conflicting country decisions for Neotoma site {site_id}"
            )
        decisions[site_id] = decision
    return dict(sorted(decisions.items()))


def neotoma_site_raw_country(
    site: Mapping[str, object],
    *,
    country_boundaries: Mapping[str, Mapping[str, object]],
    raw_country_aliases: Mapping[str, str] | None = None,
) -> str | None:
    """Return one explicit source country matching governed boundary vocabulary."""
    recognized = {country.casefold() for country in country_boundaries}
    recognized.update(
        alias.casefold() for alias in (raw_country_aliases or {}) if alias.strip()
    )
    values = site.get("geopolitical")
    if not isinstance(values, list):
        return None
    candidates: set[str] = set()
    for value in values:
        if isinstance(value, Mapping):
            candidate = clean_optional_text(value.get("country"))
        else:
            candidate = clean_optional_text(value)
        if candidate and candidate.casefold() in recognized:
            candidates.add(candidate)
    if len(candidates) != 1:
        return None
    return candidates.pop()
