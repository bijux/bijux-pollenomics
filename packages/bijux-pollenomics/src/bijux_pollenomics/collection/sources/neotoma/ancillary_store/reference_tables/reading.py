"""Read and assess the selected original buffer once without replaying its sibling."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from ...capture.reference_tables.models import (
    DEFAULT_REFERENCE_LIMITS,
    REFERENCE_TABLES,
)
from ...capture.reference_tables.protocol import assess_http, request_for
from ...capture.resources.replay import _same_json
from .metadata import pinned, read_neotoma_reference_archive_inventory


def _selected(
    directory: Path, anchor: str, table: str, *, complete: bool
) -> dict[str, Any]:
    if not isinstance(table, str) or table not in REFERENCE_TABLES:
        raise ValueError("Reference archive table selector is unsupported")
    inventory = read_neotoma_reference_archive_inventory(
        directory, expected_manifest_sha256=anchor
    )
    rows = [row for row in inventory.index["tables"] if row["table"] == table]
    if len(rows) != 1:
        raise ValueError("Selected reference table is not in this source capture")
    row = rows[0]
    if (
        complete
        and row["terminal_status"] != "received_complete_unqualified_reference_table"
    ):
        raise ValueError("Selected complete reference source table is unavailable")
    source = row["source"]
    if not source or "body_path" not in source:
        raise ValueError("Selected reference source has no retained HTTP entity")
    path = source["body_path"]
    body = pinned(
        Path(directory) / path,
        inventory.manifest["files"][path],
        DEFAULT_REFERENCE_LIMITS.max_response_bytes + 1,
    )
    assessed = assess_http(
        source["receipt"],
        request_for(table),
        body,
        DEFAULT_REFERENCE_LIMITS.max_response_bytes,
    )
    if any(not _same_json(row.get(k), v) for k, v in assessed.items()):
        raise ValueError("Selected reference source assessment differs")
    return {
        "table": table,
        "content_version": "current",
        "api_version": "v2.0",
        "native_body": body,
        "body_sha256": sha256(body).hexdigest(),
        "receipt_sha256": source["receipt_sha256"],
        "capture_manifest_sha256": inventory.manifest["capture_manifest_sha256"],
        "source_terminal_status": row["terminal_status"],
        "body_complete": source["receipt"]["body_complete"],
        "http_status": source["receipt"]["http_status"],
        "table_population_complete": False,
        "scientific_admission": "not_asserted",
        "archive": {
            "manifest_sha256": anchor,
            "integrity_scope": "archive_metadata_and_selected_reference_entity",
            "unselected_source_bodies_verified": False,
        },
    }


def read_neotoma_reference_archive_table(
    directory: Path, *, expected_manifest_sha256: str, table: str
) -> dict[str, Any]:
    """Return one complete source prefix; dictionary schema and meaning stay unqualified."""
    return _selected(directory, expected_manifest_sha256, table, complete=True)


def read_neotoma_reference_archive_entity(
    directory: Path, *, expected_manifest_sha256: str, table: str
) -> dict[str, Any]:
    """Retain the exact selected HTTP entity, including explicitly refused prefixes."""
    return _selected(directory, expected_manifest_sha256, table, complete=False)
