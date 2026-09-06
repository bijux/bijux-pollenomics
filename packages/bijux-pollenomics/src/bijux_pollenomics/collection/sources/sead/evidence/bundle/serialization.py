from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path


def _copied_file_sha256(admission: Mapping[str, object], path: str) -> str:
    copied = admission.get("copied_files")
    if not isinstance(copied, list):
        raise TypeError("SEAD admission copied_files is missing")
    matches = [
        item
        for item in copied
        if isinstance(item, Mapping) and item.get("path") == path
    ]
    if len(matches) != 1:
        raise ValueError(f"SEAD admission must bind one {path}")
    return _required_sha256(matches[0], "sha256")


def _verify_record(content: bytes, record: Mapping[str, object], label: str) -> None:
    if record.get("byte_count") != len(content):
        raise ValueError(f"SEAD admitted byte count changed: {label}")
    if _required_sha256(record, "sha256") != hashlib.sha256(content).hexdigest():
        raise ValueError(f"SEAD admitted digest changed: {label}")


def _directory_bytes(root: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Symlinks are forbidden in SEAD evidence: {path}")
        if path.is_file():
            files[path.relative_to(root).as_posix()] = path.read_bytes()
    return files


def _reject_symlink_ancestors(path: Path) -> None:
    for ancestor in (path, *path.parents):
        if ancestor.exists() and ancestor.is_symlink():
            raise ValueError(
                f"SEAD evidence acquisition path traverses a symlink: {ancestor}"
            )


def _safe_evidence_relative_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("SEAD evidence path must be nonempty text")
    candidate = Path(value)
    if candidate.is_absolute() or value != candidate.as_posix():
        raise ValueError(f"Unsafe SEAD evidence path: {value!r}")
    if any(part in {"", ".", ".."} for part in candidate.parts):
        raise ValueError(f"Unsafe SEAD evidence path: {value!r}")
    return value


def _read_object(path: Path) -> dict[str, object]:
    return _decode_object(path.read_bytes(), path.as_posix())


def _decode_object(payload: bytes, label: str) -> dict[str, object]:
    try:
        document = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"SEAD JSON is invalid: {label}") from exc
    if not isinstance(document, dict):
        raise TypeError(f"SEAD JSON object is required: {label}")
    return document


def _required_text(document: Mapping[str, object], field: str) -> str:
    value = document.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"SEAD {field} must be nonempty text")
    return value.strip()


def _required_sha256(document: Mapping[str, object], field: str) -> str:
    value = _required_text(document, field)
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(f"SEAD {field} must be a lowercase SHA-256")
    return value


def _required_prefixed_sha256(document: Mapping[str, object], field: str) -> str:
    value = _required_text(document, field)
    digest = value.removeprefix("sha256:")
    if (
        value == digest
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise ValueError(f"SEAD {field} must be a prefixed lowercase SHA-256")
    return value


def _positive_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"SEAD {label} must be a positive integer")
    return value


def _stable_id(namespace: str, *parts: str) -> str:
    digest = hashlib.sha256(_canonical_bytes(list(parts))).hexdigest()
    return f"{namespace}:{digest}"


def _canonical_bytes(payload: object) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _logical_row_count(document: Mapping[str, object], field: str) -> int:
    direct = document.get(field)
    if isinstance(direct, list):
        return len(direct)
    partitioned = document.get("partitioned_fields")
    if not isinstance(partitioned, Mapping):
        raise ValueError(f"SEAD evidence rows are absent: {field}")
    record = partitioned.get(field)
    if not isinstance(record, Mapping):
        raise ValueError(f"SEAD evidence partition is absent: {field}")
    value = record.get("row_count")
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"SEAD evidence partition row count is invalid: {field}")
    return value
