"""Closed archive schemas and bounded ordinary file/directory populations."""

from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any

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
    """Visit only declared parent directories; aliases and special entries refuse."""
    if len(expected_files) > MAX_FILES:
        raise ValueError("Neotoma source archive file population exceeds its bound")
    expected_directories: set[str] = set()
    for relative in expected_files:
        path = PurePosixPath(_member(relative))
        expected_directories.update(str(p) for p in path.parents if str(p) != ".")
    seen_files, seen_directories = set(), set()
    pending = [(root, "")]
    visited = 0
    while pending:
        directory, prefix = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                visited += 1
                if visited > len(expected_files) + len(expected_directories):
                    raise ValueError(
                        "Neotoma source archive namespace exceeds its bound"
                    )
                relative = prefix + entry.name
                node = entry.stat(follow_symlinks=False)
                if stat.S_ISDIR(node.st_mode):
                    if relative not in expected_directories:
                        raise ValueError(
                            "Neotoma source archive contains an unowned directory"
                        )
                    seen_directories.add(relative)
                    pending.append((Path(entry.path), relative + "/"))
                elif stat.S_ISREG(node.st_mode) and node.st_nlink == 1:
                    if relative not in expected_files:
                        raise ValueError(
                            "Neotoma source archive file population differs"
                        )
                    seen_files.add(relative)
                else:
                    raise ValueError(
                        "Neotoma source archive contains a nonregular namespace entry"
                    )
    if seen_files != expected_files or seen_directories != expected_directories:
        raise ValueError("Neotoma source archive closed namespace population differs")
