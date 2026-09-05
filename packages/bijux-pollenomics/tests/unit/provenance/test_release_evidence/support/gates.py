"""Recorded-gate fixture specification and evidence construction."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.provenance import hash_repository_object
from bijux_pollenomics.provenance.gates import RecordedGateSpecification

from .codec import _canonical_json, _digest, _json_digest


def _write_gate_record(
    root: Path,
    *,
    path: str | None = None,
    gate_id: str = "quality",
    status: str = "PASS",
) -> str:
    path = path or f"artifacts/gate-evidence/{gate_id}.json"
    gate_input = root / "gate-input.txt"
    gate_input.write_text("current gate input\n", encoding="utf-8")
    evidence_directory = root / "artifacts/gate-evidence"
    evidence_directory.mkdir(parents=True, exist_ok=True)
    stdout_path = evidence_directory / f"{gate_id}.stdout.log"
    stderr_path = evidence_directory / f"{gate_id}.stderr.log"
    junit_path = evidence_directory / f"{gate_id}.junit.xml"
    stdout_path.write_text("passed\n", encoding="utf-8")
    stderr_path.write_bytes(b"")
    junit_path.write_text('<testsuite failures="0"/>\n', encoding="utf-8")

    def repository_record(relative: str) -> dict[str, object]:
        return {"path": relative, **hash_repository_object(root, relative)}

    inputs = [repository_record("gate-input.txt")]
    if status == "PASS":
        exit_code: int | None = 0
        reason_code = "command_passed"
    elif status == "FAIL":
        exit_code = 1
        reason_code = "command_failed"
    else:
        exit_code = None
        reason_code = status.lower()
    specification = _fixture_specification(root, gate_id)
    specification_record = specification.as_record(root)
    content: dict[str, object] = {
        "schema_version": "recorded-gate.v4",
        "producer": specification_record["producer"],
        "attestation": specification_record["attestation"],
        "repository_root_digest": specification_record["repository_root_digest"],
        "gate_id": gate_id,
        "required": specification.required,
        "argv": ["pytest", "-q"],
        "command_digest": _json_digest(["pytest", "-q"]),
        "environment_digest": _json_digest({}),
        "environment": {},
        "inputs": inputs,
        "input_digest": _json_digest(inputs),
        "artifacts_directory": specification.artifacts_directory,
        "specification_digest": _json_digest(specification_record),
        "timeout_seconds": specification.timeout_seconds,
        "duration_monotonic_ns": 1,
        "exit_code": exit_code,
        "status": status,
        "reason_code": reason_code,
        "stdout": repository_record(f"artifacts/gate-evidence/{gate_id}.stdout.log"),
        "stderr": repository_record(f"artifacts/gate-evidence/{gate_id}.stderr.log"),
        "junit": repository_record(f"artifacts/gate-evidence/{gate_id}.junit.xml"),
    }
    record = {"record_digest": _json_digest(content), **content}
    payload = _canonical_json(record) + b"\n"
    output = root / path
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    return _digest(payload)


def _fixture_specification(root: Path, gate_id: str) -> RecordedGateSpecification:
    return RecordedGateSpecification(
        gate_id=gate_id,
        required=True,
        argv=("pytest", "-q"),
        environment=(),
        input_paths=("gate-input.txt",),
        artifacts_directory="artifacts/gate-evidence",
        junit_path=f"artifacts/gate-evidence/{gate_id}.junit.xml",
    )
