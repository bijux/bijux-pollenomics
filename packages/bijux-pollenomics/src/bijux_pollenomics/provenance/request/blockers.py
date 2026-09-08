"""Serialize explicit release blockers without weakening their evidence."""

from __future__ import annotations

from ..release_evidence.models import Blocker


def blocker_record(blocker: Blocker) -> dict[str, object]:
    """Translate a blocker into the canonical request record."""
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
