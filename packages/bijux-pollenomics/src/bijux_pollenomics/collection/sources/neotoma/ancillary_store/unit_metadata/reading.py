"""Selected unit entities use their original ledger bound and one authenticated buffer."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from ...capture.resources.models import DEFAULT_RESOURCE_LIMITS, NeotomaResourceLimits
from ...capture.unit_resources.assessment import assess_http
from ...capture.unit_resources.profiles import (
    parse_neotoma_unit_source,
    summarize_unit_source,
)
from ...capture.unit_resources.protocol import request_for
from ...client import positive_native_id
from ...resource_catalogue.source_projection import _same
from .metadata import (
    UnitMetadataInventory,
    pinned,
    read_neotoma_unit_metadata_inventory,
)


def response_bound(
    inventory: UnitMetadataInventory,
    selected: dict[str, Any],
    ordinal: int,
    limits: NeotomaResourceLimits,
) -> int:
    """Apply min(recorded,caller,default) to this capture prefix, not aggregate SDK I/O."""
    recorded = inventory.source.limits
    effective: dict[str, int] = {
        key: min(
            getattr(recorded, key),
            getattr(limits, key),
            getattr(DEFAULT_RESOURCE_LIMITS, key),
        )
        for key in (
            "max_requests",
            "max_attempts",
            "max_response_bytes",
            "max_total_bytes",
        )
    }
    count = total = 0
    for entry in inventory.source.document["units"]:
        for index, ref in enumerate(entry["attempts"], 1):
            count += 1
            if (
                count > effective["max_requests"]
                or index > effective["max_attempts"]
                or total >= effective["max_total_bytes"]
            ):
                raise ValueError("Selected unit attempt exceeds its capture budget")
            bound = min(
                effective["max_response_bytes"], effective["max_total_bytes"] - total
            )
            record = inventory.source.receipts[ref["request_name"]]
            size = record.get("retained_body_bytes", 0)
            if size > bound + int(not record["body_complete"]):
                raise ValueError(
                    "Selected unit entity exceeds remaining capture byte budget"
                )
            if entry is selected and index == ordinal:
                return bound
            total += size
    raise ValueError("Selected unit source attempt is absent")


def guard_all_bodies(
    inventory: UnitMetadataInventory, limits: NeotomaResourceLimits
) -> None:
    """Refuse all metadata-known restrictions before the first full-replay entity read."""
    for entry in inventory.source.document["units"]:
        if any("body_file" in ref for ref in entry["attempts"]):
            inventory.scopes.guard(entry["identity"]["collection_unit_id"])
    for entry in inventory.source.document["units"]:
        for ordinal in range(1, len(entry["attempts"]) + 1):
            response_bound(inventory, entry, ordinal, limits)


def _selected(
    directory: Path,
    *,
    collection_unit_id: int,
    expected_manifest_sha256: str,
    context_directory: Path,
    expected_context_sha256: str,
    native_archive_directory: Path,
    expected_native_archive_sha256: str,
    limits: NeotomaResourceLimits,
) -> tuple[dict[str, Any], dict[str, Any]]:
    unit_id = positive_native_id(collection_unit_id)
    inventory = read_neotoma_unit_metadata_inventory(
        directory,
        expected_manifest_sha256=expected_manifest_sha256,
        context_directory=context_directory,
        expected_context_sha256=expected_context_sha256,
        native_archive_directory=native_archive_directory,
        expected_native_archive_sha256=expected_native_archive_sha256,
        limits=limits,
    )
    selected = [
        row
        for row in inventory.source.document["units"]
        if row["identity"]["collection_unit_id"] == unit_id
    ]
    if len(selected) != 1:
        raise ValueError("Selected unit identity is absent or ambiguous")
    entry = selected[0]
    inventory.scopes.guard(unit_id)
    if not entry["attempts"] or "body_file" not in entry["attempts"][-1]:
        raise ValueError("Selected unit source has no retained HTTP entity")
    reference = entry["attempts"][-1]
    record = inventory.source.receipts[reference["request_name"]]
    bound = response_bound(inventory, entry, len(entry["attempts"]), limits)
    relative = "capture/" + reference["body_file"]
    body = pinned(
        inventory.root / relative,
        inventory.manifest["files"][relative],
        bound + int(not record["body_complete"]),
    )
    assessed = assess_http(
        record, request_for(entry["identity"], len(entry["attempts"])), body, bound
    )
    if not _same({key: entry.get(key) for key in assessed}, assessed):
        raise ValueError("Selected unit actual source assessment differs")
    return {
        "unit_key": entry["unit_key"],
        "collection_unit_id": unit_id,
        "body": body,
        "body_sha256": sha256(body).hexdigest(),
        "receipt_sha256": reference["receipt_sha256"],
        "capture_manifest_sha256": inventory.manifest["capture_manifest_sha256"],
        "original_roster_sha256": inventory.manifest["original_roster_sha256"],
        "current_roster_sha256": inventory.manifest["current_roster_sha256"],
        "terminal_status": entry["terminal_status"],
        "body_complete": record["body_complete"],
        "http_status": record["http_status"],
        "current_scope": inventory.scopes.account(unit_id),
        "integrity_scope": "archive_metadata_original_and_current_scope_and_selected_unit_entity",
        "unselected_source_bodies_verified": False,
        "source_capture_history_replayed": False,
        "related_resource_graph_complete": False,
        "period_basin_geometry_established": False,
        "scientific_admission": "not_asserted",
    }, entry["identity"]


def read_neotoma_unit_metadata_entity(
    directory: Path,
    *,
    collection_unit_id: int,
    expected_manifest_sha256: str,
    context_directory: Path,
    expected_context_sha256: str,
    native_archive_directory: Path,
    expected_native_archive_sha256: str,
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
) -> dict[str, Any]:
    """Return exact forensic bytes, including retained unavailable/refused HTTP entities."""
    return _selected(
        directory,
        collection_unit_id=collection_unit_id,
        expected_manifest_sha256=expected_manifest_sha256,
        context_directory=context_directory,
        expected_context_sha256=expected_context_sha256,
        native_archive_directory=native_archive_directory,
        expected_native_archive_sha256=expected_native_archive_sha256,
        limits=limits,
    )[0]


def read_neotoma_unit_metadata(
    directory: Path,
    *,
    collection_unit_id: int,
    expected_manifest_sha256: str,
    context_directory: Path,
    expected_context_sha256: str,
    native_archive_directory: Path,
    expected_native_archive_sha256: str,
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
) -> dict[str, Any]:
    """Qualify the same selected source buffer; infer no physical or scientific support."""
    result, scope = _selected(
        directory,
        collection_unit_id=collection_unit_id,
        expected_manifest_sha256=expected_manifest_sha256,
        context_directory=context_directory,
        expected_context_sha256=expected_context_sha256,
        native_archive_directory=native_archive_directory,
        expected_native_archive_sha256=expected_native_archive_sha256,
        limits=limits,
    )
    if result["terminal_status"] != "received_complete_unqualified_unit_resource":
        raise ValueError(
            "Typed unit metadata requires a complete successful source entity"
        )
    parsed = parse_neotoma_unit_source(
        scope, result["body"], expected_body_sha256=result["body_sha256"]
    )
    return {
        **result,
        "source_payload": parsed.payload,
        "source_records": parsed.records,
        "summary": summarize_unit_source(parsed),
    }
