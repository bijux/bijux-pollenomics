"""Content-addressed evidence reads without source mutations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def digest(value: object) -> str:
    """Hash canonical JSON without volatile timestamps or machine paths."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class EvidenceReader:
    """Record every consumed file and reject paths outside the audited tree."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.files: dict[str, dict[str, Any]] = {}
        self.verifications: dict[str, dict[str, Any]] = {}
        self.issues: list[dict[str, Any]] = []

    def resolve(self, relative: str) -> Path:
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError(f"Evidence path escapes repository: {relative}")
        return path

    def issue(self, code: str, path: str, **details: Any) -> None:
        self.issues.append({"reason_code": code, "path": path, **details})

    def read_bytes(self, relative: str) -> bytes | None:
        path = self.resolve(relative)
        if not path.is_file():
            if self.files.get(relative, {}).get("presence") == "present":
                raise ValueError(f"Evidence changed during audit: {relative}")
            self.files[relative] = {"path": relative, "presence": "missing"}
            return None
        content = path.read_bytes()
        entry = {
            "path": relative,
            "presence": "present",
            "byte_count": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        previous = self.files.get(relative)
        if previous is not None and previous != entry:
            raise ValueError(f"Evidence changed during audit: {relative}")
        self.files[relative] = entry
        return content

    def json(self, relative: str) -> dict[str, Any] | None:
        content = self.read_bytes(relative)
        if content is None:
            return None
        result = json.loads(content)
        if not isinstance(result, dict):
            raise ValueError(f"Expected object in {relative}")
        return result

    def verify(self, relative: str, expected: dict[str, Any]) -> bytes | None:
        content = self.read_bytes(relative)
        if content is None:
            self.issue("manifest_file_missing", relative)
            return None
        actual = self.files[relative]
        self.verifications[relative] = {
            "path": relative,
            "manifest_digest_available": expected.get("sha256") is not None,
            "manifest_byte_count_available": expected.get("byte_count") is not None,
            "observed_sha256": actual["sha256"],
        }
        for key in ("sha256", "byte_count"):
            value = expected.get(key)
            if key == "sha256" and isinstance(value, str):
                value = value.removeprefix("sha256:")
            if value is not None and value != actual[key]:
                self.issue(
                    "manifest_digest_or_size_mismatch",
                    relative,
                    field=key,
                    expected=value,
                    actual=actual[key],
                )
        return content


def indexed_rows(payload: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    """Reject duplicate identities instead of silently overwriting registry rows."""
    rows = payload["rows"]
    if payload.get("row_count", len(rows)) != len(rows):
        raise ValueError("Registry row_count does not reconcile")
    result = {row[key]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"Duplicate registry identity: {key}")
    return result
