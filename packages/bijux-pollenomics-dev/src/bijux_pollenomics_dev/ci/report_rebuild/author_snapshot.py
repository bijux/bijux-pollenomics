"""Bind an explicitly provisioned author snapshot without asserting data rights."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .contracts import ReportRebuildError, require_relative_path
from .qualified_sources import (
    FILE_FIELDS,
    SHA256,
    QualifiedReportSources,
    _checked_file,
    _object,
    _regular_path,
)

SCHEMA = "qualified-author-snapshot.v1"
FIELDS = frozenset(
    {
        "schema_version",
        "source_id",
        "snapshot_schema_version",
        "file_count",
        "manifest",
        "files",
    }
)
SNAPSHOT_FIELDS = frozenset({"schema_version", "file_count", "files"})


def _snapshot_path(value: object, label: str) -> str:
    relative = require_relative_path(value, label)
    if "\x00" in relative:
        raise ReportRebuildError(f"{label} contains a null character")
    return relative


def _snapshot_spec(value: object) -> dict[str, Any]:
    """Accept empty source files, including the original typing marker."""
    if not isinstance(value, dict) or frozenset(value) != FILE_FIELDS:
        raise ReportRebuildError("author snapshot file fields differ")
    _snapshot_path(value["path"], "author snapshot file")
    if (
        not isinstance(value["sha256"], str)
        or SHA256.fullmatch(value["sha256"]) is None
    ):
        raise ReportRebuildError("author snapshot SHA256 is invalid")
    if type(value["size"]) is not int or value["size"] < 0:
        raise ReportRebuildError("author snapshot size must be nonnegative")
    return value


def _unchanged_file(path: Path, payload: bytes, label: str) -> None:
    if _regular_path(path).read_bytes() != payload:
        raise ReportRebuildError(f"author snapshot {label} changed during validation")


def validated_author_snapshot(
    repository: Path, source_root: Path, descriptor_path: Path
) -> QualifiedReportSources:
    """Check a pinned manifest and its complete source population in place.

    The descriptor independently pins manifest bytes and every file's path,
    digest and size. The original manifest supplies a second exact population
    and digest check. This establishes input identity only; it supplies neither
    publication permission nor scientific admission. Files are never copied.
    """
    repository = _regular_path(repository, directory=True)
    relative = _snapshot_path(descriptor_path.as_posix(), "source descriptor")
    if relative.startswith("external/"):
        raise ReportRebuildError("source descriptor overlaps external input namespace")
    descriptor_file = _regular_path(repository / relative)
    descriptor_payload = descriptor_file.read_bytes()
    descriptor = _object(descriptor_payload)
    if frozenset(descriptor) != FIELDS or descriptor["schema_version"] != SCHEMA:
        raise ReportRebuildError("author snapshot descriptor schema or fields differ")
    source_id = _snapshot_path(descriptor["source_id"], "author snapshot source ID")
    snapshot_schema = descriptor["snapshot_schema_version"]
    count = descriptor["file_count"]
    if not isinstance(snapshot_schema, str) or not snapshot_schema.strip():
        raise ReportRebuildError("author snapshot manifest schema is missing")
    if type(count) is not int or not 1 <= count <= 4096:
        raise ReportRebuildError("author snapshot file count must be 1 to 4096")
    root = _regular_path(source_root, directory=True)
    if root.is_relative_to(repository) or repository.is_relative_to(root):
        raise ReportRebuildError(
            "author snapshot store must be separate from repository"
        )
    directory = _regular_path(root / source_id, directory=True)
    manifest_spec = _snapshot_spec(descriptor["manifest"])
    if not 1 <= manifest_spec["size"] <= 8 * 1024 * 1024:
        raise ReportRebuildError("author snapshot manifest size exceeds limits")
    manifest_file = _checked_file(directory, manifest_spec)
    manifest_payload = manifest_file.read_bytes()
    if (
        len(manifest_payload) != manifest_spec["size"]
        or hashlib.sha256(manifest_payload).hexdigest() != manifest_spec["sha256"]
    ):
        raise ReportRebuildError("author snapshot manifest changed before parsing")
    manifest = _object(manifest_payload)
    if (
        frozenset(manifest) != SNAPSHOT_FIELDS
        or manifest["schema_version"] != snapshot_schema
        or type(manifest["file_count"]) is not int
        or manifest["file_count"] != count
        or not isinstance(manifest["files"], dict)
    ):
        raise ReportRebuildError(
            "author snapshot manifest schema or population differs"
        )
    files = descriptor["files"]
    if not isinstance(files, list) or len(files) != count:
        raise ReportRebuildError("author snapshot descriptor population differs")
    specs = [_snapshot_spec(value) for value in files]
    names = [spec["path"] for spec in specs]
    if names != sorted(set(names)) or manifest_spec["path"] in names:
        raise ReportRebuildError(
            "author snapshot filenames must be sorted and independent"
        )
    if manifest["files"] != {spec["path"]: spec["sha256"] for spec in specs}:
        raise ReportRebuildError("author snapshot manifest file identities differ")
    inputs = {
        relative: descriptor_file,
        f"external/{source_id}/{manifest_spec['path']}": manifest_file,
    }
    for spec in specs:
        inputs[f"external/{source_id}/{spec['path']}"] = _checked_file(directory, spec)
    # Recheck the complete population so a later read cannot hide an earlier mutation.
    for spec in specs:
        _checked_file(directory, spec)
    _unchanged_file(manifest_file, manifest_payload, "manifest")
    _unchanged_file(descriptor_file, descriptor_payload, "descriptor")
    return QualifiedReportSources(
        directory, inputs, hashlib.sha256(descriptor_payload).hexdigest()
    )
