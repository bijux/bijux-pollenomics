"""Expected, embedded, and country-decision identity validation."""

from __future__ import annotations
from collections.abc import Mapping
from ..codec import (
    _expect_equal,
    _required_text,
    _sha256,
    _sha256_id,
)
from ..models import (
    SeadAdmissionExpectedIdentity,
    _COUNTRY_NAMES,
    _SAFE_RUN_ID,
    _TARGET_COUNTRY_CODES,
)


def _validate_identities(
    payload: Mapping[str, object], identities: Mapping[str, str], label: str
) -> None:
    for field, expected in identities.items():
        _expect_equal(payload.get(field), expected, f"{label} {field}")


def _validate_expected_identity(expected: SeadAdmissionExpectedIdentity) -> None:
    for field in (
        "scope_id",
        "build_id",
        "country_authority_id",
        "country_authority_artifact_digest",
    ):
        _sha256_id(getattr(expected, field), f"expected {field}")
    _sha256(
        expected.acquisition_manifest_sha256,
        "expected acquisition_manifest_sha256",
    )
    _sha256(expected.bbox_payload_sha256, "expected bbox_payload_sha256")
    _sha256(expected.country_decisions_sha256, "expected country_decisions_sha256")
    if expected.parent_admission_sha256 is not None:
        _sha256(
            expected.parent_admission_sha256,
            "expected parent_admission_sha256",
        )
    for value, label in (
        (expected.run_id, "expected run_id"),
        (expected.parent_run_id, "expected parent_run_id"),
    ):
        if not _SAFE_RUN_ID.fullmatch(value):
            raise ValueError(f"SEAD {label} is not a safe path identity")


def _validate_embedded_identities(
    identities: Mapping[str, str],
    expected: SeadAdmissionExpectedIdentity,
) -> None:
    for field in ("scope_id", "run_id", "parent_run_id", "build_id"):
        _expect_equal(
            identities[field], getattr(expected, field), f"caller-pinned {field}"
        )
    _sha256_id(identities["scope_id"], "scope_id")
    _sha256_id(identities["build_id"], "build_id")
    if not _SAFE_RUN_ID.fullmatch(identities["run_id"]):
        raise ValueError("SEAD admission run_id is not a safe path segment")
    if not _SAFE_RUN_ID.fullmatch(identities["parent_run_id"]):
        raise ValueError("SEAD admission parent_run_id is not a safe identity")


def _validate_country_decision_vocabulary(
    code: str,
    decision: Mapping[str, object],
    *,
    expected_identity: SeadAdmissionExpectedIdentity,
) -> None:
    status = _required_text(decision.get("decision_status"), "decision status")
    method = _required_text(decision.get("decision_method"), "decision method")
    _expect_equal(
        decision.get("boundary_artifact_digest"),
        expected_identity.country_authority_artifact_digest,
        "decision boundary artifact digest",
    )
    _required_text(decision.get("boundary_version"), "decision boundary version")
    candidates = decision.get("candidate_countries")
    if not isinstance(candidates, list) or any(
        candidate not in set(_COUNTRY_NAMES.values()) for candidate in candidates
    ):
        raise ValueError("SEAD country decision candidate vocabulary is invalid")
    if status == "assigned":
        if code not in _TARGET_COUNTRY_CODES:
            raise ValueError(
                "Assigned SEAD country decision requires a governed country"
            )
        expected_country = _COUNTRY_NAMES[code]
        expected = {
            "method": "strict_boundary_containment",
            "derived_country": expected_country,
            "ambiguity_reason": None,
            "refusal_reason": None,
            "candidate_countries": [expected_country],
        }
    elif status == "review":
        if code != "UNASSIGNED":
            raise ValueError("Review SEAD country decision must be UNASSIGNED")
        expected = {
            "method": "boundary_proximity",
            "derived_country": None,
            "refusal_reason": None,
        }
        if decision.get("ambiguity_reason") not in {
            "near_boundary_without_containment",
            "near_multiple_boundaries",
        }:
            raise ValueError("SEAD review decision has invalid ambiguity reason")
    elif status == "unassigned":
        if code != "UNASSIGNED":
            raise ValueError("Unassigned SEAD country decision has governed country")
        expected = {
            "method": "no_boundary_containment",
            "derived_country": None,
            "ambiguity_reason": None,
            "refusal_reason": "outside_governed_boundaries",
            "candidate_countries": [],
        }
    else:
        raise ValueError(f"Invalid SEAD country decision status: {status}")
    _expect_equal(method, expected.pop("method"), "country decision method")
    for field, value in expected.items():
        _expect_equal(decision.get(field), value, f"country decision {field}")
