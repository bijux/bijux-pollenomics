"""Fail-closed country decisions derived from governed boundary authority."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from ....spatial import CountryAttributionDecision, decide_country_attribution
from .models import BoundaryAuthority, JsonObject, PointEvidence
from .policy import (
    BOUNDARY_VERSION,
    COUNTRY_ALIASES,
    COUNTRY_CODES_BY_NAME,
    COUNTRY_ORDER,
)
from .serialization import _canonical_digest, _optional_text


def build_point_country_decision(
    point: PointEvidence,
    *,
    authority: BoundaryAuthority,
) -> JsonObject:
    """Return one fail-closed country decision with source and review lineage."""
    geometric = decide_country_attribution(
        point.longitude,
        point.latitude,
        authority.boundaries,
        boundary_artifact_digest=authority.artifact_digest,
        boundary_version=BOUNDARY_VERSION,
        raw_country=point.raw_country,
        raw_country_aliases=COUNTRY_ALIASES,
    )
    reasons = [
        value
        for value in (geometric.ambiguity_reason, geometric.refusal_reason)
        if value is not None
    ]
    published_comparison = _country_comparison(
        point.published_country, geometric.derived_country
    )
    if published_comparison == "conflicts":
        reasons.append("published_country_conflict")
    prior_comparison = _prior_decision_comparison(point.prior_decision, geometric)
    if prior_comparison == "conflicts":
        reasons.append("prior_country_decision_conflict")

    final_status = geometric.decision_status
    if final_status == "assigned" and (
        published_comparison == "conflicts" or prior_comparison == "conflicts"
    ):
        final_status = "review"
    reasons = sorted(set(reasons))
    review_required = final_status in {"review", "refused"} or (
        final_status == "unassigned" and point.source_scope == "four_country_expected"
    )
    if final_status == "unassigned" and review_required:
        reasons.append("expected_four_country_point_unassigned")
        reasons = sorted(set(reasons))
    if final_status == "refused" and not reasons:
        reasons.append("country_decision_refused")

    derived_code = (
        COUNTRY_CODES_BY_NAME.get(geometric.derived_country)
        if geometric.derived_country is not None
        else None
    )
    candidate_codes = [
        code
        for country in geometric.candidate_countries
        if (code := COUNTRY_CODES_BY_NAME.get(country)) is not None
    ]
    decision_identity = {
        "source_family": point.source_family,
        "source_record_id": point.source_record_id,
        "longitude": point.longitude,
        "latitude": point.latitude,
        "boundary_artifact_digest": authority.artifact_digest,
        "boundary_version": BOUNDARY_VERSION,
    }
    return {
        "schema_version": "country-attribution-decision.v1",
        "decision_id": f"sha256:{_canonical_digest(decision_identity)}",
        "source_family": point.source_family,
        "source_scope": point.source_scope,
        "source_record_id": point.source_record_id,
        "source_native_lineage": list(point.lineage),
        "longitude": point.longitude,
        "latitude": point.latitude,
        "coordinate_reference_system": "EPSG:4326",
        "coordinate_axis_order": "longitude,latitude",
        "raw_country": point.raw_country,
        "published_country": point.published_country,
        "derived_boundary_membership": geometric.derived_country,
        "derived_country_code": derived_code,
        "candidate_countries": list(geometric.candidate_countries),
        "candidate_country_codes": candidate_codes,
        "boundary_artifact_digest": authority.artifact_digest,
        "boundary_version": BOUNDARY_VERSION,
        "country_decision_status": final_status,
        "boundary_decision_status": geometric.decision_status,
        "decision_method": geometric.decision_method,
        "ambiguity_reason": reasons[0] if reasons else None,
        "ambiguity_reason_codes": reasons,
        "refusal_reason": geometric.refusal_reason,
        "raw_country_comparison": geometric.raw_country_comparison,
        "published_country_comparison": published_comparison,
        "prior_country_decision_comparison": prior_comparison,
        "review_requirement": (
            "qualified_review_required"
            if review_required
            else "no_point_review_required"
        ),
        "review_reason_codes": reasons if review_required else [],
        "qualified_review_status": "pending" if review_required else "not_required",
        "qualified_reviewer": None,
        "qualified_reviewed_at": None,
        "boundary_semantics": (
            "Modern country membership is a filter and denominator dimension; it "
            "is not evidence of a historical ecological barrier."
        ),
    }


def _decision_summary(decisions: Sequence[JsonObject]) -> JsonObject:
    status_counts = Counter(str(row["country_decision_status"]) for row in decisions)
    method_counts = Counter(str(row["decision_method"]) for row in decisions)
    review_counts = Counter(str(row["review_requirement"]) for row in decisions)
    country_counts = Counter(
        str(row["derived_country_code"] or "UNASSIGNED") for row in decisions
    )
    return {
        "row_count": len(decisions),
        "country_counts": {
            code: country_counts.get(code, 0) for code in (*COUNTRY_ORDER, "UNASSIGNED")
        },
        "decision_status_counts": dict(sorted(status_counts.items())),
        "decision_method_counts": dict(sorted(method_counts.items())),
        "review_requirement_counts": dict(sorted(review_counts.items())),
    }


def _prior_decision_comparison(
    prior: JsonObject | None, geometric: CountryAttributionDecision
) -> str:
    if prior is None:
        return "not_supplied"
    fields = {
        "decision_status": geometric.decision_status,
        "decision_method": geometric.decision_method,
        "derived_country": geometric.derived_country,
        "boundary_artifact_digest": geometric.boundary_artifact_digest,
    }
    return (
        "agrees"
        if all(prior.get(key) == value for key, value in fields.items())
        else "conflicts"
    )


def _country_comparison(raw: str | None, derived: str | None) -> str:
    normalized = _optional_text(raw)
    if normalized is None:
        return "not_supplied"
    if derived is None:
        return "unresolved"
    aliased = COUNTRY_ALIASES.get(normalized) or COUNTRY_ALIASES.get(normalized.upper())
    return "agrees" if aliased == derived else "conflicts"
