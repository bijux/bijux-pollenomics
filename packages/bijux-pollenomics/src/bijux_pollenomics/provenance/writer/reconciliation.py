"""Count-reconciliation and blocker request translation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, cast

from ..release_evidence import (
    Blocker,
    CountReconciliation,
    CountStatus,
    ReconciliationDimension,
    ReleaseEvidenceError,
)
from .codec import (
    _list_field,
    _mapping,
    _optional_int_field,
    _optional_string_field,
    _string_field,
    _string_value,
)


def _reconciliation(value: object) -> CountReconciliation:
    record = _mapping(value, "reconciliation")
    count_fields = (
        "candidate_count",
        "eligible_count",
        "accepted_count",
        "unresolved_count",
        "excluded_count",
        "refused_count",
    )
    expected = {
        "identity",
        "dimension",
        "source",
        "entity",
        "country_code",
        "scope",
        "count_status",
        "reason_codes",
        *count_fields,
    }
    if set(record) != expected:
        raise ReleaseEvidenceError(
            "reconciliation request fields do not match the v3 contract"
        )
    country_code = record["country_code"]
    if country_code is not None and not isinstance(country_code, str):
        raise ReleaseEvidenceError("country_code must be a string or null")
    counts = {field: _optional_int_field(record, field) for field in count_fields}
    scope = _mapping(record["scope"], "reconciliation scope")
    if any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in scope.items()
    ):
        raise ReleaseEvidenceError("reconciliation scope must contain strings")
    return CountReconciliation(
        identity=_string_field(record, "identity"),
        dimension=cast(ReconciliationDimension, _string_field(record, "dimension")),
        source=_string_field(record, "source"),
        entity=_string_field(record, "entity"),
        country_code=country_code,
        candidate_count=counts["candidate_count"],
        eligible_count=counts["eligible_count"],
        accepted_count=counts["accepted_count"],
        unresolved_count=counts["unresolved_count"],
        excluded_count=counts["excluded_count"],
        refused_count=counts["refused_count"],
        scope=tuple(sorted(cast(Mapping[str, str], scope).items())),
        count_status=cast(CountStatus, _string_field(record, "count_status")),
        reason_codes=tuple(
            _string_value(item, "reason code")
            for item in _list_field(record, "reason_codes")
        ),
    )


def _blocker(value: object) -> Blocker:
    record = _mapping(value, "blocker")
    expected = {
        "identity",
        "reason_code",
        "evidence_digest",
        "kind",
        "required_scope",
        "owner",
        "first_observed_at",
        "last_observed_at",
        "request_status",
        "request_artifact_identity",
        "request_fingerprint",
        "response_class",
        "observations",
        "attempts",
        "impact",
        "expected_artifact",
        "impacted_gates",
        "next_action",
        "recheck_condition",
    }
    if set(record) != expected:
        raise ReleaseEvidenceError(
            "blocker request fields do not match the v3 contract"
        )
    return Blocker(
        identity=_string_field(record, "identity"),
        reason_code=_string_field(record, "reason_code"),
        evidence_digest=_string_field(record, "evidence_digest"),
        kind=cast(
            Literal["external", "unverified", "refused", "reduced_scope"],
            _string_field(record, "kind"),
        ),
        required_scope=_string_field(record, "required_scope"),
        owner=_string_field(record, "owner"),
        first_observed_at=_string_field(record, "first_observed_at"),
        last_observed_at=_string_field(record, "last_observed_at"),
        request_status=cast(
            Literal["governed", "refused"], _string_field(record, "request_status")
        ),
        request_artifact_identity=_optional_string_field(
            record, "request_artifact_identity"
        ),
        request_fingerprint=_optional_string_field(record, "request_fingerprint"),
        response_class=_string_field(record, "response_class"),
        observations=tuple(
            _string_value(item, "observation")
            for item in _list_field(record, "observations")
        ),
        attempts=tuple(
            _string_value(item, "attempt") for item in _list_field(record, "attempts")
        ),
        impact=_string_field(record, "impact"),
        expected_artifact=_string_field(record, "expected_artifact"),
        impacted_gates=tuple(
            _string_value(item, "impacted gate")
            for item in _list_field(record, "impacted_gates")
        ),
        next_action=_string_field(record, "next_action"),
        recheck_condition=_string_field(record, "recheck_condition"),
    )
