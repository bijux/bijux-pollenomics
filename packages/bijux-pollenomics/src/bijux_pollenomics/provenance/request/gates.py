"""Derive canonical gate evidence and local attestation posture."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import cast

from ..release_evidence.models import ArtifactInput, GateResult, GateStatus
from ..release_evidence.models import _GATE_STATUSES, _ReleaseEvidencePolicy
from ..release_evidence.models import ReleaseEvidenceError


def derive_gate_results(
    root: Path,
    policy: _ReleaseEvidencePolicy,
    artifacts: Mapping[str, ArtifactInput],
    *,
    validate_recorded_gate: Callable[[Path, str], dict[str, object]],
) -> tuple[GateResult, ...]:
    """Bind each required gate to one validated local attestation."""
    gates: list[GateResult] = []
    for gate_id in sorted(policy.required_gate_ids):
        matches = [
            artifact
            for artifact in artifacts.values()
            if artifact.role == "validation_result"
            and artifact.path.rsplit("/", maxsplit=1)[-1] == f"{gate_id}.json"
        ]
        if len(matches) != 1:
            raise ReleaseEvidenceError(
                f"release policy lacks exact gate artifact: {gate_id}"
            )
        artifact = matches[0]
        record = validate_recorded_gate(root, artifact.path)
        if record.get("gate_id") != gate_id:
            raise ReleaseEvidenceError(
                f"recorded gate identity does not match policy: {gate_id}"
            )
        attestation = record.get("attestation")
        if not isinstance(attestation, Mapping) or attestation.get("class") != (
            "local_self_attestation"
        ):
            raise ReleaseEvidenceError(
                f"recorded gate attestation is not locally governed: {gate_id}"
            )
        status = record.get("status")
        required = record.get("required")
        if status not in _GATE_STATUSES or type(required) is not bool:
            raise ReleaseEvidenceError(f"recorded gate result is invalid: {gate_id}")
        gates.append(
            GateResult(
                identity=gate_id,
                status=cast(GateStatus, status),
                required=required,
                evidence_digest=artifact.output_digest,
                attestation="local_self_attestation",
                authority_id=None,
            )
        )
    return tuple(gates)


def gate_record(gate: GateResult) -> dict[str, object]:
    """Translate a gate result into the canonical request record."""
    return {
        "identity": gate.identity,
        "status": gate.status,
        "required": gate.required,
        "evidence_digest": gate.evidence_digest,
        "attestation": gate.attestation,
        "authority_id": gate.authority_id,
    }
