"""Bind raw Neotoma receipts and every normalized materialization member."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics.collection.sources.neotoma.production import (
    load_validated_neotoma_raw_archive,
)
from bijux_pollenomics.evidence.sources.neotoma import (
    validate_neotoma_relational_materialization,
)

from .models import SourceRow, canonical_bytes


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ValueError(f"Nonfinite JSON constant: {value}")


def json_object(content: bytes) -> dict[str, Any]:
    """Reject ambiguous objects before attributing any source observations."""
    value = json.loads(
        content, object_pairs_hook=_unique_object, parse_constant=_invalid_constant
    )
    if not isinstance(value, dict):
        raise ValueError("Source document must be an object")
    canonical_bytes(value)
    return cast(dict[str, Any], value)


def checked_directory(path: Path) -> Path:
    """Reject symlink traversal before resolving lexical dot segments."""
    absolute = path.absolute()
    if any(part.is_symlink() for part in (absolute, *absolute.parents)):
        raise ValueError("Source directory must not traverse symlinks")
    root = absolute.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Source authority must be a directory")
    return root


def evidence_inventory(root: Path) -> tuple[tuple[str, str], ...]:
    """Bind every regular file under an already checked source directory."""
    records = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("Source authority must not contain symlinks")
        if path.is_file():
            with path.open("rb") as stream:
                records.append(
                    (
                        path.relative_to(root).as_posix(),
                        hashlib.file_digest(stream, "sha256").hexdigest(),
                    )
                )
        elif not path.is_dir():
            raise ValueError("Source authority contains a nonregular member")
    return tuple(records)


@dataclass(frozen=True)
class NeotomaEvidence:
    """Immutable bytes and roots of an already validated source projection."""

    raw_root: Path
    normalized_root: Path
    manifest_bytes: bytes
    raw_files: tuple[tuple[str, str], ...]
    normalized_files: tuple[tuple[str, str], ...]

    def manifest(self) -> dict[str, Any]:
        return json_object(self.manifest_bytes)

    def assert_unchanged(self) -> None:
        normalized_inventory = evidence_inventory(self.normalized_root)
        captured_manifest_sha256 = dict(self.normalized_files).get("manifest.json")
        if (
            captured_manifest_sha256 is None
            or hashlib.sha256(self.manifest_bytes).hexdigest()
            != captured_manifest_sha256
            or evidence_inventory(self.raw_root) != self.raw_files
            or normalized_inventory != self.normalized_files
        ):
            raise ValueError("Source authority changed during admission audit")

    def input_records(self) -> list[dict[str, str]]:
        return [
            {"authority": authority, "path": path, "sha256": digest}
            for authority, files in (
                ("raw", self.raw_files),
                ("normalized", self.normalized_files),
            )
            for path, digest in files
        ]

    def rows(self, surface: str) -> Iterator[SourceRow]:
        manifest = self.manifest()
        inventory = dict(self.normalized_files)
        for part in manifest["surfaces"][surface]["parts"]:
            relative = part["path"]
            content = (self.normalized_root / relative).read_bytes()
            if hashlib.sha256(content).hexdigest() != inventory[relative]:
                raise ValueError(f"Normalized part changed: {relative}")
            document = json_object(content)
            for index, row in enumerate(document["rows"]):
                yield SourceRow(surface, relative, index, canonical_bytes(row))


def read_neotoma_evidence(raw_root: Path, normalized_root: Path) -> NeotomaEvidence:
    """Validate existing authorities and require the exact raw snapshot identity."""
    raw = checked_directory(raw_root)
    normalized = checked_directory(normalized_root)
    if raw.is_relative_to(normalized) or normalized.is_relative_to(raw):
        raise ValueError("Raw and normalized authority roots must be disjoint")
    raw_files, normalized_files = (
        evidence_inventory(raw),
        evidence_inventory(normalized),
    )
    manifest_bytes = (normalized / "manifest.json").read_bytes()
    manifest = json_object(manifest_bytes)
    validated = validate_neotoma_relational_materialization(normalized)
    if canonical_bytes(manifest) != canonical_bytes(validated):
        raise ValueError("Normalized manifest changed during validation")
    raw_rows, snapshot = load_validated_neotoma_raw_archive(raw)
    del raw_rows
    if manifest["source_snapshot_id"] != snapshot:
        raise ValueError("Normalized materialization does not bind the raw snapshot")
    evidence = NeotomaEvidence(
        raw, normalized, manifest_bytes, raw_files, normalized_files
    )
    evidence.assert_unchanged()
    return evidence
