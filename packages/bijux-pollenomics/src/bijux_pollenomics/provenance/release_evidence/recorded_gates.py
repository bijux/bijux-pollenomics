"""Validation of immutable recorded-gate attestations."""

from __future__ import annotations

import hashlib
import json
import stat
from collections.abc import Mapping
from pathlib import Path

from defusedxml import ElementTree as ET  # type: ignore[import-untyped]

from .codec import (
    _bool_field,
    _canonical_json,
    _digest_json,
    _int_field,
    _mapping,
    _mapping_list,
    _require_digest,
    _require_identity,
    _string_field,
    _string_items,
)
from .models import _GATE_STATUSES, GateResult, ReleaseEvidenceError
from .repository import (
    _hash_repository_object,
    _read_repository_file,
    _relative_path,
    _repository_root,
)


def validate_recorded_gate(
    repository_root: Path,
    recorded_gate_path: str,
    *,
    expected_gate: GateResult | None = None,
) -> dict[str, object]:
    """Validate recorded-gate evidence against its current repository inputs.

    The product-owned specification binds gate identity, required policy,
    execution shape, artifacts, source-bound producer, local attestation posture,
    and repository root. Passing an expected gate also binds its observed status
    and evidence digest.
    """
    root = _repository_root(repository_root)
    payload = _read_repository_file(root, recorded_gate_path)
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseEvidenceError("recorded gate is not valid JSON") from error
    record = _mapping(value, "recorded gate")
    if payload != _canonical_json(record) + b"\n":
        raise ReleaseEvidenceError("recorded gate is not canonical JSON")
    _validate_recorded_gate_record(root, recorded_gate_path, record)

    if expected_gate is not None:
        _require_identity(expected_gate.identity, "gate identity")
        if expected_gate.status not in _GATE_STATUSES:
            raise ReleaseEvidenceError(f"invalid gate status: {expected_gate.status}")
        if type(expected_gate.required) is not bool:
            raise ReleaseEvidenceError("gate required flag must be a boolean")
        _require_digest(expected_gate.evidence_digest, "gate evidence digest")
        if _string_field(record, "gate_id") != expected_gate.identity:
            raise ReleaseEvidenceError(
                f"recorded gate identity mismatch: {expected_gate.identity}"
            )
        if _string_field(record, "status") != expected_gate.status:
            raise ReleaseEvidenceError(
                f"recorded gate status mismatch: {expected_gate.identity}"
            )
        if _bool_field(record, "required") != expected_gate.required:
            raise ReleaseEvidenceError(
                f"recorded gate required policy mismatch: {expected_gate.identity}"
            )
        observed_digest = f"sha256:{hashlib.sha256(payload).hexdigest()}"
        if observed_digest != expected_gate.evidence_digest:
            raise ReleaseEvidenceError(
                f"recorded gate evidence digest mismatch: {expected_gate.identity}"
            )
    return dict(record)


def _validate_recorded_gate_record(
    root: Path, recorded_gate_path: str, record: Mapping[str, object]
) -> None:
    expected_fields = {
        "record_digest",
        "schema_version",
        "producer",
        "attestation",
        "repository_root_digest",
        "gate_id",
        "required",
        "argv",
        "command_digest",
        "environment",
        "environment_digest",
        "inputs",
        "input_digest",
        "artifacts_directory",
        "specification_digest",
        "timeout_seconds",
        "duration_monotonic_ns",
        "exit_code",
        "status",
        "reason_code",
        "stdout",
        "stderr",
        "junit",
    }
    if set(record) != expected_fields:
        raise ReleaseEvidenceError("recorded gate fields do not match the v4 contract")
    if record["schema_version"] != "recorded-gate.v4":
        raise ReleaseEvidenceError("unsupported recorded-gate schema")

    record_digest = _string_field(record, "record_digest")
    _require_digest(record_digest, "recorded gate record_digest")
    content = {key: value for key, value in record.items() if key != "record_digest"}
    if record_digest != _digest_json(content):
        raise ReleaseEvidenceError("recorded gate record_digest mismatch")

    gate_id = _string_field(record, "gate_id")
    _require_identity(gate_id, "recorded gate identity")
    from ..gates import build_product_gate_specification

    specification = build_product_gate_specification(root, gate_id)
    expected_specification = specification.as_record(root)
    expected_record_path = f"{specification.artifacts_directory}/{gate_id}.json"
    if recorded_gate_path != expected_record_path:
        raise ReleaseEvidenceError("recorded gate path does not match its role")
    root_digest = _string_field(record, "repository_root_digest")
    if root_digest != _digest_json(root.as_posix()):
        raise ReleaseEvidenceError("recorded gate repository root mismatch")
    producer = _mapping(record["producer"], "recorded gate producer")
    if producer != expected_specification["producer"]:
        raise ReleaseEvidenceError("recorded gate producer identity mismatch")
    attestation = _mapping(record["attestation"], "recorded gate attestation")
    if attestation != expected_specification["attestation"]:
        raise ReleaseEvidenceError("recorded gate attestation posture mismatch")
    required = _bool_field(record, "required")
    if required != specification.required:
        raise ReleaseEvidenceError("recorded gate required policy mismatch")
    specification_digest = _string_field(record, "specification_digest")
    _require_digest(specification_digest, "recorded gate specification_digest")
    if specification_digest != _digest_json(expected_specification):
        raise ReleaseEvidenceError("recorded gate specification mismatch")

    argv = _string_items(record, "argv")
    if not argv or any(not item or "\0" in item for item in argv):
        raise ReleaseEvidenceError("recorded gate argv must contain exact strings")
    command_digest = _string_field(record, "command_digest")
    _require_digest(command_digest, "recorded gate command_digest")
    if command_digest != _digest_json(argv):
        raise ReleaseEvidenceError("recorded gate command_digest mismatch")
    if argv != list(specification.argv):
        raise ReleaseEvidenceError("recorded gate command differs from product spec")

    environment = _mapping(record["environment"], "recorded gate environment")
    if any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in environment.items()
    ):
        raise ReleaseEvidenceError("recorded gate environment must contain strings")
    environment_digest = _string_field(record, "environment_digest")
    _require_digest(environment_digest, "recorded gate environment_digest")
    if environment_digest != _digest_json(dict(sorted(environment.items()))):
        raise ReleaseEvidenceError("recorded gate environment_digest mismatch")
    if dict(environment) != dict(specification.environment):
        raise ReleaseEvidenceError(
            "recorded gate environment differs from product spec"
        )

    inputs = _mapping_list(record, "inputs")
    input_paths = [_string_field(item, "path") for item in inputs]
    if input_paths != sorted(input_paths) or len(input_paths) != len(set(input_paths)):
        raise ReleaseEvidenceError("recorded gate inputs are not canonical")
    for item in inputs:
        _validate_recorded_object(root, item, "input")
    input_digest = _string_field(record, "input_digest")
    _require_digest(input_digest, "recorded gate input_digest")
    if input_digest != _digest_json(inputs):
        raise ReleaseEvidenceError("recorded gate input_digest mismatch")
    if not inputs:
        raise ReleaseEvidenceError("recorded gate inputs must not be empty")
    if input_paths != list(specification.input_paths):
        raise ReleaseEvidenceError("recorded gate inputs differ from product spec")

    artifacts_directory = _string_field(record, "artifacts_directory")
    if artifacts_directory != specification.artifacts_directory:
        raise ReleaseEvidenceError("recorded gate artifacts directory mismatch")

    timeout_seconds = record["timeout_seconds"]
    if timeout_seconds is not None and (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or timeout_seconds <= 0
    ):
        raise ReleaseEvidenceError(
            "recorded gate timeout_seconds must be positive or null"
        )
    if timeout_seconds != specification.timeout_seconds:
        raise ReleaseEvidenceError("recorded gate timeout differs from product spec")

    duration = _int_field(record, "duration_monotonic_ns")
    if duration < 0:
        raise ReleaseEvidenceError("recorded gate duration must be non-negative")
    exit_code = record["exit_code"]
    if exit_code is not None and type(exit_code) is not int:
        raise ReleaseEvidenceError("recorded gate exit_code must be an integer or null")
    status = _string_field(record, "status")
    if status not in {"PASS", "FAIL"}:
        raise ReleaseEvidenceError(f"invalid recorded gate status: {status}")
    reason_code = _string_field(record, "reason_code")
    _require_identity(reason_code, "recorded gate reason_code")
    if status == "PASS" and (exit_code != 0 or reason_code != "command_passed"):
        raise ReleaseEvidenceError(
            "recorded PASS gate contradicts its execution result"
        )
    valid_state = (
        status == "PASS" and exit_code == 0 and reason_code == "command_passed"
    ) or (
        status == "FAIL"
        and (
            (
                exit_code is not None
                and exit_code != 0
                and reason_code == "command_failed"
            )
            or (
                exit_code is None
                and reason_code in {"command_timed_out", "command_launch_failed"}
            )
            or reason_code == "input_changed_during_gate"
            or (
                exit_code == 0
                and reason_code
                in {
                    "junit_missing",
                    "junit_invalid",
                    "junit_failed",
                    "input_changed_during_gate",
                }
            )
        )
    )
    if not valid_state:
        raise ReleaseEvidenceError("recorded gate has a producer-impossible state")

    stdout = _mapping(record["stdout"], "recorded gate stdout")
    stderr = _mapping(record["stderr"], "recorded gate stderr")
    stdout_path = _string_field(stdout, "path")
    stderr_path = _string_field(stderr, "path")
    expected_stdout = f"{artifacts_directory}/{gate_id}.stdout.log"
    expected_stderr = f"{artifacts_directory}/{gate_id}.stderr.log"
    if stdout_path != expected_stdout or stderr_path != expected_stderr:
        raise ReleaseEvidenceError("recorded gate log path does not match its role")
    if stdout_path == stderr_path:
        raise ReleaseEvidenceError("recorded gate artifact roles must not alias")
    _validate_recorded_object(root, stdout, "stdout")
    _validate_recorded_object(root, stderr, "stderr")
    junit = record["junit"]
    if junit is not None:
        junit_record = _mapping(junit, "recorded gate junit")
        if set(junit_record) == {"path", "status"}:
            if junit_record["status"] != "MISSING":
                raise ReleaseEvidenceError("invalid recorded gate JUnit status")
            if _string_field(junit_record, "path") != specification.junit_path:
                raise ReleaseEvidenceError(
                    "recorded gate JUnit path does not match its role"
                )
            _validate_recorded_missing_path(
                root, _string_field(junit_record, "path"), "JUnit"
            )
            if status == "PASS":
                raise ReleaseEvidenceError("recorded PASS gate has missing JUnit")
        else:
            _validate_recorded_object(root, junit_record, "JUnit")
            junit_path = _string_field(junit_record, "path")
            if junit_path != specification.junit_path:
                raise ReleaseEvidenceError(
                    "recorded gate JUnit path does not match its role"
                )
            if junit_path in {stdout_path, stderr_path}:
                raise ReleaseEvidenceError(
                    "recorded gate artifact roles must not alias"
                )
            if status == "PASS":
                _validate_passing_junit(root, junit_path)
    elif status == "PASS":
        raise ReleaseEvidenceError("recorded PASS gate has missing JUnit")


def _validate_recorded_object(
    root: Path, record: Mapping[str, object], field: str
) -> None:
    expected_fields = {
        "path",
        "object_type",
        "output_digest",
        "byte_size",
        "file_count",
    }
    if set(record) != expected_fields:
        raise ReleaseEvidenceError(f"recorded gate {field} fields are invalid")
    path = _string_field(record, "path")
    object_type = _string_field(record, "object_type")
    if object_type not in {"file", "tree"}:
        raise ReleaseEvidenceError(f"recorded gate {field} object_type is invalid")
    _require_digest(
        _string_field(record, "output_digest"),
        f"recorded gate {field} output_digest",
    )
    byte_size = _int_field(record, "byte_size")
    file_count = _int_field(record, "file_count")
    if byte_size < 0 or file_count < 0:
        raise ReleaseEvidenceError(f"recorded gate {field} counts must be non-negative")
    observed = {"path": path, **_hash_repository_object(root, path)}
    if dict(record) != observed:
        raise ReleaseEvidenceError(f"recorded gate {field} changed: {path}")


def _validate_recorded_missing_path(root: Path, relative_path: str, field: str) -> None:
    pure = _relative_path(relative_path)
    current = root
    for part in pure.parts[:-1]:
        current /= part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError as error:
            raise ReleaseEvidenceError(
                f"recorded gate missing {field} parent does not exist"
            ) from error
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise ReleaseEvidenceError(f"recorded gate missing {field} path is unsafe")
    target = current / pure.parts[-1]
    if target.exists() or target.is_symlink():
        raise ReleaseEvidenceError(f"recorded gate missing {field} now exists")


def _validate_passing_junit(root: Path, relative_path: str) -> None:
    payload = _read_repository_file(root, relative_path)
    try:
        xml_root = ET.fromstring(payload)
    except ET.ParseError as error:
        raise ReleaseEvidenceError("recorded PASS gate has invalid JUnit") from error
    if xml_root.tag.rsplit("}", 1)[-1] not in {"testsuite", "testsuites"}:
        raise ReleaseEvidenceError("recorded PASS gate has invalid JUnit")
    for element in xml_root.iter():
        local_tag = element.tag.rsplit("}", 1)[-1]
        if local_tag in {"failure", "error", "skipped"}:
            raise ReleaseEvidenceError("recorded PASS gate has nonpassing JUnit")
        if local_tag not in {"testsuite", "testsuites"}:
            continue
        for attribute in ("failures", "errors", "skipped"):
            raw = element.attrib.get(attribute, "0")
            try:
                count = int(raw)
            except ValueError as error:
                raise ReleaseEvidenceError(
                    "recorded PASS gate has invalid JUnit"
                ) from error
            if count < 0:
                raise ReleaseEvidenceError("recorded PASS gate has invalid JUnit")
            if count:
                raise ReleaseEvidenceError("recorded PASS gate has nonpassing JUnit")
