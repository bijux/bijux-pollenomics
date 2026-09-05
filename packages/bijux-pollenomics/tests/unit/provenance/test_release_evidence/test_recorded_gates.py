"""Recorded Gates tests."""

from __future__ import annotations
import json
from pathlib import Path
import shutil
from typing import cast
import pytest
from bijux_pollenomics.provenance import (
    GateResult,
    ReleaseEvidenceError,
    hash_repository_object,
    validate_recorded_gate,
)
from bijux_pollenomics.provenance.gates import producer as gate_producer
from .conftest import (
    _artifacts,
    _build,
    _canonical_json,
    _refresh_validation_artifact,
    _rewrite_gate_record,
)


def test_recorded_gate_validator_binds_identity_status_and_required_policy(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path)
    validation = next(item for item in artifacts if item.identity == "validation")
    expected = GateResult("quality", "PASS", True, validation.output_digest)

    record = validate_recorded_gate(tmp_path, validation.path, expected_gate=expected)

    assert record["gate_id"] == "quality"
    assert record["status"] == "PASS"
    with pytest.raises(ReleaseEvidenceError, match="gate inventory"):
        _build(
            tmp_path,
            artifacts=artifacts,
            gates=[GateResult("other", "PASS", True, validation.output_digest)],
        )
    with pytest.raises(ReleaseEvidenceError, match="status mismatch"):
        _build(
            tmp_path,
            artifacts=artifacts,
            gates=[GateResult("quality", "FAIL", True, validation.output_digest)],
        )
    with pytest.raises(ReleaseEvidenceError, match="required flag"):
        _build(
            tmp_path,
            artifacts=artifacts,
            gates=[
                GateResult(
                    "quality",
                    "PASS",
                    cast(bool, 1),
                    validation.output_digest,
                )
            ],
        )
    with pytest.raises(ReleaseEvidenceError, match="required policy mismatch"):
        validate_recorded_gate(
            tmp_path,
            validation.path,
            expected_gate=GateResult(
                "quality", "PASS", False, validation.output_digest
            ),
        )


def test_recorded_gate_rejects_stale_declared_input(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    (tmp_path / "gate-input.txt").write_text("changed input\n", encoding="utf-8")

    with pytest.raises(ReleaseEvidenceError, match="input changed"):
        _build(tmp_path, artifacts=artifacts)


def test_recorded_gate_rejects_internal_record_digest_tamper(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    path = tmp_path / "artifacts/gate-evidence/quality.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["duration_monotonic_ns"] = 2
    path.write_bytes(_canonical_json(record) + b"\n")
    _refresh_validation_artifact(tmp_path, artifacts)

    with pytest.raises(ReleaseEvidenceError, match="record_digest mismatch"):
        _build(tmp_path, artifacts=artifacts)


def test_recorded_gate_producer_is_bound_to_complete_source_closure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_a = [{"module": "producer.a", "sha256": "sha256:a", "byte_count": 1}]
    source_b = [{"module": "producer.b", "sha256": "sha256:b", "byte_count": 1}]
    monkeypatch.setattr(gate_producer, "_producer_source_files", lambda: source_a)
    artifacts = _artifacts(tmp_path)
    monkeypatch.setattr(gate_producer, "_producer_source_files", lambda: source_b)

    with pytest.raises(ReleaseEvidenceError, match="producer identity mismatch"):
        _build(tmp_path, artifacts=artifacts)


@pytest.mark.parametrize("attack", ["independent", "missing", "legacy-v2", "legacy-v3"])
def test_local_gate_attestation_is_required_and_cannot_be_upgraded_or_grandfathered(
    tmp_path: Path, attack: str
) -> None:
    artifacts = _artifacts(tmp_path)

    def mutate(record: dict[str, object]) -> None:
        if attack == "independent":
            record["attestation"] = {
                "class": "independent_execution_attestation",
                "independent_execution_attested": True,
                "external_authority_id": "attacker",
            }
        elif attack == "missing":
            del record["attestation"]
        else:
            record["schema_version"] = attack.replace("legacy-", "recorded-gate.")

    _rewrite_gate_record(tmp_path, artifacts, mutate)

    with pytest.raises(ReleaseEvidenceError, match="attestation|schema|fields"):
        _build(tmp_path, artifacts=artifacts)


def test_nonlocal_gate_is_refused_without_product_owned_trust_configuration(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path)
    gate = GateResult(
        "quality",
        "PASS",
        True,
        artifacts[-1].output_digest,
        attestation="independent_execution_attestation",
        authority_id="unconfigured-verifier",
    )

    with pytest.raises(
        ReleaseEvidenceError, match="non-local gate attestation trust is not configured"
    ):
        _build(tmp_path, artifacts=artifacts, gates=[gate])


@pytest.mark.parametrize("attack", ["aliased-logs", "arbitrary-log", "aliased-junit"])
def test_gate_artifact_roles_cannot_alias_or_select_arbitrary_paths(
    tmp_path: Path, attack: str
) -> None:
    artifacts = _artifacts(tmp_path)

    def mutate(record: dict[str, object]) -> None:
        if attack == "aliased-logs":
            record["stdout"] = record["stderr"]
        elif attack == "aliased-junit":
            record["junit"] = record["stdout"]
        else:
            arbitrary = tmp_path / "arbitrary.log"
            arbitrary.write_text("arbitrary\n", encoding="utf-8")
            record["stdout"] = {
                "path": "arbitrary.log",
                **hash_repository_object(tmp_path, "arbitrary.log"),
            }

    _rewrite_gate_record(tmp_path, artifacts, mutate)

    with pytest.raises(ReleaseEvidenceError, match="role|alias"):
        _build(tmp_path, artifacts=artifacts)


@pytest.mark.parametrize(
    "junit_payload",
    [
        '<testsuite failures="1"/>\n',
        '<testsuite errors="1"/>\n',
        '<testsuite skipped="1"/>\n',
        "<testsuite><testcase><failure/></testcase></testsuite>\n",
    ],
)
def test_coherently_rehashed_pass_record_requires_passing_junit(
    tmp_path: Path, junit_payload: str
) -> None:
    artifacts = _artifacts(tmp_path)
    junit_path = tmp_path / "artifacts/gate-evidence/quality.junit.xml"
    junit_path.write_text(junit_payload, encoding="utf-8")

    def mutate(record: dict[str, object]) -> None:
        record["junit"] = {
            "path": "artifacts/gate-evidence/quality.junit.xml",
            **hash_repository_object(
                tmp_path, "artifacts/gate-evidence/quality.junit.xml"
            ),
        }

    _rewrite_gate_record(tmp_path, artifacts, mutate)

    with pytest.raises(ReleaseEvidenceError, match="nonpassing JUnit"):
        _build(tmp_path, artifacts=artifacts)


def test_recorded_gate_is_bound_to_repository_root(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    validation = next(item for item in artifacts if item.identity == "validation")
    relocated = tmp_path.parent / f"{tmp_path.name}-relocated"
    shutil.copytree(tmp_path, relocated)

    with pytest.raises(ReleaseEvidenceError, match="repository root mismatch"):
        validate_recorded_gate(relocated, validation.path)


def test_recorded_gate_timeout_is_bound_to_product_policy(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)

    def mutate(record: dict[str, object]) -> None:
        record["timeout_seconds"] = 1.0

    _rewrite_gate_record(tmp_path, artifacts, mutate)

    with pytest.raises(ReleaseEvidenceError, match="timeout differs"):
        _build(tmp_path, artifacts=artifacts)


@pytest.mark.parametrize(
    "relative_path, expected_message",
    [
        ("artifacts/gate-evidence/quality.stdout.log", "stdout changed"),
        ("artifacts/gate-evidence/quality.stderr.log", "stderr changed"),
        ("artifacts/gate-evidence/quality.junit.xml", "JUnit changed"),
    ],
)
def test_recorded_gate_rejects_tampered_result_artifact(
    tmp_path: Path, relative_path: str, expected_message: str
) -> None:
    artifacts = _artifacts(tmp_path)
    (tmp_path / relative_path).write_text("tampered\n", encoding="utf-8")

    with pytest.raises(ReleaseEvidenceError, match=expected_message):
        _build(tmp_path, artifacts=artifacts)


@pytest.mark.parametrize("status", ["SKIPPED", "BLOCKED_EXTERNAL", "NOT_APPLICABLE"])
def test_recorded_gate_refuses_statuses_the_producer_cannot_emit(
    tmp_path: Path, status: str
) -> None:
    artifacts = _artifacts(tmp_path, gate_status=status)
    with pytest.raises(ReleaseEvidenceError, match="invalid recorded gate status"):
        _build(
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
