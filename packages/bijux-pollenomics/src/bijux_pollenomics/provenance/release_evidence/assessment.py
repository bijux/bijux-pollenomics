"""Gate, reconciliation, blocker, and release-decision assessment."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from itertools import product
from pathlib import Path
from typing import cast

from .codec import (
    _counts,
    _require_digest,
    _require_identity,
    _require_unique,
    _string_field,
    _utc_timestamp,
)
from .models import (
    _COUNTRIES,
    _GATE_STATUSES,
    Blocker,
    CountReconciliation,
    GateResult,
    ReleaseEvidenceError,
    _ReleaseEvidencePolicy,
)
from .recorded_gates import validate_recorded_gate


def _validate_gates(
    root: Path,
    gates: Sequence[GateResult],
    records: Sequence[Mapping[str, object]],
    policy: _ReleaseEvidencePolicy,
) -> None:
    if not gates:
        raise ReleaseEvidenceError("at least one required gate result is required")
    _require_unique((gate.identity for gate in gates), "gate identity")
    _require_unique((gate.evidence_digest for gate in gates), "gate evidence digest")
    validation_records = [
        record for record in records if record["role"] == "validation_result"
    ]
    if frozenset(gate.identity for gate in gates) != policy.required_gate_ids:
        raise ReleaseEvidenceError("gate inventory does not match product policy")
    required_flags = {gate.required for gate in gates}
    if required_flags != {True}:
        raise ReleaseEvidenceError("every product-policy gate must be required")
    by_digest: dict[str, list[Mapping[str, object]]] = {}
    for record in validation_records:
        by_digest.setdefault(_string_field(record, "output_digest"), []).append(record)
    for gate in gates:
        _require_identity(gate.identity, "gate identity")
        if gate.status not in _GATE_STATUSES:
            raise ReleaseEvidenceError(f"invalid gate status: {gate.status}")
        if type(gate.required) is not bool:
            raise ReleaseEvidenceError("gate required flag must be a boolean")
        _require_digest(gate.evidence_digest, "gate evidence digest")
        if gate.attestation not in {
            "local_self_attestation",
            "independent_execution_attestation",
            "external_authority_attestation",
        }:
            raise ReleaseEvidenceError(f"invalid gate attestation: {gate.identity}")
        if gate.attestation == "local_self_attestation":
            if gate.authority_id is not None:
                raise ReleaseEvidenceError(
                    "local gate cannot assert external authority"
                )
        else:
            raise ReleaseEvidenceError(
                "non-local gate attestation trust is not configured"
            )
        evidence = by_digest.get(gate.evidence_digest, [])
        if len(evidence) != 1:
            raise ReleaseEvidenceError(
                f"gate evidence is not a validation artifact: {gate.identity}"
            )
        record = evidence[0]
        if gate.attestation == "local_self_attestation":
            if record["schema_version"] != "recorded-gate.v4":
                raise ReleaseEvidenceError(
                    f"gate evidence is not recorded-gate.v4: {gate.identity}"
                )
            validate_recorded_gate(
                root,
                _string_field(record, "path"),
                expected_gate=gate,
            )
    if len(validation_records) != len(gates):
        raise ReleaseEvidenceError(
            "every validation artifact must map to exactly one gate result"
        )


def _validate_reconciliations(
    items: Sequence[CountReconciliation], policy: _ReleaseEvidencePolicy
) -> None:
    if not items:
        raise ReleaseEvidenceError("source and country reconciliations are required")
    _require_unique((item.identity for item in items), "reconciliation identity")
    _require_unique(
        (
            f"{item.source}\0{item.entity}\0{item.dimension}\0{item.country_code}\0{item.scope}"
            for item in items
        ),
        "reconciliation key",
    )
    grouped: dict[tuple[str, str], dict[str, list[CountReconciliation]]] = {}
    allowed_scope_keys = {
        "country_code",
        "target_country_code",
        "resolution",
        "feature",
        "unit",
        "status",
    }
    for item in items:
        _require_identity(item.identity, "reconciliation identity")
        if item.dimension not in {"source", "country", "scope"}:
            raise ReleaseEvidenceError(
                f"invalid reconciliation dimension: {item.dimension}"
            )
        if not item.source.strip() or not item.entity.strip():
            raise ReleaseEvidenceError("reconciliation source/entity must be non-empty")
        if item.dimension == "source" and item.country_code is not None:
            raise ReleaseEvidenceError(
                "source reconciliation cannot carry a country code"
            )
        if item.dimension == "country" and item.country_code not in _COUNTRIES:
            raise ReleaseEvidenceError(f"invalid country code: {item.country_code}")
        if item.dimension != "country" and item.country_code is not None:
            raise ReleaseEvidenceError(
                "only country reconciliation can carry country_code"
            )
        if item.dimension == "scope" and not item.scope:
            raise ReleaseEvidenceError("scoped reconciliation requires scope fields")
        if item.dimension != "scope" and item.scope:
            raise ReleaseEvidenceError(
                "only scoped reconciliation can carry scope fields"
            )
        scope_keys = [key for key, _value in item.scope]
        if scope_keys != sorted(scope_keys) or len(scope_keys) != len(set(scope_keys)):
            raise ReleaseEvidenceError(
                "reconciliation scope keys must be unique/sorted"
            )
        if set(scope_keys) - allowed_scope_keys or any(
            not value for _key, value in item.scope
        ):
            raise ReleaseEvidenceError("reconciliation scope is invalid")
        if item.count_status not in {"reported", "unavailable", "refused"}:
            raise ReleaseEvidenceError(
                f"invalid reconciliation count status: {item.count_status}"
            )
        if list(item.reason_codes) != sorted(item.reason_codes):
            raise ReleaseEvidenceError("reconciliation reason codes must be sorted")
        _require_unique(item.reason_codes, "reconciliation reason code")
        for reason_code in item.reason_codes:
            _require_identity(reason_code, "reconciliation reason code")
        counts = _counts(item)
        if item.count_status == "reported" and any(
            type(value) is not int or value < 0 for value in counts.values()
        ):
            raise ReleaseEvidenceError(
                f"reported counts must be non-null non-negative integers: {item.identity}"
            )
        if item.count_status != "reported" and (
            any(value is not None for value in counts.values()) or not item.reason_codes
        ):
            raise ReleaseEvidenceError(
                f"unavailable/refused counts must be null and reason-coded: {item.identity}"
            )
        if item.count_status == "reported" and item.eligible_count != cast(
            int, item.accepted_count
        ) + cast(int, item.refused_count):
            raise ReleaseEvidenceError(
                f"eligible count is inconsistent: {item.identity}"
            )
        if item.count_status == "reported" and (
            item.candidate_count
            != cast(int, item.eligible_count)
            + cast(int, item.unresolved_count)
            + cast(int, item.excluded_count)
        ):
            raise ReleaseEvidenceError(
                f"candidate denominator is inconsistent: {item.identity}"
            )
        group = grouped.setdefault(
            (item.source, item.entity), {"source": [], "country": [], "scope": []}
        )
        group[item.dimension].append(item)

    for key, dimensions in grouped.items():
        source_rows = dimensions["source"]
        country_rows = dimensions["country"]
        if len(source_rows) != 1:
            raise ReleaseEvidenceError(
                f"one source reconciliation is required for {key}"
            )
        scope_rows = dimensions["scope"]
        if country_rows and scope_rows:
            raise ReleaseEvidenceError(
                f"reconciliation group mixes country and extensible scopes: {key}"
            )
        if country_rows:
            country_codes = {item.country_code for item in country_rows}
            if len(country_rows) != len(_COUNTRIES) or any(
                code not in country_codes for code in _COUNTRIES
            ):
                raise ReleaseEvidenceError(
                    f"complete country reconciliation is required for {key}"
                )
        partition_rows = country_rows or scope_rows
        if not partition_rows:
            raise ReleaseEvidenceError(
                f"reconciliation partitions are required for {key}"
            )
        source_counts = _counts(source_rows[0])
        if any(
            item.count_status != source_rows[0].count_status for item in partition_rows
        ):
            raise ReleaseEvidenceError(
                f"source and partition availability statuses differ for {key}"
            )
        for field, source_count in source_counts.items():
            partition_values = [_counts(item)[field] for item in partition_rows]
            if source_count is None:
                reconciles = all(value is None for value in partition_values)
            else:
                reconciles = all(value is not None for value in partition_values) and (
                    source_count == sum(cast(int, value) for value in partition_values)
                )
            if not reconciles:
                raise ReleaseEvidenceError(
                    f"country/source count mismatch (partition model) for {key}: {field}"
                )

    requirements = {
        (item.source, item.entity): item for item in policy.required_reconciliations
    }
    missing_groups = sorted(set(requirements) - set(grouped))
    if missing_groups:
        raise ReleaseEvidenceError(
            f"missing required reconciliation groups: {missing_groups}"
        )
    unexpected_groups = sorted(set(grouped) - set(requirements))
    if unexpected_groups:
        raise ReleaseEvidenceError(
            f"unexpected reconciliation groups: {unexpected_groups}"
        )
    for key, requirement in requirements.items():
        dimensions = grouped[key]
        if requirement.dimension == "country":
            if dimensions["scope"]:
                raise ReleaseEvidenceError(
                    f"country reconciliation required by policy for {key}"
                )
            continue
        if dimensions["country"]:
            raise ReleaseEvidenceError(
                f"extensible scope reconciliation required by policy for {key}"
            )
        expected_scope_keys = tuple(key for key, _values in requirement.scope_values)
        expected_scopes = {
            tuple(zip(expected_scope_keys, values, strict=True))
            for values in product(
                *(values for _key, values in requirement.scope_values)
            )
        }
        observed_scopes = {item.scope for item in dimensions["scope"]}
        if observed_scopes != expected_scopes:
            raise ReleaseEvidenceError(f"scope partition inventory mismatch for {key}")


def _validate_blockers(
    blockers: Sequence[Blocker],
    records: Sequence[Mapping[str, object]],
    gates: Sequence[GateResult],
    policy: _ReleaseEvidencePolicy,
) -> None:
    _require_unique((blocker.identity for blocker in blockers), "blocker identity")
    evidence_digests = {_string_field(record, "output_digest") for record in records}
    for blocker in blockers:
        _require_identity(blocker.identity, "blocker identity")
        _require_identity(blocker.reason_code, "blocker reason_code")
        _require_digest(blocker.evidence_digest, "blocker evidence digest")
        if blocker.kind not in {"external", "unverified", "refused", "reduced_scope"}:
            raise ReleaseEvidenceError(f"invalid blocker kind: {blocker.identity}")
        required_text = {
            "required_scope": blocker.required_scope,
            "owner": blocker.owner,
            "first_observed_at": blocker.first_observed_at,
            "last_observed_at": blocker.last_observed_at,
            "response_class": blocker.response_class,
            "impact": blocker.impact,
            "expected_artifact": blocker.expected_artifact,
            "next_action": blocker.next_action,
            "recheck_condition": blocker.recheck_condition,
        }
        if any(not value.strip() for value in required_text.values()):
            raise ReleaseEvidenceError(
                f"blocker lacks actionable fields: {blocker.identity}"
            )
        first_observed = _utc_timestamp(blocker.first_observed_at)
        last_observed = _utc_timestamp(blocker.last_observed_at)
        if first_observed > last_observed:
            raise ReleaseEvidenceError(
                f"blocker observation interval is invalid: {blocker.identity}"
            )
        if blocker.request_status == "governed":
            if (
                blocker.request_artifact_identity is None
                or blocker.request_fingerprint is None
            ):
                raise ReleaseEvidenceError(
                    f"governed blocker request lacks artifact identity: {blocker.identity}"
                )
            _require_digest(
                blocker.request_fingerprint,
                f"blocker request fingerprint: {blocker.identity}",
            )
            if (
                blocker.request_artifact_identity
                not in policy.governed_request_artifact_ids
            ):
                raise ReleaseEvidenceError(
                    f"blocker request artifact is not authorized: {blocker.identity}"
                )
            request_records = [
                record
                for record in records
                if record["identity"] == blocker.request_artifact_identity
                and record["output_digest"] == blocker.request_fingerprint
            ]
            if len(request_records) != 1:
                raise ReleaseEvidenceError(
                    f"blocker request artifact is not governed: {blocker.identity}"
                )
        elif blocker.request_status == "refused":
            if (
                blocker.request_artifact_identity is not None
                or blocker.request_fingerprint is not None
            ):
                raise ReleaseEvidenceError(
                    f"refused blocker request cannot assert a fingerprint: {blocker.identity}"
                )
        else:
            raise ReleaseEvidenceError(
                f"invalid blocker request status: {blocker.identity}"
            )
        if (
            not blocker.observations
            or not blocker.attempts
            or not blocker.impacted_gates
        ):
            raise ReleaseEvidenceError(
                f"blocker lacks observations, attempts, or impacted gates: {blocker.identity}"
            )
        if any(not item.strip() for item in (*blocker.observations, *blocker.attempts)):
            raise ReleaseEvidenceError(
                f"blocker has empty observation or attempt: {blocker.identity}"
            )
        if list(blocker.impacted_gates) != sorted(blocker.impacted_gates):
            raise ReleaseEvidenceError(
                f"blocker impacted gates are not sorted: {blocker.identity}"
            )
        unknown_gates = set(blocker.impacted_gates) - policy.required_gate_ids
        if unknown_gates:
            raise ReleaseEvidenceError(
                f"blocker names unknown impacted gates: {blocker.identity}"
            )
        if blocker.evidence_digest not in evidence_digests:
            raise ReleaseEvidenceError(
                f"blocker evidence is not in the manifest: {blocker.identity}"
            )
        evidence_identities = {
            _string_field(record, "identity")
            for record in records
            if record["output_digest"] == blocker.evidence_digest
        }
        gate_evidence_identities = {
            gate.identity: next(
                _string_field(record, "identity")
                for record in records
                if record["output_digest"] == gate.evidence_digest
            )
            for gate in gates
        }
        for gate_id in blocker.impacted_gates:
            relevant = _policy_artifact_ancestor_identities(
                gate_evidence_identities[gate_id], policy
            )
            if evidence_identities.isdisjoint(relevant):
                raise ReleaseEvidenceError(
                    f"blocker evidence is unrelated to impacted gate: {blocker.identity}"
                )


def _policy_artifact_ancestor_identities(
    identity: str, policy: _ReleaseEvidencePolicy
) -> set[str]:
    requirements = {item.identity: item for item in policy.required_artifacts}
    found = {identity}
    ready = [identity]
    while ready:
        current = ready.pop()
        for parent in requirements[current].required_parent_identities:
            if parent not in found:
                found.add(parent)
                ready.append(parent)
    return found


def _release_decision(
    dirty: bool, gates: Sequence[GateResult], blockers: Sequence[Blocker]
) -> dict[str, object]:
    required_nonpass = [
        gate for gate in gates if gate.required and gate.status != "PASS"
    ]
    reasons = [
        f"required_gate_{gate.status.lower()}:{gate.identity}"
        for gate in required_nonpass
    ]
    reasons.extend(
        f"required_gate_not_independently_attested:{gate.identity}"
        for gate in gates
        if gate.required
        and gate.status == "PASS"
        and gate.attestation == "local_self_attestation"
    )
    reasons.extend(f"blocker:{blocker.reason_code}" for blocker in blockers)
    if dirty:
        reasons.append("candidate_dirty")
    release_ready = not reasons
    blocker_kinds = {blocker.kind for blocker in blockers}
    if release_ready:
        status = "verified_complete"
    elif any(gate.status == "FAIL" for gate in required_nonpass):
        status = "failed"
    elif "external" in blocker_kinds:
        status = "external_blocked"
    elif "refused" in blocker_kinds:
        status = "refused_invalid"
    elif (
        blocker_kinds == {"reduced_scope"}
        and not required_nonpass
        and all(gate.attestation != "local_self_attestation" for gate in gates)
    ):
        status = "verified_partial"
    elif any(gate.status == "BLOCKED_EXTERNAL" for gate in required_nonpass):
        status = "external_blocked"
    else:
        status = "implemented_unverified"
    return {
        "release_ready": release_ready,
        "status": status,
        "reason_codes": sorted(reasons),
    }
