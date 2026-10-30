"""Bind declared child-key refusal labels to their original source identities."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import _regular_confined_file
from ...retained_source import SourceCapsule

_JOIN_IDENTITY_CONTRACTS: dict[
    str, tuple[int, str, tuple[tuple[bytes, bytes], ...]]
] = {
    "packages/bijux-pollenomics/src/bijux_pollenomics/collection/sources/sead/acquisition/full/__init__.py": (
        1963,
        "72551790613f2d00054cd36cf81ef5867a1a1096c71e6696369829ead7a4579d",
        (
            (
                b"_canonical_bytes = _serialization.canonical_bytes\n_utc_text = _serialization.utc_text\n_child_identity = _reconciliation.child_identity_for\n_validate_request = _validation.validate_request\n_validate_table_name = _validation.validate_table_name\n",
                b"_canonical_bytes = _serialization.canonical_bytes\n_utc_text = _serialization.utc_text\n_validate_request = _validation.validate_request\n_validate_table_name = _validation.validate_table_name\n",
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/collection/sources/sead/acquisition/full/reconciliation.py": (
        5264,
        "61a024bfd8fe8977c57c9b9ef7a73fa7ede9c5d9e848ba96e41c3a53efc46e0f",
        (
            (
                b"from __future__ import annotations\n",
                b'"""Reconcile source rows through their declared child primary-key identities."""\n\nfrom __future__ import annotations\n',
            ),
            (
                b'\n\ndef child_identity_for(row: Mapping[str, object], index: int) -> str:\n    for key in sorted(row):\n        if key.endswith("_id") and row.get(key) is not None:\n            return f"{key}:{row[key]}"\n    return f"row:{index}"\n\n\ndef _null_positions(values: list[object]) -> list[str]:\n    return [f"row:{index}" for index, value in enumerate(values) if value is None]\n',
                b'\n\ndef _null_positions(values: list[object]) -> list[str]:\n    return [f"row:{index}" for index, value in enumerate(values) if value is None]\n',
            ),
            (
                b"    matched_count = 0\n    for index, row in enumerate(rows):\n        key_values.append(row.get(child_key))\n        foreign_key = row.get(child_foreign_key)\n        identity = child_identity_for(row, index)\n        if foreign_key is None:\n            null_foreign_keys.append(identity)\n",
                b'    matched_count = 0\n    for index, row in enumerate(rows):\n        child_id = row.get(child_key)\n        key_values.append(child_id)\n        foreign_key = row.get(child_foreign_key)\n        # A foreign or unrelated key cannot stand in for the declared child PK.\n        identity = f"{child_key}:{child_id}" if child_id is not None else f"row:{index}"\n        if foreign_key is None:\n            null_foreign_keys.append(identity)\n',
            ),
        ),
    ),
}
SEAD_JOIN_IDENTITY_SOURCES = frozenset(_JOIN_IDENTITY_CONTRACTS)
_JOIN_IDENTITY_CONTEXTS = {
    "data/method-certification/author-optimizer-diagnostic-source-capture": (
        "f865795aac7585e56c4cf44faac84496d339e1c176fc6ee111cba3cbc9b4ce93",
        "executions/optimizer-diagnostics/first-party-inputs/",
    ),
    "data/atlas/sample-chronology-source-view-capture": (
        "2491a59a0d5cde5dffd05397c4a7dcc95ab98ba922019863e5ea2662681dba62",
        "source/",
    ),
}


def declared_join_identity_extension_matches(
    name: str, captured: bytes, current: bytes
) -> bool:
    """Reconstruct every original byte after the fixed child-key label changes."""
    contract = _JOIN_IDENTITY_CONTRACTS.get(name)
    if contract is None:
        return False
    size, checksum, pairs = contract
    if (
        len(captured) != size
        or hashlib.sha256(captured).hexdigest() != checksum
        or not 0 < len(current) <= 16 * 1024
    ):
        return False
    restored = current
    for previous, inserted in pairs:
        if captured.count(previous) != 1 or restored.count(inserted) != 1:
            return False
        restored = restored.replace(inserted, previous, 1)
    return restored == captured


def validated_declared_join_identity_source(
    repository: Path, historical: JsonObject, logical: str, source_buffer: SourceCapsule
) -> JsonObject:
    """Authenticate changed diagnostic labels in two fixed original source contexts."""
    name = historical.get("path")
    contract = _JOIN_IDENTITY_CONTRACTS.get(name) if isinstance(name, str) else None
    context = _JOIN_IDENTITY_CONTEXTS.get(source_buffer.prefix)
    if contract is None or context is None or not isinstance(name, str):
        raise ReportRebuildError(
            "Declared join identity source is outside its fixed scope"
        )
    size, checksum, _ = contract
    expected = {"bytes": size, "sha256": checksum}
    if (
        repository != repository.resolve()
        or source_buffer.repository != repository
        or source_buffer.descriptor.capture.get("sha256") != context[0]
        or set(historical) != {"path", "bytes", "sha256"}
        or type(historical.get("bytes")) is not int
        or historical != {"path": name, **expected}
        or logical != context[1] + name
        or logical not in source_buffer.detached
        or source_buffer.descriptor.members.get(logical) != expected
        or [
            path
            for group in source_buffer.descriptor.groups
            for original, path in group["resolved_paths"]
            if original == logical
        ]
        != [name]
    ):
        raise ReportRebuildError("Declared join identity source binding differs")
    source_buffer.fresh()
    captured = source_buffer.read_source(logical)
    path = _regular_confined_file(repository, name, "current declared join identity")
    before = path.stat()
    if before.st_nlink != 1 or not 0 < before.st_size <= 16 * 1024:
        raise ReportRebuildError(
            "Declared join identity must be bounded and single-link"
        )
    current = path.read_bytes()
    if not declared_join_identity_extension_matches(name, captured, current):
        raise ReportRebuildError(
            "Declared join identity differs beyond its fixed label changes"
        )
    source_buffer.fresh()
    again = _regular_confined_file(repository, name, "current declared join identity")
    after = again.stat()
    fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    if (
        any(getattr(before, field) != getattr(after, field) for field in fields)
        or again.read_bytes() != current
    ):
        raise ReportRebuildError("Declared join identity changed during correspondence")
    return {
        "path": name,
        "classification": "declared_child_key_refusal_identity",
        "original_member": logical,
        "original_bytes": size,
        "original_sha256": checksum,
        "whole_old_module_reconstructed": True,
        "all_other_old_source_bytes_exact": True,
        "current_regular_single_link_and_stable": True,
        "current_join_refusal_labels_intentionally_changed": True,
        "old_count_status_and_refusal_predicates_unchanged": True,
        "private_alias_removed_public_exports_unchanged": True,
        "old_native_equal_current_join_output_claimed": False,
        "new_acquisition_or_native_execution_claimed": False,
    }
