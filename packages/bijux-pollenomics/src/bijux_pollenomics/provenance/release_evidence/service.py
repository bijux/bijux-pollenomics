"""Construction and validation of canonical release-evidence manifests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from .artifacts import _artifact_record, _validate_artifact_graph
from .assessment import (
    _release_decision,
    _validate_blockers,
    _validate_gates,
    _validate_reconciliations,
)
from .codec import (
    _blocker_record,
    _bool_field,
    _canonical_json,
    _digest_json,
    _gate_record,
    _parse_artifact,
    _parse_blocker,
    _parse_gate,
    _parse_reconciliation,
    _reconciliation_record,
    _record_list,
    _require_commit,
    _require_digest,
    _require_unique,
    _string_field,
)
from .models import (
    ArtifactInput,
    Blocker,
    CountReconciliation,
    GateResult,
    ReleaseEvidenceError,
)
from .policy import _load_release_evidence_policy
from .repository import _repository_root, _repository_state


def build_release_evidence_manifest(
    repository_root: Path,
    *,
    code_commit: str,
    dirty: bool,
    dependency_lock_digest: str,
    artifacts: Sequence[ArtifactInput],
    gates: Sequence[GateResult],
    reconciliations: Sequence[CountReconciliation],
    blockers: Sequence[Blocker] = (),
) -> dict[str, object]:
    """Build canonical release evidence without consulting clocks or Git state."""
    root = _repository_root(repository_root)
    _require_commit(code_commit)
    if type(dirty) is not bool:
        raise ReleaseEvidenceError("dirty must be a boolean")
    _require_digest(dependency_lock_digest, "dependency_lock_digest")

    policy = _load_release_evidence_policy(root)
    repository_state = _repository_state(root, policy.mode)
    if policy.mode == "product":
        if repository_state["head_commit"] != code_commit:
            raise ReleaseEvidenceError("code_commit does not match repository HEAD")
        if repository_state["dirty"] != dirty:
            raise ReleaseEvidenceError("dirty flag does not match repository state")

    ordered_artifacts = sorted(artifacts, key=lambda item: item.identity)
    _require_unique((item.identity for item in ordered_artifacts), "artifact identity")
    _require_unique((item.path for item in ordered_artifacts), "artifact path")
    artifact_records = [_artifact_record(root, item) for item in ordered_artifacts]
    _validate_artifact_graph(
        root, ordered_artifacts, artifact_records, dependency_lock_digest, policy
    )
    recording_authority = next(
        record
        for record in artifact_records
        if record["path"] == policy.recording_authority_path
    )

    ordered_gates = sorted(gates, key=lambda item: item.identity)
    _validate_gates(root, ordered_gates, artifact_records, policy)
    ordered_reconciliations = sorted(
        reconciliations,
        key=lambda item: (
            item.source,
            item.entity,
            item.dimension,
            item.country_code or "",
            item.scope,
        ),
    )
    _validate_reconciliations(ordered_reconciliations, policy)
    ordered_blockers = sorted(blockers, key=lambda item: item.identity)
    _validate_blockers(ordered_blockers, artifact_records, ordered_gates, policy)

    decision = _release_decision(dirty, ordered_gates, ordered_blockers)
    content: dict[str, object] = {
        "schema_version": "release-evidence-manifest.v3",
        "code_commit": code_commit,
        "dirty": dirty,
        "repository_state": repository_state,
        "dependency_lock_digest": dependency_lock_digest,
        "recording_authority_digest": recording_authority["output_digest"],
        "artifacts": artifact_records,
        "gates": [_gate_record(item) for item in ordered_gates],
        "reconciliations": [
            _reconciliation_record(item) for item in ordered_reconciliations
        ],
        "blockers": [_blocker_record(item) for item in ordered_blockers],
        "release_decision": decision,
    }
    return {"build_id": _digest_json(content), **content}


def validate_release_evidence_manifest(
    repository_root: Path, manifest: Mapping[str, object]
) -> None:
    """Validate manifest structure, lineage, canonical identity, and current inputs."""
    try:
        expected_keys = {
            "build_id",
            "schema_version",
            "code_commit",
            "dirty",
            "repository_state",
            "dependency_lock_digest",
            "recording_authority_digest",
            "artifacts",
            "gates",
            "reconciliations",
            "blockers",
            "release_decision",
        }
        if set(manifest) != expected_keys:
            raise ReleaseEvidenceError("manifest fields do not match the v3 contract")
        if manifest["schema_version"] != "release-evidence-manifest.v3":
            raise ReleaseEvidenceError("unsupported release-evidence schema")
        artifacts = tuple(
            _parse_artifact(item) for item in _record_list(manifest, "artifacts")
        )
        gates = tuple(_parse_gate(item) for item in _record_list(manifest, "gates"))
        reconciliations = tuple(
            _parse_reconciliation(item)
            for item in _record_list(manifest, "reconciliations")
        )
        policy = _load_release_evidence_policy(_repository_root(repository_root))
        if policy.mode == "product":
            from ..request.reconciliation import derive_reconciliations

            governed_reconciliations = derive_reconciliations(
                _repository_root(repository_root), policy
            )
            if tuple(sorted(reconciliations, key=_reconciliation_sort_key)) != tuple(
                sorted(governed_reconciliations, key=_reconciliation_sort_key)
            ):
                raise ReleaseEvidenceError(
                    "manifest reconciliations differ from current governed derivation"
                )
        blockers = tuple(
            _parse_blocker(item) for item in _record_list(manifest, "blockers")
        )
        rebuilt = build_release_evidence_manifest(
            repository_root,
            code_commit=_string_field(manifest, "code_commit"),
            dirty=_bool_field(manifest, "dirty"),
            dependency_lock_digest=_string_field(manifest, "dependency_lock_digest"),
            artifacts=artifacts,
            gates=gates,
            reconciliations=reconciliations,
            blockers=blockers,
        )
        if _canonical_json(dict(manifest)) != _canonical_json(rebuilt):
            raise ReleaseEvidenceError("manifest content or an immutable input changed")
    except ReleaseEvidenceError:
        raise
    except (KeyError, TypeError, ValueError) as error:
        raise ReleaseEvidenceError(
            "manifest does not satisfy the v3 contract"
        ) from error


def _reconciliation_sort_key(
    item: CountReconciliation,
) -> tuple[str, str, str, str, tuple[tuple[str, str], ...]]:
    return (
        item.source,
        item.entity,
        item.dimension,
        item.country_code or "",
        item.scope,
    )
