"""Propagation producer identity and governed source inventory."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from .codec import _refuse, _sha256
from .inputs import _path_has_symlink_component, _read_identity_file
from .models import (
    _CLASSIFICATION_MANIFEST_NAME,
    PROPAGATION_PRODUCER_ID,
    PROPAGATION_PRODUCER_SOURCE_PATHS,
    PROPAGATION_PRODUCER_VERSION,
)


def _validate_producer_identity(
    repository_root: Path,
    *,
    propagation_producer_id: str,
    propagation_producer_version: str,
    propagation_producer_digest: str,
) -> None:
    executing_source = Path(__file__).resolve()
    governed_source = repository_root / PROPAGATION_PRODUCER_SOURCE_PATHS[0]
    if (
        not repository_root.is_absolute()
        or _path_has_symlink_component(repository_root)
        or not repository_root.is_dir()
        or not governed_source.is_file()
        or governed_source.resolve(strict=True) != executing_source
    ):
        _refuse(
            "invalid_propagation_identity",
            "repository_root does not own the executing propagation producer",
        )
    if (
        propagation_producer_id != PROPAGATION_PRODUCER_ID
        or propagation_producer_version != PROPAGATION_PRODUCER_VERSION
    ):
        _refuse(
            "invalid_propagation_identity",
            "propagation producer id or version is not governed",
        )
    records = []
    for relative_name in PROPAGATION_PRODUCER_SOURCE_PATHS:
        source_path = repository_root / relative_name
        source_bytes = _read_identity_file(
            source_path,
            parent=repository_root,
            reason_code="invalid_propagation_identity",
            allow_descendant=True,
        )
        records.append({"path": relative_name, "sha256": _sha256(source_bytes)})
    computed_digest = _sha256(
        json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    if computed_digest != propagation_producer_digest:
        _refuse(
            "invalid_propagation_identity",
            "propagation_producer_digest does not match governed source bytes",
        )


def _identity_manifest_entries(
    manifest: Mapping[str, Any],
    *,
    reason_code: str,
) -> tuple[tuple[str, str, int], ...]:
    raw_entries = manifest.get("files")
    if not isinstance(raw_entries, list):
        _refuse(reason_code, "identity manifest files must be an array")
    entries: list[tuple[str, str, int]] = []
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, dict):
            _refuse(reason_code, "identity manifest entries must be objects")
        name = raw_entry.get("path")
        digest = raw_entry.get("sha256")
        count = raw_entry.get("record_count")
        if (
            not isinstance(name, str)
            or not name
            or Path(name).name != name
            or name == _CLASSIFICATION_MANIFEST_NAME
            or not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
            or isinstance(count, bool)
            or not isinstance(count, int)
            or count < 0
        ):
            _refuse(reason_code, "identity manifest entry is invalid")
        entries.append((name, digest, count))
    if (
        len(entries) != len({entry[0] for entry in entries})
        or entries != sorted(entries)
        or manifest.get("payload_file_count") != len(entries)
    ):
        _refuse(reason_code, "identity manifest entries are not deterministic")
    return tuple(entries)


def _required_contract_section(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        _refuse(
            "invalid_propagation_identity",
            "propagation contract omits governed model sections",
        )
    return cast(dict[str, Any], value)
