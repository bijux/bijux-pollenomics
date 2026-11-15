"""Authenticate exact reference-table prefixes and the actual returned buffers."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Any

from ..receipts import (
    _object,
    _read,
    _request_record,
    _safe_root,
    _utc,
    _validate_receipt,
    _validate_transport_failure,
)
from ..resources.models import NeotomaResourceLimits
from ..resources.replay import _same_json
from .models import (
    DEFAULT_REFERENCE_LIMITS,
    METADATA_SCOPE,
    POLICY_SOURCES,
    REFERENCE_SCHEMA,
    REFERENCE_TABLES,
    NeotomaReferenceTableBody,
    NeotomaReferenceTableCapture,
    NeotomaReferenceTablePlan,
)
from .protocol import assess_http, plan_from_json, request_for, validate_plan

SNAPSHOT_CONSISTENCY = "individually timed current reference prefixes; no complete dictionary or transaction claim"
_ENTRY = {
    "table",
    "content_version",
    "api_version",
    "metadata_role",
    "attempts",
    "scientific_admission",
}


def _control(
    root: Path, expected: str | None
) -> tuple[dict[str, Any], NeotomaReferenceTablePlan, NeotomaResourceLimits, str]:
    content = _read(root / "capture-manifest.json", 4 * 1024 * 1024)
    digest = sha256(content).hexdigest()
    if expected is not None and digest != expected:
        raise ValueError("Neotoma reference manifest identity differs")
    manifest = _object(content)
    if (
        set(manifest)
        != {
            "schema_version",
            "status",
            "capture_utc_start",
            "capture_utc_end",
            "plan_sha256",
            "tables",
            "request_count",
            "response_bytes",
            "partitions",
            "metadata_scope",
            "snapshot_consistency",
            "scientific_admission",
        }
        or manifest["schema_version"] != REFERENCE_SCHEMA
        or manifest["status"] != "closed"
        or manifest["metadata_scope"] != METADATA_SCOPE
        or manifest["snapshot_consistency"] != SNAPSHOT_CONSISTENCY
        or manifest["scientific_admission"] != "not_asserted"
    ):
        raise ValueError("Neotoma reference manifest fields or scope differ")
    content = _read(root / "request-plan.json", 1024 * 1024)
    if sha256(content).hexdigest() != manifest["plan_sha256"]:
        raise ValueError("Neotoma reference plan identity differs")
    control = _object(content)
    if (
        set(control)
        != {"schema_version", "plan", "limits", "metadata_scope", "policy_sources"}
        or control["schema_version"] != REFERENCE_SCHEMA
        or control["metadata_scope"] != METADATA_SCOPE
        or not _same_json(control["policy_sources"], list(POLICY_SOURCES))
    ):
        raise ValueError("Neotoma reference control fields or scope differ")
    plan, recorded = plan_from_json(control)
    return manifest, plan, recorded, digest


def replay_neotoma_reference_tables(
    directory: Path,
    *,
    expected_manifest_sha256: str | None = None,
    limits: NeotomaResourceLimits = DEFAULT_REFERENCE_LIMITS,
) -> NeotomaReferenceTableCapture:
    """Verify closed prefixes; native dictionary keys and completeness stay unqualified."""
    root = _safe_root(directory)
    manifest, plan, recorded, digest = _control(root, expected_manifest_sha256)
    validate_plan(plan, limits)
    entries = manifest["tables"]
    if not isinstance(entries, list) or len(entries) != len(plan.tables):
        raise ValueError("Neotoma reference table population differs")
    maximum_requests = min(limits.max_requests, recorded.max_requests)
    maximum_body = min(limits.max_response_bytes, recorded.max_response_bytes)
    maximum_total = min(limits.max_total_bytes, recorded.max_total_bytes)
    count = total = 0
    previous_end, end = (
        _utc(manifest["capture_utc_start"]),
        _utc(manifest["capture_utc_end"]),
    )
    if previous_end > end:
        raise ValueError("Neotoma reference capture timestamps are reversed")
    files = {"capture-manifest.json", "request-plan.json"}
    for entry, table in zip(entries, plan.tables, strict=True):
        if (
            not isinstance(entry, dict)
            or entry.get("table") != table
            or entry.get("content_version") != "current"
            or entry.get("api_version") != "v2.0"
            or entry.get("metadata_role") != "reference_metadata"
            or entry.get("scientific_admission") != "not_asserted"
            or not isinstance(entry.get("attempts"), list)
            or len(entry["attempts"]) > 1
        ):
            raise ValueError("Neotoma reference table identity or attempts differ")
        assessed: dict[str, Any] = {"terminal_status": "not_attempted_budget"}
        if entry["attempts"]:
            count += 1
            if count > maximum_requests or total >= maximum_total:
                raise ValueError("Neotoma reference capture exceeds caller budget")
            reference = entry["attempts"][0]
            request = request_for(table)
            receipt_name = f"{request.name}.receipt.json"
            if (
                not isinstance(reference, dict)
                or reference.get("request_name") != request.name
                or reference.get("receipt_file") != receipt_name
            ):
                raise ValueError("Neotoma reference receipt pointer differs")
            content = _read(root / receipt_name, 1024 * 1024)
            if sha256(content).hexdigest() != reference.get("receipt_sha256"):
                raise ValueError("Neotoma reference receipt identity differs")
            record = _object(content)
            files.add(receipt_name)
            started, finished = (
                _utc(record.get("utc_start")),
                _utc(record.get("utc_end")),
            )
            if started < previous_end or finished < started or finished > end:
                raise ValueError("Neotoma reference request timestamps differ")
            previous_end = finished
            if record.get("terminal_status") == "transport_failure":
                if set(reference) != {
                    "request_name",
                    "receipt_file",
                    "receipt_sha256",
                } or set(record) != set(
                    _request_record(request, record["utc_start"])
                ) | {"utc_end", "terminal_status", "error", "body_complete"}:
                    raise ValueError("Neotoma reference transport fields differ")
                _validate_transport_failure(record, request)
                assessed = {
                    "terminal_status": "transport_failure",
                    "reason": record["error"],
                }
            else:
                name = f"{request.name}.body"
                if (
                    set(reference)
                    != {"request_name", "receipt_file", "receipt_sha256", "body_file"}
                    or reference["body_file"] != name
                    or record.get("body_file") != name
                ):
                    raise ValueError("Neotoma reference body pointer differs")
                bound = min(maximum_body, maximum_total - total)
                body = _read(root / name, bound + 1)
                assessed = assess_http(record, request, body, bound)
                total += len(body)
                files.add(name)
        if set(entry) != _ENTRY | set(assessed) or not _same_json(
            {key: entry[key] for key in assessed}, assessed
        ):
            raise ValueError("Neotoma reference derived source assessment differs")
    partitions = dict(Counter(row["terminal_status"] for row in entries))
    if (
        type(manifest["request_count"]) is not int
        or type(manifest["response_bytes"]) is not int
        or manifest["request_count"] != count
        or manifest["response_bytes"] != total
        or not _same_json(manifest["partitions"], partitions)
    ):
        raise ValueError("Neotoma reference denominator closure differs")
    if (
        any(path.is_symlink() or not path.is_file() for path in root.iterdir())
        or {path.name for path in root.iterdir()} != files
    ):
        raise ValueError("Neotoma reference file inventory differs")
    return NeotomaReferenceTableCapture(
        digest, tuple(entries), count, total, partitions
    )


def read_neotoma_reference_table_body(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    table: str,
    limits: NeotomaResourceLimits = DEFAULT_REFERENCE_LIMITS,
) -> NeotomaReferenceTableBody:
    """Gate the literal table before any source body, then hash the actual buffer."""
    if table not in REFERENCE_TABLES:
        raise ValueError("Neotoma reference table is unsupported")
    root = _safe_root(directory)
    _, plan, _, _ = _control(root, expected_manifest_sha256)
    if table not in plan.tables:
        raise ValueError("Neotoma reference table was not selected")
    captured = replay_neotoma_reference_tables(
        root, expected_manifest_sha256=expected_manifest_sha256, limits=limits
    )
    entry = next(row for row in captured.tables if row["table"] == table)
    if entry["terminal_status"] != "received_complete_unqualified_reference_table":
        raise ValueError("Neotoma complete reference source entity is unavailable")
    reference = entry["attempts"][0]
    content = _read(root / reference["receipt_file"], 1024 * 1024)
    if sha256(content).hexdigest() != reference["receipt_sha256"]:
        raise ValueError("Neotoma reference receipt changed during body access")
    record = _object(content)
    body = _read(root / reference["body_file"], limits.max_response_bytes)
    _validate_receipt(record, request_for(table), body, limits.max_response_bytes)
    return NeotomaReferenceTableBody(
        table, body, sha256(body).hexdigest(), reference["receipt_sha256"]
    )
