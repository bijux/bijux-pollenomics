"""Reuse the qualified SEAD capture without relabeling its boundary epoch."""

from __future__ import annotations

from collections.abc import Mapping

from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_ADMISSION_SHA256,
    SEAD_GOVERNED_COUNTRY_AUTHORITY_DIGEST,
    SEAD_GOVERNED_COUNTRY_AUTHORITY_ID,
    SEAD_GOVERNED_COUNTRY_DECISIONS_SHA256,
)

from ...boundaries import _validate_admission_copied_file
from ...constants import _CODE_TO_NAME, _NORDIC_COUNTRY_CODES, CountryCoverageError
from ...decoding import (
    _bbox,
    _country_code,
    _decode_object,
    _object,
    _rows,
    _sead_canonical_bytes,
    _sha256,
)
from ..sead_validation import (
    _validate_admission_counts,
    _validate_admission_identity,
    _validate_assignment_identity,
    _validate_decision_counts,
)
from .model import SeadDecisionEvidence
from .records import _decision_evidence, _parse_decision_identity


def retained_sead_decision_evidence(
    *,
    admission_payload: bytes,
    decision_payload: bytes,
    site_payload: bytes,
    admitted_sites: Mapping[int, tuple[str, float, float]],
) -> SeadDecisionEvidence:
    """Authorize retained accounting only for the exact qualified source bytes.

    This is custody and disposition validation, not a fresh geometry replay.
    There is deliberately no caller-controlled flag to disable spatial checks.
    """
    for payload, expected, label in (
        (admission_payload, SEAD_GOVERNED_ADMISSION_SHA256, "admission"),
        (decision_payload, SEAD_GOVERNED_COUNTRY_DECISIONS_SHA256, "country decisions"),
    ):
        if _sha256(payload) != expected:
            raise CountryCoverageError(f"retained SEAD {label} identity changed")
    admission = _decode_object(admission_payload, "retained SEAD admission")
    document = _decode_object(decision_payload, "retained SEAD decisions")
    _validate_admission_identity(admission, document)
    authority = _captured_authority(document)
    for path, payload in (
        ("country-decisions.json", decision_payload),
        ("payloads/tbl_sites.json", site_payload),
    ):
        _validate_admission_copied_file(admission, relative_path=path, payload=payload)
    decisions = _rows(document, "retained SEAD decisions", key="decisions")
    bbox = _bbox(document.get("bbox"), "SEAD country decision bbox")
    seen_ids: set[int] = set()
    seen_uuids: set[str] = set()
    parsed_rows = []
    for row in decisions:
        parsed = _parse_decision_identity(
            row, bbox=bbox, seen_site_ids=seen_ids, seen_site_uuids=seen_uuids
        )
        decision = _object(row.get("decision"), "SEAD decision")
        _validate_captured_decision(decision)
        expected_country = (
            _country_code(decision["derived_country"])
            if parsed.status == "assigned"
            else "UNASSIGNED"
        )
        if parsed.country_code != expected_country:
            raise CountryCoverageError("retained SEAD governed country is inconsistent")
        parsed_rows.append(parsed)
    evidence = _decision_evidence(decisions, parsed_rows, admitted_sites=admitted_sites)
    accounting = _object(admission.get("country_accounting"), "country accounting")
    _validate_assignment_identity(
        accounting,
        authority=authority,
        country_assignment_sha256=evidence.country_assignment_sha256,
    )
    _validate_decision_counts(
        document,
        decision_count=len(decisions),
        decision_statuses=evidence.statuses,
        decision_methods=evidence.methods,
        decision_country_codes=evidence.country_codes,
    )
    _validate_admission_counts(
        accounting,
        decision_count=len(decisions),
        decision_statuses=evidence.statuses,
        governed=evidence.governed,
        boundary_counts=dict.fromkeys(_NORDIC_COUNTRY_CODES, 1),
    )
    return evidence


def _captured_authority(document: Mapping[str, object]) -> Mapping[str, object]:
    authority = _object(document.get("boundary_authority"), "boundary authority")
    identity_keys = {
        "schema",
        "manifest_sha256",
        "source_asset_sha256",
        "country_artifact_sha256",
        "normalized_artifact_sha256",
        "version",
    }
    if set(authority) != identity_keys | {"authority_id", "artifact_digest"}:
        raise CountryCoverageError("retained SEAD boundary authority inventory changed")
    identity = {key: authority[key] for key in identity_keys}
    if (
        authority["schema"] != "nordic-boundary-authority-identity.v1"
        or authority["version"] != "5.1.1"
        or authority["authority_id"] != SEAD_GOVERNED_COUNTRY_AUTHORITY_ID
        or authority["artifact_digest"] != SEAD_GOVERNED_COUNTRY_AUTHORITY_DIGEST
        or "sha256:" + str(authority["normalized_artifact_sha256"])
        != SEAD_GOVERNED_COUNTRY_AUTHORITY_DIGEST
        or "sha256:" + _sha256(_sead_canonical_bytes(identity))
        != SEAD_GOVERNED_COUNTRY_AUTHORITY_ID
    ):
        raise CountryCoverageError("retained SEAD boundary authority is inconsistent")
    return authority


def _validate_captured_decision(decision: Mapping[str, object]) -> None:
    expected_keys = {
        "ambiguity_reason",
        "boundary_artifact_digest",
        "boundary_version",
        "candidate_countries",
        "decision_method",
        "decision_status",
        "derived_country",
        "raw_country",
        "raw_country_comparison",
        "refusal_reason",
    }
    if set(decision) != expected_keys or (
        decision["boundary_artifact_digest"] != SEAD_GOVERNED_COUNTRY_AUTHORITY_DIGEST
        or decision["boundary_version"] != "natural-earth:5.1.1"
        or decision["raw_country"] is not None
        or decision["raw_country_comparison"] != "not_supplied"
    ):
        raise CountryCoverageError("retained SEAD decision authority or fields changed")
    countries = decision["candidate_countries"]
    if (
        not isinstance(countries, list)
        or any(
            not isinstance(country, str) or country not in _CODE_TO_NAME.values()
            for country in countries
        )
        or len(set(countries)) != len(countries)
    ):
        raise CountryCoverageError("retained SEAD candidate countries are invalid")
    status = decision["decision_status"]
    if status == "assigned":
        valid = (
            countries == [decision["derived_country"]]
            and len(countries) == 1
            and decision["decision_method"] == "strict_boundary_containment"
            and decision["ambiguity_reason"] is None
            and decision["refusal_reason"] is None
        )
    elif status == "review":
        valid = (
            bool(countries)
            and decision["derived_country"] is None
            and decision["decision_method"] == "boundary_proximity"
            and isinstance(decision["ambiguity_reason"], str)
            and bool(decision["ambiguity_reason"])
            and decision["refusal_reason"] is None
        )
    elif status == "unassigned":
        valid = (
            not countries
            and decision["derived_country"] is None
            and decision["decision_method"] == "no_boundary_containment"
            and decision["ambiguity_reason"] is None
            and decision["refusal_reason"] == "outside_governed_boundaries"
        )
    else:
        valid = False
    if not valid:
        raise CountryCoverageError("retained SEAD decision state is inconsistent")
