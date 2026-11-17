"""Bounded physical custody for the declared evidence materialization files."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path

from bijux_pollenomics.core.filesystem import (
    BoundedInputTree,
    validate_regular_namespace,
)

from .constants import EVIDENCE_MANIFEST_SCHEMA_VERSION
from .serialization import (
    _canonical_bytes,
    _decode_object,
    _required_sha256,
    _safe_evidence_relative_path,
    _verify_record,
)

_LOGICAL_DOCUMENT_NAMES = frozenset(
    {
        "chronology_claims.json",
        "source_native_observations.json",
        "observation_relation_index.json",
        "evidence_events.json",
        "source_key_ledger.json",
    }
)


def _count(record: Mapping[str, object], field: str) -> int:
    value = record.get(field)
    if type(value) is not int or value < 0:
        raise ValueError(f"SEAD evidence {field} must be a nonnegative integer")
    return value


def _part_names(
    manifest: Mapping[str, object],
    records: Mapping[str, Mapping[str, object]],
    contents: Mapping[str, bytes],
) -> set[str]:
    """Authorize part reads only after both canonical metadata indexes agree."""
    declared = manifest.get("multipart_documents")
    if not isinstance(declared, Mapping):
        raise TypeError("SEAD evidence multipart_documents must be an object")
    if not set(declared) <= _LOGICAL_DOCUMENT_NAMES:
        raise ValueError("SEAD multipart declaration has an unknown logical owner")
    parts: set[str] = set()
    for name, raw in contents.items():
        document = _decode_object(raw, name)
        if raw != _canonical_bytes(document):
            raise ValueError(f"SEAD evidence document is not canonical: {name}")
        if "partitioned_fields" not in document:
            if name in declared:
                raise ValueError("SEAD multipart declaration lacks its logical index")
            continue
        partitioned = document["partitioned_fields"]
        if not isinstance(partitioned, Mapping) or not partitioned:
            raise TypeError("SEAD multipart index lacks partitioned_fields")
        owner = declared.get(name)
        if not isinstance(owner, Mapping):
            raise ValueError("SEAD multipart logical index lacks its declared owner")
        if owner.get("partitioned_fields") != sorted(partitioned):
            raise ValueError("SEAD multipart field declaration changed")
        document_parts: list[str] = []
        for field_record in partitioned.values():
            if not isinstance(field_record, Mapping) or not isinstance(
                field_record.get("parts"), list
            ):
                raise TypeError("SEAD evidence partition parts must be a list")
            field_parts = field_record["parts"]
            if _count(field_record, "part_count") != len(field_parts):
                raise ValueError("SEAD evidence partition part count changed")
            cursor = 0
            for number, part_record in enumerate(field_parts, start=1):
                if not isinstance(part_record, Mapping):
                    raise TypeError("SEAD evidence part record is invalid")
                path = _safe_evidence_relative_path(part_record.get("path"))
                if path in parts or path in _LOGICAL_DOCUMENT_NAMES:
                    raise ValueError(f"SEAD evidence part is duplicated: {path}")
                record = records.get(path)
                if record is None:
                    raise ValueError(f"SEAD evidence part is absent: {path}")
                if _count(part_record, "byte_count") != record.get(
                    "byte_count"
                ) or _required_sha256(part_record, "sha256") != _required_sha256(
                    record, "sha256"
                ):
                    raise ValueError("SEAD evidence part metadata identities differ")
                if (
                    _count(part_record, "part_number") != number
                    or _count(part_record, "row_start") != cursor
                    or _count(part_record, "row_end")
                    != cursor + _count(part_record, "row_count")
                ):
                    raise ValueError("SEAD evidence part row metadata differs")
                cursor = _count(part_record, "row_end")
                document_parts.append(path)
                parts.add(path)
            if _count(field_record, "row_count") != cursor:
                raise ValueError("SEAD evidence partition row denominator changed")
        if _count(owner, "part_count") != len(document_parts) or owner.get(
            "parts"
        ) != sorted(document_parts):
            raise ValueError("SEAD multipart document file set changed")
    return parts


@contextmanager
def open_evidence_files(
    root: Path, *, max_member_bytes: int
) -> Iterator[
    tuple[dict[str, object], dict[str, Mapping[str, object]], dict[str, bytes]]
]:
    """Keep the manifest attachment and exact namespace live through validation."""
    manifest_name = "evidence_materialization_manifest.json"
    manifest_path = root / manifest_name
    with BoundedInputTree(
        root, max_bytes=max_member_bytes, max_files=1, selected=manifest_name
    ) as manifest_tree:
        raw = manifest_tree.read(manifest_path, max_bytes=max_member_bytes)
        manifest = _decode_object(raw, manifest_path.as_posix())
        if raw != _canonical_bytes(manifest):
            raise ValueError("SEAD evidence manifest is not canonical")
        if manifest.get("schema_version") != EVIDENCE_MANIFEST_SCHEMA_VERSION:
            raise ValueError("SEAD evidence manifest schema version changed")
        declarations = manifest.get("files")
        if not isinstance(declarations, list):
            raise TypeError("SEAD evidence manifest files must be a list")
        records: dict[str, Mapping[str, object]] = {}
        limits = {manifest_name: len(raw)}
        for record in declarations:
            if not isinstance(record, Mapping):
                raise TypeError("SEAD evidence file record must be an object")
            relative = _safe_evidence_relative_path(record.get("path"))
            if relative in limits:
                raise ValueError(f"Duplicate SEAD evidence path: {relative}")
            size = record.get("byte_count")
            if type(size) is not int or not 0 <= size <= max_member_bytes:
                raise ValueError(f"SEAD evidence file exceeds size limit: {relative}")
            records[relative] = record
            limits[relative] = size
        expected_paths = set(limits)
        total = max(1, sum(limits.values()))
        sizes = validate_regular_namespace(
            root,
            expected_paths,
            max_files=len(limits),
            max_bytes=len(limits) * max_member_bytes,
        )
        for name, expected in limits.items():
            if sizes[name] != expected:
                raise ValueError(f"SEAD admitted byte count changed: {name}")
        manifest_tree.check()
        with BoundedInputTree(
            root, max_bytes=total, max_files=len(limits), member_limits=limits
        ) as tree:
            if tree.files[manifest_name] != manifest_tree.files[manifest_name]:
                raise ValueError("SEAD evidence manifest attachment changed")
            tree.digests[manifest_name] = sha256(raw).hexdigest()
            contents: dict[str, bytes] = {}
            if not records.keys() >= _LOGICAL_DOCUMENT_NAMES:
                raise ValueError(
                    "SEAD evidence materialization lacks a logical document"
                )

            def read_record(relative: str) -> None:
                tree.check()
                content = tree.read(root / relative, max_bytes=limits[relative])
                _verify_record(content, records[relative], relative)
                tree.check()
                contents[relative] = content

            for relative in sorted(_LOGICAL_DOCUMENT_NAMES):
                read_record(relative)
            parts = _part_names(manifest, records, contents)
            if frozenset(records) != _LOGICAL_DOCUMENT_NAMES | parts:
                raise ValueError("SEAD evidence contains missing or unreferenced parts")
            for relative in sorted(parts):
                read_record(relative)
            yield manifest, records, contents
            tree.check()
            manifest_tree.check()
