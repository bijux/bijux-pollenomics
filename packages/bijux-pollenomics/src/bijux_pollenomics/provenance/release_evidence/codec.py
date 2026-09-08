"""Canonical release-evidence records and primitive contract decoders."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
import hashlib
import json
from typing import Literal, cast

from .models import (
    _COMMIT_PATTERN,
    _DIGEST_PATTERN,
    _IDENTITY_PATTERN,
    _UTC_TIMESTAMP_PATTERN,
    ArtifactInput,
    ArtifactReference,
    ArtifactRole,
    Blocker,
    CountReconciliation,
    CountStatus,
    GateResult,
    GateStatus,
    ReconciliationDimension,
    ReleaseEvidenceError,
)


def _digest_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _gate_record(item: GateResult) -> dict[str, object]:
    return {
        "identity": item.identity,
        "status": item.status,
        "required": item.required,
        "evidence_digest": item.evidence_digest,
        "attestation": item.attestation,
        "authority_id": item.authority_id,
    }


def _reconciliation_record(item: CountReconciliation) -> dict[str, object]:
    return {
        "identity": item.identity,
        "dimension": item.dimension,
        "source": item.source,
        "entity": item.entity,
        "country_code": item.country_code,
        "scope": dict(item.scope),
        "count_status": item.count_status,
        "reason_codes": list(item.reason_codes),
        **_counts(item),
    }


def _blocker_record(item: Blocker) -> dict[str, object]:
    return {
        "identity": item.identity,
        "reason_code": item.reason_code,
        "evidence_digest": item.evidence_digest,
        "kind": item.kind,
        "required_scope": item.required_scope,
        "owner": item.owner,
        "first_observed_at": item.first_observed_at,
        "last_observed_at": item.last_observed_at,
        "request_fingerprint": item.request_fingerprint,
        "request_status": item.request_status,
        "request_artifact_identity": item.request_artifact_identity,
        "response_class": item.response_class,
        "observations": list(item.observations),
        "attempts": list(item.attempts),
        "impact": item.impact,
        "expected_artifact": item.expected_artifact,
        "impacted_gates": list(item.impacted_gates),
        "next_action": item.next_action,
        "recheck_condition": item.recheck_condition,
    }


def _counts(item: CountReconciliation) -> dict[str, int | None]:
    return {
        "candidate_count": item.candidate_count,
        "eligible_count": item.eligible_count,
        "accepted_count": item.accepted_count,
        "unresolved_count": item.unresolved_count,
        "excluded_count": item.excluded_count,
        "refused_count": item.refused_count,
    }


def _parse_artifact(value: object) -> ArtifactInput:
    record = _mapping(value, "artifact")
    expected = {
        "identity",
        "role",
        "path",
        "media_type",
        "schema_version",
        "parents",
        "config_digests",
        "producer_digest",
        "object_type",
        "output_digest",
        "byte_size",
        "file_count",
    }
    if set(record) != expected:
        raise ReleaseEvidenceError("artifact fields do not match the v3 contract")
    parents = tuple(
        ArtifactReference(
            identity=_string_field(parent, "identity"),
            output_digest=_string_field(parent, "output_digest"),
        )
        for parent in _mapping_list(record, "parents")
    )
    config_digests = tuple(_string_items(record, "config_digests"))
    producer_digest = record["producer_digest"]
    if producer_digest is not None and not isinstance(producer_digest, str):
        raise ReleaseEvidenceError("artifact producer_digest must be a string or null")
    return ArtifactInput(
        identity=_string_field(record, "identity"),
        role=cast(ArtifactRole, _string_field(record, "role")),
        path=_string_field(record, "path"),
        media_type=_string_field(record, "media_type"),
        schema_version=_string_field(record, "schema_version"),
        parents=parents,
        config_digests=config_digests,
        producer_digest=producer_digest,
        output_digest=_string_field(record, "output_digest"),
    )


def _parse_gate(value: object) -> GateResult:
    record = _mapping(value, "gate")
    if set(record) != {
        "identity",
        "status",
        "required",
        "evidence_digest",
        "attestation",
        "authority_id",
    }:
        raise ReleaseEvidenceError("gate fields do not match the v3 contract")
    authority_id = record["authority_id"]
    if authority_id is not None and not isinstance(authority_id, str):
        raise ReleaseEvidenceError("gate authority_id must be a string or null")
    return GateResult(
        identity=_string_field(record, "identity"),
        status=cast(GateStatus, _string_field(record, "status")),
        required=_bool_field(record, "required"),
        evidence_digest=_string_field(record, "evidence_digest"),
        attestation=cast(
            Literal[
                "local_self_attestation",
                "independent_execution_attestation",
                "external_authority_attestation",
            ],
            _string_field(record, "attestation"),
        ),
        authority_id=authority_id,
    )


def _parse_reconciliation(value: object) -> CountReconciliation:
    record = _mapping(value, "reconciliation")
    count_fields = {
        "candidate_count",
        "eligible_count",
        "accepted_count",
        "unresolved_count",
        "excluded_count",
        "refused_count",
    }
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
        raise ReleaseEvidenceError("reconciliation fields do not match the v3 contract")
    country = record["country_code"]
    if country is not None and not isinstance(country, str):
        raise ReleaseEvidenceError("country_code must be a string or null")
    counts = {field: _optional_int_field(record, field) for field in count_fields}
    scope_record = _mapping(record["scope"], "reconciliation scope")
    if any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in scope_record.items()
    ):
        raise ReleaseEvidenceError("reconciliation scope must contain strings")
    return CountReconciliation(
        identity=_string_field(record, "identity"),
        dimension=cast(ReconciliationDimension, _string_field(record, "dimension")),
        source=_string_field(record, "source"),
        entity=_string_field(record, "entity"),
        country_code=country,
        candidate_count=counts["candidate_count"],
        eligible_count=counts["eligible_count"],
        accepted_count=counts["accepted_count"],
        unresolved_count=counts["unresolved_count"],
        excluded_count=counts["excluded_count"],
        refused_count=counts["refused_count"],
        scope=tuple(sorted(cast(Mapping[str, str], scope_record).items())),
        count_status=cast(CountStatus, _string_field(record, "count_status")),
        reason_codes=tuple(_string_items(record, "reason_codes")),
    )


def _parse_blocker(value: object) -> Blocker:
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
        "request_fingerprint",
        "request_status",
        "request_artifact_identity",
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
        raise ReleaseEvidenceError("blocker fields do not match the v3 contract")
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
        observations=tuple(_string_items(record, "observations")),
        attempts=tuple(_string_items(record, "attempts")),
        impact=_string_field(record, "impact"),
        expected_artifact=_string_field(record, "expected_artifact"),
        impacted_gates=tuple(_string_items(record, "impacted_gates")),
        next_action=_string_field(record, "next_action"),
        recheck_condition=_string_field(record, "recheck_condition"),
    )


def _record_list(manifest: Mapping[str, object], field: str) -> list[object]:
    value = manifest[field]
    if not isinstance(value, list):
        raise ReleaseEvidenceError(f"{field} must be a list")
    return value


def _mapping_list(
    record: Mapping[str, object], field: str
) -> list[Mapping[str, object]]:
    value = record[field]
    if not isinstance(value, list):
        raise ReleaseEvidenceError(f"{field} must be a list")
    return [_mapping(item, field) for item in value]


def _string_items(record: Mapping[str, object], field: str) -> list[str]:
    value = record[field]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ReleaseEvidenceError(f"{field} must be a list of strings")
    return cast(list[str], value)


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ReleaseEvidenceError(f"{field} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise ReleaseEvidenceError(f"{field} keys must be strings")
    return cast(Mapping[str, object], value)


def _string_field(record: Mapping[str, object], field: str) -> str:
    value = record[field]
    if not isinstance(value, str):
        raise ReleaseEvidenceError(f"{field} must be a string")
    return value


def _optional_string_field(record: Mapping[str, object], field: str) -> str | None:
    value = record[field]
    if value is not None and not isinstance(value, str):
        raise ReleaseEvidenceError(f"{field} must be a string or null")
    return value


def _bool_field(record: Mapping[str, object], field: str) -> bool:
    value = record[field]
    if type(value) is not bool:
        raise ReleaseEvidenceError(f"{field} must be a boolean")
    return value


def _int_field(record: Mapping[str, object], field: str) -> int:
    value = record[field]
    if type(value) is not int:
        raise ReleaseEvidenceError(f"{field} must be an integer")
    return value


def _optional_int_field(record: Mapping[str, object], field: str) -> int | None:
    value = record[field]
    if value is not None and type(value) is not int:
        raise ReleaseEvidenceError(f"{field} must be an integer or null")
    return value


def _require_commit(value: str) -> None:
    if not isinstance(value, str) or _COMMIT_PATTERN.fullmatch(value) is None:
        raise ReleaseEvidenceError(
            "code_commit must be a lowercase 40- or 64-character Git SHA"
        )


def _require_digest(value: str, field: str) -> None:
    if not isinstance(value, str) or _DIGEST_PATTERN.fullmatch(value) is None:
        raise ReleaseEvidenceError(f"{field} must be a canonical SHA-256 digest")


def _require_identity(value: str, field: str) -> None:
    if not isinstance(value, str) or _IDENTITY_PATTERN.fullmatch(value) is None:
        raise ReleaseEvidenceError(f"invalid {field}: {value!r}")


def _utc_timestamp(value: str) -> datetime:
    if _UTC_TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise ReleaseEvidenceError("blocker observation timestamp is invalid")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError as error:
        raise ReleaseEvidenceError(
            "blocker observation timestamp is invalid"
        ) from error


def _require_unique(values: Iterable[str], field: str) -> None:
    materialized = list(values)
    if len(materialized) != len(set(materialized)):
        suffix = " (output overwrite)" if field == "artifact path" else ""
        raise ReleaseEvidenceError(f"duplicate {field}{suffix}")


def _digest_json(value: object) -> str:
    return f"sha256:{hashlib.sha256(_canonical_json(value)).hexdigest()}"


def _canonical_json(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ReleaseEvidenceError("release evidence is not canonical JSON") from error
