"""Derive canonical release-evidence requests from repository-owned policy."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .. import release_evidence as evidence
from ..release_evidence.models import _ReleaseEvidencePolicy
from ..release_evidence.policy import _load_release_evidence_policy
from ..release_evidence.repository import (
    _hash_repository_object,
    _repository_root,
    _repository_state,
)
from .artifacts import artifact_record, derive_artifact_inputs
from .blockers import blocker_record
from .gates import derive_gate_results, gate_record
from .identity import code_commit, dirty_state
from .reconciliation import derive_reconciliations, reconciliation_record


def derive_release_evidence_request(repository_root: Path) -> dict[str, object]:
    """Derive and validate the exact request for the current repository state."""
    root = _repository_root(repository_root)
    policy = _load_release_evidence_policy(root)
    state = _repository_state(root, policy.mode)
    artifacts, digests = _artifact_inputs(root, policy)
    gates = _gate_results(
        root,
        policy,
        {artifact.identity: artifact for artifact in artifacts},
    )
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
    if _repository_state(root, policy.mode) != state:
        raise evidence.ReleaseEvidenceError(
            "repository identity changed while deriving release-evidence request"
        )

    request = {
        "schema_version": "release-evidence-request.v3",
        "code_commit": code_commit(state),
        "dirty": dirty_state(state),
        "dependency_lock_digest": dependency_lock_digest,
        "artifacts": [artifact_record(artifact) for artifact in artifacts],
        "gates": [gate_record(gate) for gate in gates],
        "reconciliations": [
            reconciliation_record(reconciliation) for reconciliation in reconciliations
        ],
        "blockers": [blocker_record(blocker) for blocker in blockers],
    }
    evidence.build_release_evidence_manifest(
        root,
        code_commit=code_commit(state),
        dirty=dirty_state(state),
        dependency_lock_digest=dependency_lock_digest,
        artifacts=artifacts,
        gates=gates,
        reconciliations=reconciliations,
        blockers=blockers,
    )
    return request


def validate_release_evidence_request(
    repository_root: Path, request: Mapping[str, object]
) -> None:
    """Reject a request that is not the exact derivation for current inputs."""
    expected = derive_release_evidence_request(repository_root)
    if dict(request) != expected:
        raise evidence.ReleaseEvidenceError(
            "release-evidence request differs from current product derivation"
        )


def _artifact_inputs(
    root: Path, policy: _ReleaseEvidencePolicy
) -> tuple[tuple[evidence.ArtifactInput, ...], dict[str, str]]:
    return derive_artifact_inputs(
        root,
        policy,
        hash_repository_object=_hash_repository_object,
    )


def _gate_results(
    root: Path,
    policy: _ReleaseEvidencePolicy,
    artifacts: Mapping[str, evidence.ArtifactInput],
) -> tuple[evidence.GateResult, ...]:
    return derive_gate_results(
        root,
        policy,
        artifacts,
        validate_recorded_gate=evidence.validate_recorded_gate,
    )


def _reconciliations(
    root: Path, policy: _ReleaseEvidencePolicy
) -> tuple[evidence.CountReconciliation, ...]:
    return derive_reconciliations(root, policy)
