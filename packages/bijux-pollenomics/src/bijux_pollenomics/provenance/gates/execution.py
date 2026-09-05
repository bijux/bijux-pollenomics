"""Shell-free gate execution and evidence recording."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import os
from pathlib import Path
import shutil
import subprocess  # nosec B404
import time

from ..release_evidence import ReleaseEvidenceError
from .artifacts import (
    _artifact_member,
    _atomic_replace,
    _fsync_directory,
    _prepare_artifacts_directory,
    _temporary_path,
)
from .codec import _canonical_bytes, _digest_json
from .model import RecordedGateSpecification
from .producer import _runtime_identity
from .repository import _input_records, _output_record, _repository_root
from .validation import (
    _exact_argv,
    _exact_environment,
    _validate_gate_id,
    _validate_passing_junit,
)


def run_recorded_gate(
    repository_root: Path,
    *,
    gate_id: str,
    argv: Sequence[str],
    environment: Mapping[str, str],
    input_paths: Sequence[str],
    artifacts_directory: str,
    junit_path: str | None = None,
    timeout_seconds: float | None = None,
) -> dict[str, object]:
    """Run exact argv without a shell and atomically publish its evidence record."""
    root = _repository_root(repository_root)
    _validate_gate_id(gate_id)
    command = _exact_argv(argv)
    execution_environment = _exact_environment(environment)
    if timeout_seconds is not None and (
        isinstance(timeout_seconds, bool) or timeout_seconds <= 0
    ):
        raise ReleaseEvidenceError("timeout_seconds must be positive or null")
    directory = _prepare_artifacts_directory(root, artifacts_directory)
    junit = (
        _artifact_member(root, directory, junit_path, "JUnit path")
        if junit_path is not None
        else None
    )
    inputs = _input_records(root, input_paths)
    specification = RecordedGateSpecification(
        gate_id=gate_id,
        required=True,
        argv=tuple(command),
        environment=tuple(execution_environment.items()),
        input_paths=tuple(sorted(input_paths)),
        artifacts_directory=artifacts_directory,
        junit_path=junit_path or "",
        timeout_seconds=timeout_seconds,
        runtime_identity=_runtime_identity(command[0], shutil.which("node")),
    )
    specification_record = specification.as_record(root)
    stdout_path = directory / f"{gate_id}.stdout.log"
    stderr_path = directory / f"{gate_id}.stderr.log"
    record_path = directory / f"{gate_id}.json"

    stdout_temporary = _temporary_path(directory, stdout_path.name)
    stderr_temporary = _temporary_path(directory, stderr_path.name)
    started = time.monotonic_ns()
    exit_code: int | None
    reason_code: str
    try:
        with (
            stdout_temporary.open("wb") as stdout_stream,
            stderr_temporary.open("wb") as stderr_stream,
        ):
            try:
                # The gate contract requires exact shell-free argv execution.
                completed = subprocess.run(  # nosec B603
                    command,
                    cwd=root,
                    env=execution_environment,
                    stdin=subprocess.DEVNULL,
                    stdout=stdout_stream,
                    stderr=stderr_stream,
                    check=False,
                    shell=False,
                    timeout=timeout_seconds,
                )
                exit_code = completed.returncode
                reason_code = "command_passed" if exit_code == 0 else "command_failed"
            except subprocess.TimeoutExpired:
                exit_code = None
                reason_code = "command_timed_out"
            except OSError as error:
                exit_code = None
                reason_code = "command_launch_failed"
                stderr_stream.write(f"{type(error).__name__}: {error}\n".encode())
            stdout_stream.flush()
            stderr_stream.flush()
            os.fsync(stdout_stream.fileno())
            os.fsync(stderr_stream.fileno())
        duration = time.monotonic_ns() - started
        os.replace(stdout_temporary, stdout_path)
        os.replace(stderr_temporary, stderr_path)
        _fsync_directory(directory)
    finally:
        for temporary in (stdout_temporary, stderr_temporary):
            if temporary.exists():
                temporary.unlink()

    stdout_record = _output_record(root, stdout_path)
    stderr_record = _output_record(root, stderr_path)
    junit_record: dict[str, object] | None = None
    if junit is not None:
        if junit.exists() or junit.is_symlink():
            junit_record = _output_record(root, junit)
            if reason_code == "command_passed":
                try:
                    _validate_passing_junit(junit)
                except ReleaseEvidenceError as error:
                    reason_code = str(error)
        else:
            junit_record = {
                "path": junit.relative_to(root).as_posix(),
                "status": "MISSING",
            }
            if reason_code == "command_passed":
                reason_code = "junit_missing"
    elif reason_code == "command_passed":
        reason_code = "junit_missing"
    try:
        current_inputs = _input_records(root, input_paths)
    except ReleaseEvidenceError:
        current_inputs = None
    if current_inputs != inputs:
        reason_code = "input_changed_during_gate"
    status = "PASS" if exit_code == 0 and reason_code == "command_passed" else "FAIL"
    record_content: dict[str, object] = {
        "schema_version": "recorded-gate.v4",
        "producer": specification_record["producer"],
        "attestation": specification_record["attestation"],
        "repository_root_digest": _digest_json(root.as_posix()),
        "gate_id": gate_id,
        "required": specification.required,
        "argv": command,
        "command_digest": _digest_json(command),
        "environment": execution_environment,
        "environment_digest": _digest_json(dict(sorted(execution_environment.items()))),
        "inputs": inputs,
        "input_digest": _digest_json(inputs),
        "artifacts_directory": artifacts_directory,
        "specification_digest": _digest_json(specification_record),
        "timeout_seconds": timeout_seconds,
        "duration_monotonic_ns": duration,
        "exit_code": exit_code,
        "status": status,
        "reason_code": reason_code,
        "stdout": stdout_record,
        "stderr": stderr_record,
        "junit": junit_record,
    }
    record = {"record_digest": _digest_json(record_content), **record_content}
    _atomic_replace(record_path, _canonical_bytes(record))
    return record
