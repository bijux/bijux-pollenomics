"""Authenticate reference capture declarations without opening table entities."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import validate_regular_namespace

from ...capture.receipts import (
    _object,
    _read,
    _request_record,
    _safe_root,
    _utc,
    _validate_transport_failure,
)
from ...capture.reference_tables.models import DEFAULT_REFERENCE_LIMITS, METADATA_SCOPE
from ...capture.reference_tables.protocol import request_for
from ...capture.reference_tables.replay import SNAPSHOT_CONSISTENCY, _control
from ...capture.resources.replay import _same_json
from ...resource_catalogue.archive.files import _digest, _member, encoded_json

SCHEMA = "neotoma-reference-table-source-archive.v1"
INDEX_SCHEMA = "neotoma-reference-table-source-index.v1"
MAX_BYTES = 16 * 1024 * 1024
MAX_METADATA = 4 * 1024 * 1024
MAX_FILES = 16
_FIELDS = {
    "schema_version",
    "capture_manifest_sha256",
    "files",
    "source_bytes",
    "scientific_admission",
    "metadata_scope",
    "table_population_complete",
    "historical_snapshot_replaced",
}
_ENTRY = {
    "table",
    "content_version",
    "api_version",
    "metadata_role",
    "attempts",
    "scientific_admission",
}
_SUMMARY: dict[str, Any] = {
    "schema_qualified": False,
    "prefix_limit": 10000,
    "prefix_offset": 0,
    "table_population_complete": False,
    "absence_certified": False,
    "units_interpreted": False,
}


@dataclass(frozen=True)
class NeotomaReferenceArchiveInventory:
    """Authenticated metadata does not certify any retained reference entity."""

    manifest: dict[str, Any]
    index: dict[str, Any]
    integrity_scope: str = field(default="archive_and_reference_metadata", init=False)
    source_entity_bodies_verified: bool = field(default=False, init=False)
    source_assessments_replayed: bool = field(default=False, init=False)


def pinned(path: Path, member: dict[str, Any], bound: int) -> bytes:
    raw = _read(path, bound)
    if len(raw) != member["bytes"] or sha256(raw).hexdigest() != member["sha256"]:
        raise ValueError("Reference archive member identity differs")
    return raw


def source_index(
    root: Path, capture_digest: str, files: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Bind source rows and receipts; retain source assessment as an unverified claim."""
    manifest, plan, limits, digest = _control(root, capture_digest)
    entries = manifest["tables"]
    if not isinstance(entries, list) or len(entries) != len(plan.tables):
        raise ValueError("Reference archive source table population differs")
    names = {"capture/capture-manifest.json", "capture/request-plan.json"}
    start, end = _utc(manifest["capture_utc_start"]), _utc(manifest["capture_utc_end"])
    if start > end:
        raise ValueError("Reference archive source timestamps are reversed")
    rows, requests, total = [], 0, 0
    total_limit = min(limits.max_total_bytes, DEFAULT_REFERENCE_LIMITS.max_total_bytes)
    request_limit = min(limits.max_requests, DEFAULT_REFERENCE_LIMITS.max_requests)
    for entry, table in zip(entries, plan.tables, strict=True):
        if (
            not isinstance(entry, dict)
            or entry.get("table") != table
            or entry.get("metadata_role") != "reference_metadata"
            or entry.get("content_version") != "current"
            or entry.get("api_version") != "v2.0"
            or entry.get("scientific_admission") != "not_asserted"
            or not isinstance(entry.get("attempts"), list)
            or len(entry["attempts"]) > 1
        ):
            raise ValueError("Reference archive source table identity differs")
        row = dict(entry)
        row["source"] = None
        assessed: dict[str, Any]
        if not entry["attempts"]:
            assessed = {"terminal_status": "not_attempted_budget"}
        else:
            if requests >= request_limit or total >= total_limit:
                raise ValueError("Reference archive attempt exceeds its source budget")
            body_bound = min(
                limits.max_response_bytes,
                DEFAULT_REFERENCE_LIMITS.max_response_bytes,
                total_limit - total,
            )
            requests += 1
            ref = entry["attempts"][0]
            request = request_for(table)
            receipt_name = f"{request.name}.receipt.json"
            path = "capture/" + receipt_name
            if (
                not isinstance(ref, dict)
                or ref.get("request_name") != request.name
                or ref.get("receipt_file") != receipt_name
                or not _digest(ref.get("receipt_sha256"))
                or path not in files
                or files[path]["sha256"] != ref["receipt_sha256"]
            ):
                raise ValueError("Reference archive receipt identity differs")
            names.add(path)
            record = _object(pinned(root / receipt_name, files[path], 1024 * 1024))
            baseline = _request_record(request, record.get("utc_start", ""))
            if any(not _same_json(record.get(k), v) for k, v in baseline.items()):
                raise ValueError("Reference archive request binding differs")
            opened, finished = (
                _utc(record.get("utc_start")),
                _utc(record.get("utc_end")),
            )
            if opened < start or finished < opened or finished > end:
                raise ValueError("Reference archive receipt epoch differs")
            start = finished
            row["source"] = {
                "receipt_path": path,
                "receipt_sha256": ref["receipt_sha256"],
                "receipt": record,
            }
            if record.get("terminal_status") == "transport_failure":
                if set(ref) != {
                    "request_name",
                    "receipt_file",
                    "receipt_sha256",
                } or set(record) != set(baseline) | {
                    "utc_end",
                    "terminal_status",
                    "error",
                    "body_complete",
                }:
                    raise ValueError("Reference archive transport pointer differs")
                _validate_transport_failure(record, request)
                assessed = {
                    "terminal_status": "transport_failure",
                    "reason": record["error"],
                }
            else:
                body_name = f"{request.name}.body"
                body_path = "capture/" + body_name
                status, complete, size = (
                    record.get("http_status"),
                    record.get("body_complete"),
                    record.get("retained_body_bytes"),
                )
                headers = record.get("response_headers")
                if (
                    set(ref)
                    != {"request_name", "receipt_file", "receipt_sha256", "body_file"}
                    or set(record)
                    != set(baseline)
                    | {
                        "utc_end",
                        "final_url",
                        "http_status",
                        "response_headers",
                        "body_file",
                        "body_complete",
                        "retained_body_bytes",
                        "retained_body_sha256",
                        "terminal_status",
                    }
                    or ref["body_file"] != body_name
                    or record.get("body_file") != body_name
                    or record.get("final_url") != request.url
                    or type(status) is not int
                    or not 100 <= status <= 599
                    or type(complete) is not bool
                    or type(size) is not int
                    or size < 0
                    or size > body_bound + int(not complete)
                    or body_path not in files
                    or files[body_path]
                    != {"bytes": size, "sha256": record.get("retained_body_sha256")}
                    or record.get("terminal_status")
                    != (
                        "complete_http_200"
                        if status == 200 and complete
                        else "refused_http_response"
                    )
                    or not isinstance(headers, list)
                    or any(
                        not isinstance(pair, list)
                        or len(pair) != 2
                        or any(not isinstance(value, str) for value in pair)
                        for pair in headers
                    )
                ):
                    raise ValueError(
                        "Reference archive HTTP entity declaration differs"
                    )
                if complete and any(
                    name.lower() == "content-length" and int(value) != size
                    for name, value in headers
                ):
                    raise ValueError("Reference archive HTTP content length differs")
                names.add(body_path)
                total += size
                row["source"].update(body_path=body_path)
                if status != 200:
                    assessed = {
                        "terminal_status": "unavailable_http",
                        "http_status": status,
                        "absence_certified": False,
                    }
                elif not complete:
                    assessed = {
                        "terminal_status": "refused_incomplete_body",
                        "reason": "Incomplete or bounded reference entity",
                    }
                elif (
                    entry.get("terminal_status")
                    == "received_complete_unqualified_reference_table"
                ):
                    assessed = {
                        "terminal_status": entry["terminal_status"],
                        "summary": _SUMMARY,
                    }
                elif entry.get("terminal_status") in {
                    "refused_http_receipt",
                    "refused_native_json",
                } and isinstance(entry.get("reason"), str):
                    assessed = {
                        "terminal_status": entry["terminal_status"],
                        "reason": entry["reason"],
                    }
                else:
                    raise ValueError(
                        "Reference archive source assessment contradicts its receipt"
                    )
        if set(entry) != _ENTRY | set(assessed) or any(
            not _same_json(entry.get(k), v) for k, v in assessed.items()
        ):
            raise ValueError("Reference archive source assessment metadata differs")
        rows.append(row)
    if (
        requests > request_limit
        or type(manifest["request_count"]) is not int
        or manifest["request_count"] != requests
        or type(manifest["response_bytes"]) is not int
        or manifest["response_bytes"] != total
        or not _same_json(
            manifest["partitions"],
            dict(Counter(row["terminal_status"] for row in entries)),
        )
        or set(files) != names | {"index.json"}
    ):
        raise ValueError("Reference archive source count or namespace differs")
    return {
        "schema_version": INDEX_SCHEMA,
        "capture_manifest_sha256": digest,
        "metadata_scope": METADATA_SCOPE,
        "snapshot_consistency": SNAPSHOT_CONSISTENCY,
        "tables": rows,
        "scientific_admission": "not_asserted",
    }


def read_neotoma_reference_archive_inventory(
    directory: Path, *, expected_manifest_sha256: str
) -> NeotomaReferenceArchiveInventory:
    """Check the complete closed namespace and metadata, without reading entity bodies."""
    root = _safe_root(directory)
    raw = _read(root / "manifest.json", MAX_METADATA)
    if (
        not _digest(expected_manifest_sha256)
        or sha256(raw).hexdigest() != expected_manifest_sha256
    ):
        raise ValueError("Reference archive manifest anchor differs")
    manifest = _object(raw)
    if (
        set(manifest) != _FIELDS
        or manifest["schema_version"] != SCHEMA
        or not _digest(manifest["capture_manifest_sha256"])
        or manifest["scientific_admission"] != "not_asserted"
        or manifest["metadata_scope"] != METADATA_SCOPE
        or manifest["table_population_complete"] is not False
        or manifest["historical_snapshot_replaced"] is not False
        or not isinstance(manifest["files"], dict)
        or type(manifest["source_bytes"]) is not int
    ):
        raise ValueError("Reference archive manifest scope differs")
    files = manifest["files"]
    total = 0
    for name, member in files.items():
        _member(name)
        if (
            name == "manifest.json"
            or not isinstance(member, dict)
            or set(member) != {"bytes", "sha256"}
            or type(member["bytes"]) is not int
            or not 0 <= member["bytes"] <= MAX_METADATA
            or not _digest(member["sha256"])
        ):
            raise ValueError("Reference archive member declaration is invalid")
        total += member["bytes"]
    if total != manifest["source_bytes"] or total + len(raw) > MAX_BYTES:
        raise ValueError("Reference archive byte population differs")
    sizes = validate_regular_namespace(
        root, {"manifest.json", *files}, max_files=MAX_FILES, max_bytes=MAX_BYTES
    )
    for name, member in files.items():
        if sizes[name] != member["bytes"]:
            raise ValueError("Reference archive member size differs")
        if not name.endswith(".body"):
            pinned(root / name, member, MAX_METADATA)
    index = source_index(root / "capture", manifest["capture_manifest_sha256"], files)
    if pinned(root / "index.json", files["index.json"], MAX_METADATA) != encoded_json(
        index
    ):
        raise ValueError("Reference archive index correspondence differs")
    return NeotomaReferenceArchiveInventory(manifest, index)
