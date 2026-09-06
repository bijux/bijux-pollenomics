"""Parent admission and downstream release-posture validation."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping

from ..codec import _expect_equal, _json_object
from ..models import (
    _DOWNSTREAM_REFUSALS,
    _FULL_EVIDENCE_PROFILE,
    _SCOPED_PROFILE,
    ADMISSION_SCHEMA_VERSION,
    SeadAdmissionExpectedIdentity,
    _AdmissionProfile,
)


def _validate_parent_admission(
    payload: bytes,
    *,
    expected_identity: SeadAdmissionExpectedIdentity,
    parent_run_id: str,
    country_decisions_sha256: str,
) -> str:
    expected_sha256 = expected_identity.parent_admission_sha256
    if expected_sha256 is None:
        raise ValueError(
            "Full-evidence expected identity lacks parent admission SHA-256"
        )
    observed_sha256 = hashlib.sha256(payload).hexdigest()
    _expect_equal(
        observed_sha256,
        expected_sha256,
        "caller-pinned parent admission SHA-256",
    )
    parent = _json_object(payload, "parent-admission.json")
    _expect_equal(
        parent.get("schema_version"),
        ADMISSION_SCHEMA_VERSION,
        "parent admission schema_version",
    )
    _expect_equal(parent.get("source_family"), "sead", "parent admission source")
    _expect_equal(parent.get("run_id"), parent_run_id, "parent admission run_id")
    copied_files = parent.get("copied_files")
    if not isinstance(copied_files, list):
        raise TypeError("Parent SEAD admission copied_files must be a list")
    country_records = [
        item
        for item in copied_files
        if isinstance(item, Mapping) and item.get("path") == "country-decisions.json"
    ]
    if len(country_records) != 1:
        raise ValueError("Parent SEAD admission must bind one country-decisions file")
    _expect_equal(
        country_records[0].get("sha256"),
        country_decisions_sha256,
        "parent admission country decisions SHA-256",
    )
    return observed_sha256


def _downstream_statuses(profile: _AdmissionProfile) -> dict[str, dict[str, str]]:
    reasons = (
        {
            "chronology_claims": "typed_chronology_claims_not_materialized",
            "evidence_events": "source_native_evidence_events_not_materialized",
            "propagation_events": "propagation_events_not_materialized",
        }
        if profile is _FULL_EVIDENCE_PROFILE
        else _DOWNSTREAM_REFUSALS
    )
    return {
        name: {"status": "refused", "reason_code": reason}
        for name, reason in reasons.items()
    }


def _release_reason_codes(profile: _AdmissionProfile) -> set[str]:
    reasons = {item["reason_code"] for item in _downstream_statuses(profile).values()}
    reasons.add("excluded_country_coordinates_lack_preserved_preflight_payload")
    if profile is _SCOPED_PROFILE:
        reasons.add("declared_relation_scope_is_not_full_wp01_scope")
    return reasons
