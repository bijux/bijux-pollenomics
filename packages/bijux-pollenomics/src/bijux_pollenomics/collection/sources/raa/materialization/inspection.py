"""Exact raw replay before private source-member inspection."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re

from .contracts import BOUNDARY, SCHEMA_VERSION
from .ownership import canonical_bytes, iter_audit_documents
from .reading import read_only_database
from .service import implementation_identity


def _object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("RAÄ audit duplicate JSON key")
        result[key] = value
    return result


def _inventory(directory: Path) -> None:
    for path in (directory, *directory.parents):
        if path.is_symlink():
            raise ValueError("RAÄ audit inspection cannot use symlinks")
    if {path.name for path in directory.iterdir()} != {
        "manifest.json",
        "rows.ndjson",
    } or any(path.is_symlink() or not path.is_file() for path in directory.iterdir()):
        raise ValueError("RAÄ saved audit inventory mismatch")


def inspect_raa_ownership_audit(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    source_path: Path,
    expected_source_sha256: str,
    expected_source_byte_count: int,
    native_uuid: str | None = None,
) -> dict[str, object]:
    """Reproduce all saved bytes from raw before returning selected native lineage."""
    if not re.fullmatch("[0-9a-f]{64}", expected_manifest_sha256):
        raise ValueError("RAÄ audit manifest SHA256 is required")
    if native_uuid is not None and not isinstance(native_uuid, str):
        raise ValueError("RAÄ native UUID selection must be text")
    _inventory(directory)
    path = directory / "manifest.json"
    content = path.read_bytes()
    if sha256(content).hexdigest() != expected_manifest_sha256:
        raise ValueError("RAÄ audit manifest identity mismatch")
    manifest = json.loads(content, object_pairs_hook=_object)
    if not isinstance(manifest, dict) or canonical_bytes(manifest) != content:
        raise ValueError("RAÄ audit manifest encoding mismatch")
    implementation = implementation_identity()
    if (
        manifest.get("schema_version") != SCHEMA_VERSION
        or canonical_bytes(manifest.get("boundary")) != canonical_bytes(BOUNDARY)
        or manifest.get("implementation") != implementation
    ):
        raise ValueError("RAÄ audit schema/boundary/producer mismatch")
    source = {
        "sha256": expected_source_sha256,
        "byte_count": expected_source_byte_count,
    }
    if canonical_bytes(manifest.get("source")) != canonical_bytes(source):
        raise ValueError("RAÄ audit pinned raw source mismatch")
    digest = sha256()
    count = size = 0
    summary: dict[str, object] | None = None
    selected: list[dict[str, object]] = []
    rows = directory / "rows.ndjson"
    before = rows.stat()
    with (
        read_only_database(
            source_path,
            expected_sha256=expected_source_sha256,
            expected_byte_count=expected_source_byte_count,
        ) as connection,
        rows.open("rb") as stream,
    ):
        for record in iter_audit_documents(connection):
            expected = canonical_bytes(record)
            if stream.readline() != expected:
                raise ValueError("RAÄ raw replay/source row mismatch")
            digest.update(expected)
            count += 1
            size += len(expected)
            if record["kind"] == "summary":
                summary = record
            owner = record.get("owner_relation")
            if native_uuid is not None and isinstance(owner, dict):
                lineage = owner.get("lamning_lineage_via_nested_row")
                if owner.get("native_lamning_uuid") == native_uuid or (
                    isinstance(lineage, dict)
                    and lineage.get("native_lamning_uuid") == native_uuid
                ):
                    selected.append(record)
        if stream.read(1):
            raise ValueError("RAÄ saved audit contains extra rows")
    expected_files = {
        "rows.ndjson": {
            "sha256": digest.hexdigest(),
            "byte_count": size,
            "record_count": count,
        }
    }
    if canonical_bytes(manifest.get("files")) != canonical_bytes(
        expected_files
    ) or canonical_bytes(manifest.get("summary")) != canonical_bytes(summary):
        raise ValueError("RAÄ audit descriptor/denominator mismatch")
    _inventory(directory)
    after = rows.stat()
    if (
        (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        or path.read_bytes() != content
        or implementation_identity() != implementation
    ):
        raise ValueError("RAÄ saved audit or producer changed during inspection")
    return {
        "manifest_sha256": expected_manifest_sha256,
        "summary": summary,
        "selected_native_uuid": native_uuid,
        "selected_source_rows": selected,
        "raw_replay_verified": True,
        "boundary": dict(BOUNDARY),
    }
