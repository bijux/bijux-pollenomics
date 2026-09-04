"""Atomic repository-owned writer and CLI for canonical release evidence."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import cast

from .release_evidence import (
    ArtifactInput,
    ArtifactReference,
    ArtifactRole,
    Blocker,
    CountReconciliation,
    GateResult,
    GateStatus,
    ReconciliationDimension,
    ReleaseEvidenceError,
    build_release_evidence_manifest,
    validate_release_evidence_manifest,
)

__all__ = ["main", "write_release_evidence_manifest"]


def write_release_evidence_manifest(
    repository_root: Path,
    output_path: str,
    *,
    code_commit: str,
    dirty: bool,
    dependency_lock_digest: str,
    artifacts: Sequence[ArtifactInput],
    gates: Sequence[GateResult],
    reconciliations: Sequence[CountReconciliation],
    blockers: Sequence[Blocker] = (),
) -> dict[str, object]:
    """Build, validate, and atomically publish canonical release evidence."""
    root = _repository_root(repository_root)
    manifest = build_release_evidence_manifest(
        root,
        code_commit=code_commit,
        dirty=dirty,
        dependency_lock_digest=dependency_lock_digest,
        artifacts=artifacts,
        gates=gates,
        reconciliations=reconciliations,
        blockers=blockers,
    )
    validate_release_evidence_manifest(root, manifest)
    payload = _canonical_bytes(manifest)
    destination = _prepare_output_path(root, output_path)

    if destination.exists() or destination.is_symlink():
        existing = _read_regular_bytes(destination)
        if existing != payload:
            raise ReleaseEvidenceError(
                f"release-evidence output exists with different bytes: {output_path}"
            )
        _validate_written_manifest(root, existing)
        return manifest

    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.", suffix=".writing", dir=destination.parent
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), 0o644)
        try:
            os.link(temporary_path, destination, follow_symlinks=False)
        except FileExistsError:
            existing = _read_regular_bytes(destination)
            if existing != payload:
                raise ReleaseEvidenceError(
                    f"release-evidence output appeared with different bytes: {output_path}"
                )
        temporary_path.unlink()
        temporary_path = None
        _fsync_directory(destination.parent)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

    written = _read_regular_bytes(destination)
    if written != payload:
        raise ReleaseEvidenceError(
            "release-evidence output changed during atomic write"
        )
    _validate_written_manifest(root, written)
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    """Run the callable release-evidence writer or validation gate."""
    args = _parser().parse_args(argv)
    try:
        root = Path(args.repository_root)
        manifest: Mapping[str, object]
        if args.command == "write":
            request = _read_repository_json(root, args.request, require_artifacts=False)
            manifest = _write_request(root, args.output, request)
            output = args.output
        else:
            manifest = _read_repository_json(
                root, args.manifest, require_artifacts=True
            )
            validate_release_evidence_manifest(root, manifest)
            output = args.manifest
        decision = _mapping_field(manifest, "release_decision")
        release_ready = _bool_field(decision, "release_ready")
        summary = {
            "build_id": _string_field(manifest, "build_id"),
            "output": output,
            "release_ready": release_ready,
            "status": _string_field(decision, "status"),
        }
        sys.stdout.buffer.write(_canonical_bytes(summary))
        return 0 if release_ready else 1
    except (OSError, ReleaseEvidenceError, UnicodeError, json.JSONDecodeError) as error:
        print(f"release evidence refused: {error}", file=sys.stderr)
        return 2


def _write_request(
    root: Path, output_path: str, request: Mapping[str, object]
) -> dict[str, object]:
    expected = {
        "schema_version",
        "code_commit",
        "dirty",
        "dependency_lock_digest",
        "artifacts",
        "gates",
        "reconciliations",
        "blockers",
    }
    if set(request) != expected:
        raise ReleaseEvidenceError("write request fields do not match the v1 contract")
    if request["schema_version"] != "release-evidence-request.v1":
        raise ReleaseEvidenceError("unsupported release-evidence request schema")
    return write_release_evidence_manifest(
        root,
        output_path,
        code_commit=_string_field(request, "code_commit"),
        dirty=_bool_field(request, "dirty"),
        dependency_lock_digest=_string_field(request, "dependency_lock_digest"),
        artifacts=tuple(_artifact(item) for item in _list_field(request, "artifacts")),
        gates=tuple(_gate(item) for item in _list_field(request, "gates")),
        reconciliations=tuple(
            _reconciliation(item) for item in _list_field(request, "reconciliations")
        ),
        blockers=tuple(_blocker(item) for item in _list_field(request, "blockers")),
    )


def _artifact(value: object) -> ArtifactInput:
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
        "output_digest",
    }
    if set(record) != expected:
        raise ReleaseEvidenceError(
            "artifact request fields do not match the v1 contract"
        )
    parents = tuple(_parent(item) for item in _list_field(record, "parents"))
    config_digests = tuple(
        _string_value(item, "config digest")
        for item in _list_field(record, "config_digests")
    )
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


def _parent(value: object) -> ArtifactReference:
    record = _mapping(value, "parent")
    if set(record) != {"identity", "output_digest"}:
        raise ReleaseEvidenceError("parent fields do not match the v1 contract")
    return ArtifactReference(
        identity=_string_field(record, "identity"),
        output_digest=_string_field(record, "output_digest"),
    )


def _gate(value: object) -> GateResult:
    record = _mapping(value, "gate")
    if set(record) != {"identity", "status", "required", "evidence_digest"}:
        raise ReleaseEvidenceError("gate request fields do not match the v1 contract")
    return GateResult(
        identity=_string_field(record, "identity"),
        status=cast(GateStatus, _string_field(record, "status")),
        required=_bool_field(record, "required"),
        evidence_digest=_string_field(record, "evidence_digest"),
    )


def _reconciliation(value: object) -> CountReconciliation:
    record = _mapping(value, "reconciliation")
    count_fields = (
        "candidate_count",
        "eligible_count",
        "accepted_count",
        "unresolved_count",
        "excluded_count",
        "refused_count",
    )
    expected = {
        "identity",
        "dimension",
        "source",
        "entity",
        "country_code",
        *count_fields,
    }
    if set(record) != expected:
        raise ReleaseEvidenceError(
            "reconciliation request fields do not match the v1 contract"
        )
    country_code = record["country_code"]
    if country_code is not None and not isinstance(country_code, str):
        raise ReleaseEvidenceError("country_code must be a string or null")
    counts = {field: _int_field(record, field) for field in count_fields}
    return CountReconciliation(
        identity=_string_field(record, "identity"),
        dimension=cast(ReconciliationDimension, _string_field(record, "dimension")),
        source=_string_field(record, "source"),
        entity=_string_field(record, "entity"),
        country_code=country_code,
        candidate_count=counts["candidate_count"],
        eligible_count=counts["eligible_count"],
        accepted_count=counts["accepted_count"],
        unresolved_count=counts["unresolved_count"],
        excluded_count=counts["excluded_count"],
        refused_count=counts["refused_count"],
    )


def _blocker(value: object) -> Blocker:
    record = _mapping(value, "blocker")
    if set(record) != {"identity", "reason_code", "evidence_digest"}:
        raise ReleaseEvidenceError(
            "blocker request fields do not match the v1 contract"
        )
    return Blocker(
        identity=_string_field(record, "identity"),
        reason_code=_string_field(record, "reason_code"),
        evidence_digest=_string_field(record, "evidence_digest"),
    )


def _read_repository_json(
    repository_root: Path, relative_path: str, *, require_artifacts: bool
) -> Mapping[str, object]:
    root = _repository_root(repository_root)
    path = _existing_repository_path(
        root, relative_path, require_artifacts=require_artifacts
    )
    return _load_json(_read_regular_bytes(path))


def _validate_written_manifest(root: Path, payload: bytes) -> None:
    validate_release_evidence_manifest(root, _load_json(payload))


def _load_json(payload: bytes) -> Mapping[str, object]:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ReleaseEvidenceError(f"duplicate JSON field: {key}")
            result[key] = value
        return result

    value = json.loads(payload, object_pairs_hook=reject_duplicates)
    return _mapping(value, "JSON document")


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
        raise ReleaseEvidenceError("release evidence is not canonical JSON") from error


def _prepare_output_path(root: Path, relative_path: str) -> Path:
    parts = _relative_parts(relative_path, require_artifacts=True)
    parent = root
    for part in parts[:-1]:
        candidate = parent / part
        try:
            mode = candidate.lstat().st_mode
        except FileNotFoundError:
            try:
                candidate.mkdir(mode=0o755)
            except FileExistsError:
                pass
            mode = candidate.lstat().st_mode
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise ReleaseEvidenceError(f"unsafe output directory: {candidate}")
        parent = candidate
    destination = parent / parts[-1]
    if destination.exists() or destination.is_symlink():
        mode = destination.lstat().st_mode
        if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
            raise ReleaseEvidenceError(
                f"unsafe release-evidence output: {relative_path}"
            )
    return destination


def _existing_repository_path(
    root: Path, relative_path: str, *, require_artifacts: bool
) -> Path:
    parts = _relative_parts(relative_path, require_artifacts=require_artifacts)
    current = root
    for part in parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError as error:
            raise ReleaseEvidenceError(
                f"repository path is missing: {relative_path}"
            ) from error
        if stat.S_ISLNK(mode):
            raise ReleaseEvidenceError(f"symlink paths are forbidden: {relative_path}")
    if not stat.S_ISREG(current.lstat().st_mode):
        raise ReleaseEvidenceError(
            f"repository path is not a regular file: {relative_path}"
        )
    return current


def _relative_parts(relative_path: str, *, require_artifacts: bool) -> tuple[str, ...]:
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
    if require_artifacts and (not pure.parts or pure.parts[0] != "artifacts"):
        raise ReleaseEvidenceError("release-evidence output must be under artifacts/")
    return pure.parts


def _read_regular_bytes(path: Path) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise ReleaseEvidenceError(
            f"could not safely open repository file: {path}"
        ) from error
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise ReleaseEvidenceError(f"repository path is not a regular file: {path}")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            payload = stream.read()
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    current = path.lstat()
    opened_identity = (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns)
    if opened_identity != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise ReleaseEvidenceError(f"repository file changed while reading: {path}")
    if opened_identity != (
        current.st_dev,
        current.st_ino,
        current.st_size,
        current.st_mtime_ns,
    ) or not stat.S_ISREG(current.st_mode):
        raise ReleaseEvidenceError(
            f"repository file identity changed while reading: {path}"
        )
    return payload


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _repository_root(repository_root: Path) -> Path:
    try:
        root = repository_root.resolve(strict=True)
    except OSError as error:
        raise ReleaseEvidenceError("repository root does not exist") from error
    if not root.is_dir():
        raise ReleaseEvidenceError("repository root must be a directory")
    return root


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ReleaseEvidenceError(f"{field} must be an object with string keys")
    return cast(Mapping[str, object], value)


def _mapping_field(record: Mapping[str, object], field: str) -> Mapping[str, object]:
    return _mapping(record[field], field)


def _list_field(record: Mapping[str, object], field: str) -> list[object]:
    value = record[field]
    if not isinstance(value, list):
        raise ReleaseEvidenceError(f"{field} must be a list")
    return value


def _string_value(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ReleaseEvidenceError(f"{field} must be a string")
    return value


def _string_field(record: Mapping[str, object], field: str) -> str:
    return _string_value(record[field], field)


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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bijux-pollenomics-release-evidence")
    subparsers = parser.add_subparsers(dest="command", required=True)
    write = subparsers.add_parser("write", help="build and atomically write evidence")
    write.add_argument("--repository-root", required=True)
    write.add_argument(
        "--request", required=True, help="repository-relative request JSON"
    )
    write.add_argument("--output", required=True, help="path below artifacts/")
    validate = subparsers.add_parser("validate", help="validate existing evidence")
    validate.add_argument("--repository-root", required=True)
    validate.add_argument("--manifest", required=True, help="path below artifacts/")
    return parser
