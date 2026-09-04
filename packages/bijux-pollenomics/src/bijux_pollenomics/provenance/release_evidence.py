"""Canonical, fail-closed release evidence over immutable repository inputs."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from collections.abc import Iterable
from typing import Final, Literal, Mapping, Sequence, TypeAlias, cast

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
ReconciliationDimension: TypeAlias = Literal["source", "country"]

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
_DERIVED_ROLES: Final = frozenset(
    {"source_snapshot", "generated_output", "validation_result"}
)
_OUTPUT_ROLES: Final = frozenset({"generated_output", "validation_result"})
_GATE_STATUSES: Final = frozenset(
    {"PASS", "FAIL", "BLOCKED_EXTERNAL", "NOT_APPLICABLE", "SKIPPED"}
)
_COUNTRIES: Final = frozenset({"SE", "DK", "NO", "FI", "UNASSIGNED"})
_DIGEST_PATTERN: Final = re.compile(r"sha256:[0-9a-f]{64}\Z")
_COMMIT_PATTERN: Final = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_IDENTITY_PATTERN: Final = re.compile(r"[a-z0-9][a-z0-9._:-]*\Z")


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
    producer_digest: str
    output_digest: str


@dataclass(frozen=True)
class GateResult:
    """A validation-gate result backed by an immutable evidence artifact."""

    identity: str
    status: GateStatus
    required: bool
    evidence_digest: str


@dataclass(frozen=True)
class CountReconciliation:
    """One source-level or country-level count partition."""

    identity: str
    dimension: ReconciliationDimension
    source: str
    entity: str
    country_code: str | None
    candidate_count: int
    eligible_count: int
    accepted_count: int
    unresolved_count: int
    excluded_count: int
    refused_count: int


@dataclass(frozen=True)
class Blocker:
    """An unresolved release blocker with stable, evidence-backed identity."""

    identity: str
    reason_code: str
    evidence_digest: str


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

    ordered_artifacts = sorted(artifacts, key=lambda item: item.identity)
    _require_unique((item.identity for item in ordered_artifacts), "artifact identity")
    _require_unique((item.path for item in ordered_artifacts), "artifact path")
    artifact_records = [_artifact_record(root, item) for item in ordered_artifacts]
    _validate_artifact_graph(
        ordered_artifacts, artifact_records, dependency_lock_digest
    )

    ordered_gates = sorted(gates, key=lambda item: item.identity)
    _validate_gates(ordered_gates, artifact_records)
    ordered_reconciliations = sorted(
        reconciliations,
        key=lambda item: (
            item.source,
            item.entity,
            item.dimension,
            item.country_code or "",
        ),
    )
    _validate_reconciliations(ordered_reconciliations)
    ordered_blockers = sorted(blockers, key=lambda item: item.identity)
    _validate_blockers(ordered_blockers, artifact_records)

    decision = _release_decision(dirty, ordered_gates, ordered_blockers)
    content: dict[str, object] = {
        "schema_version": "release-evidence-manifest.v1",
        "code_commit": code_commit,
        "dirty": dirty,
        "dependency_lock_digest": dependency_lock_digest,
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
            "dependency_lock_digest",
            "artifacts",
            "gates",
            "reconciliations",
            "blockers",
            "release_decision",
        }
        if set(manifest) != expected_keys:
            raise ReleaseEvidenceError("manifest fields do not match the v1 contract")
        if manifest["schema_version"] != "release-evidence-manifest.v1":
            raise ReleaseEvidenceError("unsupported release-evidence schema")
        artifacts = tuple(
            _parse_artifact(item) for item in _record_list(manifest, "artifacts")
        )
        gates = tuple(_parse_gate(item) for item in _record_list(manifest, "gates"))
        reconciliations = tuple(
            _parse_reconciliation(item)
            for item in _record_list(manifest, "reconciliations")
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
            "manifest does not satisfy the v1 contract"
        ) from error


def hash_repository_object(
    repository_root: Path, relative_path: str
) -> dict[str, object]:
    """Hash a safe repository-relative regular file or tree canonically."""
    return _hash_repository_object(_repository_root(repository_root), relative_path)


def _artifact_record(root: Path, item: ArtifactInput) -> dict[str, object]:
    _require_identity(item.identity, "artifact identity")
    if item.role not in _ARTIFACT_ROLES:
        raise ReleaseEvidenceError(f"invalid artifact role: {item.role}")
    if not item.media_type.strip() or not item.schema_version.strip():
        raise ReleaseEvidenceError(
            f"artifact {item.identity} lacks media/schema identity"
        )
    _require_digest(item.producer_digest, f"{item.identity} producer_digest")
    _require_digest(item.output_digest, f"{item.identity} output_digest")
    _require_unique((parent.identity for parent in item.parents), "parent identity")
    for parent in item.parents:
        _require_identity(parent.identity, "parent identity")
        _require_digest(parent.output_digest, "parent output_digest")
    _require_unique(item.config_digests, "config digest")
    for digest in item.config_digests:
        _require_digest(digest, "config digest")

    observed = _hash_repository_object(root, item.path)
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


def _validate_artifact_graph(
    artifacts: Sequence[ArtifactInput],
    records: Sequence[Mapping[str, object]],
    dependency_lock_digest: str,
) -> None:
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
    if len(producer_digests) != 1:
        raise ReleaseEvidenceError("exactly one producer artifact is required")
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
    if input_paths & output_paths:
        raise ReleaseEvidenceError(
            "generated output would overwrite an immutable input"
        )

    for item in artifacts:
        if item.producer_digest not in producer_digests:
            raise ReleaseEvidenceError(f"unknown producer digest: {item.identity}")
        if item.role in _DERIVED_ROLES and not item.parents:
            raise ReleaseEvidenceError(
                f"derived artifact lacks a parent: {item.identity}"
            )
        if item.role in _OUTPUT_ROLES and not item.config_digests:
            raise ReleaseEvidenceError(f"output lacks config digests: {item.identity}")
        unknown_configs = set(item.config_digests) - config_digests
        if unknown_configs:
            raise ReleaseEvidenceError(f"unknown config digest: {item.identity}")
        for parent in item.parents:
            if parent.identity not in by_identity:
                raise ReleaseEvidenceError(f"missing parent: {parent.identity}")
            if digest_by_identity[parent.identity] != parent.output_digest:
                raise ReleaseEvidenceError(f"parent digest mismatch: {parent.identity}")

    _reject_cycles(by_identity)
    for item in artifacts:
        if item.role in _OUTPUT_ROLES and not _has_source_ancestor(
            item.identity, by_identity
        ):
            raise ReleaseEvidenceError(f"output lacks source lineage: {item.identity}")


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
    gates: Sequence[GateResult], records: Sequence[Mapping[str, object]]
) -> None:
    if not gates or not any(gate.required for gate in gates):
        raise ReleaseEvidenceError("at least one required gate result is required")
    _require_unique((gate.identity for gate in gates), "gate identity")
    evidence_digests = {
        _string_field(record, "output_digest")
        for record in records
        if record["role"] == "validation_result"
    }
    for gate in gates:
        _require_identity(gate.identity, "gate identity")
        if gate.status not in _GATE_STATUSES:
            raise ReleaseEvidenceError(f"invalid gate status: {gate.status}")
        if type(gate.required) is not bool:
            raise ReleaseEvidenceError("gate required flag must be a boolean")
        _require_digest(gate.evidence_digest, "gate evidence digest")
        if gate.evidence_digest not in evidence_digests:
            raise ReleaseEvidenceError(
                f"gate evidence is not a validation artifact: {gate.identity}"
            )


def _validate_reconciliations(items: Sequence[CountReconciliation]) -> None:
    if not items:
        raise ReleaseEvidenceError("source and country reconciliations are required")
    _require_unique((item.identity for item in items), "reconciliation identity")
    _require_unique(
        (
            f"{item.source}\0{item.entity}\0{item.dimension}\0{item.country_code}"
            for item in items
        ),
        "reconciliation key",
    )
    grouped: dict[tuple[str, str], dict[str, list[CountReconciliation]]] = {}
    for item in items:
        _require_identity(item.identity, "reconciliation identity")
        if item.dimension not in {"source", "country"}:
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
        counts = _counts(item)
        if any(type(value) is not int or value < 0 for value in counts.values()):
            raise ReleaseEvidenceError(
                f"counts must be non-null non-negative integers: {item.identity}"
            )
        if item.eligible_count != item.accepted_count + item.refused_count:
            raise ReleaseEvidenceError(
                f"eligible count is inconsistent: {item.identity}"
            )
        if (
            item.candidate_count
            != item.eligible_count + item.unresolved_count + item.excluded_count
        ):
            raise ReleaseEvidenceError(
                f"candidate denominator is inconsistent: {item.identity}"
            )
        group = grouped.setdefault(
            (item.source, item.entity), {"source": [], "country": []}
        )
        group[item.dimension].append(item)

    for key, dimensions in grouped.items():
        source_rows = dimensions["source"]
        country_rows = dimensions["country"]
        if len(source_rows) != 1:
            raise ReleaseEvidenceError(
                f"one source reconciliation is required for {key}"
            )
        if {item.country_code for item in country_rows} != _COUNTRIES:
            raise ReleaseEvidenceError(
                f"complete country reconciliation is required for {key}"
            )
        source_counts = _counts(source_rows[0])
        for field, source_count in source_counts.items():
            country_count = sum(_counts(item)[field] for item in country_rows)
            if source_count != country_count:
                raise ReleaseEvidenceError(
                    f"country/source count mismatch for {key}: {field}"
                )


def _validate_blockers(
    blockers: Sequence[Blocker], records: Sequence[Mapping[str, object]]
) -> None:
    _require_unique((blocker.identity for blocker in blockers), "blocker identity")
    evidence_digests = {_string_field(record, "output_digest") for record in records}
    for blocker in blockers:
        _require_identity(blocker.identity, "blocker identity")
        _require_identity(blocker.reason_code, "blocker reason_code")
        _require_digest(blocker.evidence_digest, "blocker evidence digest")
        if blocker.evidence_digest not in evidence_digests:
            raise ReleaseEvidenceError(
                f"blocker evidence is not in the manifest: {blocker.identity}"
            )


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
    reasons.extend(f"blocker:{blocker.reason_code}" for blocker in blockers)
    if dirty:
        reasons.append("candidate_dirty")
    release_ready = not reasons
    if release_ready:
        status = "verified_complete"
    elif any(gate.status == "FAIL" for gate in required_nonpass):
        status = "failed"
    elif any(gate.status == "BLOCKED_EXTERNAL" for gate in required_nonpass):
        status = "external_blocked"
    else:
        status = "implemented_unverified"
    return {
        "release_ready": release_ready,
        "status": status,
        "reason_codes": sorted(reasons),
    }


def _hash_repository_object(root: Path, relative_path: str) -> dict[str, object]:
    path = _safe_repository_path(root, relative_path)
    mode = path.lstat().st_mode
    if stat.S_ISREG(mode):
        digest, byte_size = _hash_file(path)
        return {
            "object_type": "file",
            "output_digest": digest,
            "byte_size": byte_size,
            "file_count": 1,
        }
    if stat.S_ISDIR(mode):
        entries = _tree_entries(path)
        return {
            "object_type": "tree",
            "output_digest": _digest_json(entries),
            "byte_size": sum(cast(int, entry["byte_size"]) for entry in entries),
            "file_count": len(entries),
        }
    raise ReleaseEvidenceError(
        f"artifact is not a regular file or directory: {relative_path}"
    )


def _safe_repository_path(root: Path, relative_path: str) -> Path:
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
    current = root
    for part in pure.parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError as error:
            raise ReleaseEvidenceError(
                f"artifact path is missing: {relative_path}"
            ) from error
        if stat.S_ISLNK(mode):
            raise ReleaseEvidenceError(f"symlink paths are forbidden: {relative_path}")
    try:
        current.resolve(strict=True).relative_to(root)
    except (OSError, ValueError) as error:
        raise ReleaseEvidenceError(
            f"path escapes repository root: {relative_path}"
        ) from error
    return current


def _repository_root(repository_root: Path) -> Path:
    try:
        root = repository_root.resolve(strict=True)
    except OSError as error:
        raise ReleaseEvidenceError("repository root does not exist") from error
    if not root.is_dir():
        raise ReleaseEvidenceError("repository root must be a directory")
    return root


def _tree_entries(root: Path) -> list[dict[str, object]]:
    paths = _tree_paths(root)
    entries: list[dict[str, object]] = []
    for path in paths:
        digest, byte_size = _hash_file(path)
        entries.append(
            {
                "path": path.relative_to(root).as_posix(),
                "output_digest": digest,
                "byte_size": byte_size,
            }
        )
    if paths != _tree_paths(root):
        raise ReleaseEvidenceError(f"tree changed while hashing: {root}")
    return entries


def _tree_paths(root: Path) -> list[Path]:
    found: list[Path] = []

    def visit(directory: Path) -> None:
        with os.scandir(directory) as members:
            entries = sorted(members, key=lambda member: member.name)
        for entry in entries:
            if entry.is_symlink():
                raise ReleaseEvidenceError(f"symlink in artifact tree: {entry.path}")
            path = Path(entry.path)
            if entry.is_dir(follow_symlinks=False):
                visit(path)
            elif entry.is_file(follow_symlinks=False):
                found.append(path)
            else:
                raise ReleaseEvidenceError(
                    f"special file in artifact tree: {entry.path}"
                )

    visit(root)
    return sorted(found, key=lambda path: path.relative_to(root).as_posix())


def _hash_file(path: Path) -> tuple[str, int]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise ReleaseEvidenceError(
            f"could not safely open artifact file: {path}"
        ) from error
    digest = hashlib.sha256()
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ReleaseEvidenceError(f"artifact is not a regular file: {path}")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    path_after = path.lstat()
    stable_identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    final_identity = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    path_identity = (
        path_after.st_dev,
        path_after.st_ino,
        path_after.st_size,
        path_after.st_mtime_ns,
    )
    if (
        stable_identity != final_identity
        or stable_identity != path_identity
        or not stat.S_ISREG(path_after.st_mode)
    ):
        raise ReleaseEvidenceError(f"file changed while hashing: {path}")
    return f"sha256:{digest.hexdigest()}", before.st_size


def _gate_record(item: GateResult) -> dict[str, object]:
    return {
        "identity": item.identity,
        "status": item.status,
        "required": item.required,
        "evidence_digest": item.evidence_digest,
    }


def _reconciliation_record(item: CountReconciliation) -> dict[str, object]:
    return {
        "identity": item.identity,
        "dimension": item.dimension,
        "source": item.source,
        "entity": item.entity,
        "country_code": item.country_code,
        **_counts(item),
    }


def _blocker_record(item: Blocker) -> dict[str, object]:
    return {
        "identity": item.identity,
        "reason_code": item.reason_code,
        "evidence_digest": item.evidence_digest,
    }


def _counts(item: CountReconciliation) -> dict[str, int]:
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
        raise ReleaseEvidenceError("artifact fields do not match the v1 contract")
    parents = tuple(
        ArtifactReference(
            identity=_string_field(parent, "identity"),
            output_digest=_string_field(parent, "output_digest"),
        )
        for parent in _mapping_list(record, "parents")
    )
    config_digests = tuple(_string_items(record, "config_digests"))
    return ArtifactInput(
        identity=_string_field(record, "identity"),
        role=cast(ArtifactRole, _string_field(record, "role")),
        path=_string_field(record, "path"),
        media_type=_string_field(record, "media_type"),
        schema_version=_string_field(record, "schema_version"),
        parents=parents,
        config_digests=config_digests,
        producer_digest=_string_field(record, "producer_digest"),
        output_digest=_string_field(record, "output_digest"),
    )


def _parse_gate(value: object) -> GateResult:
    record = _mapping(value, "gate")
    if set(record) != {"identity", "status", "required", "evidence_digest"}:
        raise ReleaseEvidenceError("gate fields do not match the v1 contract")
    return GateResult(
        identity=_string_field(record, "identity"),
        status=cast(GateStatus, _string_field(record, "status")),
        required=_bool_field(record, "required"),
        evidence_digest=_string_field(record, "evidence_digest"),
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
        *count_fields,
    }
    if set(record) != expected:
        raise ReleaseEvidenceError("reconciliation fields do not match the v1 contract")
    country = record["country_code"]
    if country is not None and not isinstance(country, str):
        raise ReleaseEvidenceError("country_code must be a string or null")
    counts = {field: _int_field(record, field) for field in count_fields}
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
    )


def _parse_blocker(value: object) -> Blocker:
    record = _mapping(value, "blocker")
    if set(record) != {"identity", "reason_code", "evidence_digest"}:
        raise ReleaseEvidenceError("blocker fields do not match the v1 contract")
    return Blocker(
        identity=_string_field(record, "identity"),
        reason_code=_string_field(record, "reason_code"),
        evidence_digest=_string_field(record, "evidence_digest"),
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
