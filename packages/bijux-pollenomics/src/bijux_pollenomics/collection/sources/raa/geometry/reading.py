"""Authenticate retained geometry bytes against an exact native source replay."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re

from ..materialization.ownership import canonical_bytes
from ..materialization.reading import read_only_database
from .models import BOUNDARY, SCHEMA_VERSION, RaaGeometryAudit
from .rows import iter_geometry_documents
from .service import implementation_identity


def _object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("RAÄ geometry audit duplicate JSON key")
        result[key] = value
    return result


def _inventory(directory: Path) -> None:
    for path in (directory, *directory.parents):
        if path.is_symlink():
            raise ValueError("RAÄ geometry audit inspection cannot use symlinks")
    if {p.name for p in directory.iterdir()} != {
        "manifest.json",
        "geometry.ndjson",
    } or any(p.is_symlink() or not p.is_file() for p in directory.iterdir()):
        raise ValueError("RAÄ geometry audit inventory mismatch")


def inspect_raa_geometry_audit(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    source_path: Path,
    expected_source_sha256: str,
    expected_source_byte_count: int,
) -> RaaGeometryAudit:
    """Replay all source occurrences; do not trust rehashed derived status fields."""
    if not isinstance(expected_manifest_sha256, str) or not re.fullmatch(
        "[0-9a-f]{64}", expected_manifest_sha256
    ):
        raise ValueError("RAÄ geometry manifest SHA256 is required")
    _inventory(directory)
    path = directory / "manifest.json"
    content = path.read_bytes()
    if sha256(content).hexdigest() != expected_manifest_sha256:
        raise ValueError("RAÄ geometry manifest identity mismatch")
    manifest = json.loads(content, object_pairs_hook=_object)
    if not isinstance(manifest, dict) or canonical_bytes(manifest) != content:
        raise ValueError("RAÄ geometry manifest encoding mismatch")
    implementation = implementation_identity()
    if (
        set(manifest)
        != {
            "schema_version",
            "source",
            "boundary",
            "implementation",
            "files",
            "summary",
        }
        or manifest["schema_version"] != SCHEMA_VERSION
    ):
        raise ValueError("RAÄ geometry manifest schema mismatch")
    if (
        canonical_bytes(manifest["boundary"]) != canonical_bytes(BOUNDARY)
        or manifest["implementation"] != implementation
    ):
        raise ValueError("RAÄ geometry boundary or producer mismatch")
    expected_source = {
        "sha256": expected_source_sha256,
        "byte_count": expected_source_byte_count,
    }
    if canonical_bytes(manifest["source"]) != canonical_bytes(expected_source):
        raise ValueError("RAÄ geometry raw source pin mismatch")
    digest = sha256()
    count = size = 0
    summary: dict[str, object] | None = None
    rows = directory / "geometry.ndjson"
    before = rows.stat()
    with (
        read_only_database(
            source_path,
            expected_sha256=expected_source_sha256,
            expected_byte_count=expected_source_byte_count,
        ) as connection,
        rows.open("rb") as stream,
    ):
        for record in iter_geometry_documents(connection):
            expected = canonical_bytes(record)
            if stream.readline() != expected:
                raise ValueError("RAÄ geometry raw replay mismatch")
            digest.update(expected)
            count += 1
            size += len(expected)
            if record["kind"] == "summary":
                summary = record
        if stream.read(1):
            raise ValueError("RAÄ geometry audit contains extra rows")
    expected_files = {
        "geometry.ndjson": {
            "sha256": digest.hexdigest(),
            "byte_count": size,
            "record_count": count,
        }
    }
    if canonical_bytes(manifest["files"]) != canonical_bytes(
        expected_files
    ) or canonical_bytes(manifest["summary"]) != canonical_bytes(summary):
        raise ValueError("RAÄ geometry descriptor or denominator mismatch")
    _inventory(directory)
    after = rows.stat()
    names = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    if (
        any(getattr(before, n) != getattr(after, n) for n in names)
        or path.read_bytes() != content
        or implementation_identity() != implementation
    ):
        raise ValueError("RAÄ geometry audit or producer changed")
    return RaaGeometryAudit(directory, expected_manifest_sha256, content.decode())
