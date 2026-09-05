"""Fail-closed Neotoma observation admission to chronology nodes."""

from __future__ import annotations

from collections.abc import Mapping
from math import isfinite

from bijux_pollenomics.collection.sources.neotoma.country import (
    neotoma_site_representative_point,
)
from bijux_pollenomics.core.temporal_semantics import (
    InvalidBpIntervalError,
    canonical_bp_interval,
)

from .constants import COUNTRY_CODES
from .identity import finite_number, optional_text


def source_coordinate(
    site: Mapping[str, object],
) -> tuple[float, float, str] | None:
    """Return a validated representative point and explicit quality posture."""
    payload = site.get("source_payload")
    if not isinstance(payload, Mapping):
        return None
    point = neotoma_site_representative_point(payload)
    if point is None:
        return None
    longitude, latitude, geometry_type = point
    if (
        not isfinite(longitude)
        or not isfinite(latitude)
        or not -180.0 <= longitude <= 180.0
        or not -90.0 <= latitude <= 90.0
    ):
        return None
    quality = (
        "reported"
        if geometry_type == "Point"
        else "centroid"
        if geometry_type in {"Polygon", "MultiPolygon"}
        else "approximate"
    )
    return longitude, latitude, quality


def chronology_reason(claim: Mapping[str, object]) -> str | None:
    """Return the source chronology posture that prevented comparison."""
    return optional_text(claim.get("refusal_reason")) or optional_text(
        claim.get("admission_reason")
    )


def canonical_claim_interval(
    claim: Mapping[str, object],
) -> tuple[float | int, float | int] | None:
    """Return a canonical ``[younger_bp, older_bp]`` interval or ``None``."""
    if claim.get("comparability_status") != "comparable":
        return None
    younger_bp = claim.get("younger_bp")
    older_bp = claim.get("older_bp")
    if not finite_number(younger_bp) or not finite_number(older_bp):
        return None
    try:
        interval = canonical_bp_interval(younger_bp, older_bp)
    except InvalidBpIntervalError:
        return None
    if interval is None:
        return None
    return younger_bp, older_bp


def source_refusal_reason(
    observation: Mapping[str, object],
    sample: Mapping[str, object] | None,
    site: Mapping[str, object] | None,
    claim: Mapping[str, object] | None,
) -> tuple[str | None, str | None]:
    """Return node-admission refusal and chronology detail for one observation."""
    if optional_text(observation.get("country_code")) not in COUNTRY_CODES:
        return "ungoverned_country", None
    if optional_text(observation.get("source_element_type")) != "pollen":
        return "non_pollen_observation", None
    if optional_text(observation.get("detection_status")) != "reported_value":
        return "non_positive_observation", None
    value = observation.get("source_value")
    if not finite_number(value) or float(value) <= 0:
        return "non_positive_observation", None
    if sample is None:
        return "missing_sample", None
    if site is None:
        return "missing_site", None
    sample_id = optional_text(observation.get("sample_id"))
    site_id = optional_text(observation.get("site_id"))
    if (
        sample_id != optional_text(sample.get("sample_id"))
        or site_id != optional_text(sample.get("site_id"))
        or site_id != optional_text(site.get("site_id"))
    ):
        return "source_relation_mismatch", None
    country = optional_text(observation.get("country_code"))
    if any(optional_text(row.get("country_code")) != country for row in (sample, site)):
        return "source_lineage_mismatch", None
    if claim is None:
        return "missing_source_default_chronology", None
    if (
        sample_id != optional_text(claim.get("source_record_id"))
        or site_id != optional_text(claim.get("site_id"))
        or optional_text(claim.get("country_code")) != country
    ):
        return "source_relation_mismatch", None
    identities = (observation, sample, site, claim)
    for field_name in ("source_snapshot_id", "build_id"):
        values = {optional_text(row.get(field_name)) for row in identities}
        if len(values) != 1 or None in values:
            return "source_lineage_mismatch", None
    if claim.get("comparability_status") != "comparable":
        return "non_comparable_source_default_chronology", chronology_reason(claim)
    if canonical_claim_interval(claim) is None:
        return "invalid_source_default_chronology_interval", None
    if optional_text(claim.get("provenance_record_id")) is None:
        return "source_lineage_mismatch", None
    if optional_text(observation.get("source_unit")) is None:
        return "measurement_semantics_missing", None
    if source_coordinate(site) is None:
        return "missing_or_invalid_coordinates", None
    return None, None


__all__ = [
    "canonical_claim_interval",
    "chronology_reason",
    "source_coordinate",
    "source_refusal_reason",
]
