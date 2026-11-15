"""Read-only request, response and population verification for captured metadata."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from .models import (
    _SCHEMA,
    DEFAULT_METADATA_LIMITS,
    NeotomaMetadataCapture,
    NeotomaMetadataLimits,
    _Request,
)
from .protocol import _plan_from_spec, _validate_plan, _walk_plan
from .receipts import _object, _read, _safe_root, _utc, _validate_receipt


def replay_neotoma_metadata_capture(
    directory: Path,
    *,
    expected_manifest_sha256: str | None = None,
    limits: NeotomaMetadataLimits = DEFAULT_METADATA_LIMITS,
) -> NeotomaMetadataCapture:
    """Verify exact request/body closure and native metadata without network access."""
    root = _safe_root(directory)
    manifest_bytes = _read(root / "capture-manifest.json", 1024 * 1024)
    digest = sha256(manifest_bytes).hexdigest()
    if expected_manifest_sha256 is not None and digest != expected_manifest_sha256:
        raise ValueError("Neotoma metadata manifest identity differs")
    manifest = _object(manifest_bytes)
    if (
        manifest.get("schema_version") != _SCHEMA
        or manifest.get("status") != "complete"
        or manifest.get("plan_file") != "request-plan.json"
    ):
        raise ValueError("Neotoma metadata capture is incomplete or unsupported")
    plan_bytes = _read(root / "request-plan.json", 100000)
    if sha256(plan_bytes).hexdigest() != manifest.get("plan_sha256"):
        raise ValueError("Neotoma metadata request-plan identity differs")
    spec = _object(plan_bytes)
    if (
        spec.get("schema_version") != _SCHEMA
        or spec.get("historical_capture_replaced") is not False
    ):
        raise ValueError("Neotoma metadata source role differs")
    plan, recorded_limits = _plan_from_spec(spec)
    _validate_plan(plan, limits)
    records = manifest.get("records")
    if not isinstance(records, list) or len(records) > min(
        limits.max_requests, recorded_limits.max_requests
    ):
        raise ValueError("Neotoma metadata request population exceeds its limit")
    cursor = 0
    total = 0
    files = {"capture-manifest.json", "request-plan.json"}
    capture_start, capture_end = (
        _utc(manifest.get(name)) for name in ("capture_utc_start", "capture_utc_end")
    )
    if capture_start > capture_end:
        raise ValueError("Neotoma capture timestamps are reversed")
    previous_request_end = capture_start

    def consume(request: _Request) -> bytes:
        nonlocal cursor, total, previous_request_end
        if cursor >= len(records):
            raise ValueError("Neotoma metadata request closure is incomplete")
        reference = records[cursor]
        if not isinstance(reference, dict) or set(reference) != {
            "request_name",
            "receipt_file",
            "receipt_sha256",
        }:
            raise ValueError(
                "Neotoma metadata request reference is not its exact record object"
            )
        receipt_name = f"{request.name}.receipt.json"
        body_name = f"{request.name}.body"
        if (
            reference.get("request_name") != request.name
            or reference.get("receipt_file") != receipt_name
        ):
            raise ValueError("Neotoma metadata request ordering or identity differs")
        receipt_bytes = _read(root / receipt_name, 65536)
        if sha256(receipt_bytes).hexdigest() != reference.get("receipt_sha256"):
            raise ValueError("Neotoma metadata receipt identity differs")
        record = _object(receipt_bytes)
        if record.get("body_file") != body_name:
            raise ValueError("Neotoma metadata body path identity differs")
        bound = min(limits.max_response_bytes, recorded_limits.max_response_bytes)
        body = _read(root / body_name, bound)
        _validate_receipt(record, request, body, bound)
        if (
            not previous_request_end
            <= _utc(record["utc_start"])
            <= _utc(record["utc_end"])
            <= capture_end
        ):
            raise ValueError("Neotoma request time is outside its capture")
        previous_request_end = _utc(record["utc_end"])
        total += len(body)
        if total > min(limits.max_total_bytes, recorded_limits.max_total_bytes):
            raise ValueError("Neotoma metadata total-byte budget exceeded")
        cursor += 1
        files.update((receipt_name, body_name))
        return body

    effective_limits = replace(
        recorded_limits,
        max_pages_per_inventory=min(
            limits.max_pages_per_inventory, recorded_limits.max_pages_per_inventory
        ),
    )
    inventories, sites, datasets = _walk_plan(plan, effective_limits, consume)
    if (
        cursor != len(records)
        or manifest.get("request_count") != cursor
        or manifest.get("response_bytes") != total
    ):
        raise ValueError("Neotoma metadata aggregate request closure differs")
    if {path.name for path in root.iterdir()} != files:
        raise ValueError("Neotoma metadata capture contains unmanifested files")
    return NeotomaMetadataCapture(
        digest, inventories, sites, cursor, total, dataset_responses=datasets
    )
