"""Canonical, fail-closed release evidence over immutable repository inputs."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
from itertools import product
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess  # nosec B404
from typing import Final, Literal, TypeAlias, cast

from defusedxml import ElementTree as ET  # type: ignore[import-untyped]

ArtifactRole: TypeAlias = Literal[
    "source_receipt",
    "source_snapshot",
    "configuration",
    "classification",
    "scenario",
    "boundary",
    "producer",
    "dependency_lock",
    "generated_output",
    "validation_result",
]
GateStatus: TypeAlias = Literal[
    "PASS", "FAIL", "BLOCKED_EXTERNAL", "NOT_APPLICABLE", "SKIPPED"
]
ReconciliationDimension: TypeAlias = Literal["source", "country", "scope"]
CountStatus: TypeAlias = Literal["reported", "unavailable", "refused"]

_ARTIFACT_ROLES: Final = frozenset(
    {
        "source_receipt",
        "source_snapshot",
        "configuration",
        "classification",
        "scenario",
        "boundary",
        "producer",
        "dependency_lock",
        "generated_output",
        "validation_result",
    }
)
_REQUIRED_ROLES: Final = _ARTIFACT_ROLES
_CONFIG_ROLES: Final = frozenset(
    {"configuration", "classification", "scenario", "boundary", "dependency_lock"}
)
_DERIVED_ROLES: Final = frozenset({"generated_output", "validation_result"})
_OUTPUT_ROLES: Final = frozenset({"generated_output", "validation_result"})
_GATE_STATUSES: Final = frozenset(
    {"PASS", "FAIL", "BLOCKED_EXTERNAL", "NOT_APPLICABLE", "SKIPPED"}
)
_COUNTRIES: Final = frozenset({"SE", "DK", "NO", "FI", "UNASSIGNED", "OUTSIDE"})
_DIGEST_PATTERN: Final = re.compile(r"sha256:[0-9a-f]{64}\Z")
_RAW_SHA256_PATTERN: Final = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT_PATTERN: Final = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_IDENTITY_PATTERN: Final = re.compile(r"[a-z0-9][a-z0-9._:-]*\Z")
_UTC_TIMESTAMP_PATTERN: Final = re.compile(
    r"[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])"
    r"T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]Z\Z"
)
_RELEASE_POLICY_PATH: Final = "configs/release_evidence_policy.json"


class ReleaseEvidenceError(ValueError):
    """Raised when release evidence is incomplete, unsafe, or inconsistent."""


@dataclass(frozen=True)
class ArtifactReference:
    """An immutable parent identity paired with its expected content digest."""

    identity: str
    output_digest: str


@dataclass(frozen=True)
class ArtifactInput:
    """A repository object and the explicit lineage claims made for it."""

    identity: str
    role: ArtifactRole
    path: str
    media_type: str
    schema_version: str
    parents: tuple[ArtifactReference, ...]
    config_digests: tuple[str, ...]
    producer_digest: str | None
    output_digest: str


@dataclass(frozen=True)
class GateResult:
    """A validation-gate result backed by an immutable evidence artifact."""

    identity: str
    status: GateStatus
    required: bool
    evidence_digest: str
    attestation: Literal[
        "local_self_attestation",
        "independent_execution_attestation",
        "external_authority_attestation",
    ] = "local_self_attestation"
    authority_id: str | None = None


@dataclass(frozen=True)
class CountReconciliation:
    """One source-level or country-level count partition."""

    identity: str
    dimension: ReconciliationDimension
    source: str
    entity: str
    country_code: str | None
    candidate_count: int | None
    eligible_count: int | None
    accepted_count: int | None
    unresolved_count: int | None
    excluded_count: int | None
    refused_count: int | None
    scope: tuple[tuple[str, str], ...] = ()
    count_status: CountStatus = "reported"
    reason_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Blocker:
    """An unresolved release blocker with stable, evidence-backed identity."""

    identity: str
    reason_code: str
    evidence_digest: str
    kind: Literal["external", "unverified", "refused", "reduced_scope"] = "unverified"
    required_scope: str = ""
    owner: str = ""
    first_observed_at: str = ""
    last_observed_at: str = ""
    request_status: Literal["governed", "refused"] = "refused"
    request_artifact_identity: str | None = None
    request_fingerprint: str | None = None
    response_class: str = ""
    observations: tuple[str, ...] = ()
    attempts: tuple[str, ...] = ()
    impact: str = ""
    expected_artifact: str = ""
    impacted_gates: tuple[str, ...] = ()
    next_action: str = ""
    recheck_condition: str = ""


@dataclass(frozen=True)
class _ArtifactOwnershipRule:
    artifact_role: ArtifactRole
    artifact_path_prefix: str
    producer_path: str


@dataclass(frozen=True)
class _RequiredArtifact:
    identity: str
    role: ArtifactRole
    path: str
    media_type: str
    schema_version: str
    schema_identity_field: str | None
    producer_path: str | None
    required_config_identities: tuple[str, ...]
    required_parent_identities: tuple[str, ...]
    required_embedded_input_paths: tuple[str, ...]


@dataclass(frozen=True)
class _EmbeddedProducerIdentity:
    artifact_identity: str
    producer_artifact_identity: str
    producer_id: str
    producer_version: str
    id_field: str
    version_field: str
    digest_field: str
    digest_prefix: str
    source_paths: tuple[str, ...]


@dataclass(frozen=True)
class _BundleInventory:
    artifact_identity: str
    filenames: tuple[str, ...]


@dataclass(frozen=True)
class _RequiredReconciliation:
    source: str
    entity: str
    dimension: Literal["country", "scope"]
    scope_values: tuple[tuple[str, tuple[str, ...]], ...]
    derivation_adapter: str
    derivation_metric: str
    unavailable_status: Literal["unavailable", "refused"]
    unavailable_reason_code: str


@dataclass(frozen=True)
class _PropagationContractIdentity:
    contract_id: str
    contract_version: str
    output_digest: str
    scenario_id: str
    maximum_distance_km: float
    maximum_lag_years: float


@dataclass(frozen=True)
class _ReleaseEvidencePolicy:
    mode: str
    recording_authority_path: str
    authorized_producer_paths: tuple[str, ...]
    artifact_ownership: tuple[_ArtifactOwnershipRule, ...]
    required_artifacts: tuple[_RequiredArtifact, ...]
    embedded_producer_identities: tuple[_EmbeddedProducerIdentity, ...]
    bundle_inventories: tuple[_BundleInventory, ...]
    allowed_cross_role_digest_aliases: frozenset[frozenset[str]]
    required_gate_ids: frozenset[str]
    governed_request_artifact_ids: frozenset[str]
    propagation_contract: _PropagationContractIdentity
    required_reconciliations: tuple[_RequiredReconciliation, ...]
    output_digest: str


def build_release_evidence_manifest(
    repository_root: Path,
    *,
    code_commit: str,
    dirty: bool,
    dependency_lock_digest: str,
    artifacts: Sequence[ArtifactInput],
    gates: Sequence[GateResult],
    reconciliations: Sequence[CountReconciliation],
    blockers: Sequence[Blocker] = (),
) -> dict[str, object]:
    """Build canonical release evidence without consulting clocks or Git state."""
    root = _repository_root(repository_root)
    _require_commit(code_commit)
    if type(dirty) is not bool:
        raise ReleaseEvidenceError("dirty must be a boolean")
    _require_digest(dependency_lock_digest, "dependency_lock_digest")

    policy = _load_release_evidence_policy(root)
    repository_state = _repository_state(root, policy.mode)
    if policy.mode == "product":
        if repository_state["head_commit"] != code_commit:
            raise ReleaseEvidenceError("code_commit does not match repository HEAD")
        if repository_state["dirty"] != dirty:
            raise ReleaseEvidenceError("dirty flag does not match repository state")

    ordered_artifacts = sorted(artifacts, key=lambda item: item.identity)
    _require_unique((item.identity for item in ordered_artifacts), "artifact identity")
    _require_unique((item.path for item in ordered_artifacts), "artifact path")
    artifact_records = [_artifact_record(root, item) for item in ordered_artifacts]
    _validate_artifact_graph(
        root, ordered_artifacts, artifact_records, dependency_lock_digest, policy
    )
    recording_authority = next(
        record
        for record in artifact_records
        if record["path"] == policy.recording_authority_path
    )

    ordered_gates = sorted(gates, key=lambda item: item.identity)
    _validate_gates(root, ordered_gates, artifact_records, policy)
    ordered_reconciliations = sorted(
        reconciliations,
        key=lambda item: (
            item.source,
            item.entity,
            item.dimension,
            item.country_code or "",
            item.scope,
        ),
    )
    _validate_reconciliations(ordered_reconciliations, policy)
    ordered_blockers = sorted(blockers, key=lambda item: item.identity)
    _validate_blockers(ordered_blockers, artifact_records, ordered_gates, policy)

    decision = _release_decision(dirty, ordered_gates, ordered_blockers)
    content: dict[str, object] = {
        "schema_version": "release-evidence-manifest.v3",
        "code_commit": code_commit,
        "dirty": dirty,
        "repository_state": repository_state,
        "dependency_lock_digest": dependency_lock_digest,
        "recording_authority_digest": recording_authority["output_digest"],
        "artifacts": artifact_records,
        "gates": [_gate_record(item) for item in ordered_gates],
        "reconciliations": [
            _reconciliation_record(item) for item in ordered_reconciliations
        ],
        "blockers": [_blocker_record(item) for item in ordered_blockers],
        "release_decision": decision,
    }
    return {"build_id": _digest_json(content), **content}


def validate_release_evidence_manifest(
    repository_root: Path, manifest: Mapping[str, object]
) -> None:
    """Validate manifest structure, lineage, canonical identity, and current inputs."""
    try:
        expected_keys = {
            "build_id",
            "schema_version",
            "code_commit",
            "dirty",
            "repository_state",
            "dependency_lock_digest",
            "recording_authority_digest",
            "artifacts",
            "gates",
            "reconciliations",
            "blockers",
            "release_decision",
        }
        if set(manifest) != expected_keys:
            raise ReleaseEvidenceError("manifest fields do not match the v3 contract")
        if manifest["schema_version"] != "release-evidence-manifest.v3":
            raise ReleaseEvidenceError("unsupported release-evidence schema")
        artifacts = tuple(
            _parse_artifact(item) for item in _record_list(manifest, "artifacts")
        )
        gates = tuple(_parse_gate(item) for item in _record_list(manifest, "gates"))
        reconciliations = tuple(
            _parse_reconciliation(item)
            for item in _record_list(manifest, "reconciliations")
        )
        policy = _load_release_evidence_policy(_repository_root(repository_root))
        if policy.mode == "product":
            from .request import _reconciliations

            governed_reconciliations = _reconciliations(
                _repository_root(repository_root), policy
            )
            if tuple(sorted(reconciliations, key=_reconciliation_sort_key)) != tuple(
                sorted(governed_reconciliations, key=_reconciliation_sort_key)
            ):
                raise ReleaseEvidenceError(
                    "manifest reconciliations differ from current governed derivation"
                )
        blockers = tuple(
            _parse_blocker(item) for item in _record_list(manifest, "blockers")
        )
        rebuilt = build_release_evidence_manifest(
            repository_root,
            code_commit=_string_field(manifest, "code_commit"),
            dirty=_bool_field(manifest, "dirty"),
            dependency_lock_digest=_string_field(manifest, "dependency_lock_digest"),
            artifacts=artifacts,
            gates=gates,
            reconciliations=reconciliations,
            blockers=blockers,
        )
        if _canonical_json(dict(manifest)) != _canonical_json(rebuilt):
            raise ReleaseEvidenceError("manifest content or an immutable input changed")
    except ReleaseEvidenceError:
        raise
    except (KeyError, TypeError, ValueError) as error:
        raise ReleaseEvidenceError(
            "manifest does not satisfy the v3 contract"
        ) from error


def _reconciliation_sort_key(
    item: CountReconciliation,
) -> tuple[str, str, str, str, tuple[tuple[str, str], ...]]:
    return (
        item.source,
        item.entity,
        item.dimension,
        item.country_code or "",
        item.scope,
    )


def hash_repository_object(
    repository_root: Path, relative_path: str
) -> dict[str, object]:
    """Hash a safe repository-relative regular file or tree canonically."""
    return _hash_repository_object(_repository_root(repository_root), relative_path)


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
    from .gates import build_product_gate_specification

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


def _relative_path(relative_path: str) -> PurePosixPath:
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
    return pure


def _artifact_record(root: Path, item: ArtifactInput) -> dict[str, object]:
    _require_identity(item.identity, "artifact identity")
    if item.role not in _ARTIFACT_ROLES:
        raise ReleaseEvidenceError(f"invalid artifact role: {item.role}")
    if not item.media_type.strip() or not item.schema_version.strip():
        raise ReleaseEvidenceError(
            f"artifact {item.identity} lacks media/schema identity"
        )
    if item.producer_digest is not None:
        _require_digest(item.producer_digest, f"{item.identity} producer_digest")
    _require_digest(item.output_digest, f"{item.identity} output_digest")
    _require_unique((parent.identity for parent in item.parents), "parent identity")
    for parent in item.parents:
        _require_identity(parent.identity, "parent identity")
        _require_digest(parent.output_digest, "parent output_digest")
    _require_unique(item.config_digests, "config digest")
    for digest in item.config_digests:
        _require_digest(digest, "config digest")

    observed = _hash_repository_object(
        root,
        item.path,
        exclude_python_cache=item.role == "producer",
    )
    if observed["output_digest"] != item.output_digest:
        raise ReleaseEvidenceError(f"artifact digest changed: {item.identity}")
    return {
        "identity": item.identity,
        "role": item.role,
        "path": item.path,
        "media_type": item.media_type,
        "schema_version": item.schema_version,
        "parents": [
            {"identity": parent.identity, "output_digest": parent.output_digest}
            for parent in sorted(item.parents, key=lambda parent: parent.identity)
        ],
        "config_digests": sorted(item.config_digests),
        "producer_digest": item.producer_digest,
        **observed,
    }


def _load_release_evidence_policy(root: Path) -> _ReleaseEvidencePolicy:
    payload = _read_repository_file(root, _RELEASE_POLICY_PATH)

    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ReleaseEvidenceError(f"duplicate release policy field: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(payload, object_pairs_hook=reject_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseEvidenceError(
            "release evidence policy is not valid JSON"
        ) from error
    record = _mapping(value, "release evidence policy")
    if payload != _canonical_json(record) + b"\n":
        raise ReleaseEvidenceError("release evidence policy is not canonical JSON")
    if set(record) != {
        "schema_version",
        "mode",
        "recording_authority_path",
        "authorized_producer_paths",
        "artifact_ownership",
        "required_artifacts",
        "embedded_producer_identities",
        "bundle_inventories",
        "allowed_cross_role_digest_aliases",
        "required_gate_ids",
        "governed_request_artifact_ids",
        "propagation_contract",
        "required_reconciliations",
    }:
        raise ReleaseEvidenceError("release evidence policy fields are invalid")
    if record["schema_version"] != "release-evidence-policy.v3":
        raise ReleaseEvidenceError("unsupported release evidence policy schema")
    mode = _string_field(record, "mode")
    if mode not in {"product", "fixture"}:
        raise ReleaseEvidenceError("invalid release evidence policy mode")
    if mode == "fixture" and (root / ".git").exists():
        raise ReleaseEvidenceError(
            "fixture release policy is forbidden in a Git worktree"
        )

    authorized = tuple(_string_items(record, "authorized_producer_paths"))
    if not authorized or list(authorized) != sorted(authorized):
        raise ReleaseEvidenceError(
            "authorized producer paths must be non-empty and sorted"
        )
    _require_unique(authorized, "authorized producer path")
    for path in authorized:
        _relative_path(path)
    recording_authority_path = _string_field(record, "recording_authority_path")
    if recording_authority_path not in authorized:
        raise ReleaseEvidenceError("recording authority must be an authorized producer")

    ownership: list[_ArtifactOwnershipRule] = []
    ownership_keys: list[str] = []
    for item in _mapping_list(record, "artifact_ownership"):
        if set(item) != {"artifact_role", "artifact_path_prefix", "producer_path"}:
            raise ReleaseEvidenceError("artifact ownership policy fields are invalid")
        role = _string_field(item, "artifact_role")
        if role not in _ARTIFACT_ROLES:
            raise ReleaseEvidenceError(f"invalid artifact ownership role: {role}")
        prefix = _string_field(item, "artifact_path_prefix")
        producer_path = _string_field(item, "producer_path")
        _relative_path(prefix)
        _relative_path(producer_path)
        if producer_path not in authorized:
            raise ReleaseEvidenceError(
                f"artifact ownership names an unauthorized producer: {producer_path}"
            )
        ownership.append(
            _ArtifactOwnershipRule(
                artifact_role=cast(ArtifactRole, role),
                artifact_path_prefix=prefix,
                producer_path=producer_path,
            )
        )
        ownership_keys.append(f"{prefix}\0{role}")
    if not ownership:
        raise ReleaseEvidenceError("artifact ownership policy must not be empty")
    _require_unique(ownership_keys, "artifact ownership rule")
    if ownership_keys != sorted(ownership_keys):
        raise ReleaseEvidenceError("artifact ownership rules must be sorted")

    required_artifacts: list[_RequiredArtifact] = []
    required_artifact_identities: list[str] = []
    required_artifact_paths: list[str] = []
    for item in _mapping_list(record, "required_artifacts"):
        if set(item) != {
            "identity",
            "role",
            "path",
            "media_type",
            "schema_version",
            "schema_identity_field",
            "producer_path",
            "required_config_identities",
            "required_parent_identities",
            "required_embedded_input_paths",
        }:
            raise ReleaseEvidenceError("required artifact policy fields are invalid")
        identity = _string_field(item, "identity")
        role = _string_field(item, "role")
        path = _string_field(item, "path")
        media_type = _string_field(item, "media_type")
        schema_version = _string_field(item, "schema_version")
        raw_schema_identity_field = item["schema_identity_field"]
        if raw_schema_identity_field not in {
            None,
            "$schema",
            "schema",
            "schema_version",
        }:
            raise ReleaseEvidenceError(
                f"required artifact schema identity field is invalid: {identity}"
            )
        raw_producer_path = item["producer_path"]
        if raw_producer_path is not None and not isinstance(raw_producer_path, str):
            raise ReleaseEvidenceError(
                f"required artifact producer path is invalid: {identity}"
            )
        required_producer_path = raw_producer_path
        config_identities = tuple(_string_items(item, "required_config_identities"))
        parent_identities = tuple(_string_items(item, "required_parent_identities"))
        embedded_input_paths = tuple(
            _string_items(item, "required_embedded_input_paths")
        )
        _require_identity(identity, "required artifact identity")
        if role not in _ARTIFACT_ROLES:
            raise ReleaseEvidenceError(f"invalid required artifact role: {role}")
        _relative_path(path)
        if not media_type.strip() or not schema_version.strip():
            raise ReleaseEvidenceError(
                f"required artifact lacks media/schema identity: {identity}"
            )
        if (
            required_producer_path is not None
            and required_producer_path not in authorized
        ):
            raise ReleaseEvidenceError(
                f"required artifact names an unauthorized producer: {identity}"
            )
        if list(config_identities) != sorted(config_identities):
            raise ReleaseEvidenceError(
                f"required config identities are not sorted: {identity}"
            )
        _require_unique(config_identities, "required config identity")
        if list(parent_identities) != sorted(parent_identities):
            raise ReleaseEvidenceError(
                f"required parent identities are not sorted: {identity}"
            )
        _require_unique(parent_identities, "required parent identity")
        if list(embedded_input_paths) != sorted(embedded_input_paths):
            raise ReleaseEvidenceError(
                f"required embedded input paths are not sorted: {identity}"
            )
        _require_unique(embedded_input_paths, "required embedded input path")
        for embedded_path in embedded_input_paths:
            _relative_path(embedded_path)
        required_artifacts.append(
            _RequiredArtifact(
                identity=identity,
                role=cast(ArtifactRole, role),
                path=path,
                media_type=media_type,
                schema_version=schema_version,
                schema_identity_field=raw_schema_identity_field,
                producer_path=required_producer_path,
                required_config_identities=config_identities,
                required_parent_identities=parent_identities,
                required_embedded_input_paths=embedded_input_paths,
            )
        )
        required_artifact_identities.append(identity)
        required_artifact_paths.append(path)
    if not required_artifacts:
        raise ReleaseEvidenceError("required artifact inventory must not be empty")
    _require_unique(required_artifact_identities, "required artifact identity")
    _require_unique(required_artifact_paths, "required artifact path")
    if required_artifact_identities != sorted(required_artifact_identities):
        raise ReleaseEvidenceError("required artifacts must be sorted by identity")
    known_required = set(required_artifact_identities)
    for requirement in required_artifacts:
        unknown_configs = set(requirement.required_config_identities) - known_required
        if unknown_configs:
            raise ReleaseEvidenceError(
                f"required artifact has unknown config identities: {requirement.identity}"
            )
        unknown_parents = set(requirement.required_parent_identities) - known_required
        if (
            unknown_parents
            or requirement.identity in requirement.required_parent_identities
        ):
            raise ReleaseEvidenceError(
                f"required artifact has unknown/self parent identities: {requirement.identity}"
            )

    embedded_producers: list[_EmbeddedProducerIdentity] = []
    for item in _mapping_list(record, "embedded_producer_identities"):
        if set(item) != {
            "artifact_identity",
            "producer_artifact_identity",
            "producer_id",
            "producer_version",
            "id_field",
            "version_field",
            "digest_field",
            "digest_prefix",
            "source_paths",
        }:
            raise ReleaseEvidenceError(
                "embedded producer identity policy fields are invalid"
            )
        artifact_identity = _string_field(item, "artifact_identity")
        producer_artifact_identity = _string_field(item, "producer_artifact_identity")
        producer_id = _string_field(item, "producer_id")
        producer_version = _string_field(item, "producer_version")
        id_field = _string_field(item, "id_field")
        version_field = _string_field(item, "version_field")
        digest_field = _string_field(item, "digest_field")
        digest_prefix = _string_field(item, "digest_prefix")
        source_paths = tuple(_string_items(item, "source_paths"))
        if artifact_identity not in known_required:
            raise ReleaseEvidenceError(
                "embedded producer names an unknown artifact identity"
            )
        if producer_artifact_identity not in known_required:
            raise ReleaseEvidenceError(
                "embedded producer names an unknown producer artifact"
            )
        producer_requirement = next(
            requirement
            for requirement in required_artifacts
            if requirement.identity == producer_artifact_identity
        )
        artifact_requirement = next(
            requirement
            for requirement in required_artifacts
            if requirement.identity == artifact_identity
        )
        if (
            producer_requirement.role != "producer"
            or artifact_requirement.producer_path != producer_requirement.path
        ):
            raise ReleaseEvidenceError(
                "embedded producer does not match artifact ownership"
            )
        for value, field_name in (
            (producer_id, "embedded producer id"),
            (producer_version, "embedded producer version"),
            (id_field, "embedded producer id field"),
            (version_field, "embedded producer version field"),
            (digest_field, "embedded producer digest field"),
        ):
            _require_identity(value, field_name)
        if digest_prefix not in {"", "sha256:"}:
            raise ReleaseEvidenceError("embedded producer digest prefix is invalid")
        if not source_paths:
            raise ReleaseEvidenceError("embedded producer source closure is empty")
        _require_unique(source_paths, "embedded producer source path")
        for source_path in source_paths:
            _relative_path(source_path)
        if not any(
            _path_has_prefix(source_path, producer_requirement.path)
            for source_path in source_paths
        ):
            raise ReleaseEvidenceError(
                "embedded producer closure does not include its owned source tree"
            )
        embedded_producers.append(
            _EmbeddedProducerIdentity(
                artifact_identity=artifact_identity,
                producer_artifact_identity=producer_artifact_identity,
                producer_id=producer_id,
                producer_version=producer_version,
                id_field=id_field,
                version_field=version_field,
                digest_field=digest_field,
                digest_prefix=digest_prefix,
                source_paths=source_paths,
            )
        )
    embedded_artifact_identities = [
        item.artifact_identity for item in embedded_producers
    ]
    _require_unique(embedded_artifact_identities, "embedded producer artifact identity")
    if embedded_artifact_identities != sorted(embedded_artifact_identities):
        raise ReleaseEvidenceError(
            "embedded producer identities must be sorted by artifact identity"
        )

    bundle_inventories: list[_BundleInventory] = []
    for item in _mapping_list(record, "bundle_inventories"):
        if set(item) != {"artifact_identity", "filenames"}:
            raise ReleaseEvidenceError("bundle inventory policy fields are invalid")
        artifact_identity = _string_field(item, "artifact_identity")
        filenames = tuple(_string_items(item, "filenames"))
        if artifact_identity not in known_required:
            raise ReleaseEvidenceError("bundle inventory names an unknown artifact")
        artifact_requirement = next(
            requirement
            for requirement in required_artifacts
            if requirement.identity == artifact_identity
        )
        if (
            artifact_requirement.media_type != "application/json"
            or PurePosixPath(artifact_requirement.path).name != "manifest.json"
        ):
            raise ReleaseEvidenceError(
                "bundle inventory artifact is not a JSON manifest"
            )
        if not filenames or list(filenames) != sorted(filenames):
            raise ReleaseEvidenceError(
                "bundle inventory filenames must be non-empty and sorted"
            )
        _require_unique(filenames, "bundle inventory filename")
        for filename in filenames:
            pure_filename = _relative_path(filename)
            if len(pure_filename.parts) != 1 or filename == "manifest.json":
                raise ReleaseEvidenceError("bundle inventory filename is unsafe")
        bundle_inventories.append(
            _BundleInventory(
                artifact_identity=artifact_identity,
                filenames=filenames,
            )
        )
    bundle_artifact_identities = [item.artifact_identity for item in bundle_inventories]
    _require_unique(bundle_artifact_identities, "bundle inventory artifact identity")
    if bundle_artifact_identities != sorted(bundle_artifact_identities):
        raise ReleaseEvidenceError(
            "bundle inventories must be sorted by artifact identity"
        )

    governed_request_artifact_ids = _string_items(
        record, "governed_request_artifact_ids"
    )
    if governed_request_artifact_ids != sorted(governed_request_artifact_ids):
        raise ReleaseEvidenceError("governed request artifact IDs must be sorted")
    _require_unique(governed_request_artifact_ids, "governed request artifact ID")
    if set(governed_request_artifact_ids) - known_required:
        raise ReleaseEvidenceError("governed request artifact IDs must be known")

    propagation_contract_record = _mapping(
        record["propagation_contract"], "propagation contract identity"
    )
    if set(propagation_contract_record) != {
        "contract_id",
        "contract_version",
        "sha256",
        "default_scenario",
    }:
        raise ReleaseEvidenceError("propagation contract identity fields are invalid")
    default_scenario = _mapping(
        propagation_contract_record["default_scenario"],
        "default propagation scenario",
    )
    if set(default_scenario) != {
        "scenario_id",
        "maximum_distance_km",
        "maximum_lag_years",
    }:
        raise ReleaseEvidenceError("default propagation scenario fields are invalid")
    propagation_digest = _string_field(propagation_contract_record, "sha256")
    _require_digest(propagation_digest, "propagation contract digest")
    contract_id = _string_field(propagation_contract_record, "contract_id")
    contract_version = _string_field(propagation_contract_record, "contract_version")
    scenario_id = _string_field(default_scenario, "scenario_id")
    _require_identity(contract_id, "propagation contract ID")
    _require_identity(contract_version, "propagation contract version")
    _require_identity(scenario_id, "default propagation scenario ID")
    maximum_distance_km = default_scenario["maximum_distance_km"]
    maximum_lag_years = default_scenario["maximum_lag_years"]
    if (
        isinstance(maximum_distance_km, bool)
        or not isinstance(maximum_distance_km, (int, float))
        or isinstance(maximum_lag_years, bool)
        or not isinstance(maximum_lag_years, (int, float))
        or maximum_distance_km <= 0
        or maximum_lag_years <= 0
    ):
        raise ReleaseEvidenceError("default propagation thresholds are invalid")
    propagation_contract = _PropagationContractIdentity(
        contract_id=contract_id,
        contract_version=contract_version,
        output_digest=propagation_digest,
        scenario_id=scenario_id,
        maximum_distance_km=float(maximum_distance_km),
        maximum_lag_years=float(maximum_lag_years),
    )

    allowed_aliases: set[frozenset[str]] = set()
    for item in _mapping_list(record, "allowed_cross_role_digest_aliases"):
        if set(item) != {"artifact_identities"}:
            raise ReleaseEvidenceError("digest alias policy fields are invalid")
        identities = _string_items(item, "artifact_identities")
        if len(identities) != 2 or identities != sorted(identities):
            raise ReleaseEvidenceError(
                "digest alias policy requires two sorted artifact identities"
            )
        pair = frozenset(identities)
        if not pair <= known_required:
            raise ReleaseEvidenceError("digest alias policy names unknown artifacts")
        if pair in allowed_aliases:
            raise ReleaseEvidenceError("duplicate digest alias policy")
        allowed_aliases.add(pair)

    required_gate_ids = tuple(_string_items(record, "required_gate_ids"))
    if not required_gate_ids or list(required_gate_ids) != sorted(required_gate_ids):
        raise ReleaseEvidenceError("required gate IDs must be non-empty and sorted")
    _require_unique(required_gate_ids, "required gate ID")
    for gate_id in required_gate_ids:
        _require_identity(gate_id, "required gate ID")

    required: list[_RequiredReconciliation] = []
    for item in _mapping_list(record, "required_reconciliations"):
        if set(item) != {
            "source",
            "entity",
            "dimension",
            "scope_values",
            "derivation_adapter",
            "derivation_metric",
            "unavailable_status",
            "unavailable_reason_code",
        }:
            raise ReleaseEvidenceError(
                "required reconciliation policy fields are invalid"
            )
        source = _string_field(item, "source")
        entity = _string_field(item, "entity")
        dimension = _string_field(item, "dimension")
        derivation_adapter = _string_field(item, "derivation_adapter")
        derivation_metric = _string_field(item, "derivation_metric")
        unavailable_status = _string_field(item, "unavailable_status")
        unavailable_reason_code = _string_field(item, "unavailable_reason_code")
        if dimension not in {"country", "scope"}:
            raise ReleaseEvidenceError("invalid required reconciliation dimension")
        if derivation_adapter not in {
            "classification_observation_memberships",
            "country_coverage",
            "neotoma_relational_reconciliation",
            "propagation_primary_reconciliation",
            "sead_chronology_claims",
            "unavailable",
        }:
            raise ReleaseEvidenceError("invalid reconciliation derivation adapter")
        if unavailable_status not in {"unavailable", "refused"}:
            raise ReleaseEvidenceError("invalid reconciliation unavailable status")
        _require_identity(derivation_metric, "reconciliation derivation metric")
        _require_identity(
            unavailable_reason_code, "reconciliation unavailable reason code"
        )
        raw_scope_values = _mapping(item["scope_values"], "scope values")
        scope_values: list[tuple[str, tuple[str, ...]]] = []
        for key, values in sorted(raw_scope_values.items()):
            if (
                not isinstance(key, str)
                or not isinstance(values, list)
                or any(not isinstance(value, str) for value in values)
            ):
                raise ReleaseEvidenceError("scope values must be string arrays")
            typed_values = tuple(cast(list[str], values))
            if not typed_values or list(typed_values) != sorted(typed_values):
                raise ReleaseEvidenceError("scope values must be non-empty and sorted")
            _require_unique(typed_values, "scope value")
            scope_values.append((key, typed_values))
        if dimension == "country" and scope_values:
            raise ReleaseEvidenceError("country requirement cannot define scope values")
        if dimension == "scope" and not scope_values:
            raise ReleaseEvidenceError("scope requirement must define scope values")
        _require_identity(source, "required reconciliation source")
        _require_identity(entity, "required reconciliation entity")
        required.append(
            _RequiredReconciliation(
                source=source,
                entity=entity,
                dimension=cast(Literal["country", "scope"], dimension),
                scope_values=tuple(scope_values),
                derivation_adapter=derivation_adapter,
                derivation_metric=derivation_metric,
                unavailable_status=cast(
                    Literal["unavailable", "refused"], unavailable_status
                ),
                unavailable_reason_code=unavailable_reason_code,
            )
        )
    if not required:
        raise ReleaseEvidenceError("required reconciliation policy must not be empty")
    _require_unique(
        (f"{item.source}\0{item.entity}" for item in required),
        "required reconciliation",
    )
    if [(item.source, item.entity) for item in required] != sorted(
        (item.source, item.entity) for item in required
    ):
        raise ReleaseEvidenceError("required reconciliations must be sorted")

    return _ReleaseEvidencePolicy(
        mode=mode,
        recording_authority_path=recording_authority_path,
        authorized_producer_paths=authorized,
        artifact_ownership=tuple(ownership),
        required_artifacts=tuple(required_artifacts),
        embedded_producer_identities=tuple(embedded_producers),
        bundle_inventories=tuple(bundle_inventories),
        allowed_cross_role_digest_aliases=frozenset(allowed_aliases),
        required_gate_ids=frozenset(required_gate_ids),
        governed_request_artifact_ids=frozenset(governed_request_artifact_ids),
        propagation_contract=propagation_contract,
        required_reconciliations=tuple(required),
        output_digest=f"sha256:{hashlib.sha256(payload).hexdigest()}",
    )


def _validate_artifact_graph(
    root: Path,
    artifacts: Sequence[ArtifactInput],
    records: Sequence[Mapping[str, object]],
    dependency_lock_digest: str,
    policy: _ReleaseEvidencePolicy,
) -> None:
    requirements = {item.identity: item for item in policy.required_artifacts}
    if set(requirements) != {item.identity for item in artifacts}:
        missing = sorted(set(requirements) - {item.identity for item in artifacts})
        unexpected = sorted({item.identity for item in artifacts} - set(requirements))
        raise ReleaseEvidenceError(
            f"artifact inventory mismatch; missing={missing}, unexpected={unexpected}"
        )
    roles = {item.role for item in artifacts}
    missing_roles = sorted(_REQUIRED_ROLES - roles)
    if missing_roles:
        raise ReleaseEvidenceError(f"missing required artifact roles: {missing_roles}")
    by_identity = {item.identity: item for item in artifacts}
    digest_by_identity = {
        _string_field(record, "identity"): _string_field(record, "output_digest")
        for record in records
    }
    config_digests = {
        digest_by_identity[item.identity]
        for item in artifacts
        if item.role in _CONFIG_ROLES
    }
    producer_digests = {
        digest_by_identity[item.identity]
        for item in artifacts
        if item.role == "producer"
    }
    if not producer_digests:
        raise ReleaseEvidenceError("at least one producer artifact is required")
    producer_items = [item for item in artifacts if item.role == "producer"]
    _require_unique(
        (digest_by_identity[item.identity] for item in producer_items),
        "producer digest",
    )
    producer_digest_by_path = {
        item.path: digest_by_identity[item.identity] for item in producer_items
    }
    unknown_producer_paths = sorted(
        set(producer_digest_by_path) - set(policy.authorized_producer_paths)
    )
    if unknown_producer_paths:
        raise ReleaseEvidenceError(
            f"unauthorized producer paths: {unknown_producer_paths}"
        )
    lock_digests = {
        digest_by_identity[item.identity]
        for item in artifacts
        if item.role == "dependency_lock"
    }
    if lock_digests != {dependency_lock_digest}:
        raise ReleaseEvidenceError(
            "dependency lock digest does not identify the lock artifact"
        )

    input_paths = {item.path for item in artifacts if item.role not in _OUTPUT_ROLES}
    output_paths = {item.path for item in artifacts if item.role in _OUTPUT_ROLES}
    overlapping_paths = sorted(
        (input_path, output_path)
        for input_path in input_paths
        for output_path in output_paths
        if _path_has_prefix(input_path, output_path)
        or _path_has_prefix(output_path, input_path)
    )
    if overlapping_paths:
        raise ReleaseEvidenceError(
            "generated output overlaps an immutable input (output overwrite): "
            f"{overlapping_paths}"
        )

    policy_artifacts = [
        item
        for item in artifacts
        if item.identity == "release-evidence-policy"
        or item.path == _RELEASE_POLICY_PATH
    ]
    if len(policy_artifacts) != 1:
        raise ReleaseEvidenceError(
            "the fixed release evidence policy artifact is required exactly once"
        )
    policy_artifact = policy_artifacts[0]
    if (
        policy_artifact.identity != "release-evidence-policy"
        or policy_artifact.role != "configuration"
        or policy_artifact.path != _RELEASE_POLICY_PATH
        or policy_artifact.output_digest != policy.output_digest
    ):
        raise ReleaseEvidenceError("release evidence policy artifact is inconsistent")

    for item in artifacts:
        requirement = requirements[item.identity]
        if (
            item.role != requirement.role
            or item.path != requirement.path
            or item.media_type != requirement.media_type
            or item.schema_version != requirement.schema_version
        ):
            raise ReleaseEvidenceError(
                f"artifact does not match its exact product inventory: {item.identity}"
            )
        _validate_embedded_schema_identity(root, item, requirement)
        _validate_embedded_input_inventory(root, item, requirement)
        observed_parent_identities = tuple(
            sorted(parent.identity for parent in item.parents)
        )
        if observed_parent_identities != requirement.required_parent_identities:
            raise ReleaseEvidenceError(
                f"artifact parent inventory mismatch: {item.identity}"
            )
        if requirement.producer_path is None:
            if item.producer_digest is not None:
                raise ReleaseEvidenceError(
                    f"producer asserted for producerless input: {item.identity}"
                )
        elif item.producer_digest not in producer_digests:
            raise ReleaseEvidenceError(f"unknown producer digest: {item.identity}")
        matching_rules = [
            rule
            for rule in policy.artifact_ownership
            if rule.artifact_role == item.role
            and _path_has_prefix(item.path, rule.artifact_path_prefix)
        ]
        if requirement.producer_path is not None and len(matching_rules) != 1:
            raise ReleaseEvidenceError(
                f"artifact ownership policy is not exact for {item.identity}"
            )
        expected_producer = (
            producer_digest_by_path.get(matching_rules[0].producer_path)
            if matching_rules
            else None
        )
        if requirement.producer_path is not None and expected_producer is None:
            raise ReleaseEvidenceError(
                f"authorized producer is absent for {item.identity}"
            )
        if (
            requirement.producer_path is not None
            and item.producer_digest != expected_producer
        ):
            raise ReleaseEvidenceError(
                f"artifact producer ownership mismatch: {item.identity}"
            )
        required_producer_digest = (
            producer_digest_by_path.get(requirement.producer_path)
            if requirement.producer_path is not None
            else None
        )
        if item.producer_digest != required_producer_digest:
            raise ReleaseEvidenceError(
                f"artifact producer does not match exact inventory: {item.identity}"
            )
        if item.role == "producer" and item.producer_digest != item.output_digest:
            raise ReleaseEvidenceError(
                f"producer artifact is not self-identifying: {item.identity}"
            )
        if item.role in _DERIVED_ROLES and not item.parents:
            raise ReleaseEvidenceError(
                f"derived artifact lacks a parent: {item.identity}"
            )
        if item.role in _OUTPUT_ROLES and not item.config_digests:
            raise ReleaseEvidenceError(f"output lacks config digests: {item.identity}")
        if (
            item.role in _OUTPUT_ROLES
            and policy.output_digest not in item.config_digests
        ):
            raise ReleaseEvidenceError(
                f"output lacks release policy digest: {item.identity}"
            )
        expected_config_digests = {
            digest_by_identity[identity]
            for identity in requirement.required_config_identities
        }
        if set(item.config_digests) != expected_config_digests:
            raise ReleaseEvidenceError(
                f"artifact configuration closure mismatch: {item.identity}"
            )
        unknown_configs = set(item.config_digests) - config_digests
        if unknown_configs:
            raise ReleaseEvidenceError(f"unknown config digest: {item.identity}")
        for parent in item.parents:
            if parent.identity not in by_identity:
                raise ReleaseEvidenceError(f"missing parent: {parent.identity}")
            if digest_by_identity[parent.identity] != parent.output_digest:
                raise ReleaseEvidenceError(f"parent digest mismatch: {parent.identity}")

    records_by_digest: dict[str, list[ArtifactInput]] = {}
    for item in artifacts:
        records_by_digest.setdefault(digest_by_identity[item.identity], []).append(item)
    for digest, aliases in records_by_digest.items():
        if len({item.role for item in aliases}) <= 1:
            continue
        identities = {item.identity for item in aliases}
        unauthorized_pairs = [
            frozenset((left, right))
            for left in identities
            for right in identities
            if left < right
            and requirements[left].role != requirements[right].role
            and frozenset((left, right)) not in policy.allowed_cross_role_digest_aliases
        ]
        if unauthorized_pairs:
            raise ReleaseEvidenceError(
                f"unauthorized cross-role digest alias: {digest}"
            )

    used_producers = {
        item.producer_digest for item in artifacts if item.role != "producer"
    }
    unused_producers = sorted(producer_digests - used_producers)
    if unused_producers:
        raise ReleaseEvidenceError(f"unused producer artifacts: {unused_producers}")

    _reject_cycles(by_identity)
    _validate_embedded_producer_identities(root, by_identity, policy)
    _validate_manifest_bundle_closures(root, by_identity, policy)
    if policy.mode == "product":
        _validate_propagation_contract_binding(root, by_identity, policy)
    for item in artifacts:
        if item.role == "generated_output" and not _has_source_ancestor(
            item.identity, by_identity
        ):
            raise ReleaseEvidenceError(f"output lacks source lineage: {item.identity}")


def _path_has_prefix(path: str, prefix: str) -> bool:
    return path == prefix or path.startswith(prefix + "/")


def _validate_embedded_producer_identities(
    root: Path,
    artifacts: Mapping[str, ArtifactInput],
    policy: _ReleaseEvidencePolicy,
) -> None:
    for requirement in policy.embedded_producer_identities:
        artifact = artifacts[requirement.artifact_identity]
        try:
            document = json.loads(_read_repository_file(root, artifact.path))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ReleaseEvidenceError(
                f"embedded producer identity is not valid JSON: {artifact.identity}"
            ) from error
        if not isinstance(document, Mapping):
            raise ReleaseEvidenceError(
                f"embedded producer identity is missing: {artifact.identity}"
            )
        if (
            document.get(requirement.id_field) != requirement.producer_id
            or document.get(requirement.version_field) != requirement.producer_version
        ):
            raise ReleaseEvidenceError(
                f"embedded producer id/version mismatch: {artifact.identity}"
            )
        source_records = [
            {
                "path": source_path,
                "sha256": hashlib.sha256(
                    _read_repository_file(root, source_path)
                ).hexdigest(),
            }
            for source_path in requirement.source_paths
        ]
        producer_digest = hashlib.sha256(
            json.dumps(source_records, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest()
        expected_digest = requirement.digest_prefix + producer_digest
        if document.get(requirement.digest_field) != expected_digest:
            raise ReleaseEvidenceError(
                f"embedded producer digest mismatch: {artifact.identity}"
            )


def _validate_manifest_bundle_closures(
    root: Path,
    artifacts: Mapping[str, ArtifactInput],
    policy: _ReleaseEvidencePolicy,
) -> None:
    for inventory in policy.bundle_inventories:
        artifact = artifacts[inventory.artifact_identity]
        manifest_path = PurePosixPath(artifact.path)
        directory_path = manifest_path.parent.as_posix()
        descriptor = _open_repository_object(root, directory_path)
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISDIR(before.st_mode):
                raise ReleaseEvidenceError(
                    f"bundle parent is not a directory: {artifact.identity}"
                )
            _require_public_directory_identity(
                root, directory_path, descriptor, before, artifact.identity
            )
            try:
                observed_names = sorted(os.listdir(descriptor))
            except OSError as error:
                raise ReleaseEvidenceError(
                    f"could not safely list bundle: {artifact.identity}"
                ) from error
            _require_public_directory_identity(
                root, directory_path, descriptor, before, artifact.identity
            )
            expected_names = sorted((*inventory.filenames, manifest_path.name))
            if observed_names != expected_names:
                raise ReleaseEvidenceError(
                    f"bundle file inventory mismatch: {artifact.identity}"
                )
            payloads = {
                name: _read_bundle_member(descriptor, name, artifact.identity)
                for name in expected_names
            }
            after = os.fstat(descriptor)
            if _stat_identity(before) != _stat_identity(after):
                raise ReleaseEvidenceError(
                    f"bundle changed while validating: {artifact.identity}"
                )
            _require_public_directory_identity(
                root, directory_path, descriptor, before, artifact.identity
            )

            _validate_bundle_payload_closure(
                artifact, manifest_path, inventory, payloads
            )
            _require_public_directory_identity(
                root, directory_path, descriptor, before, artifact.identity
            )
        finally:
            os.close(descriptor)


def _require_public_directory_identity(
    root: Path,
    directory_path: str,
    held_descriptor: int,
    expected: os.stat_result,
    artifact_identity: str,
) -> None:
    try:
        public_descriptor = _open_repository_object(root, directory_path)
    except ReleaseEvidenceError as error:
        raise ReleaseEvidenceError(
            f"public bundle directory changed: {artifact_identity}"
        ) from error
    try:
        held = os.fstat(held_descriptor)
        public = os.fstat(public_descriptor)
        if (
            not stat.S_ISDIR(held.st_mode)
            or not stat.S_ISDIR(public.st_mode)
            or _stat_identity(held) != _stat_identity(expected)
            or _stat_identity(public) != _stat_identity(expected)
        ):
            raise ReleaseEvidenceError(
                f"public bundle directory changed: {artifact_identity}"
            )
    finally:
        os.close(public_descriptor)


def _validate_bundle_payload_closure(
    artifact: ArtifactInput,
    manifest_path: PurePosixPath,
    inventory: _BundleInventory,
    payloads: Mapping[str, bytes],
) -> None:
    manifest_payload = payloads[manifest_path.name]
    if _digest_bytes(manifest_payload) != artifact.output_digest:
        raise ReleaseEvidenceError(
            f"bundle manifest identity changed: {artifact.identity}"
        )
    manifest = _json_object(manifest_payload, f"{artifact.identity} manifest")
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise ReleaseEvidenceError(
            f"bundle manifest files are missing: {artifact.identity}"
        )
    if manifest.get("payload_file_count") != len(inventory.filenames):
        raise ReleaseEvidenceError(
            f"bundle payload count mismatch: {artifact.identity}"
        )
    normalized_entries: list[tuple[str, str, int]] = []
    for raw_entry in entries:
        entry = _mapping(raw_entry, "bundle manifest entry")
        if set(entry) != {"path", "sha256", "record_count"}:
            raise ReleaseEvidenceError(
                f"bundle manifest entry fields are invalid: {artifact.identity}"
            )
        filename = _string_field(entry, "path")
        digest = _string_field(entry, "sha256")
        record_count = _int_field(entry, "record_count")
        if _RAW_SHA256_PATTERN.fullmatch(digest) is None or record_count < 0:
            raise ReleaseEvidenceError(
                f"bundle manifest entry identity is invalid: {artifact.identity}"
            )
        normalized_entries.append((filename, digest, record_count))
    entry_filenames = [entry[0] for entry in normalized_entries]
    if entry_filenames != list(inventory.filenames):
        raise ReleaseEvidenceError(
            f"bundle manifest inventory mismatch: {artifact.identity}"
        )
    _require_unique(entry_filenames, "bundle manifest filename")
    for filename, expected_digest, expected_record_count in normalized_entries:
        payload = payloads[filename]
        if hashlib.sha256(payload).hexdigest() != expected_digest:
            raise ReleaseEvidenceError(
                f"bundle member digest mismatch: {artifact.identity}: {filename}"
            )
        document = _json_object(
            payload, f"{artifact.identity} bundle member {filename}"
        )
        observed_record_count = document.get("record_count")
        if (
            isinstance(observed_record_count, bool)
            or not isinstance(observed_record_count, int)
            or observed_record_count < 0
            or observed_record_count != expected_record_count
        ):
            raise ReleaseEvidenceError(
                f"bundle member record count mismatch: {artifact.identity}: {filename}"
            )
    digest_input = "".join(
        f"{filename}\0{digest}\0{record_count}\n"
        for filename, digest, record_count in normalized_entries
    ).encode("utf-8")
    if manifest.get("bundle_digest") != hashlib.sha256(digest_input).hexdigest():
        raise ReleaseEvidenceError(
            f"bundle digest reconciliation mismatch: {artifact.identity}"
        )


def _read_bundle_member(
    directory_descriptor: int, filename: str, artifact_identity: str
) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(filename, flags, dir_fd=directory_descriptor)
    except OSError as error:
        raise ReleaseEvidenceError(
            f"bundle member is missing or unsafe: {artifact_identity}: {filename}"
        ) from error
    try:
        opened = os.fstat(descriptor)
        linked = os.stat(filename, dir_fd=directory_descriptor, follow_symlinks=False)
        if not stat.S_ISREG(opened.st_mode) or _object_identity(
            opened
        ) != _object_identity(linked):
            raise ReleaseEvidenceError(
                f"bundle member is not a stable regular file: "
                f"{artifact_identity}: {filename}"
            )
        return _read_file_descriptor(
            descriptor, f"{artifact_identity} bundle member {filename}"
        )
    finally:
        os.close(descriptor)


def _json_object(payload: bytes, label: str) -> Mapping[str, object]:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ReleaseEvidenceError(f"duplicate JSON field in {label}: {key}")
            result[key] = value
        return result

    try:
        document = json.loads(payload, object_pairs_hook=reject_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseEvidenceError(f"invalid JSON in {label}") from error
    if not isinstance(document, Mapping):
        raise ReleaseEvidenceError(f"JSON object required in {label}")
    return document


def _validate_propagation_contract_binding(
    root: Path,
    artifacts: Mapping[str, ArtifactInput],
    policy: _ReleaseEvidencePolicy,
) -> None:
    contract = policy.propagation_contract
    propagation = json.loads(_read_repository_file(root, artifacts["propagation"].path))
    scenario = json.loads(_read_repository_file(root, artifacts["scenario"].path))
    if not isinstance(propagation, Mapping) or not isinstance(scenario, Mapping):
        raise ReleaseEvidenceError("propagation contract evidence must be JSON objects")
    propagation_path = PurePosixPath(artifacts["propagation"].path)
    scenario_path = PurePosixPath(artifacts["scenario"].path)
    if propagation_path.parent != scenario_path.parent:
        raise ReleaseEvidenceError(
            "propagation manifest and sensitivity must share one immutable bundle"
        )
    shared_identity_fields = (
        "build_id",
        "event_manifest_digest",
        "propagation_contract_version",
        "propagation_contract_digest",
        "propagation_producer_id",
        "propagation_producer_version",
        "propagation_producer_digest",
    )
    if any(
        propagation.get(field) is None or propagation.get(field) != scenario.get(field)
        for field in shared_identity_fields
    ):
        raise ReleaseEvidenceError("propagation bundle identity mismatch")
    if propagation.get(
        "propagation_contract_version"
    ) != contract.contract_version or propagation.get(
        "propagation_contract_digest"
    ) != contract.output_digest.removeprefix("sha256:"):
        raise ReleaseEvidenceError("propagation manifest contract identity mismatch")
    files = propagation.get("files")
    if not isinstance(files, list):
        raise ReleaseEvidenceError("propagation manifest file inventory is missing")
    sensitivity_entries = [
        entry
        for entry in files
        if isinstance(entry, Mapping) and entry.get("path") == scenario_path.name
    ]
    sensitivity_payload = _read_repository_file(root, artifacts["scenario"].path)
    if (
        len(sensitivity_entries) != 1
        or sensitivity_entries[0].get("sha256")
        != hashlib.sha256(sensitivity_payload).hexdigest()
    ):
        raise ReleaseEvidenceError(
            "propagation manifest does not bind the sensitivity artifact"
        )
    classification_payload = _read_repository_file(
        root, artifacts["classification"].path
    )
    classification = json.loads(classification_payload)
    if not isinstance(classification, Mapping):
        raise ReleaseEvidenceError("classification lineage evidence is invalid")
    classification_files = classification.get("files")
    accepted_queue_entries = (
        [
            entry
            for entry in classification_files
            if isinstance(entry, Mapping)
            and entry.get("path") == "accepted_mapping_queue.json"
        ]
        if isinstance(classification_files, list)
        else []
    )
    if (
        scenario.get("classification_review_digest")
        != hashlib.sha256(classification_payload).hexdigest()
        or scenario.get("classification_contract_version")
        != classification.get("classification_contract_version")
        or len(accepted_queue_entries) != 1
        or scenario.get("accepted_classification_mapping_count")
        != accepted_queue_entries[0].get("record_count")
    ):
        raise ReleaseEvidenceError("propagation classification lineage mismatch")
    scenarios = scenario.get("scenarios")
    if not isinstance(scenarios, list):
        raise ReleaseEvidenceError("propagation sensitivity scenarios are missing")
    matches = [
        item
        for item in scenarios
        if isinstance(item, Mapping) and item.get("scenario_id") == contract.scenario_id
    ]
    if len(matches) != 1 or (
        matches[0].get("maximum_distance_km") != contract.maximum_distance_km
        or matches[0].get("maximum_lag_years") != contract.maximum_lag_years
    ):
        raise ReleaseEvidenceError("default propagation scenario identity mismatch")


def _validate_embedded_schema_identity(
    root: Path, item: ArtifactInput, requirement: _RequiredArtifact
) -> None:
    if item.media_type != "application/json" and not item.media_type.endswith("+json"):
        if requirement.schema_identity_field is not None:
            raise ReleaseEvidenceError(
                f"non-JSON artifact declares embedded schema identity: {item.identity}"
            )
        return
    payload = _read_repository_file(root, item.path)

    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ReleaseEvidenceError(
                    f"duplicate JSON field in artifact: {item.identity}"
                )
            result[key] = value
        return result

    try:
        parsed = json.loads(payload, object_pairs_hook=reject_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseEvidenceError(
            f"artifact is not valid JSON: {item.identity}"
        ) from error
    if not isinstance(parsed, Mapping):
        raise ReleaseEvidenceError(f"JSON artifact is not an object: {item.identity}")
    field = requirement.schema_identity_field
    if field is None:
        if any(
            candidate in parsed for candidate in ("schema_version", "schema", "$schema")
        ):
            raise ReleaseEvidenceError(
                f"unversioned JSON artifact exposes an undeclared schema identity: {item.identity}"
            )
        return
    if parsed.get(field) != requirement.schema_version:
        raise ReleaseEvidenceError(
            f"embedded schema identity mismatch: {item.identity}"
        )


def _validate_embedded_input_inventory(
    root: Path, item: ArtifactInput, requirement: _RequiredArtifact
) -> None:
    if not requirement.required_embedded_input_paths:
        return
    try:
        parsed = json.loads(_read_repository_file(root, item.path))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseEvidenceError(
            f"embedded input inventory is not valid JSON: {item.identity}"
        ) from error
    if not isinstance(parsed, Mapping) or not isinstance(
        parsed.get("input_artifacts"), list
    ):
        raise ReleaseEvidenceError(
            f"embedded input inventory is missing: {item.identity}"
        )
    observed: dict[str, Mapping[str, object]] = {}
    for raw_record in parsed["input_artifacts"]:
        record = _mapping(raw_record, "embedded input artifact")
        if set(record) != {"path", "sha256", "byte_count"}:
            raise ReleaseEvidenceError(
                f"embedded input record fields are invalid: {item.identity}"
            )
        path = _string_field(record, "path")
        if path in observed:
            raise ReleaseEvidenceError(
                f"duplicate embedded input path: {item.identity}"
            )
        observed[path] = record
    if set(observed) != set(requirement.required_embedded_input_paths):
        raise ReleaseEvidenceError(
            f"embedded input inventory mismatch: {item.identity}"
        )
    for path in requirement.required_embedded_input_paths:
        payload = _read_repository_file(root, path)
        record = observed[path]
        if record["sha256"] != hashlib.sha256(payload).hexdigest() or record[
            "byte_count"
        ] != len(payload):
            raise ReleaseEvidenceError(
                f"embedded input digest mismatch: {item.identity}: {path}"
            )


def _reject_cycles(artifacts: Mapping[str, ArtifactInput]) -> None:
    visited: set[str] = set()
    active: set[str] = set()

    def visit(identity: str) -> None:
        if identity in active:
            raise ReleaseEvidenceError(f"artifact lineage cycle at {identity}")
        if identity in visited:
            return
        active.add(identity)
        for parent in artifacts[identity].parents:
            visit(parent.identity)
        active.remove(identity)
        visited.add(identity)

    for identity in sorted(artifacts):
        visit(identity)


def _has_source_ancestor(identity: str, artifacts: Mapping[str, ArtifactInput]) -> bool:
    item = artifacts[identity]
    if item.role in {"source_receipt", "source_snapshot"}:
        return True
    return any(
        _has_source_ancestor(parent.identity, artifacts) for parent in item.parents
    )


def _validate_gates(
    root: Path,
    gates: Sequence[GateResult],
    records: Sequence[Mapping[str, object]],
    policy: _ReleaseEvidencePolicy,
) -> None:
    if not gates:
        raise ReleaseEvidenceError("at least one required gate result is required")
    _require_unique((gate.identity for gate in gates), "gate identity")
    _require_unique((gate.evidence_digest for gate in gates), "gate evidence digest")
    validation_records = [
        record for record in records if record["role"] == "validation_result"
    ]
    if frozenset(gate.identity for gate in gates) != policy.required_gate_ids:
        raise ReleaseEvidenceError("gate inventory does not match product policy")
    required_flags = {gate.required for gate in gates}
    if required_flags != {True}:
        raise ReleaseEvidenceError("every product-policy gate must be required")
    by_digest: dict[str, list[Mapping[str, object]]] = {}
    for record in validation_records:
        by_digest.setdefault(_string_field(record, "output_digest"), []).append(record)
    for gate in gates:
        _require_identity(gate.identity, "gate identity")
        if gate.status not in _GATE_STATUSES:
            raise ReleaseEvidenceError(f"invalid gate status: {gate.status}")
        if type(gate.required) is not bool:
            raise ReleaseEvidenceError("gate required flag must be a boolean")
        _require_digest(gate.evidence_digest, "gate evidence digest")
        if gate.attestation not in {
            "local_self_attestation",
            "independent_execution_attestation",
            "external_authority_attestation",
        }:
            raise ReleaseEvidenceError(f"invalid gate attestation: {gate.identity}")
        if gate.attestation == "local_self_attestation":
            if gate.authority_id is not None:
                raise ReleaseEvidenceError(
                    "local gate cannot assert external authority"
                )
        else:
            raise ReleaseEvidenceError(
                "non-local gate attestation trust is not configured"
            )
        evidence = by_digest.get(gate.evidence_digest, [])
        if len(evidence) != 1:
            raise ReleaseEvidenceError(
                f"gate evidence is not a validation artifact: {gate.identity}"
            )
        record = evidence[0]
        if gate.attestation == "local_self_attestation":
            if record["schema_version"] != "recorded-gate.v4":
                raise ReleaseEvidenceError(
                    f"gate evidence is not recorded-gate.v4: {gate.identity}"
                )
            validate_recorded_gate(
                root,
                _string_field(record, "path"),
                expected_gate=gate,
            )
    if len(validation_records) != len(gates):
        raise ReleaseEvidenceError(
            "every validation artifact must map to exactly one gate result"
        )


def _validate_reconciliations(
    items: Sequence[CountReconciliation], policy: _ReleaseEvidencePolicy
) -> None:
    if not items:
        raise ReleaseEvidenceError("source and country reconciliations are required")
    _require_unique((item.identity for item in items), "reconciliation identity")
    _require_unique(
        (
            f"{item.source}\0{item.entity}\0{item.dimension}\0{item.country_code}\0{item.scope}"
            for item in items
        ),
        "reconciliation key",
    )
    grouped: dict[tuple[str, str], dict[str, list[CountReconciliation]]] = {}
    allowed_scope_keys = {
        "country_code",
        "target_country_code",
        "resolution",
        "feature",
        "unit",
        "status",
    }
    for item in items:
        _require_identity(item.identity, "reconciliation identity")
        if item.dimension not in {"source", "country", "scope"}:
            raise ReleaseEvidenceError(
                f"invalid reconciliation dimension: {item.dimension}"
            )
        if not item.source.strip() or not item.entity.strip():
            raise ReleaseEvidenceError("reconciliation source/entity must be non-empty")
        if item.dimension == "source" and item.country_code is not None:
            raise ReleaseEvidenceError(
                "source reconciliation cannot carry a country code"
            )
        if item.dimension == "country" and item.country_code not in _COUNTRIES:
            raise ReleaseEvidenceError(f"invalid country code: {item.country_code}")
        if item.dimension != "country" and item.country_code is not None:
            raise ReleaseEvidenceError(
                "only country reconciliation can carry country_code"
            )
        if item.dimension == "scope" and not item.scope:
            raise ReleaseEvidenceError("scoped reconciliation requires scope fields")
        if item.dimension != "scope" and item.scope:
            raise ReleaseEvidenceError(
                "only scoped reconciliation can carry scope fields"
            )
        scope_keys = [key for key, _value in item.scope]
        if scope_keys != sorted(scope_keys) or len(scope_keys) != len(set(scope_keys)):
            raise ReleaseEvidenceError(
                "reconciliation scope keys must be unique/sorted"
            )
        if set(scope_keys) - allowed_scope_keys or any(
            not value for _key, value in item.scope
        ):
            raise ReleaseEvidenceError("reconciliation scope is invalid")
        if item.count_status not in {"reported", "unavailable", "refused"}:
            raise ReleaseEvidenceError(
                f"invalid reconciliation count status: {item.count_status}"
            )
        if list(item.reason_codes) != sorted(item.reason_codes):
            raise ReleaseEvidenceError("reconciliation reason codes must be sorted")
        _require_unique(item.reason_codes, "reconciliation reason code")
        for reason_code in item.reason_codes:
            _require_identity(reason_code, "reconciliation reason code")
        counts = _counts(item)
        if item.count_status == "reported" and any(
            type(value) is not int or value < 0 for value in counts.values()
        ):
            raise ReleaseEvidenceError(
                f"reported counts must be non-null non-negative integers: {item.identity}"
            )
        if item.count_status != "reported" and (
            any(value is not None for value in counts.values()) or not item.reason_codes
        ):
            raise ReleaseEvidenceError(
                f"unavailable/refused counts must be null and reason-coded: {item.identity}"
            )
        if item.count_status == "reported" and item.eligible_count != cast(
            int, item.accepted_count
        ) + cast(int, item.refused_count):
            raise ReleaseEvidenceError(
                f"eligible count is inconsistent: {item.identity}"
            )
        if item.count_status == "reported" and (
            item.candidate_count
            != cast(int, item.eligible_count)
            + cast(int, item.unresolved_count)
            + cast(int, item.excluded_count)
        ):
            raise ReleaseEvidenceError(
                f"candidate denominator is inconsistent: {item.identity}"
            )
        group = grouped.setdefault(
            (item.source, item.entity), {"source": [], "country": [], "scope": []}
        )
        group[item.dimension].append(item)

    for key, dimensions in grouped.items():
        source_rows = dimensions["source"]
        country_rows = dimensions["country"]
        if len(source_rows) != 1:
            raise ReleaseEvidenceError(
                f"one source reconciliation is required for {key}"
            )
        scope_rows = dimensions["scope"]
        if country_rows and scope_rows:
            raise ReleaseEvidenceError(
                f"reconciliation group mixes country and extensible scopes: {key}"
            )
        if country_rows:
            country_codes = {item.country_code for item in country_rows}
            if len(country_rows) != len(_COUNTRIES) or any(
                code not in country_codes for code in _COUNTRIES
            ):
                raise ReleaseEvidenceError(
                    f"complete country reconciliation is required for {key}"
                )
        partition_rows = country_rows or scope_rows
        if not partition_rows:
            raise ReleaseEvidenceError(
                f"reconciliation partitions are required for {key}"
            )
        source_counts = _counts(source_rows[0])
        if any(
            item.count_status != source_rows[0].count_status for item in partition_rows
        ):
            raise ReleaseEvidenceError(
                f"source and partition availability statuses differ for {key}"
            )
        for field, source_count in source_counts.items():
            partition_values = [_counts(item)[field] for item in partition_rows]
            if source_count is None:
                reconciles = all(value is None for value in partition_values)
            else:
                reconciles = all(value is not None for value in partition_values) and (
                    source_count == sum(cast(int, value) for value in partition_values)
                )
            if not reconciles:
                raise ReleaseEvidenceError(
                    f"country/source count mismatch (partition model) for {key}: {field}"
                )

    requirements = {
        (item.source, item.entity): item for item in policy.required_reconciliations
    }
    missing_groups = sorted(set(requirements) - set(grouped))
    if missing_groups:
        raise ReleaseEvidenceError(
            f"missing required reconciliation groups: {missing_groups}"
        )
    unexpected_groups = sorted(set(grouped) - set(requirements))
    if unexpected_groups:
        raise ReleaseEvidenceError(
            f"unexpected reconciliation groups: {unexpected_groups}"
        )
    for key, requirement in requirements.items():
        dimensions = grouped[key]
        if requirement.dimension == "country":
            if dimensions["scope"]:
                raise ReleaseEvidenceError(
                    f"country reconciliation required by policy for {key}"
                )
            continue
        if dimensions["country"]:
            raise ReleaseEvidenceError(
                f"extensible scope reconciliation required by policy for {key}"
            )
        expected_scope_keys = tuple(key for key, _values in requirement.scope_values)
        expected_scopes = {
            tuple(zip(expected_scope_keys, values, strict=True))
            for values in product(
                *(values for _key, values in requirement.scope_values)
            )
        }
        observed_scopes = {item.scope for item in dimensions["scope"]}
        if observed_scopes != expected_scopes:
            raise ReleaseEvidenceError(f"scope partition inventory mismatch for {key}")


def _validate_blockers(
    blockers: Sequence[Blocker],
    records: Sequence[Mapping[str, object]],
    gates: Sequence[GateResult],
    policy: _ReleaseEvidencePolicy,
) -> None:
    _require_unique((blocker.identity for blocker in blockers), "blocker identity")
    evidence_digests = {_string_field(record, "output_digest") for record in records}
    for blocker in blockers:
        _require_identity(blocker.identity, "blocker identity")
        _require_identity(blocker.reason_code, "blocker reason_code")
        _require_digest(blocker.evidence_digest, "blocker evidence digest")
        if blocker.kind not in {"external", "unverified", "refused", "reduced_scope"}:
            raise ReleaseEvidenceError(f"invalid blocker kind: {blocker.identity}")
        required_text = {
            "required_scope": blocker.required_scope,
            "owner": blocker.owner,
            "first_observed_at": blocker.first_observed_at,
            "last_observed_at": blocker.last_observed_at,
            "response_class": blocker.response_class,
            "impact": blocker.impact,
            "expected_artifact": blocker.expected_artifact,
            "next_action": blocker.next_action,
            "recheck_condition": blocker.recheck_condition,
        }
        if any(not value.strip() for value in required_text.values()):
            raise ReleaseEvidenceError(
                f"blocker lacks actionable fields: {blocker.identity}"
            )
        first_observed = _utc_timestamp(blocker.first_observed_at)
        last_observed = _utc_timestamp(blocker.last_observed_at)
        if first_observed > last_observed:
            raise ReleaseEvidenceError(
                f"blocker observation interval is invalid: {blocker.identity}"
            )
        if blocker.request_status == "governed":
            if (
                blocker.request_artifact_identity is None
                or blocker.request_fingerprint is None
            ):
                raise ReleaseEvidenceError(
                    f"governed blocker request lacks artifact identity: {blocker.identity}"
                )
            _require_digest(
                blocker.request_fingerprint,
                f"blocker request fingerprint: {blocker.identity}",
            )
            if (
                blocker.request_artifact_identity
                not in policy.governed_request_artifact_ids
            ):
                raise ReleaseEvidenceError(
                    f"blocker request artifact is not authorized: {blocker.identity}"
                )
            request_records = [
                record
                for record in records
                if record["identity"] == blocker.request_artifact_identity
                and record["output_digest"] == blocker.request_fingerprint
            ]
            if len(request_records) != 1:
                raise ReleaseEvidenceError(
                    f"blocker request artifact is not governed: {blocker.identity}"
                )
        elif blocker.request_status == "refused":
            if (
                blocker.request_artifact_identity is not None
                or blocker.request_fingerprint is not None
            ):
                raise ReleaseEvidenceError(
                    f"refused blocker request cannot assert a fingerprint: {blocker.identity}"
                )
        else:
            raise ReleaseEvidenceError(
                f"invalid blocker request status: {blocker.identity}"
            )
        if (
            not blocker.observations
            or not blocker.attempts
            or not blocker.impacted_gates
        ):
            raise ReleaseEvidenceError(
                f"blocker lacks observations, attempts, or impacted gates: {blocker.identity}"
            )
        if any(not item.strip() for item in (*blocker.observations, *blocker.attempts)):
            raise ReleaseEvidenceError(
                f"blocker has empty observation or attempt: {blocker.identity}"
            )
        if list(blocker.impacted_gates) != sorted(blocker.impacted_gates):
            raise ReleaseEvidenceError(
                f"blocker impacted gates are not sorted: {blocker.identity}"
            )
        unknown_gates = set(blocker.impacted_gates) - policy.required_gate_ids
        if unknown_gates:
            raise ReleaseEvidenceError(
                f"blocker names unknown impacted gates: {blocker.identity}"
            )
        if blocker.evidence_digest not in evidence_digests:
            raise ReleaseEvidenceError(
                f"blocker evidence is not in the manifest: {blocker.identity}"
            )
        evidence_identities = {
            _string_field(record, "identity")
            for record in records
            if record["output_digest"] == blocker.evidence_digest
        }
        gate_evidence_identities = {
            gate.identity: next(
                _string_field(record, "identity")
                for record in records
                if record["output_digest"] == gate.evidence_digest
            )
            for gate in gates
        }
        for gate_id in blocker.impacted_gates:
            relevant = _policy_artifact_ancestor_identities(
                gate_evidence_identities[gate_id], policy
            )
            if evidence_identities.isdisjoint(relevant):
                raise ReleaseEvidenceError(
                    f"blocker evidence is unrelated to impacted gate: {blocker.identity}"
                )


def _policy_artifact_ancestor_identities(
    identity: str, policy: _ReleaseEvidencePolicy
) -> set[str]:
    requirements = {item.identity: item for item in policy.required_artifacts}
    found = {identity}
    ready = [identity]
    while ready:
        current = ready.pop()
        for parent in requirements[current].required_parent_identities:
            if parent not in found:
                found.add(parent)
                ready.append(parent)
    return found


def _release_decision(
    dirty: bool, gates: Sequence[GateResult], blockers: Sequence[Blocker]
) -> dict[str, object]:
    required_nonpass = [
        gate for gate in gates if gate.required and gate.status != "PASS"
    ]
    reasons = [
        f"required_gate_{gate.status.lower()}:{gate.identity}"
        for gate in required_nonpass
    ]
    reasons.extend(
        f"required_gate_not_independently_attested:{gate.identity}"
        for gate in gates
        if gate.required
        and gate.status == "PASS"
        and gate.attestation == "local_self_attestation"
    )
    reasons.extend(f"blocker:{blocker.reason_code}" for blocker in blockers)
    if dirty:
        reasons.append("candidate_dirty")
    release_ready = not reasons
    blocker_kinds = {blocker.kind for blocker in blockers}
    if release_ready:
        status = "verified_complete"
    elif any(gate.status == "FAIL" for gate in required_nonpass):
        status = "failed"
    elif "external" in blocker_kinds:
        status = "external_blocked"
    elif "refused" in blocker_kinds:
        status = "refused_invalid"
    elif (
        blocker_kinds == {"reduced_scope"}
        and not required_nonpass
        and all(gate.attestation != "local_self_attestation" for gate in gates)
    ):
        status = "verified_partial"
    elif any(gate.status == "BLOCKED_EXTERNAL" for gate in required_nonpass):
        status = "external_blocked"
    else:
        status = "implemented_unverified"
    return {
        "release_ready": release_ready,
        "status": status,
        "reason_codes": sorted(reasons),
    }


def _hash_repository_object(
    root: Path,
    relative_path: str,
    *,
    exclude_python_cache: bool = False,
) -> dict[str, object]:
    descriptor = _open_repository_object(root, relative_path)
    try:
        mode = os.fstat(descriptor).st_mode
        if stat.S_ISREG(mode):
            digest, byte_size = _hash_file_descriptor(descriptor, relative_path)
            return {
                "object_type": "file",
                "output_digest": digest,
                "byte_size": byte_size,
                "file_count": 1,
            }
        if stat.S_ISDIR(mode):
            entries = _tree_entries_descriptor(
                descriptor, exclude_python_cache=exclude_python_cache
            )
            return {
                "object_type": "tree",
                "output_digest": _digest_json(entries),
                "byte_size": sum(cast(int, entry["byte_size"]) for entry in entries),
                "file_count": len(entries),
            }
    finally:
        os.close(descriptor)
    raise ReleaseEvidenceError(
        f"artifact is not a regular file or directory: {relative_path}"
    )


def _open_repository_object(root: Path, relative_path: str) -> int:
    pure = _relative_path(relative_path)
    directory_flags = (
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    )
    object_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        root_before = os.stat(root, follow_symlinks=False)
        descriptor = os.open(root, directory_flags)
        root_opened = os.fstat(descriptor)
        root_after = os.stat(root, follow_symlinks=False)
        if (
            not stat.S_ISDIR(root_opened.st_mode)
            or _object_identity(root_before) != _object_identity(root_opened)
            or _object_identity(root_opened) != _object_identity(root_after)
        ):
            raise ReleaseEvidenceError("repository root changed while opening")
        for index, part in enumerate(pure.parts):
            flags = object_flags if index == len(pure.parts) - 1 else directory_flags
            next_descriptor = os.open(part, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except ReleaseEvidenceError:
        with suppress(UnboundLocalError):
            os.close(descriptor)
        raise
    except OSError as error:
        with suppress(UnboundLocalError):
            os.close(descriptor)
        raise ReleaseEvidenceError(
            f"artifact path is missing or unsafe: {relative_path}"
        ) from error


def _read_repository_file(root: Path, relative_path: str) -> bytes:
    descriptor = _open_repository_object(root, relative_path)
    try:
        mode = os.fstat(descriptor).st_mode
        if not stat.S_ISREG(mode):
            raise ReleaseEvidenceError(
                f"artifact is not a regular file: {relative_path}"
            )
        return _read_file_descriptor(descriptor, relative_path)
    finally:
        os.close(descriptor)


def _read_file_descriptor(descriptor: int, label: str) -> bytes:
    before = os.fstat(descriptor)
    with os.fdopen(os.dup(descriptor), "rb") as stream:
        payload = stream.read()
    after = os.fstat(descriptor)
    if _stat_identity(before) != _stat_identity(after):
        raise ReleaseEvidenceError(f"file changed while reading: {label}")
    return payload


def _hash_file_descriptor(descriptor: int, label: str) -> tuple[str, int]:
    before = os.fstat(descriptor)
    if not stat.S_ISREG(before.st_mode):
        raise ReleaseEvidenceError(f"artifact is not a regular file: {label}")
    digest = hashlib.sha256()
    with os.fdopen(os.dup(descriptor), "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    after = os.fstat(descriptor)
    if _stat_identity(before) != _stat_identity(after):
        raise ReleaseEvidenceError(f"file changed while hashing: {label}")
    return f"sha256:{digest.hexdigest()}", before.st_size


def _tree_entries_descriptor(
    descriptor: int,
    prefix: PurePosixPath | None = None,
    *,
    exclude_python_cache: bool = False,
) -> list[dict[str, object]]:
    if prefix is None:
        prefix = PurePosixPath()
    before = os.fstat(descriptor)
    entries: list[dict[str, object]] = []
    try:
        names = sorted(os.listdir(descriptor))
    except OSError as error:
        raise ReleaseEvidenceError("could not safely list artifact tree") from error
    for name in names:
        relative = prefix / name
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            child = os.open(name, flags, dir_fd=descriptor)
        except OSError as error:
            raise ReleaseEvidenceError(
                f"could not safely open artifact tree member: {relative.as_posix()}"
            ) from error
        try:
            member = os.fstat(child)
            path_member = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            if (member.st_dev, member.st_ino) != (
                path_member.st_dev,
                path_member.st_ino,
            ):
                raise ReleaseEvidenceError(
                    f"artifact tree member changed: {relative.as_posix()}"
                )
            if (
                stat.S_ISREG(member.st_mode)
                and exclude_python_cache
                and name.endswith((".pyc", ".pyo"))
            ):
                continue
            if stat.S_ISREG(member.st_mode):
                digest, byte_size = _hash_file_descriptor(child, relative.as_posix())
                entries.append(
                    {
                        "path": relative.as_posix(),
                        "output_digest": digest,
                        "byte_size": byte_size,
                    }
                )
            elif stat.S_ISDIR(member.st_mode):
                entries.extend(
                    _tree_entries_descriptor(
                        child,
                        relative,
                        exclude_python_cache=exclude_python_cache,
                    )
                )
            else:
                raise ReleaseEvidenceError(
                    f"special file in artifact tree: {relative.as_posix()}"
                )
        finally:
            os.close(child)
    after = os.fstat(descriptor)
    if _stat_identity(before) != _stat_identity(after):
        raise ReleaseEvidenceError("artifact tree changed while hashing")
    return entries


def _stat_identity(value: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _object_identity(value: os.stat_result) -> tuple[int, int]:
    return (value.st_dev, value.st_ino)


def _repository_state(root: Path, mode: str) -> dict[str, object]:
    if mode == "fixture":
        return {
            "mode": "fixture",
            "head_commit": None,
            "head_tree": None,
            "dirty": False,
            "status_digest": None,
            "tracked_paths_digest": None,
            "tracked_diff_digest": None,
            "untracked_objects": [],
        }

    def run(*arguments: str) -> bytes:
        try:
            # The executable is fixed and arguments are internal repository probes.
            completed = subprocess.run(  # nosec B603
                ("git", "-C", str(root), *arguments),
                check=True,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                shell=False,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            raise ReleaseEvidenceError(
                "product release evidence requires an inspectable Git worktree"
            ) from error
        return completed.stdout

    top_level = run("rev-parse", "--show-toplevel").decode().strip()
    if Path(top_level).resolve() != root:
        raise ReleaseEvidenceError("release evidence root is not the Git worktree root")
    head_commit = run("rev-parse", "HEAD").decode().strip()
    head_tree = run("rev-parse", "HEAD^{tree}").decode().strip()
    status = run("status", "--porcelain=v1", "-z", "--untracked-files=all")
    tracked_paths = run("ls-files", "-z")
    tracked_diff = run("diff", "--binary", "HEAD", "--")
    untracked_paths = [
        item.decode("utf-8")
        for item in run("ls-files", "--others", "--exclude-standard", "-z").split(b"\0")
        if item
    ]
    untracked_objects = [
        {"path": path, **_hash_repository_object(root, path)}
        for path in sorted(untracked_paths)
    ]
    return {
        "mode": "product",
        "head_commit": head_commit,
        "head_tree": head_tree,
        "dirty": bool(status),
        "status_digest": _digest_bytes(status),
        "tracked_paths_digest": _digest_bytes(tracked_paths),
        "tracked_diff_digest": _digest_bytes(tracked_diff),
        "untracked_objects": untracked_objects,
    }


def _digest_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _repository_root(repository_root: Path) -> Path:
    try:
        root = repository_root.resolve(strict=True)
    except OSError as error:
        raise ReleaseEvidenceError("repository root does not exist") from error
    if not root.is_dir():
        raise ReleaseEvidenceError("repository root must be a directory")
    return root


def _gate_record(item: GateResult) -> dict[str, object]:
    return {
        "identity": item.identity,
        "status": item.status,
        "required": item.required,
        "evidence_digest": item.evidence_digest,
        "attestation": item.attestation,
        "authority_id": item.authority_id,
    }


def _reconciliation_record(item: CountReconciliation) -> dict[str, object]:
    return {
        "identity": item.identity,
        "dimension": item.dimension,
        "source": item.source,
        "entity": item.entity,
        "country_code": item.country_code,
        "scope": dict(item.scope),
        "count_status": item.count_status,
        "reason_codes": list(item.reason_codes),
        **_counts(item),
    }


def _blocker_record(item: Blocker) -> dict[str, object]:
    return {
        "identity": item.identity,
        "reason_code": item.reason_code,
        "evidence_digest": item.evidence_digest,
        "kind": item.kind,
        "required_scope": item.required_scope,
        "owner": item.owner,
        "first_observed_at": item.first_observed_at,
        "last_observed_at": item.last_observed_at,
        "request_fingerprint": item.request_fingerprint,
        "request_status": item.request_status,
        "request_artifact_identity": item.request_artifact_identity,
        "response_class": item.response_class,
        "observations": list(item.observations),
        "attempts": list(item.attempts),
        "impact": item.impact,
        "expected_artifact": item.expected_artifact,
        "impacted_gates": list(item.impacted_gates),
        "next_action": item.next_action,
        "recheck_condition": item.recheck_condition,
    }


def _counts(item: CountReconciliation) -> dict[str, int | None]:
    return {
        "candidate_count": item.candidate_count,
        "eligible_count": item.eligible_count,
        "accepted_count": item.accepted_count,
        "unresolved_count": item.unresolved_count,
        "excluded_count": item.excluded_count,
        "refused_count": item.refused_count,
    }


def _parse_artifact(value: object) -> ArtifactInput:
    record = _mapping(value, "artifact")
    expected = {
        "identity",
        "role",
        "path",
        "media_type",
        "schema_version",
        "parents",
        "config_digests",
        "producer_digest",
        "object_type",
        "output_digest",
        "byte_size",
        "file_count",
    }
    if set(record) != expected:
        raise ReleaseEvidenceError("artifact fields do not match the v3 contract")
    parents = tuple(
        ArtifactReference(
            identity=_string_field(parent, "identity"),
            output_digest=_string_field(parent, "output_digest"),
        )
        for parent in _mapping_list(record, "parents")
    )
    config_digests = tuple(_string_items(record, "config_digests"))
    producer_digest = record["producer_digest"]
    if producer_digest is not None and not isinstance(producer_digest, str):
        raise ReleaseEvidenceError("artifact producer_digest must be a string or null")
    return ArtifactInput(
        identity=_string_field(record, "identity"),
        role=cast(ArtifactRole, _string_field(record, "role")),
        path=_string_field(record, "path"),
        media_type=_string_field(record, "media_type"),
        schema_version=_string_field(record, "schema_version"),
        parents=parents,
        config_digests=config_digests,
        producer_digest=producer_digest,
        output_digest=_string_field(record, "output_digest"),
    )


def _parse_gate(value: object) -> GateResult:
    record = _mapping(value, "gate")
    if set(record) != {
        "identity",
        "status",
        "required",
        "evidence_digest",
        "attestation",
        "authority_id",
    }:
        raise ReleaseEvidenceError("gate fields do not match the v3 contract")
    authority_id = record["authority_id"]
    if authority_id is not None and not isinstance(authority_id, str):
        raise ReleaseEvidenceError("gate authority_id must be a string or null")
    return GateResult(
        identity=_string_field(record, "identity"),
        status=cast(GateStatus, _string_field(record, "status")),
        required=_bool_field(record, "required"),
        evidence_digest=_string_field(record, "evidence_digest"),
        attestation=cast(
            Literal[
                "local_self_attestation",
                "independent_execution_attestation",
                "external_authority_attestation",
            ],
            _string_field(record, "attestation"),
        ),
        authority_id=authority_id,
    )


def _parse_reconciliation(value: object) -> CountReconciliation:
    record = _mapping(value, "reconciliation")
    count_fields = {
        "candidate_count",
        "eligible_count",
        "accepted_count",
        "unresolved_count",
        "excluded_count",
        "refused_count",
    }
    expected = {
        "identity",
        "dimension",
        "source",
        "entity",
        "country_code",
        "scope",
        "count_status",
        "reason_codes",
        *count_fields,
    }
    if set(record) != expected:
        raise ReleaseEvidenceError("reconciliation fields do not match the v3 contract")
    country = record["country_code"]
    if country is not None and not isinstance(country, str):
        raise ReleaseEvidenceError("country_code must be a string or null")
    counts = {field: _optional_int_field(record, field) for field in count_fields}
    scope_record = _mapping(record["scope"], "reconciliation scope")
    if any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in scope_record.items()
    ):
        raise ReleaseEvidenceError("reconciliation scope must contain strings")
    return CountReconciliation(
        identity=_string_field(record, "identity"),
        dimension=cast(ReconciliationDimension, _string_field(record, "dimension")),
        source=_string_field(record, "source"),
        entity=_string_field(record, "entity"),
        country_code=country,
        candidate_count=counts["candidate_count"],
        eligible_count=counts["eligible_count"],
        accepted_count=counts["accepted_count"],
        unresolved_count=counts["unresolved_count"],
        excluded_count=counts["excluded_count"],
        refused_count=counts["refused_count"],
        scope=tuple(sorted(cast(Mapping[str, str], scope_record).items())),
        count_status=cast(CountStatus, _string_field(record, "count_status")),
        reason_codes=tuple(_string_items(record, "reason_codes")),
    )


def _parse_blocker(value: object) -> Blocker:
    record = _mapping(value, "blocker")
    expected = {
        "identity",
        "reason_code",
        "evidence_digest",
        "kind",
        "required_scope",
        "owner",
        "first_observed_at",
        "last_observed_at",
        "request_fingerprint",
        "request_status",
        "request_artifact_identity",
        "response_class",
        "observations",
        "attempts",
        "impact",
        "expected_artifact",
        "impacted_gates",
        "next_action",
        "recheck_condition",
    }
    if set(record) != expected:
        raise ReleaseEvidenceError("blocker fields do not match the v3 contract")
    return Blocker(
        identity=_string_field(record, "identity"),
        reason_code=_string_field(record, "reason_code"),
        evidence_digest=_string_field(record, "evidence_digest"),
        kind=cast(
            Literal["external", "unverified", "refused", "reduced_scope"],
            _string_field(record, "kind"),
        ),
        required_scope=_string_field(record, "required_scope"),
        owner=_string_field(record, "owner"),
        first_observed_at=_string_field(record, "first_observed_at"),
        last_observed_at=_string_field(record, "last_observed_at"),
        request_status=cast(
            Literal["governed", "refused"], _string_field(record, "request_status")
        ),
        request_artifact_identity=_optional_string_field(
            record, "request_artifact_identity"
        ),
        request_fingerprint=_optional_string_field(record, "request_fingerprint"),
        response_class=_string_field(record, "response_class"),
        observations=tuple(_string_items(record, "observations")),
        attempts=tuple(_string_items(record, "attempts")),
        impact=_string_field(record, "impact"),
        expected_artifact=_string_field(record, "expected_artifact"),
        impacted_gates=tuple(_string_items(record, "impacted_gates")),
        next_action=_string_field(record, "next_action"),
        recheck_condition=_string_field(record, "recheck_condition"),
    )


def _record_list(manifest: Mapping[str, object], field: str) -> list[object]:
    value = manifest[field]
    if not isinstance(value, list):
        raise ReleaseEvidenceError(f"{field} must be a list")
    return value


def _mapping_list(
    record: Mapping[str, object], field: str
) -> list[Mapping[str, object]]:
    value = record[field]
    if not isinstance(value, list):
        raise ReleaseEvidenceError(f"{field} must be a list")
    return [_mapping(item, field) for item in value]


def _string_items(record: Mapping[str, object], field: str) -> list[str]:
    value = record[field]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ReleaseEvidenceError(f"{field} must be a list of strings")
    return cast(list[str], value)


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ReleaseEvidenceError(f"{field} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise ReleaseEvidenceError(f"{field} keys must be strings")
    return cast(Mapping[str, object], value)


def _string_field(record: Mapping[str, object], field: str) -> str:
    value = record[field]
    if not isinstance(value, str):
        raise ReleaseEvidenceError(f"{field} must be a string")
    return value


def _optional_string_field(record: Mapping[str, object], field: str) -> str | None:
    value = record[field]
    if value is not None and not isinstance(value, str):
        raise ReleaseEvidenceError(f"{field} must be a string or null")
    return value


def _bool_field(record: Mapping[str, object], field: str) -> bool:
    value = record[field]
    if type(value) is not bool:
        raise ReleaseEvidenceError(f"{field} must be a boolean")
    return value


def _int_field(record: Mapping[str, object], field: str) -> int:
    value = record[field]
    if type(value) is not int:
        raise ReleaseEvidenceError(f"{field} must be an integer")
    return value


def _optional_int_field(record: Mapping[str, object], field: str) -> int | None:
    value = record[field]
    if value is not None and type(value) is not int:
        raise ReleaseEvidenceError(f"{field} must be an integer or null")
    return value


def _require_commit(value: str) -> None:
    if not isinstance(value, str) or _COMMIT_PATTERN.fullmatch(value) is None:
        raise ReleaseEvidenceError(
            "code_commit must be a lowercase 40- or 64-character Git SHA"
        )


def _require_digest(value: str, field: str) -> None:
    if not isinstance(value, str) or _DIGEST_PATTERN.fullmatch(value) is None:
        raise ReleaseEvidenceError(f"{field} must be a canonical SHA-256 digest")


def _require_identity(value: str, field: str) -> None:
    if not isinstance(value, str) or _IDENTITY_PATTERN.fullmatch(value) is None:
        raise ReleaseEvidenceError(f"invalid {field}: {value!r}")


def _utc_timestamp(value: str) -> datetime:
    if _UTC_TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise ReleaseEvidenceError("blocker observation timestamp is invalid")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError as error:
        raise ReleaseEvidenceError(
            "blocker observation timestamp is invalid"
        ) from error


def _require_unique(values: Iterable[str], field: str) -> None:
    materialized = list(values)
    if len(materialized) != len(set(materialized)):
        suffix = " (output overwrite)" if field == "artifact path" else ""
        raise ReleaseEvidenceError(f"duplicate {field}{suffix}")


def _digest_json(value: object) -> str:
    return f"sha256:{hashlib.sha256(_canonical_json(value)).hexdigest()}"


def _canonical_json(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ReleaseEvidenceError("release evidence is not canonical JSON") from error
