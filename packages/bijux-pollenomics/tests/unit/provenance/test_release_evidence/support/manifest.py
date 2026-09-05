"""Release-evidence manifest fixture assembly."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.provenance import (
    ArtifactInput,
    Blocker,
    CountReconciliation,
    GateResult,
    build_release_evidence_manifest,
)

from .artifacts import _artifacts
from .reconciliation import _reconciliations

COMMIT = "1" * 40


def _build(
    root: Path,
    *,
    artifacts: list[ArtifactInput] | None = None,
    gates: list[GateResult] | None = None,
    reconciliations: list[CountReconciliation] | None = None,
    blockers: list[Blocker] | None = None,
) -> dict[str, object]:
    artifacts = artifacts or _artifacts(root)
    by_identity = {artifact.identity: artifact for artifact in artifacts}
    gates = gates or [
        GateResult(
            identity="quality",
            status="PASS",
            required=True,
            evidence_digest=by_identity["validation"].output_digest,
        )
    ]
    return build_release_evidence_manifest(
        root,
        code_commit=COMMIT,
        dirty=False,
        dependency_lock_digest=by_identity["lock"].output_digest,
        artifacts=artifacts,
        gates=gates,
        reconciliations=reconciliations or _reconciliations(),
        blockers=blockers or (),
    )
