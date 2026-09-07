"""Read governed SEAD evidence from validated source materializations."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final, cast

_MANIFEST_NAME: Final = "evidence_materialization_manifest.json"
_MANIFEST_SCHEMA: Final = "sead-evidence-materialization-manifest.v1"
_MULTIPART_SCHEMA: Final = "sead-evidence-multipart.v1"
_MAX_FILE_BYTES: Final = 50 * 1024 * 1024
_LOGICAL_DOCUMENTS: Final = frozenset(
    {
        "chronology_claims.json",
        "evidence_events.json",
        "observation_relation_index.json",
        "source_key_ledger.json",
        "source_native_observations.json",
    }
)
SEAD_GOVERNED_EVIDENCE_RUN_ID: Final = "sead-full-evidence-39bfff6a-ce80714e"
SEAD_GOVERNED_EVIDENCE_SCOPE_ID: Final = (
    "sha256:39bfff6abd80041dc01c554711b2a57daf6ee68e1757e3515668a18874ffb7d7"
)
SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256: Final = (
    "c5ec51e8e7360e4f47cffceeb7a907e022da4445caf853317cbcc908269b0093"
)
SEAD_GOVERNED_ADMISSION_SHA256: Final = (
    "69f93b6bd34e457bedc4047077024de1beefc900142f45051fab60dce03751ea"
)
SEAD_GOVERNED_BUILD_ID: Final = (
    "sha256:ce80714e4c9e9974b24913e5da50f49854670ed642879c1ca5076499e1d56725"
)
SEAD_GOVERNED_PARENT_RUN_ID: Final = (
    "sead-live-d1fd2058913372eda1c12e526e0eb7c8a6cec415e9f9e9b5b92b8896597b35ac"
)
SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256: Final = (
    "6fc2428046d148f9ce6c158f982afbbbbaea39de2132850a4fb8f41acf8a4c14"
)
SEAD_GOVERNED_COUNTRY_DECISIONS_SHA256: Final = (
    "e08c2fa2f70d9a3491b95a87b81c992ec3902051aa6e30c35dbcb0f86e214528"
)
SEAD_GOVERNED_PARENT_ADMISSION_SHA256: Final = (
    "168ad1efe6fa68cdb7789246a6cce16670377cdbacd14d1673beaab8ddd1ebd1"
)
SEAD_GOVERNED_BBOX_PAYLOAD_SHA256: Final = (
    "2b0f000db8d26d61ea4b08e3399428cb76ace24e1ba021e58caf182242ce3607"
)
SEAD_GOVERNED_COUNTRY_AUTHORITY_ID: Final = (
    "sha256:e67d7e498df146bcdd65c398f67cdf2372298258288bcba9af734486fa2fe8d0"
)
SEAD_GOVERNED_COUNTRY_AUTHORITY_DIGEST: Final = (
    "sha256:bc248e555d39828187df43e27f6150c73bcbd209ce43cb3e41be2c914510b32f"
)


def governed_sead_evidence_root(data_root: Path) -> Path:
    """Return the immutable normalized evidence location below a data root."""
    return (
        Path(data_root)
        / "sead"
        / "normalized"
        / "acquisitions"
        / SEAD_GOVERNED_EVIDENCE_RUN_ID
    )


def read_validated_sead_evidence_document(
    output_directory: Path,
    logical_document: str,
    *,
    expected_run_id: str,
    expected_manifest_sha256: str,
) -> dict[str, object]:
    """Validate an evidence materialization and reconstruct one logical document."""
    return read_validated_sead_evidence_documents(
        output_directory,
        (logical_document,),
        expected_run_id=expected_run_id,
        expected_manifest_sha256=expected_manifest_sha256,
    )[logical_document]


def read_validated_sead_evidence_documents(
    output_directory: Path,
    logical_documents: Sequence[str],
    *,
    expected_run_id: str,
    expected_manifest_sha256: str,
) -> dict[str, dict[str, object]]:
    """Validate once and reconstruct the requested governed logical documents."""
    requested_names = tuple(logical_documents)
    if not requested_names or len(requested_names) != len(set(requested_names)):
        raise ValueError("SEAD evidence document request must be nonempty and unique")
    unsupported = set(requested_names) - _LOGICAL_DOCUMENTS
    if unsupported:
        raise ValueError(
            f"Unsupported SEAD evidence documents: {sorted(unsupported)!r}"
        )
    root = Path(output_directory)
    if not root.is_absolute() or root == Path(root.anchor):
        raise ValueError("SEAD evidence materialization must be a safe absolute path")
    _reject_symlink_ancestors(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("SEAD evidence materialization must be a regular directory")

    manifest_path = root / _MANIFEST_NAME
    manifest_bytes = _read_regular_file(manifest_path, _MANIFEST_NAME)
    if hashlib.sha256(manifest_bytes).hexdigest() != expected_manifest_sha256:
        raise ValueError("SEAD evidence manifest changed from the bound input")
    manifest = _canonical_object(manifest_bytes, _MANIFEST_NAME)
    if manifest.get("schema_version") != _MANIFEST_SCHEMA:
        raise ValueError("SEAD evidence manifest schema version changed")
    if manifest.get("maximum_file_byte_count") != _MAX_FILE_BYTES:
        raise ValueError("SEAD evidence manifest file limit changed")
    source_run_id = manifest.get("source_run_id")
    if not isinstance(source_run_id, str) or not source_run_id:
        raise ValueError("SEAD evidence manifest source run is invalid")
    if source_run_id != expected_run_id:
        raise ValueError("SEAD evidence manifest source run changed")
    records_value = manifest.get("files")
    if not isinstance(records_value, list):
        raise TypeError("SEAD evidence manifest files must be a list")

    records: dict[str, Mapping[str, object]] = {}
    record_paths: list[str] = []
    for record in records_value:
        if not isinstance(record, Mapping):
            raise TypeError("SEAD evidence file record must be an object")
        relative_path = _safe_relative_path(record.get("path"))
        if relative_path in records:
            raise ValueError(f"Duplicate SEAD evidence path: {relative_path}")
        records[relative_path] = record
        record_paths.append(relative_path)
    if record_paths != sorted(record_paths):
        raise ValueError("SEAD evidence manifest file inventory is not ordered")

    expected_paths = set(records) | {_MANIFEST_NAME}
    if not set(records) >= _LOGICAL_DOCUMENTS:
        raise ValueError("SEAD evidence materialization lacks a logical document")
    verified_files: dict[str, tuple[str, int]] = {}
    logical: dict[str, dict[str, object]] = {}
    for name in _LOGICAL_DOCUMENTS:
        content = _read_regular_file(root / name, name)
        _verify_record(content, records[name], name)
        verified_files[name] = (hashlib.sha256(content).hexdigest(), len(content))
        logical[name] = _canonical_object(content, name)
    for name, document in logical.items():
        if document.get("source_run_id") != source_run_id:
            raise ValueError(f"SEAD evidence source run diverges in {name}")
        build_field = (
            "source_build_id" if name == "chronology_claims.json" else "build_id"
        )
        if document.get(build_field) != manifest.get("build_id"):
            raise ValueError(f"SEAD evidence build identity diverges in {name}")
        if document.get("acquisition_manifest_sha256") != manifest.get(
            "acquisition_manifest_sha256"
        ):
            raise ValueError(f"SEAD evidence acquisition identity diverges in {name}")
    multipart = manifest.get("multipart_documents")
    if not isinstance(multipart, Mapping):
        raise TypeError("SEAD evidence multipart_documents must be an object")
    if not set(multipart) <= _LOGICAL_DOCUMENTS:
        raise ValueError("SEAD evidence manifest names an unknown logical document")

    referenced_parts: set[str] = set()
    requested = {name: dict(logical[name]) for name in requested_names}
    for document_name, declaration in sorted(multipart.items()):
        if not isinstance(document_name, str) or not isinstance(declaration, Mapping):
            raise TypeError("SEAD evidence multipart declaration is invalid")
        index = logical[document_name]
        partitioned = index.get("partitioned_fields")
        if not isinstance(partitioned, Mapping):
            raise TypeError("SEAD multipart index lacks partitioned_fields")
        if declaration.get("partitioned_fields") != sorted(partitioned):
            raise ValueError("SEAD multipart field declaration changed")
        document_parts: list[str] = []
        for field, field_record in sorted(partitioned.items()):
            if not isinstance(field, str) or not isinstance(field_record, Mapping):
                raise TypeError("SEAD evidence partition record is invalid")
            parts = field_record.get("parts")
            if not isinstance(parts, list):
                raise TypeError("SEAD evidence partition parts must be a list")
            if field_record.get("part_count") != len(parts):
                raise ValueError("SEAD evidence partition part count changed")
            rows: list[object] = []
            row_cursor = 0
            for part_number, part_record in enumerate(parts, start=1):
                if not isinstance(part_record, Mapping):
                    raise TypeError("SEAD evidence part record must be an object")
                part_path = _safe_relative_path(part_record.get("path"))
                if part_path in referenced_parts:
                    raise ValueError(f"SEAD evidence part is duplicated: {part_path}")
                manifest_record = records.get(part_path)
                if manifest_record is None:
                    raise ValueError(f"SEAD evidence part is absent: {part_path}")
                part_content = _read_regular_file(
                    root.joinpath(*Path(part_path).parts), part_path
                )
                _verify_record(part_content, manifest_record, part_path)
                _verify_record(part_content, part_record, part_path)
                verified_files[part_path] = (
                    hashlib.sha256(part_content).hexdigest(),
                    len(part_content),
                )
                part = _canonical_object(part_content, part_path)
                part_rows = part.get(field)
                if not isinstance(part_rows, list):
                    raise TypeError(f"SEAD evidence part rows are invalid: {part_path}")
                row_end = row_cursor + len(part_rows)
                for key, expected in (
                    ("schema_version", _MULTIPART_SCHEMA),
                    ("logical_document", document_name),
                    ("field", field),
                    ("part_number", part_number),
                    ("row_start", row_cursor),
                    ("row_end", row_end),
                ):
                    if part.get(key) != expected:
                        raise ValueError(
                            f"SEAD evidence part {key} changed: {part_path}"
                        )
                for key, expected in (
                    ("part_number", part_number),
                    ("row_start", row_cursor),
                    ("row_end", row_end),
                    ("row_count", len(part_rows)),
                ):
                    if part_record.get(key) != expected:
                        raise ValueError(
                            f"SEAD evidence part record {key} changed: {part_path}"
                        )
                if document_name in requested:
                    rows.extend(part_rows)
                row_cursor = row_end
                document_parts.append(part_path)
                referenced_parts.add(part_path)
            if field_record.get("row_count") != row_cursor:
                raise ValueError("SEAD evidence partition row denominator changed")
            if document_name in requested:
                requested[document_name][field] = rows
        if declaration.get("part_count") != len(document_parts):
            raise ValueError("SEAD multipart document part count changed")
        if declaration.get("parts") != sorted(document_parts):
            raise ValueError("SEAD multipart document file set changed")
    if referenced_parts != set(records) - _LOGICAL_DOCUMENTS:
        raise ValueError("SEAD multipart evidence has unreferenced files")
    expected_file_set = _stable_digest(
        *(
            f"{name}:{digest}:{byte_count}"
            for name, (digest, byte_count) in sorted(verified_files.items())
        )
    )
    if manifest.get("file_set_sha256") != expected_file_set:
        raise ValueError("SEAD evidence file-set digest does not reconcile")
    if _regular_file_inventory(root) != expected_paths:
        raise ValueError("SEAD evidence manifest does not cover the exact file set")
    for document in requested.values():
        document.pop("partitioned_fields", None)
    return requested


def _read_regular_file(path: Path, label: str) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"SEAD evidence file is not regular: {label}")
    content = path.read_bytes()
    if len(content) > _MAX_FILE_BYTES:
        raise ValueError(f"SEAD evidence file exceeds size limit: {label}")
    return content


def _regular_file_inventory(root: Path) -> set[str]:
    files: set[str] = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Symlinks are forbidden in SEAD evidence: {path}")
        if path.is_file():
            files.add(path.relative_to(root).as_posix())
        elif not path.is_dir():
            raise ValueError(f"Unsupported filesystem object in SEAD evidence: {path}")
    return files


def _reject_symlink_ancestors(path: Path) -> None:
    for ancestor in (path, *path.parents):
        if ancestor.exists() and ancestor.is_symlink():
            raise ValueError(
                f"SEAD evidence materialization traverses a symlink: {ancestor}"
            )


def _safe_relative_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("SEAD evidence path must be nonempty text")
    candidate = Path(value)
    if candidate.is_absolute() or value != candidate.as_posix():
        raise ValueError(f"Unsafe SEAD evidence path: {value!r}")
    if any(part in {"", ".", ".."} for part in candidate.parts):
        raise ValueError(f"Unsafe SEAD evidence path: {value!r}")
    return value


def _verify_record(content: bytes, record: Mapping[str, object], label: str) -> None:
    if record.get("byte_count") != len(content):
        raise ValueError(f"SEAD evidence byte count changed: {label}")
    digest = record.get("sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError(f"SEAD evidence digest is invalid: {label}")
    if any(character not in "0123456789abcdef" for character in digest):
        raise ValueError(f"SEAD evidence digest is invalid: {label}")
    if digest != hashlib.sha256(content).hexdigest():
        raise ValueError(f"SEAD evidence digest changed: {label}")


def _canonical_object(payload: bytes, label: str) -> dict[str, object]:
    try:
        document = json.loads(payload, parse_constant=_reject_json_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"SEAD evidence JSON is invalid: {label}") from exc
    if not isinstance(document, dict):
        raise TypeError(f"SEAD evidence JSON object is required: {label}")
    if payload != _canonical_bytes(document):
        raise ValueError(f"SEAD evidence JSON is not canonical: {label}")
    return cast(dict[str, object], document)


def _reject_json_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON number is forbidden: {value}")


def _stable_digest(*parts: str) -> str:
    return hashlib.sha256(_canonical_bytes(list(parts))).hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


__all__ = [
    "SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256",
    "SEAD_GOVERNED_ADMISSION_SHA256",
    "SEAD_GOVERNED_BBOX_PAYLOAD_SHA256",
    "SEAD_GOVERNED_BUILD_ID",
    "SEAD_GOVERNED_COUNTRY_AUTHORITY_DIGEST",
    "SEAD_GOVERNED_COUNTRY_AUTHORITY_ID",
    "SEAD_GOVERNED_COUNTRY_DECISIONS_SHA256",
    "SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256",
    "SEAD_GOVERNED_EVIDENCE_RUN_ID",
    "SEAD_GOVERNED_EVIDENCE_SCOPE_ID",
    "SEAD_GOVERNED_PARENT_ADMISSION_SHA256",
    "SEAD_GOVERNED_PARENT_RUN_ID",
    "governed_sead_evidence_root",
    "read_validated_sead_evidence_document",
    "read_validated_sead_evidence_documents",
]
