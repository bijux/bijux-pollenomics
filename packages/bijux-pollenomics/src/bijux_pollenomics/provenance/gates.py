"""Exact-command gate execution with durable, canonical evidence records."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
import time
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath

from .release_evidence import ReleaseEvidenceError, hash_repository_object

__all__ = ["run_recorded_gate"]

_IDENTITY_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]*\Z")


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
                completed = subprocess.run(
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
                stderr_stream.write(
                    f"{type(error).__name__}: {error}\n".encode("utf-8")
                )
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
        else:
            junit_record = {
                "path": junit.relative_to(root).as_posix(),
                "status": "MISSING",
            }
            if reason_code == "command_passed":
                reason_code = "junit_missing"
    try:
        current_inputs = _input_records(root, input_paths)
    except ReleaseEvidenceError:
        current_inputs = None
    if current_inputs != inputs:
        reason_code = "input_changed_during_gate"
    status = "PASS" if exit_code == 0 and reason_code == "command_passed" else "FAIL"
    record_content: dict[str, object] = {
        "schema_version": "recorded-gate.v1",
        "gate_id": gate_id,
        "argv": command,
        "command_digest": _digest_json(command),
        "environment_digest": _digest_json(dict(sorted(execution_environment.items()))),
        "environment_keys": sorted(execution_environment),
        "inputs": inputs,
        "input_digest": _digest_json(inputs),
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


def _input_records(root: Path, input_paths: Sequence[str]) -> list[dict[str, object]]:
    if any(not isinstance(path, str) for path in input_paths):
        raise ReleaseEvidenceError("input paths must be strings")
    paths = sorted(input_paths)
    if len(paths) != len(set(paths)):
        raise ReleaseEvidenceError("duplicate gate input path")
    return [{"path": path, **hash_repository_object(root, path)} for path in paths]


def _output_record(root: Path, path: Path) -> dict[str, object]:
    relative = path.relative_to(root).as_posix()
    result = hash_repository_object(root, relative)
    return {"path": relative, **result}


def _exact_argv(argv: Sequence[str]) -> list[str]:
    if not argv or any(
        not isinstance(argument, str) or not argument or "\0" in argument
        for argument in argv
    ):
        raise ReleaseEvidenceError("argv must contain exact non-empty strings")
    return list(argv)


def _exact_environment(environment: Mapping[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in environment.items():
        if (
            not isinstance(key, str)
            or not key
            or "=" in key
            or "\0" in key
            or not isinstance(value, str)
            or "\0" in value
        ):
            raise ReleaseEvidenceError("environment must contain valid string pairs")
        result[key] = value
    return dict(sorted(result.items()))


def _prepare_artifacts_directory(root: Path, relative_path: str) -> Path:
    parts = _relative_parts(relative_path)
    if not parts or parts[0] != "artifacts":
        raise ReleaseEvidenceError("gate evidence must be under artifacts/")
    current = root
    for part in parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            try:
                current.mkdir(mode=0o755)
            except FileExistsError:
                pass
            mode = current.lstat().st_mode
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise ReleaseEvidenceError(
                f"unsafe gate artifacts directory: {relative_path}"
            )
    return current


def _artifact_member(
    root: Path, directory: Path, relative_path: str, field: str
) -> Path:
    parts = _relative_parts(relative_path)
    path = root.joinpath(*parts)
    try:
        path.relative_to(directory)
    except ValueError as error:
        raise ReleaseEvidenceError(
            f"{field} must be inside the gate artifacts directory"
        ) from error
    current = root
    for part in parts[:-1]:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError as error:
            raise ReleaseEvidenceError(f"{field} parent does not exist") from error
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise ReleaseEvidenceError(f"unsafe {field}")
    if path.exists() or path.is_symlink():
        raise ReleaseEvidenceError(f"{field} must not reuse existing evidence")
    return path


def _relative_parts(relative_path: str) -> tuple[str, ...]:
    if not relative_path or "\\" in relative_path:
        raise ReleaseEvidenceError(
            f"invalid repository-relative path: {relative_path!r}"
        )
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or pure.as_posix() != relative_path:
        raise ReleaseEvidenceError(
            f"invalid repository-relative path: {relative_path!r}"
        )
    if any(part in {"", ".", ".."} for part in pure.parts):
        raise ReleaseEvidenceError(f"path escapes repository root: {relative_path!r}")
    return pure.parts


def _temporary_path(directory: Path, name: str) -> Path:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{name}.", suffix=".writing", dir=directory
    )
    os.close(descriptor)
    return Path(temporary_name)


def _atomic_replace(destination: Path, payload: bytes) -> None:
    temporary = _temporary_path(destination.parent, destination.name)
    try:
        with temporary.open("wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), 0o644)
        os.replace(temporary, destination)
        _fsync_directory(destination.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def _canonical_bytes(value: Mapping[str, object]) -> bytes:
    try:
        return (
            json.dumps(
                dict(value),
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
    except (TypeError, ValueError) as error:
        raise ReleaseEvidenceError("gate evidence is not canonical JSON") from error


def _digest_json(value: object) -> str:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ReleaseEvidenceError("gate evidence is not canonical JSON") from error
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _validate_gate_id(gate_id: str) -> None:
    if not isinstance(gate_id, str) or _IDENTITY_PATTERN.fullmatch(gate_id) is None:
        raise ReleaseEvidenceError(f"invalid gate identity: {gate_id!r}")


def _repository_root(repository_root: Path) -> Path:
    try:
        root = repository_root.resolve(strict=True)
    except OSError as error:
        raise ReleaseEvidenceError("repository root does not exist") from error
    if not root.is_dir():
        raise ReleaseEvidenceError("repository root must be a directory")
    return root


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
