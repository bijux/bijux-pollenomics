"""Derive canonical release-evidence requests from repository-owned policy."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from itertools import product
import json
from pathlib import Path
from typing import cast

from . import release_evidence as evidence

__all__ = ["derive_release_evidence_request", "validate_release_evidence_request"]


@dataclass(frozen=True, slots=True)
class _DerivedCount:
    candidate: int
    eligible: int
    accepted: int
    unresolved: int
    excluded: int
    refused: int
    reason_codes: tuple[str, ...] = ()


def derive_release_evidence_request(repository_root: Path) -> dict[str, object]:
    """Derive and validate the exact request for the current repository state."""
    root = evidence._repository_root(repository_root)
    policy = evidence._load_release_evidence_policy(root)
    state = evidence._repository_state(root, policy.mode)
    code_commit = _code_commit(state)
    dirty = _dirty_state(state)

    artifacts, digests = _artifact_inputs(root, policy)
    artifact_by_identity = {artifact.identity: artifact for artifact in artifacts}
    gates = _gate_results(root, policy, artifact_by_identity)
    reconciliations = _reconciliations(root, policy)
    blockers: tuple[evidence.Blocker, ...] = ()
    lock_requirements = [
        requirement
        for requirement in policy.required_artifacts
        if requirement.role == "dependency_lock"
    ]
    if len(lock_requirements) != 1:
        raise evidence.ReleaseEvidenceError(
            "release policy must govern exactly one dependency lock"
        )
    dependency_lock_digest = digests[lock_requirements[0].identity]
    if evidence._repository_state(root, policy.mode) != state:
        raise evidence.ReleaseEvidenceError(
            "repository identity changed while deriving release-evidence request"
        )

    evidence.build_release_evidence_manifest(
        root,
        code_commit=code_commit,
        dirty=dirty,
        dependency_lock_digest=dependency_lock_digest,
        artifacts=artifacts,
        gates=gates,
        reconciliations=reconciliations,
        blockers=blockers,
    )
    return {
        "schema_version": "release-evidence-request.v3",
        "code_commit": code_commit,
        "dirty": dirty,
        "dependency_lock_digest": dependency_lock_digest,
        "artifacts": [_artifact_record(artifact) for artifact in artifacts],
        "gates": [_gate_record(gate) for gate in gates],
        "reconciliations": [
            _reconciliation_record(reconciliation) for reconciliation in reconciliations
        ],
        "blockers": [_blocker_record(blocker) for blocker in blockers],
    }


def _artifact_inputs(
    root: Path, policy: evidence._ReleaseEvidencePolicy
) -> tuple[tuple[evidence.ArtifactInput, ...], dict[str, str]]:
    """Bind the exact governed artifact graph to its current repository objects."""
    digests = {
        requirement.identity: cast(
            str,
            evidence.hash_repository_object(root, requirement.path)["output_digest"],
        )
        for requirement in policy.required_artifacts
    }
    producer_digests = {
        requirement.path: digests[requirement.identity]
        for requirement in policy.required_artifacts
        if requirement.role == "producer"
    }
    artifacts = tuple(
        evidence.ArtifactInput(
            identity=requirement.identity,
            role=requirement.role,
            path=requirement.path,
            media_type=requirement.media_type,
            schema_version=requirement.schema_version,
            parents=tuple(
                evidence.ArtifactReference(identity, digests[identity])
                for identity in requirement.required_parent_identities
            ),
            config_digests=tuple(
                digests[identity] for identity in requirement.required_config_identities
            ),
            producer_digest=(
                producer_digests[requirement.producer_path]
                if requirement.producer_path is not None
                else None
            ),
            output_digest=digests[requirement.identity],
        )
        for requirement in policy.required_artifacts
    )
    return artifacts, digests


def validate_release_evidence_request(
    repository_root: Path, request: Mapping[str, object]
) -> None:
    """Reject a request that is not the exact derivation for current inputs."""
    expected = derive_release_evidence_request(repository_root)
    if dict(request) != expected:
        raise evidence.ReleaseEvidenceError(
            "release-evidence request differs from current product derivation"
        )


def _code_commit(state: Mapping[str, object]) -> str:
    value = state.get("head_commit")
    if value is None:
        return "0" * 40
    if not isinstance(value, str):
        raise evidence.ReleaseEvidenceError("repository HEAD identity is invalid")
    return value


def _dirty_state(state: Mapping[str, object]) -> bool:
    value = state.get("dirty")
    if type(value) is not bool:
        raise evidence.ReleaseEvidenceError("repository dirty state is invalid")
    return value


def _gate_results(
    root: Path,
    policy: evidence._ReleaseEvidencePolicy,
    artifacts: Mapping[str, evidence.ArtifactInput],
) -> tuple[evidence.GateResult, ...]:
    gates: list[evidence.GateResult] = []
    for gate_id in sorted(policy.required_gate_ids):
        matches = [
            artifact
            for artifact in artifacts.values()
            if artifact.role == "validation_result"
            and artifact.path.rsplit("/", maxsplit=1)[-1] == f"{gate_id}.json"
        ]
        if len(matches) != 1:
            raise evidence.ReleaseEvidenceError(
                f"release policy lacks exact gate artifact: {gate_id}"
            )
        artifact = matches[0]
        record = evidence.validate_recorded_gate(root, artifact.path)
        if record.get("gate_id") != gate_id:
            raise evidence.ReleaseEvidenceError(
                f"recorded gate identity does not match policy: {gate_id}"
            )
        attestation = record.get("attestation")
        if not isinstance(attestation, Mapping) or attestation.get("class") != (
            "local_self_attestation"
        ):
            raise evidence.ReleaseEvidenceError(
                f"recorded gate attestation is not locally governed: {gate_id}"
            )
        status = record.get("status")
        required = record.get("required")
        if status not in evidence._GATE_STATUSES or type(required) is not bool:
            raise evidence.ReleaseEvidenceError(
                f"recorded gate result is invalid: {gate_id}"
            )
        gates.append(
            evidence.GateResult(
                identity=gate_id,
                status=cast(evidence.GateStatus, status),
                required=required,
                evidence_digest=artifact.output_digest,
                attestation="local_self_attestation",
                authority_id=None,
            )
        )
    return tuple(gates)


def _reconciliations(
    root: Path, policy: evidence._ReleaseEvidencePolicy
) -> tuple[evidence.CountReconciliation, ...]:
    rows: list[evidence.CountReconciliation] = []
    for requirement in policy.required_reconciliations:
        stem = f"{requirement.source}.{requirement.entity}"
        if requirement.dimension == "country":
            values = _governed_country_values(root, requirement)
            partitions: list[evidence.CountReconciliation] = []
            for country_code in sorted(evidence._COUNTRIES):
                if values is None:
                    partition = _unavailable_count(
                        f"{stem}.country.{country_code.lower()}",
                        requirement,
                        "country",
                        country_code=country_code,
                    )
                else:
                    partition = _derived_count(
                        f"{stem}.country.{country_code.lower()}",
                        requirement,
                        "country",
                        values[country_code],
                        country_code=country_code,
                    )
                partitions.append(partition)
            rows.append(
                _aggregate_source_count(f"{stem}.source", requirement, partitions)
            )
            rows.extend(partitions)
            continue
        scope_partitions = _propagation_scope_counts(root, requirement)
        if scope_partitions is None:
            scope_partitions = []
            scope_keys = tuple(key for key, _values in requirement.scope_values)
            for scope_values in product(
                *(values for _key, values in requirement.scope_values)
            ):
                scope = tuple(zip(scope_keys, scope_values, strict=True))
                scope_partitions.append(
                    _unavailable_count(
                        f"{stem}.scope.{_scope_suffix(scope)}",
                        requirement,
                        "scope",
                        scope=scope,
                    )
                )
        rows.append(
            _aggregate_source_count(f"{stem}.source", requirement, scope_partitions)
        )
        rows.extend(scope_partitions)
    return tuple(rows)


def _governed_country_values(
    root: Path, requirement: evidence._RequiredReconciliation
) -> dict[str, _DerivedCount] | None:
    if requirement.derivation_adapter == "classification_observation_memberships":
        return _classification_country_values(root, requirement.derivation_metric)
    if requirement.derivation_adapter == "unavailable":
        return None
    if requirement.derivation_adapter == "neotoma_relational_reconciliation":
        document = _optional_json_object(
            root, "data/neotoma/relational/reconciliation.json"
        )
        reconciliation = document.get("reconciliation") if document else None
        country_counts = (
            reconciliation.get("country_counts")
            if isinstance(reconciliation, Mapping)
            else None
        )
        if isinstance(country_counts, Mapping):
            values: dict[str, _DerivedCount] = {}
            for country in evidence._COUNTRIES:
                if country == "OUTSIDE":
                    values[country] = _partition_posture(country, 0, ())
                    continue
                record = country_counts.get(country)
                value = (
                    record.get(requirement.derivation_metric)
                    if isinstance(record, Mapping)
                    else None
                )
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    return None
                values[country] = _partition_posture(country, value, ())
            return values
    if requirement.derivation_adapter != "country_coverage":
        return None
    ledger = _optional_json_object(root, "data/country_dimension_coverage.json")
    cells = ledger.get("cells") if ledger else None
    if not isinstance(cells, list):
        return None
    values = {}
    for country in evidence._COUNTRIES:
        matches = [
            cell
            for cell in cells
            if isinstance(cell, Mapping)
            and cell.get("source_family") == requirement.source
            and cell.get("country_dimension") == "governed_assignment"
            and cell.get("resolution") == "source"
            and cell.get("country_code") == country
        ]
        if len(matches) != 1:
            return None
        cell = matches[0]
        counts = cell.get("counts")
        value = (
            counts.get(requirement.derivation_metric)
            if isinstance(counts, Mapping)
            else None
        )
        reason_codes = cell.get("reason_codes")
        if (
            value is None
            and isinstance(counts, Mapping)
            and counts.get("sites") == 0
            and reason_codes == ["explicit_empty_partition"]
        ):
            value = 0
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return None
        if not isinstance(reason_codes, list) or any(
            not isinstance(item, str) for item in reason_codes
        ):
            return None
        values[country] = _partition_posture(
            country, value, tuple(sorted(cast(list[str], reason_codes)))
        )
    return values


def _classification_country_values(
    root: Path, metric: str
) -> dict[str, _DerivedCount] | None:
    bundle = "artifacts/execution-control/classification/neotoma-audit-f0e5a830"
    document = _optional_json_object(root, f"{bundle}/observation_memberships.json")
    records = document.get("records") if document else None
    if not isinstance(records, list):
        return None
    concept_memberships: dict[str, dict[str, set[str]]] = {
        country: {
            "accepted": set(),
            "unresolved": set(),
            "excluded": set(),
            "refused": set(),
        }
        for country in evidence._COUNTRIES
    }
    for record in records:
        if not isinstance(record, Mapping):
            return None
        country = record.get("governed_country_code")
        concept = record.get("classification_concept_id")
        status = record.get("mapping_status")
        if country not in concept_memberships or not isinstance(concept, str):
            return None
        bucket: str | None
        if status in {
            "accepted",
            "accepted_qualified",
        }:
            bucket = "accepted"
        elif status == "unmapped" or status == "contested":
            bucket = "unresolved"
        elif status == "not_applicable":
            bucket = "excluded"
        elif status == "refused":
            bucket = "refused"
        else:
            return None
        selected = (
            metric == "distinct_concepts"
            or (metric == "mapped_concepts" and bucket == "accepted")
            or (metric == "unmapped_concepts" and status == "unmapped")
            or (metric == "ambiguous_concepts" and status in {"contested", "refused"})
        )
        if selected:
            concept_memberships[cast(str, country)][bucket].add(concept)
    return {
        country: _DerivedCount(
            candidate=sum(len(concepts) for concepts in parts.values()),
            eligible=len(parts["accepted"]) + len(parts["refused"]),
            accepted=len(parts["accepted"]),
            unresolved=len(parts["unresolved"]),
            excluded=len(parts["excluded"]),
            refused=len(parts["refused"]),
        )
        for country, parts in concept_memberships.items()
    }


def _partition_posture(
    country: str, value: int, reason_codes: tuple[str, ...]
) -> _DerivedCount:
    if country == "UNASSIGNED":
        return _DerivedCount(value, 0, 0, value, 0, 0, reason_codes)
    if country == "OUTSIDE":
        return _DerivedCount(value, 0, 0, 0, value, 0, reason_codes)
    return _DerivedCount(value, value, value, 0, 0, 0, reason_codes)


def _propagation_scope_counts(
    root: Path, requirement: evidence._RequiredReconciliation
) -> list[evidence.CountReconciliation] | None:
    if requirement.derivation_adapter != "propagation_primary_reconciliation":
        return None
    document = _optional_json_object(
        root,
        "artifacts/execution-control/propagation/"
        "neotoma-pollen-release-refusal-87ac6d28/"
        "primary_scenario_reconciliation.json",
    )
    reconciliation = document.get("reconciliation") if document else None
    if not isinstance(reconciliation, Mapping):
        return None
    stem = f"{requirement.source}.{requirement.entity}"
    scopes = _required_scopes(requirement)
    if requirement.derivation_metric == "candidate_statuses":
        status_counts = reconciliation.get("status_counts")
        if not isinstance(status_counts, Mapping):
            return None
        rows: list[evidence.CountReconciliation] = []
        for scope in scopes:
            status = dict(scope)["status"]
            value = status_counts.get(status)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                return None
            rows.append(
                _propagation_status_count(stem, requirement, scope, status, value)
            )
        return rows
    total_field = {
        "evaluated_pairs": "evaluated_pair_count",
        "nodes": "input_event_count",
        "pair_refusals": "refused_pair_count",
    }.get(requirement.derivation_metric)
    total = reconciliation.get(total_field) if total_field else None
    if isinstance(total, bool) or not isinstance(total, int) or total != 0:
        return None
    return [
        _reported_count(
            f"{stem}.scope.{_scope_suffix(scope)}",
            requirement,
            "scope",
            0,
            scope=scope,
        )
        for scope in scopes
    ]


def _required_scopes(
    requirement: evidence._RequiredReconciliation,
) -> tuple[tuple[tuple[str, str], ...], ...]:
    keys = tuple(key for key, _values in requirement.scope_values)
    return tuple(
        tuple(zip(keys, values, strict=True))
        for values in product(*(values for _key, values in requirement.scope_values))
    )


def _scope_suffix(scope: tuple[tuple[str, str], ...]) -> str:
    return ".".join(f"{key}-{value.lower()}" for key, value in scope)


def _propagation_status_count(
    stem: str,
    requirement: evidence._RequiredReconciliation,
    scope: tuple[tuple[str, str], ...],
    status: str,
    value: int,
) -> evidence.CountReconciliation:
    fields = {
        "candidate_count": value,
        "eligible_count": 0,
        "accepted_count": 0,
        "unresolved_count": 0,
        "excluded_count": 0,
        "refused_count": 0,
    }
    if status in {"definite_candidate", "possible_candidate"}:
        fields["eligible_count"] = value
        fields["accepted_count"] = value
    elif status in {"indeterminate_order", "unresolved"}:
        fields["unresolved_count"] = value
    else:
        fields["excluded_count"] = value
    return evidence.CountReconciliation(
        identity=f"{stem}.scope.{_scope_suffix(scope)}",
        dimension="scope",
        source=requirement.source,
        entity=requirement.entity,
        country_code=None,
        scope=scope,
        count_status="reported",
        reason_codes=(),
        **fields,
    )


def _reported_count(
    identity: str,
    requirement: evidence._RequiredReconciliation,
    dimension: evidence.ReconciliationDimension,
    value: int,
    *,
    country_code: str | None = None,
    scope: tuple[tuple[str, str], ...] = (),
) -> evidence.CountReconciliation:
    return evidence.CountReconciliation(
        identity=identity,
        dimension=dimension,
        source=requirement.source,
        entity=requirement.entity,
        country_code=country_code,
        candidate_count=value,
        eligible_count=value,
        accepted_count=value,
        unresolved_count=0,
        excluded_count=0,
        refused_count=0,
        scope=scope,
        count_status="reported",
        reason_codes=(),
    )


def _derived_count(
    identity: str,
    requirement: evidence._RequiredReconciliation,
    dimension: evidence.ReconciliationDimension,
    value: _DerivedCount,
    *,
    country_code: str | None = None,
    scope: tuple[tuple[str, str], ...] = (),
) -> evidence.CountReconciliation:
    return evidence.CountReconciliation(
        identity=identity,
        dimension=dimension,
        source=requirement.source,
        entity=requirement.entity,
        country_code=country_code,
        candidate_count=value.candidate,
        eligible_count=value.eligible,
        accepted_count=value.accepted,
        unresolved_count=value.unresolved,
        excluded_count=value.excluded,
        refused_count=value.refused,
        scope=scope,
        count_status="reported",
        reason_codes=value.reason_codes,
    )


def _aggregate_source_count(
    identity: str,
    requirement: evidence._RequiredReconciliation,
    partitions: list[evidence.CountReconciliation],
) -> evidence.CountReconciliation:
    if any(item.count_status != "reported" for item in partitions):
        return _unavailable_count(identity, requirement, "source")
    fields = {
        field: sum(cast(int, getattr(item, field)) for item in partitions)
        for field in (
            "candidate_count",
            "eligible_count",
            "accepted_count",
            "unresolved_count",
            "excluded_count",
            "refused_count",
        )
    }
    return evidence.CountReconciliation(
        identity=identity,
        dimension="source",
        source=requirement.source,
        entity=requirement.entity,
        country_code=None,
        scope=(),
        count_status="reported",
        reason_codes=(),
        **fields,
    )


def _unavailable_count(
    identity: str,
    requirement: evidence._RequiredReconciliation,
    dimension: evidence.ReconciliationDimension,
    *,
    country_code: str | None = None,
    scope: tuple[tuple[str, str], ...] = (),
) -> evidence.CountReconciliation:
    return evidence.CountReconciliation(
        identity=identity,
        dimension=dimension,
        source=requirement.source,
        entity=requirement.entity,
        country_code=country_code,
        candidate_count=None,
        eligible_count=None,
        accepted_count=None,
        unresolved_count=None,
        excluded_count=None,
        refused_count=None,
        scope=scope,
        count_status=requirement.unavailable_status,
        reason_codes=(requirement.unavailable_reason_code,),
    )


def _optional_json_object(
    root: Path, relative_path: str
) -> Mapping[str, object] | None:
    try:
        value = json.loads(evidence._read_repository_file(root, relative_path))
    except (evidence.ReleaseEvidenceError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, Mapping) else None


def _artifact_record(artifact: evidence.ArtifactInput) -> dict[str, object]:
    return {
        "identity": artifact.identity,
        "role": artifact.role,
        "path": artifact.path,
        "media_type": artifact.media_type,
        "schema_version": artifact.schema_version,
        "parents": [
            {
                "identity": parent.identity,
                "output_digest": parent.output_digest,
            }
            for parent in artifact.parents
        ],
        "config_digests": list(artifact.config_digests),
        "producer_digest": artifact.producer_digest,
        "output_digest": artifact.output_digest,
    }


def _gate_record(gate: evidence.GateResult) -> dict[str, object]:
    return {
        "identity": gate.identity,
        "status": gate.status,
        "required": gate.required,
        "evidence_digest": gate.evidence_digest,
        "attestation": gate.attestation,
        "authority_id": gate.authority_id,
    }


def _reconciliation_record(
    item: evidence.CountReconciliation,
) -> dict[str, object]:
    return {
        "identity": item.identity,
        "dimension": item.dimension,
        "source": item.source,
        "entity": item.entity,
        "country_code": item.country_code,
        "candidate_count": item.candidate_count,
        "eligible_count": item.eligible_count,
        "accepted_count": item.accepted_count,
        "unresolved_count": item.unresolved_count,
        "excluded_count": item.excluded_count,
        "refused_count": item.refused_count,
        "scope": dict(item.scope),
        "count_status": item.count_status,
        "reason_codes": list(item.reason_codes),
    }


def _blocker_record(blocker: evidence.Blocker) -> dict[str, object]:
    return {
        "identity": blocker.identity,
        "reason_code": blocker.reason_code,
        "evidence_digest": blocker.evidence_digest,
        "kind": blocker.kind,
        "required_scope": blocker.required_scope,
        "owner": blocker.owner,
        "first_observed_at": blocker.first_observed_at,
        "last_observed_at": blocker.last_observed_at,
        "request_status": blocker.request_status,
        "request_artifact_identity": blocker.request_artifact_identity,
        "request_fingerprint": blocker.request_fingerprint,
        "response_class": blocker.response_class,
        "observations": list(blocker.observations),
        "attempts": list(blocker.attempts),
        "impact": blocker.impact,
        "expected_artifact": blocker.expected_artifact,
        "impacted_gates": list(blocker.impacted_gates),
        "next_action": blocker.next_action,
        "recheck_condition": blocker.recheck_condition,
    }
