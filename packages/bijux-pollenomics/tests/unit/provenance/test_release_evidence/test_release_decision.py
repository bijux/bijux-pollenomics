"""Release Decision tests."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, cast

import pytest
from bijux_pollenomics.provenance import (
    ArtifactInput,
    Blocker,
    GateResult,
    ReleaseEvidenceError,
    build_release_evidence_manifest,
)

from .support import COMMIT, _artifacts, _build, _digest, _reconciliations


def test_failed_required_gate_never_claims_release_ready(tmp_path: Path) -> None:
    status = "FAIL"
    artifacts = _artifacts(tmp_path, gate_status=status)
    manifest = _build(
        tmp_path,
        artifacts=artifacts,
        gates=[
            GateResult(
                "quality",
                status,  # type: ignore[arg-type]
                True,
                artifacts[-1].output_digest,
            )
        ],
    )

    decision = manifest["release_decision"]
    assert isinstance(decision, dict)
    assert decision["release_ready"] is False
    assert decision["status"] != "verified_complete"


def test_blockers_and_dirty_state_refuse_release_ready_claim(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    manifest = _build(
        tmp_path,
        artifacts=artifacts,
        blockers=[
            Blocker(
                "rights-review",
                "source_rights_unverified",
                artifacts[0].output_digest,
                kind="unverified",
                required_scope="public redistribution rights",
                owner="data-governance",
                first_observed_at="2026-09-04T00:00:00Z",
                last_observed_at="2026-09-05T00:00:00Z",
                request_status="governed",
                request_artifact_identity=artifacts[0].identity,
                request_fingerprint=artifacts[0].output_digest,
                response_class="human_review_pending",
                observations=("licence decision absent",),
                attempts=("review packet prepared",),
                impact="public release remains unavailable",
                expected_artifact="signed rights decision",
                impacted_gates=("quality",),
                next_action="obtain qualified rights decision",
                recheck_condition="signed decision is attached",
            )
        ],
    )
    assert manifest["release_decision"] == {
        "release_ready": False,
        "status": "implemented_unverified",
        "reason_codes": [
            "blocker:source_rights_unverified",
            "required_gate_not_independently_attested:quality",
        ],
    }

    dirty = build_release_evidence_manifest(
        tmp_path,
        code_commit=COMMIT,
        dirty=True,
        dependency_lock_digest=next(
            item.output_digest for item in artifacts if item.identity == "lock"
        ),
        artifacts=artifacts,
        gates=[GateResult("quality", "PASS", True, artifacts[-1].output_digest)],
        reconciliations=_reconciliations(),
    )
    assert dirty["release_decision"] == {
        "release_ready": False,
        "status": "implemented_unverified",
        "reason_codes": [
            "candidate_dirty",
            "required_gate_not_independently_attested:quality",
        ],
    }


@pytest.mark.parametrize(
    ("kind", "expected_status"),
    [("external", "external_blocked"), ("refused", "refused_invalid")],
)
def test_actionable_blocker_kind_controls_truthful_release_state(
    tmp_path: Path, kind: str, expected_status: str
) -> None:
    artifacts = _artifacts(tmp_path)
    blocker = Blocker(
        identity=f"{kind}-source",
        reason_code=f"{kind}_source_unavailable",
        evidence_digest=artifacts[0].output_digest,
        kind=cast(Literal["external", "unverified", "refused", "reduced_scope"], kind),
        required_scope="governed source capture",
        owner="source-acquisition",
        first_observed_at="2026-09-04T00:00:00Z",
        last_observed_at="2026-09-05T00:00:00Z",
        request_status="refused",
        response_class="source_response",
        observations=("source response recorded",),
        attempts=("one bounded acquisition attempt",),
        impact="affected source cannot be released",
        expected_artifact="immutable source receipt",
        impacted_gates=("quality",),
        next_action="recheck source under approved authority",
        recheck_condition="source response or review decision changes",
    )

    manifest = _build(tmp_path, artifacts=artifacts, blockers=[blocker])

    assert (
        cast(dict[str, object], manifest["release_decision"])["status"]
        == expected_status
    )


def test_rejects_duplicate_paths_invalid_sha_and_output_overwrite(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path)
    output = next(item for item in artifacts if item.identity == "output")
    artifacts[artifacts.index(output)] = ArtifactInput(
        **{
            **output.__dict__,
            "path": "receipt.json",
            "output_digest": _digest(b"receipt\n"),
        }
    )
    with pytest.raises(ReleaseEvidenceError, match="output overwrite"):
        _build(tmp_path, artifacts=artifacts)

    with pytest.raises(ReleaseEvidenceError, match="Git SHA"):
        build_release_evidence_manifest(
            tmp_path,
            code_commit="ABC",
            dirty=False,
            dependency_lock_digest="sha256:" + "0" * 64,
            artifacts=(),
            gates=(),
            reconciliations=(),
        )


def test_rejects_missing_paths_duplicate_identities_and_invalid_vocabularies(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path)
    receipt = next(item for item in artifacts if item.identity == "receipt")
    artifacts[artifacts.index(receipt)] = ArtifactInput(
        **{**receipt.__dict__, "path": "missing.json"}
    )
    with pytest.raises(ReleaseEvidenceError, match="path is missing"):
        _build(tmp_path, artifacts=artifacts)

    artifacts = _artifacts(tmp_path)
    duplicate = ArtifactInput(**{**artifacts[0].__dict__, "path": "duplicate.json"})
    (tmp_path / "duplicate.json").write_bytes(b"receipt\n")
    artifacts.append(duplicate)
    with pytest.raises(ReleaseEvidenceError, match="duplicate artifact identity"):
        _build(tmp_path, artifacts=artifacts)

    artifacts = _artifacts(tmp_path)
    validation_digest = next(
        item.output_digest for item in artifacts if item.identity == "validation"
    )
    with pytest.raises(ReleaseEvidenceError, match="invalid gate status"):
        _build(
            tmp_path,
            artifacts=artifacts,
            gates=[
                GateResult(
                    "quality",
                    "pass",  # type: ignore[arg-type]
                    True,
                    validation_digest,
                )
            ],
        )

    output = next(item for item in artifacts if item.identity == "output")
    artifacts[artifacts.index(output)] = ArtifactInput(
        **{**output.__dict__, "output_digest": "0" * 64}
    )
    with pytest.raises(ReleaseEvidenceError, match="canonical SHA-256"):
        _build(tmp_path, artifacts=artifacts)
