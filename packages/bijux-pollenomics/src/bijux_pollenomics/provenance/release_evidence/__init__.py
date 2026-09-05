"""Canonical, fail-closed release evidence over immutable repository inputs."""

from .models import (
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
from .recorded_gates import validate_recorded_gate
from .repository import (
    hash_repository_object,
)
from .service import build_release_evidence_manifest, validate_release_evidence_manifest

__all__ = [
    "ArtifactInput",
    "ArtifactReference",
    "ArtifactRole",
    "Blocker",
    "CountReconciliation",
    "CountStatus",
    "GateResult",
    "GateStatus",
    "ReconciliationDimension",
    "ReleaseEvidenceError",
    "build_release_evidence_manifest",
    "hash_repository_object",
    "validate_recorded_gate",
    "validate_release_evidence_manifest",
]
