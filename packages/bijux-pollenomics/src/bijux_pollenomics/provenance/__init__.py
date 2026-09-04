"""Deterministic provenance and release-evidence contracts."""

from .release_evidence import (
    ArtifactInput,
    ArtifactReference,
    Blocker,
    CountReconciliation,
    GateResult,
    ReleaseEvidenceError,
    build_release_evidence_manifest,
    hash_repository_object,
    validate_release_evidence_manifest,
)
from .writer import main as release_evidence_main
from .writer import write_release_evidence_manifest

__all__ = [
    "ArtifactInput",
    "ArtifactReference",
    "Blocker",
    "CountReconciliation",
    "GateResult",
    "ReleaseEvidenceError",
    "build_release_evidence_manifest",
    "hash_repository_object",
    "release_evidence_main",
    "validate_release_evidence_manifest",
    "write_release_evidence_manifest",
]
