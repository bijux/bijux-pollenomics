"""Closed archive schemas and bounded ordinary file/directory populations."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

from bijux_pollenomics.core.filesystem import validate_regular_namespace

ARCHIVE_SCHEMA = "neotoma-source-resource-archive.v1"
MAX_BYTES = 512 * 1024 * 1024
MAX_FILES = 20000
MAX_MANIFEST_BYTES = 16 * 1024 * 1024
_MANIFEST_FIELDS = {
    "schema_version",
    "catalogue_manifest_sha256",
    "files",
    "retained_sources",
    "source_bytes",
    "scientific_admission",
    "historical_snapshot_replaced",
}
_RETAINED_FIELDS = {"body", "provenance", "body_sha256", "provenance_sha256"}


def encoded_json(value: object) -> bytes:
    """Keep existing source archive serialization literal and finite."""
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2)
        + "\n"
    ).encode()


def _member(relative: object) -> str:
    if (
        not isinstance(relative, str)
        or not relative
        or "\\" in relative
        or "\x00" in relative
    ):
        raise ValueError("Neotoma archive member is not a canonical relative path")
    path = PurePosixPath(relative)
    if (
        path.is_absolute()
        or path.as_posix() != relative
        or not path.parts
        or ".." in path.parts
        or len(path.parts) > 32
    ):
        raise ValueError("Neotoma archive member escapes its bounded namespace")
    return relative


def _digest(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def validate_manifest(manifest: dict[str, Any]) -> None:
    """Refuse every unowned root, retained-source or file identity field."""
    if (
        set(manifest)
        not in (
            _MANIFEST_FIELDS,
            _MANIFEST_FIELDS | {"original_metadata"},
        )
        or manifest["schema_version"] != ARCHIVE_SCHEMA
        or manifest["scientific_admission"] != "not_asserted"
        or manifest["historical_snapshot_replaced"] is not False
        or not _digest(manifest["catalogue_manifest_sha256"])
        or not isinstance(manifest["files"], dict)
        or len(manifest["files"]) + 1 > MAX_FILES
        or not isinstance(manifest["retained_sources"], dict)
        or type(manifest["source_bytes"]) is not int
        or not 0 <= manifest["source_bytes"] <= MAX_BYTES
    ):
        raise ValueError("Neotoma source archive manifest fields or identity differ")
    declared = 0
    for relative, member in manifest["files"].items():
        _member(relative)
        if relative == "manifest.json" or (
            not isinstance(member, dict)
            or set(member) != {"bytes", "sha256"}
            or type(member.get("bytes")) is not int
            or member["bytes"] < 0
            or not _digest(member.get("sha256"))
        ):
            raise ValueError("Neotoma source archive member identity is malformed")
        declared += member["bytes"]
    if declared != manifest["source_bytes"] or declared > MAX_BYTES:
        raise ValueError("Neotoma source archive declared byte population differs")
    for key, row in manifest["retained_sources"].items():
        _member(key)
        if (
            not isinstance(row, dict)
            or set(row) != _RETAINED_FIELDS
            or not _digest(row.get("body_sha256"))
            or not _digest(row.get("provenance_sha256"))
            or row.get("body") != f"captures/retained/{key}/native.body"
            or row.get("provenance") != f"captures/retained/{key}/provenance.json"
        ):
            raise ValueError("Neotoma source archive retained source fields differ")
        _member(row["body"])
        _member(row["provenance"])


def validate_namespace(root: Path, expected_files: set[str]) -> None:
    """Keep archive namespace refusals under the shared ordinary file owner."""
    try:
        validate_regular_namespace(
            root, expected_files, max_files=MAX_FILES, max_bytes=MAX_BYTES
        )
    except ValueError as error:
        raise ValueError(f"Neotoma source archive {error}") from error
