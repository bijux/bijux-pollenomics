"""Canonical release-evidence document services."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from ..release_evidence import (
    ArtifactInput,
    Blocker,
    CountReconciliation,
    GateResult,
    build_release_evidence_manifest,
    validate_release_evidence_manifest,
)
from .codec import _load_json
from .publication import _publish_canonical_document
from .repository import _repository_root


def write_release_evidence_manifest(
    repository_root: Path,
    output_path: str,
    *,
    code_commit: str,
    dirty: bool,
    dependency_lock_digest: str,
    artifacts: Sequence[ArtifactInput],
    gates: Sequence[GateResult],
    reconciliations: Sequence[CountReconciliation],
    blockers: Sequence[Blocker] = (),
) -> dict[str, object]:
    """Build, validate, and atomically publish canonical release evidence."""
    root = _repository_root(repository_root)
    manifest = build_release_evidence_manifest(
        root,
        code_commit=code_commit,
        dirty=dirty,
        dependency_lock_digest=dependency_lock_digest,
        artifacts=artifacts,
        gates=gates,
        reconciliations=reconciliations,
        blockers=blockers,
    )
    validate_release_evidence_manifest(root, manifest)
    _publish_canonical_document(
        root,
        output_path,
        manifest,
        document_name="release-evidence output",
        validate_payload=lambda payload: _validate_written_manifest(root, payload),
    )
    return manifest


def write_release_evidence_request(
    repository_root: Path, output_path: str
) -> dict[str, object]:
    """Derive, validate, and atomically publish the current canonical request."""
    from ..request import (
        derive_release_evidence_request,
        validate_release_evidence_request,
    )

    root = _repository_root(repository_root)
    request = derive_release_evidence_request(root)
    _publish_canonical_document(
        root,
        output_path,
        request,
        document_name="release-evidence request",
        validate_payload=lambda payload: validate_release_evidence_request(
            root, _load_json(payload)
        ),
    )
    return request


def _validate_written_manifest(root: Path, payload: bytes) -> None:
    validate_release_evidence_manifest(root, _load_json(payload))
