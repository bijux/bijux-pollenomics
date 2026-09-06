"""Country assignment accounting and spatial reconciliation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
import hashlib

from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    NORDIC_COUNTRY_CODES,
)

from ..codec import (
    _bbox,
    _canonical_bytes,
    _coordinate,
    _country_counts,
    _expect_equal,
    _json_object,
    _mapping,
    _non_negative_int,
    _positive_int,
    _required_text,
    _sha256_id,
)
from ..models import (
    _COUNTRY_DECISIONS_SCHEMA_VERSION,
    _COUNTRY_NAMES,
    _COUNTRY_RECONCILIATION_SCHEMA_VERSION,
    _FULL_EVIDENCE_PROFILE,
    _PREFLIGHT_MAX_PAGES,
    _SITE_PRIMARY_KEY,
    _SITE_PROJECTION,
    _TARGET_COUNTRY_CODES,
    SeadAdmissionExpectedIdentity,
    _AdmissionProfile,
    _BoundaryAuthority,
)
from .contracts import _bbox_query_parameters
from .identity import (
    _validate_country_decision_vocabulary,
    _validate_identities,
)
from .receipts import _validate_acquisition_receipt


def _validate_site_rows(rows: Sequence[Mapping[str, object]]) -> None:
    uuids: list[str] = []
    for row in rows:
        uuids.append(_required_text(row.get("site_uuid"), "tbl_sites.site_uuid"))
    if len(uuids) != len(set(uuids)):
        raise ValueError("SEAD site_uuid values must be unique")


def _validate_country_accounting(
    reconciliation: Mapping[str, object],
    *,
    decisions_bytes: bytes,
    site_rows: Sequence[Mapping[str, object]],
    site_receipt: Mapping[str, object],
    identities: Mapping[str, str],
    expected_identity: SeadAdmissionExpectedIdentity,
    boundary_authority: _BoundaryAuthority,
    profile: _AdmissionProfile,
) -> dict[str, object]:
    from ......spatial import decide_country_attribution

    _expect_equal(
        reconciliation.get("schema_version"),
        _COUNTRY_RECONCILIATION_SCHEMA_VERSION,
        "country reconciliation schema_version",
    )
    _validate_identities(reconciliation, identities, "country reconciliation")
    _expect_equal(reconciliation.get("reconciles"), True, "country reconciliation")
    _expect_equal(reconciliation.get("duplicate_site_ids"), [], "duplicate site IDs")
    counts = _country_counts(reconciliation.get("counts"), "country reconciliation")
    row_count = _non_negative_int(reconciliation.get("row_count"), "country row_count")
    _expect_equal(sum(counts.values()), row_count, "country partition row_count")
    _expect_equal(row_count, len(site_rows), "country rows versus site payload")
    _expect_equal(counts["UNASSIGNED"], 0, "admitted UNASSIGNED rows")
    _expect_equal(
        reconciliation.get("assigned_count"),
        sum(counts[code] for code in _TARGET_COUNTRY_CODES),
        "assigned country count",
    )
    _expect_equal(reconciliation.get("unassigned_count"), 0, "unassigned count")

    decisions = _json_object(decisions_bytes, "country-decisions.json")
    _expect_equal(
        decisions.get("schema_version"),
        _COUNTRY_DECISIONS_SCHEMA_VERSION,
        "country decisions schema_version",
    )
    decision_identities = (
        {
            "scope_id": _required_text(decisions.get("input_id"), "decisions input_id"),
            "run_id": _required_text(decisions.get("run_id"), "decisions run_id"),
            "parent_run_id": _required_text(
                decisions.get("job_id"), "decisions job_id"
            ),
            "build_id": _required_text(decisions.get("build_id"), "decisions build_id"),
        }
        if profile is _FULL_EVIDENCE_PROFILE
        else identities
    )
    _expect_equal(
        decisions.get("run_id"), decision_identities["run_id"], "decisions run_id"
    )
    _expect_equal(
        decisions.get("input_id"), decision_identities["scope_id"], "decisions scope_id"
    )
    _expect_equal(
        decisions.get("job_id"),
        decision_identities["parent_run_id"],
        "decisions parent_run_id",
    )
    _expect_equal(
        decisions.get("build_id"), decision_identities["build_id"], "decisions build_id"
    )
    if profile is _FULL_EVIDENCE_PROFILE:
        _expect_equal(
            decisions.get("run_id"),
            identities["parent_run_id"],
            "full-evidence parent country-decision run",
        )
    bbox = _bbox(decisions.get("bbox"), "country decisions bbox")
    boundary_record = _mapping(
        decisions.get("boundary_authority"), "country boundary authority"
    )
    _expect_equal(
        boundary_record.get("authority_id"),
        expected_identity.country_authority_id,
        "country boundary authority ID",
    )
    _expect_equal(
        boundary_record.get("artifact_digest"),
        expected_identity.country_authority_artifact_digest,
        "country boundary authority artifact digest",
    )
    _sha256_id(boundary_record.get("authority_id"), "country authority ID")
    _sha256_id(
        boundary_record.get("artifact_digest"), "country authority artifact digest"
    )
    _expect_equal(
        boundary_record.get("version"),
        boundary_authority.source_version,
        "country boundary authority version",
    )
    for field, expected in (
        ("manifest_sha256", boundary_authority.manifest_sha256),
        (
            "normalized_artifact_sha256",
            boundary_authority.artifact_digest.removeprefix("sha256:"),
        ),
        ("source_asset_sha256", boundary_authority.source_asset_sha256),
        ("country_artifact_sha256", boundary_authority.country_artifact_sha256),
    ):
        _expect_equal(
            boundary_record.get(field), expected, f"country boundary authority {field}"
        )
    preflight = _mapping(
        decisions.get("preflight_receipt"), "country preflight receipt"
    )
    preflight_count = _validate_acquisition_receipt(
        preflight,
        table="tbl_sites",
        identities=decision_identities,
        label="country preflight receipt",
        require_orchestration_identity=False,
        expected_parameters=_bbox_query_parameters(bbox, _SITE_PROJECTION),
        expected_order=[_SITE_PRIMARY_KEY],
        expected_max_pages=_PREFLIGHT_MAX_PAGES,
        expected_rows=None,
    )
    _expect_equal(
        _mapping(preflight.get("spatial_scope"), "preflight spatial_scope").get("kind"),
        "governed_bbox_country_decision_preflight",
        "preflight scope kind",
    )
    _expect_equal(
        _mapping(preflight.get("spatial_scope"), "preflight spatial_scope").get("bbox"),
        list(bbox),
        "preflight spatial bbox",
    )
    _expect_equal(
        _mapping(preflight.get("spatial_scope"), "preflight spatial_scope").get(
            "boundary_authority_id"
        ),
        expected_identity.country_authority_id,
        "preflight boundary authority ID",
    )
    _expect_equal(
        preflight.get("content_sha256"),
        expected_identity.bbox_payload_sha256,
        "caller-pinned preflight payload SHA-256",
    )
    decision_rows = decisions.get("decisions")
    if not isinstance(decision_rows, list) or any(
        not isinstance(row, Mapping) for row in decision_rows
    ):
        raise ValueError("SEAD country decisions must be object rows")
    bbox_count = _non_negative_int(
        decisions.get("bbox_site_count"), "decisions bbox_site_count"
    )
    _expect_equal(len(decision_rows), bbox_count, "country decision denominator")
    decision_codes: Counter[str] = Counter(dict.fromkeys(NORDIC_COUNTRY_CODES, 0))
    decision_statuses: Counter[str] = Counter()
    decision_methods: Counter[str] = Counter()
    decision_by_site: dict[int, tuple[str, str]] = {}
    site_coordinates = {
        _positive_int(row.get("site_id"), "tbl_sites.site_id"): (
            _coordinate(row.get("latitude_dd"), "tbl_sites.latitude_dd", -90, 90),
            _coordinate(row.get("longitude_dd"), "tbl_sites.longitude_dd", -180, 180),
        )
        for row in site_rows
    }
    for row in decision_rows:
        if not isinstance(row, Mapping):
            raise TypeError("SEAD country decision row must be an object")
        site_id = _positive_int(row.get("site_id"), "country decision site_id")
        if site_id in decision_by_site:
            raise ValueError(f"Duplicate SEAD country decision: {site_id}")
        site_uuid = _required_text(row.get("site_uuid"), "country decision site_uuid")
        code = _required_text(row.get("governed_country_code"), "governed country code")
        if code not in NORDIC_COUNTRY_CODES:
            raise ValueError(f"Invalid governed SEAD country code: {code}")
        decision = row.get("decision")
        if not isinstance(decision, Mapping):
            raise TypeError("SEAD country decision detail must be an object")
        status = _required_text(decision.get("decision_status"), "decision status")
        method = _required_text(decision.get("decision_method"), "decision method")
        _validate_country_decision_vocabulary(
            code, decision, expected_identity=expected_identity
        )
        latitude = _coordinate(row.get("latitude_dd"), "decision latitude", -90, 90)
        longitude = _coordinate(
            row.get("longitude_dd"), "decision longitude", -180, 180
        )
        if not (bbox[1] <= latitude <= bbox[3] and bbox[0] <= longitude <= bbox[2]):
            raise ValueError(f"SEAD country decision is outside bbox: {site_id}")
        _expect_equal(decision.get("raw_country"), None, "country decision raw_country")
        recomputed = decide_country_attribution(
            longitude,
            latitude,
            boundary_authority.boundaries,
            boundary_artifact_digest=boundary_authority.artifact_digest,
            boundary_version=boundary_authority.version,
        )
        recomputed_code = (
            next(
                (
                    country_code
                    for country_code, country_name in _COUNTRY_NAMES.items()
                    if country_name == recomputed.derived_country
                ),
                "UNASSIGNED",
            )
            if recomputed.decision_status == "assigned"
            else "UNASSIGNED"
        )
        _expect_equal(code, recomputed_code, f"country geometry assignment {site_id}")
        for field, expected_value in (
            ("decision_status", recomputed.decision_status),
            ("decision_method", recomputed.decision_method),
            ("ambiguity_reason", recomputed.ambiguity_reason),
            ("refusal_reason", recomputed.refusal_reason),
            ("derived_country", recomputed.derived_country),
            ("candidate_countries", list(recomputed.candidate_countries)),
            ("raw_country_comparison", recomputed.raw_country_comparison),
            ("boundary_artifact_digest", recomputed.boundary_artifact_digest),
            ("boundary_version", recomputed.boundary_version),
        ):
            _expect_equal(
                decision.get(field),
                expected_value,
                f"country geometry {field} {site_id}",
            )
        if code in _TARGET_COUNTRY_CODES:
            _expect_equal(
                (latitude, longitude),
                site_coordinates.get(site_id),
                f"admitted country decision coordinates {site_id}",
            )
        decision_by_site[site_id] = (code, site_uuid)
        decision_codes[code] += 1
        decision_statuses[status] += 1
        decision_methods[method] += 1
    _expect_equal(
        dict(decision_codes),
        _country_counts(decisions.get("country_counts"), "country decisions"),
        "country decision counts",
    )
    _expect_equal(
        dict(sorted(decision_statuses.items())),
        decisions.get("decision_status_counts"),
        "country decision status counts",
    )
    _expect_equal(
        dict(sorted(decision_methods.items())),
        decisions.get("decision_method_counts"),
        "country decision method counts",
    )
    for code in _TARGET_COUNTRY_CODES:
        _expect_equal(decision_codes[code], counts[code], f"{code} country count")

    admitted_sites = {
        _positive_int(row.get("site_id"), "tbl_sites.site_id"): _required_text(
            row.get("site_uuid"), "tbl_sites.site_uuid"
        )
        for row in site_rows
    }
    expected_admitted = {
        site_id: site_uuid
        for site_id, (code, site_uuid) in decision_by_site.items()
        if code in _TARGET_COUNTRY_CODES
    }
    _expect_equal(admitted_sites, expected_admitted, "admitted country site identities")
    excluded_ids = sorted(
        site_id
        for site_id, (code, _) in decision_by_site.items()
        if code == "UNASSIGNED"
    )
    _expect_equal(
        reconciliation.get("bbox_row_count"), bbox_count, "bbox site denominator"
    )
    _expect_equal(preflight_count, bbox_count, "preflight bbox site denominator")
    _expect_equal(
        reconciliation.get("scope_excluded_count"),
        len(excluded_ids),
        "scope exclusion count",
    )
    _expect_equal(
        reconciliation.get("scope_excluded_site_ids"),
        excluded_ids,
        "scope exclusion IDs",
    )
    _expect_equal(row_count + len(excluded_ids), bbox_count, "bbox disposition")
    _expect_equal(
        site_receipt.get("scope_excluded_site_ids"),
        excluded_ids,
        "site receipt exclusions",
    )
    assignments = site_receipt.get("governed_country_assignments")
    if not isinstance(assignments, list):
        raise TypeError("SEAD site receipt lacks governed country assignments")
    assignment_map: dict[int, str] = {}
    for item in assignments:
        if not isinstance(item, Mapping):
            raise TypeError("SEAD governed country assignment must be an object")
        site_id = _positive_int(item.get("site_id"), "assignment site_id")
        code = _required_text(item.get("country_code"), "assignment country_code")
        if site_id in assignment_map:
            raise ValueError(f"Duplicate governed country assignment: {site_id}")
        assignment_map[site_id] = code
    _expect_equal(
        assignment_map,
        {site_id: code for site_id, (code, _) in decision_by_site.items()},
        "governed country assignments",
    )
    assignment_payload = [
        {"site_id": site_id, "country_code": code}
        for site_id, code in sorted(assignment_map.items())
    ]
    assignment_sha256 = hashlib.sha256(_canonical_bytes(assignment_payload)).hexdigest()
    site_scope = _mapping(site_receipt.get("spatial_scope"), "site spatial_scope")
    _expect_equal(
        site_scope.get("country_assignment_id"),
        expected_identity.country_authority_id,
        "site country assignment authority ID",
    )
    _expect_equal(
        site_scope.get("country_assignment_sha256"),
        assignment_sha256,
        "site country assignment SHA-256",
    )
    _expect_equal(
        reconciliation.get("country_assignment_id"),
        expected_identity.country_authority_id,
        "country reconciliation authority ID",
    )
    _expect_equal(
        reconciliation.get("country_assignment_sha256"),
        assignment_sha256,
        "country reconciliation assignment SHA-256",
    )
    site_queries = site_receipt.get("query_receipts")
    if not isinstance(site_queries, list) or len(site_queries) != 1:
        raise ValueError(
            "SEAD site receipt must preserve exactly one bbox query receipt"
        )
    site_query = _mapping(site_queries[0], "site bbox query receipt")
    _expect_equal(
        site_query.get("content_sha256"),
        expected_identity.bbox_payload_sha256,
        "caller-pinned site-query payload SHA-256",
    )
    for field in ("content_sha256", "canonical_schema", "canonical_schema_sha256"):
        _expect_equal(preflight.get(field), site_query.get(field), f"preflight {field}")
    _expect_equal(
        _mapping(site_query.get("spatial_scope"), "site query spatial_scope").get(
            "bbox"
        ),
        list(bbox),
        "site query bbox",
    )
    return {
        "bbox_site_count": bbox_count,
        "admitted_site_count": row_count,
        "scope_excluded_count": len(excluded_ids),
        "country_counts": {code: counts[code] for code in _TARGET_COUNTRY_CODES},
        "review_site_count": decision_statuses["review"],
        "unassigned_site_count": decision_statuses["unassigned"],
        "country_assignment_sha256": assignment_sha256,
        "boundary_authority_id": expected_identity.country_authority_id,
        "excluded_coordinate_validation": {
            "status": "not_independently_verified",
            "reason_code": "preflight_payload_not_preserved",
        },
        "reconciles": True,
    }
