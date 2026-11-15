"""Body-free context metadata, closed source namespaces and immutable indexes."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import validate_regular_namespace

from ...capture.context_resources.models import (
    DEFAULT_CONTEXT_LIMITS,
    NeotomaContextResourcePlan,
)
from ...capture.context_resources.protocol import (
    digest,
    native_dataset_ids,
    request_for,
    validate_plan,
    verify_request_metadata,
)
from ...capture.context_resources.replay import _ENTRY, _control, _files
from ...capture.receipts import (
    _object,
    _read,
    _request_record,
    _safe_root,
    _utc,
    _validate_transport_failure,
)
from ...capture.resources.models import NeotomaResourceLimits
from ...capture.resources.replay import _same_json
from ...resource_catalogue.archive.files import _member, encoded_json
from .scope import ContextScopes, NeotomaContextArchiveBindings, prepare_scopes

SCHEMA = "neotoma-current-context-resource-archive.v1"
INDEX_SCHEMA = "neotoma-current-context-resource-index.v1"
MAX_BYTES = 512 * 1024 * 1024
MAX_FILES = 20_000
MAX_METADATA = 16 * 1024 * 1024


def pinned(path: Path, member: dict[str, Any], bound: int) -> bytes:
    path = _safe_root(path)
    if path.stat(follow_symlinks=False).st_size != member["bytes"]:
        raise ValueError("Context archive member physical size differs")
    raw = _read(path, min(member["bytes"], bound))
    if sha256(raw).hexdigest() != member["sha256"]:
        raise ValueError("Context archive member digest differs")
    return raw


@dataclass
class ContextSourceMetadata:
    document: dict[str, Any]
    control: dict[str, Any]
    plan: NeotomaContextResourcePlan
    limits: NeotomaResourceLimits
    files: dict[str, dict[str, Any]]
    buffers: dict[str, bytes]
    receipts: dict[str, dict[str, Any]]
    proof: dict[str, Any]


def source_request(entry: dict[str, Any], proof: dict[str, Any]) -> Any:
    """Reconstruct the original query from its authenticated whole-site owners."""
    kind, site = entry["resource_kind"], entry["site_id"]
    if kind == "dataset_depositional_environment":
        parents = [row for row in proof["requested_sites"] if row["site_id"] == site]
        if len(parents) != 1:
            raise ValueError("Context original native request parent is ambiguous")
        return request_for(kind, site, dataset_ids=native_dataset_ids(parents[0]))
    return request_for(kind, site)


def _receipt(
    record: dict[str, Any], request: Any, entry: dict[str, Any]
) -> dict[str, Any] | None:
    verify_request_metadata(record, request)
    baseline = set(_request_record(request, record.get("utc_start", "")))
    if record.get("terminal_status") == "transport_failure":
        if set(record) != baseline | {
            "utc_end",
            "terminal_status",
            "error",
            "body_complete",
        }:
            raise ValueError("Context source transport receipt fields differ")
        _validate_transport_failure(record, request)
        return {"terminal_status": "transport_failure", "reason": record["error"]}
    status, complete, size = (
        record.get("http_status"),
        record.get("body_complete"),
        record.get("retained_body_bytes"),
    )
    if (
        set(record)
        != baseline
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
        or record.get("final_url") != request.url
        or type(status) is not int
        or not 100 <= status <= 599
        or type(complete) is not bool
        or type(size) is not int
        or size < 0
        or record["terminal_status"]
        != (
            "complete_http_200"
            if status == 200 and complete
            else "refused_http_response"
        )
    ):
        raise ValueError("Context source HTTP transport declarations differ")
    digest(record.get("retained_body_sha256"))
    headers = record.get("response_headers")
    if not isinstance(headers, list) or any(
        not isinstance(pair, list)
        or len(pair) != 2
        or any(not isinstance(value, str) for value in pair)
        for pair in headers
    ):
        raise ValueError("Context source response headers are malformed")
    if status != 200:
        return {
            "terminal_status": "unavailable_http",
            "http_status": status,
            "absence_certified": False,
        }
    if not complete:
        return {
            "terminal_status": "refused_incomplete_body",
            "reason": "Incomplete or bounded context source entity",
        }
    if entry.get("terminal_status") == "received_complete_unqualified_context_resource":
        return {
            "terminal_status": entry["terminal_status"],
            "summary": {
                "schema_qualified": False,
                "native_payload_owner_verified": False,
                "dated_basin_geometry_admitted": False,
                "absence_certified": False,
                "scientific_admission": "not_asserted",
            },
        }
    if entry.get("terminal_status") in {
        "refused_http_receipt",
        "refused_native_json",
    } and isinstance(entry.get("reason"), str):
        return {"terminal_status": entry["terminal_status"], "reason": entry["reason"]}
    raise ValueError("Context source declared complete-entity assessment differs")


def source_metadata(directory: Path, expected: str) -> ContextSourceMetadata:
    digest(expected)
    root = _safe_root(directory)
    document, control, plan, limits, _ = _control(root, expected)
    entries = document["resources"]
    if not isinstance(entries, list):
        raise ValueError("Context source population differs")
    names = _files(entries, plan)
    sizes = validate_regular_namespace(
        root, names, max_files=MAX_FILES, max_bytes=MAX_BYTES
    )
    files: dict[str, dict[str, Any]] = {}
    buffers = {}
    receipts = {}
    for name, pin in (
        ("capture-manifest.json", expected),
        ("request-plan.json", document["plan_sha256"]),
        ("parent-scope.json", control["parent_scope_sha256"]),
    ):
        raw = _read(root / name, MAX_METADATA)
        if sha256(raw).hexdigest() != pin:
            raise ValueError("Context source metadata buffer differs")
        files["capture/" + name] = {"bytes": len(raw), "sha256": pin}
        buffers["capture/" + name] = raw
    proof = _object(buffers["capture/parent-scope.json"])
    parents = {row["site_id"]: row for row in proof["requested_sites"]}
    previous, end = (
        _utc(document["capture_utc_start"]),
        _utc(document["capture_utc_end"]),
    )
    if previous > end:
        raise ValueError("Context source capture timestamps are reversed")
    count = total = 0
    for entry in entries:
        parent = parents.get(entry["site_id"])
        if (
            parent is None
            or entry["scope_status"] != parent["scope_status"]
            or not _same_json(entry["exposure_role"], parent["effective_scope_role"])
        ):
            raise ValueError("Context original parent declaration differs")
        assessed: dict[str, Any] | None = {
            "terminal_status": "not_attempted_parent_scope"
            if entry["scope_status"] != "eligible_current_scope"
            else "not_attempted_budget"
        }
        for reference in entry["attempts"]:
            if entry["scope_status"] != "eligible_current_scope":
                raise ValueError(
                    "Original context protected scope forbids a source entity"
                )
            count += 1
            if count > limits.max_requests or total >= limits.max_total_bytes:
                raise ValueError(
                    "Context recorded source request/byte budget is contradictory"
                )
            request = source_request(entry, proof)
            name = reference["receipt_file"]
            raw = _read(root / name, 1024 * 1024)
            if sha256(raw).hexdigest() != reference["receipt_sha256"]:
                raise ValueError("Context source receipt digest differs")
            files["capture/" + name] = {
                "bytes": len(raw),
                "sha256": reference["receipt_sha256"],
            }
            buffers["capture/" + name] = raw
            record = _object(raw)
            receipts[request.name] = record
            start, finish = _utc(record.get("utc_start")), _utc(record.get("utc_end"))
            if not previous <= start <= finish <= end:
                raise ValueError("Context source receipt timing differs")
            previous = finish
            assessed = _receipt(record, request, entry)
            if "body_file" in reference:
                body_name = reference["body_file"]
                if record.get("body_file") != body_name or sizes.get(
                    body_name
                ) != record.get("retained_body_bytes"):
                    raise ValueError("Context source body declaration differs")
                files["capture/" + body_name] = {
                    "bytes": record["retained_body_bytes"],
                    "sha256": record["retained_body_sha256"],
                }
                bound = min(limits.max_response_bytes, limits.max_total_bytes - total)
                if record["retained_body_bytes"] > bound + int(
                    not record["body_complete"]
                ):
                    raise ValueError(
                        "Context recorded source body exceeds remaining budget"
                    )
                total += record["retained_body_bytes"]
            elif record.get("terminal_status") != "transport_failure":
                raise ValueError("Context HTTP entity lacks a body declaration")
        if (
            assessed is None
            or set(entry) != _ENTRY | set(assessed)
            or not _same_json({key: entry.get(key) for key in assessed}, assessed)
        ):
            raise ValueError("Context source outcome assessment fields differ")
    if (
        set(files) != {"capture/" + name for name in names}
        or type(document["request_count"]) is not int
        or document["request_count"] != count
        or type(document["response_bytes"]) is not int
        or document["response_bytes"] != total
        or not _same_json(
            document["partitions"],
            dict(Counter(row["terminal_status"] for row in entries)),
        )
    ):
        raise ValueError("Context source file or outcome denominator differs")
    return ContextSourceMetadata(
        document, control, plan, limits, files, buffers, receipts, proof
    )


def source_index(source: ContextSourceMetadata) -> dict[str, Any]:
    return {
        "schema_version": INDEX_SCHEMA,
        "resources": source.document["resources"],
        "capture_utc_start": source.document["capture_utc_start"],
        "capture_utc_end": source.document["capture_utc_end"],
        "request_count": source.document["request_count"],
        "response_bytes": source.document["response_bytes"],
        "partitions": source.document["partitions"],
        "native_profiles_verified": False,
        "numerical_payloads_in_index": False,
        "scientific_admission": "not_asserted",
    }


@dataclass(frozen=True)
class NeotomaContextResourceInventory:
    root: Path
    manifest: dict[str, Any]
    index: dict[str, Any]
    source: ContextSourceMetadata
    scopes: ContextScopes
    body_hashes_verified: bool = False
    native_profiles_verified: bool = False


def read_neotoma_context_resource_inventory(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    original: NeotomaContextArchiveBindings,
    current: NeotomaContextArchiveBindings,
    limits: NeotomaResourceLimits = DEFAULT_CONTEXT_LIMITS,
) -> NeotomaContextResourceInventory:
    digest(expected_manifest_sha256)
    root = _safe_root(directory)
    raw = _read(root / "manifest.json", MAX_METADATA)
    if sha256(raw).hexdigest() != expected_manifest_sha256:
        raise ValueError("Context archive manifest digest differs")
    manifest = _object(raw)
    if (
        set(manifest)
        != {
            "schema_version",
            "capture_manifest_sha256",
            "original_context_manifest_sha256",
            "original_native_archive_manifest_sha256",
            "files",
            "source_bytes",
            "native_body_copies",
            "scientific_admission",
            "historical_snapshot_replaced",
            "related_resource_graph_complete",
        }
        or manifest["schema_version"] != SCHEMA
        or manifest["scientific_admission"] != "not_asserted"
        or type(manifest["native_body_copies"]) is not int
        or manifest["native_body_copies"] != 0
        or manifest["historical_snapshot_replaced"] is not False
        or manifest["related_resource_graph_complete"] is not False
        or not isinstance(manifest["files"], dict)
        or type(manifest["source_bytes"]) is not int
    ):
        raise ValueError("Context archive schema or source-only claims differ")
    total = 0
    for name, member in manifest["files"].items():
        _member(name)
        if (
            name == "manifest.json"
            or not isinstance(member, dict)
            or set(member) != {"bytes", "sha256"}
            or type(member.get("bytes")) is not int
            or not 0 <= member["bytes"] <= 32 * 1024 * 1024
        ):
            raise ValueError("Context archive member declaration differs")
        digest(member.get("sha256"))
        total += member["bytes"]
    if total != manifest["source_bytes"] or total + len(raw) > MAX_BYTES:
        raise ValueError("Context archive exceeds finite byte budget")
    sizes = validate_regular_namespace(
        root,
        {"manifest.json", *manifest["files"]},
        max_files=MAX_FILES,
        max_bytes=MAX_BYTES,
    )
    if any(
        sizes[name] != member["bytes"] for name, member in manifest["files"].items()
    ):
        raise ValueError("Context archive physical member size differs")
    source = source_metadata(root / "capture", manifest["capture_manifest_sha256"])
    validate_plan(source.plan, limits)
    if (
        manifest["original_context_manifest_sha256"]
        != source.plan.context_manifest_sha256
        or manifest["original_native_archive_manifest_sha256"]
        != source.plan.native_archive_manifest_sha256
    ):
        raise ValueError("Context archive original source anchors differ")
    if set(manifest["files"]) != {*source.files, "index.json"} or any(
        not _same_json(member, manifest["files"][name])
        for name, member in source.files.items()
    ):
        raise ValueError("Context archive exact source closure differs")
    index = source_index(source)
    if pinned(
        root / "index.json", manifest["files"]["index.json"], MAX_METADATA
    ) != encoded_json(index):
        raise ValueError("Context archive derived metadata index differs")
    scopes = prepare_scopes(
        source.plan, source.proof, original=original, current=current
    )
    return NeotomaContextResourceInventory(root, manifest, index, source, scopes)
