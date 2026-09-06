"""Derive canonical release-evidence requests from repository-owned policy."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .. import release_evidence as evidence
from ..release_evidence.models import _ReleaseEvidencePolicy
from ..release_evidence.policy import (
    _load_release_evidence_policy as _load_release_evidence_policy,
)
from ..release_evidence.repository import (
    _hash_repository_object as _hash_repository_object,
)
from ..release_evidence.repository import (
    _read_repository_file as _read_repository_file,
)
from ..release_evidence.repository import (
    _repository_root as _repository_root,
)
from ..release_evidence.repository import (
    _repository_state as _repository_state,
)
from .artifacts import artifact_record as _artifact_record
from .artifacts import derive_artifact_inputs
from .blockers import blocker_record as _blocker_record
from .gates import derive_gate_results
from .gates import gate_record as _gate_record
from .identity import code_commit as _code_commit
from .identity import dirty_state as _dirty_state
from .reconciliation import (
    DerivedCount as _DerivedCount,
)
from .reconciliation import (
    aggregate_source_count as _aggregate_source_count,
)
from .reconciliation import (
    classification_country_values as _classification_country_values,
)
from .reconciliation import (
    derive_reconciliations,
)
from .reconciliation import (
    derived_count as _derived_count,
)
from .reconciliation import (
    governed_country_values as _governed_country_values,
)
from .reconciliation import (
    optional_json_object as _optional_json_object,
)
from .reconciliation import (
    partition_posture as _partition_posture,
)
from .reconciliation import (
    propagation_scope_counts as _propagation_scope_counts,
)
from .reconciliation import (
    propagation_status_count as _propagation_status_count,
)
from .reconciliation import (
    reconciliation_record as _reconciliation_record,
)
from .reconciliation import (
    reported_count as _reported_count,
)
from .reconciliation import (
    required_scopes as _required_scopes,
)
from .reconciliation import (
    scope_suffix as _scope_suffix,
)
from .reconciliation import (
    sead_chronology_claim_values as _sead_chronology_claim_values,
)
from .reconciliation import (
    unavailable_count as _unavailable_count,
)

__all__ = ["derive_release_evidence_request", "validate_release_evidence_request"]

# Existing verification code imports these internal derivation seams directly.
# Keep them available at the facade while their implementations have single owners.
_PRIVATE_COMPATIBILITY = (
    _DerivedCount,
    _aggregate_source_count,
    _classification_country_values,
    _derived_count,
    _governed_country_values,
    _optional_json_object,
    _partition_posture,
    _propagation_scope_counts,
    _propagation_status_count,
    _read_repository_file,
    _reported_count,
    _required_scopes,
    _scope_suffix,
    _sead_chronology_claim_values,
    _unavailable_count,
)


def derive_release_evidence_request(repository_root: Path) -> dict[str, object]:
    """Derive and validate the exact request for the current repository state."""
    root = _repository_root(repository_root)
    policy = _load_release_evidence_policy(root)
    state = _repository_state(root, policy.mode)
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
    if _repository_state(root, policy.mode) != state:
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
