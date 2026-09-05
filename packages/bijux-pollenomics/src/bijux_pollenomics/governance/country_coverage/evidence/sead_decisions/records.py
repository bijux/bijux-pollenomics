"""Governed SEAD country-decision validation and accounting."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping

from bijux_pollenomics.core.geospatial.geojson import CountryBoundaryCollection

from ...boundaries import _boundary_component_index, _recomputed_country_decision
from ...constants import CountryCoverageError, _UUID_PATTERN
from ...decoding import (
    _bbox,
    _coordinate,
    _country_code,
    _object,
    _positive_integer,
    _required_text,
    _rows,
    _sead_canonical_bytes,
    _sha256,
)
from .model import ParsedSeadCountryDecision, SeadDecisionEvidence

BoundaryComponentIndex = list[
    tuple[str, Mapping[str, object], tuple[float, float, float, float]]
]

_DECISION_FIELDS = {
    "decision",
    "governed_country_code",
    "latitude_dd",
    "longitude_dd",
    "site_id",
    "site_uuid",
}


def derive_sead_country_decisions(
    decision_document: Mapping[str, object],
    *,
    admitted_sites: Mapping[int, tuple[str, float, float]],
    boundary_collections: CountryBoundaryCollection,
    boundary_digest: str,
    boundary_version: str,
) -> SeadDecisionEvidence:
    """Validate governed decisions and reconcile their country partitions."""
    decisions = _rows(decision_document, "SEAD country decisions", key="decisions")
    governed: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    methods: Counter[str] = Counter()
    country_codes: Counter[str] = Counter()
    seen_site_ids: set[int] = set()
    seen_site_uuids: set[str] = set()
    assigned_sites: dict[int, tuple[str, float, float]] = {}
    bbox = _bbox(decision_document.get("bbox"), "SEAD country decision bbox")
    boundary_index = _boundary_component_index(boundary_collections)

    for record in decisions:
        parsed = _parse_decision(
            record,
            bbox=bbox,
            boundary_index=boundary_index,
            boundary_digest=boundary_digest,
            boundary_version=boundary_version,
            seen_site_ids=seen_site_ids,
            seen_site_uuids=seen_site_uuids,
        )
        statuses[parsed.status] += 1
        methods[parsed.method] += 1
        country_codes[parsed.country_code] += 1
        _record_disposition(
            parsed,
            assigned_sites=assigned_sites,
            governed=governed,
        )

    if assigned_sites != admitted_sites:
        raise CountryCoverageError(
            "SEAD admitted site identities and coordinates do not reconcile"
        )
    assignment_payload = [
        {"site_id": site_id, "country_code": country_code}
        for site_id, country_code in sorted(
            (
                _positive_integer(record.get("site_id"), "SEAD assignment site_id"),
                _required_text(record, "governed_country_code"),
            )
            for record in decisions
        )
    ]
    return SeadDecisionEvidence(
        decisions=decisions,
        governed=governed,
        statuses=statuses,
        methods=methods,
        country_codes=country_codes,
        country_assignment_sha256=_sha256(_sead_canonical_bytes(assignment_payload)),
    )


def _parse_decision(
    record: Mapping[str, object],
    *,
    bbox: tuple[float, float, float, float],
    boundary_index: BoundaryComponentIndex,
    boundary_digest: str,
    boundary_version: str,
    seen_site_ids: set[int],
    seen_site_uuids: set[str],
) -> ParsedSeadCountryDecision:
    if set(record) != _DECISION_FIELDS:
        raise CountryCoverageError("SEAD country decision row inventory changed")
    site_id = _positive_integer(record.get("site_id"), "SEAD site identity")
    site_uuid = _required_text(record, "site_uuid")
    if _UUID_PATTERN.fullmatch(site_uuid) is None:
        raise CountryCoverageError("SEAD country decision site_uuid is invalid")
    if site_id in seen_site_ids or site_uuid in seen_site_uuids:
        raise CountryCoverageError("SEAD country decisions contain duplicate identity")
    seen_site_ids.add(site_id)
    seen_site_uuids.add(site_uuid)

    decision = _object(record.get("decision"), "SEAD country decision")
    latitude = _coordinate(record.get("latitude_dd"), "SEAD decision latitude", -90, 90)
    longitude = _coordinate(
        record.get("longitude_dd"), "SEAD decision longitude", -180, 180
    )
    if not (bbox[1] <= latitude <= bbox[3] and bbox[0] <= longitude <= bbox[2]):
        raise CountryCoverageError(
            f"SEAD country decision is outside its governed bbox: {site_id}"
        )
    status = _required_text(decision, "decision_status")
    method = _required_text(decision, "decision_method")
    country_code = _required_text(record, "governed_country_code")
    refusal_reason = decision.get("refusal_reason")
    if decision.get("raw_country") is not None:
        raise CountryCoverageError("SEAD country decision raw_country must be null")

    recomputed = _recomputed_country_decision(
        longitude,
        latitude,
        boundary_index=boundary_index,
        boundary_digest=boundary_digest,
        boundary_version=boundary_version,
    )
    recomputed_country_code = (
        _country_code(recomputed.derived_country)
        if recomputed.decision_status == "assigned"
        else "UNASSIGNED"
    )
    expected_decision = {
        "ambiguity_reason": recomputed.ambiguity_reason,
        "boundary_artifact_digest": recomputed.boundary_artifact_digest,
        "boundary_version": recomputed.boundary_version,
        "candidate_countries": list(recomputed.candidate_countries),
        "decision_method": recomputed.decision_method,
        "decision_status": recomputed.decision_status,
        "derived_country": recomputed.derived_country,
        "raw_country": recomputed.raw_country,
        "raw_country_comparison": recomputed.raw_country_comparison,
        "refusal_reason": recomputed.refusal_reason,
    }
    if dict(decision) != expected_decision:
        raise CountryCoverageError(
            f"SEAD country decision does not match governed geometry: {site_id}"
        )
    if country_code != recomputed_country_code:
        raise CountryCoverageError(
            f"SEAD governed country does not match governed geometry: {site_id}"
        )
    return ParsedSeadCountryDecision(
        site_id=site_id,
        site_uuid=site_uuid,
        latitude=latitude,
        longitude=longitude,
        status=status,
        method=method,
        country_code=country_code,
        refusal_reason=refusal_reason,
    )


def _record_disposition(
    decision: ParsedSeadCountryDecision,
    *,
    assigned_sites: dict[int, tuple[str, float, float]],
    governed: Counter[str],
) -> None:
    if decision.status == "assigned":
        assigned_sites[decision.site_id] = (
            decision.site_uuid,
            decision.latitude,
            decision.longitude,
        )
        governed[decision.country_code] += 1
        return
    if decision.status == "review":
        if decision.country_code != "UNASSIGNED" or decision.refusal_reason is not None:
            raise CountryCoverageError("review SEAD country decision is inconsistent")
        governed["UNASSIGNED"] += 1
        return
    if decision.status == "unassigned":
        if (
            decision.country_code != "UNASSIGNED"
            or decision.refusal_reason != "outside_governed_boundaries"
        ):
            raise CountryCoverageError(
                "unassigned SEAD country decision is inconsistent"
            )
        governed["OUTSIDE"] += 1
        return
    raise CountryCoverageError("unsupported SEAD country decision status")
