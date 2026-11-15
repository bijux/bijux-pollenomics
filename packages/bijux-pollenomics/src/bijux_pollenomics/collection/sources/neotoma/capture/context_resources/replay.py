"""Recompute current parent obligations before any literal context entity read."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import validate_regular_namespace

from ..receipts import (
    _object,
    _read,
    _request_record,
    _safe_root,
    _utc,
    _validate_transport_failure,
)
from ..resources.models import NeotomaResourceLimits
from ..resources.replay import _same_json
from .models import (
    CONTEXT_SCHEMA,
    DEFAULT_CONTEXT_LIMITS,
    MAX_BYTES,
    MAX_FILES,
    MAX_METADATA_BYTES,
    POLICY_SOURCES,
    SNAPSHOT_CONSISTENCY,
    SOURCE_SCOPE,
    NeotomaContextResourceCapture,
    NeotomaContextResourcePlan,
)
from .protocol import (
    assess_http,
    digest,
    native_dataset_ids,
    plan_from_json,
    request_for,
    request_name,
    validate_plan,
    verify_request_metadata,
)
from .scope import prepare_scope

_ENTRY = {
    "site_id",
    "resource_kind",
    "content_version",
    "api_version",
    "scope_status",
    "exposure_role",
    "attempts",
    "scientific_admission",
}


def _control(
    root: Path, expected: str | None
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    NeotomaContextResourcePlan,
    NeotomaResourceLimits,
    str,
]:
    raw = _read(root / "capture-manifest.json", MAX_METADATA_BYTES)
    pin = sha256(raw).hexdigest()
    if expected is not None and pin != digest(expected):
        raise ValueError("Context resource manifest identity differs")
    manifest = _object(raw)
    if (
        set(manifest)
        != {
            "schema_version",
            "status",
            "capture_utc_start",
            "capture_utc_end",
            "plan_sha256",
            "resources",
            "request_count",
            "response_bytes",
            "partitions",
            "source_scope",
            "snapshot_consistency",
            "scientific_admission",
        }
        or manifest["schema_version"] != CONTEXT_SCHEMA
        or manifest["status"] != "closed"
        or manifest["source_scope"] != SOURCE_SCOPE
        or manifest["snapshot_consistency"] != SNAPSHOT_CONSISTENCY
        or manifest["scientific_admission"] != "not_asserted"
    ):
        raise ValueError("Context resource manifest fields or scope differ")
    raw = _read(root / "request-plan.json", 1024 * 1024)
    if sha256(raw).hexdigest() != manifest["plan_sha256"]:
        raise ValueError("Context resource plan identity differs")
    control = _object(raw)
    if (
        set(control)
        != {
            "schema_version",
            "plan",
            "limits",
            "parent_scope_sha256",
            "source_scope",
            "policy_sources",
        }
        or control["schema_version"] != CONTEXT_SCHEMA
        or control["source_scope"] != SOURCE_SCOPE
        or not _same_json(control["policy_sources"], list(POLICY_SOURCES))
    ):
        raise ValueError("Context resource control fields differ")
    plan, recorded = plan_from_json(control)
    return manifest, control, plan, recorded, pin


def _files(entries: list[Any], plan: NeotomaContextResourcePlan) -> set[str]:
    files = {"capture-manifest.json", "request-plan.json", "parent-scope.json"}
    expected = [(kind, site) for kind in plan.resource_kinds for site in plan.site_ids]
    if len(entries) != len(expected):
        raise ValueError("Context resource selected population differs")
    for entry, (kind, site_id) in zip(entries, expected, strict=True):
        if (
            not isinstance(entry, dict)
            or type(entry.get("site_id")) is not int
            or entry["site_id"] != site_id
            or entry.get("resource_kind") != kind
            or entry.get("content_version") != "current"
            or entry.get("api_version") != "v2.0"
            or entry.get("scientific_admission") != "not_asserted"
            or not isinstance(entry.get("attempts"), list)
            or len(entry["attempts"]) > 1
        ):
            raise ValueError("Context resource identity or attempts differ")
        if not entry["attempts"]:
            continue
        name = request_name(kind, site_id)
        reference = entry["attempts"][0]
        if (
            not isinstance(reference, dict)
            or set(reference)
            not in (
                {"request_name", "receipt_file", "receipt_sha256"},
                {"request_name", "receipt_file", "receipt_sha256", "body_file"},
            )
            or reference.get("request_name") != name
            or reference.get("receipt_file") != f"{name}.receipt.json"
        ):
            raise ValueError("Context resource receipt pointer differs")
        digest(reference["receipt_sha256"])
        files.add(reference["receipt_file"])
        if "body_file" in reference:
            if reference["body_file"] != f"{name}.body":
                raise ValueError("Context resource body pointer differs")
            files.add(reference["body_file"])
    return files


def replay_neotoma_context_resources(
    directory: Path,
    *,
    expected_context_sha256: str,
    expected_native_archive_sha256: str,
    context_directory: Path,
    native_archive_directory: Path,
    expected_manifest_sha256: str | None = None,
    limits: NeotomaResourceLimits = DEFAULT_CONTEXT_LIMITS,
) -> NeotomaContextResourceCapture:
    """Full source replay, preserving original receipts and unqualified payloads."""
    digest(expected_context_sha256)
    digest(expected_native_archive_sha256)
    root = _safe_root(directory)
    manifest, control, plan, recorded, pin = _control(root, expected_manifest_sha256)
    validate_plan(plan, limits)
    if (
        plan.context_manifest_sha256 != expected_context_sha256
        or plan.native_archive_manifest_sha256 != expected_native_archive_sha256
    ):
        raise ValueError("Context independently expected source epoch differs")
    entries = manifest["resources"]
    if not isinstance(entries, list):
        raise ValueError("Context source resource population is malformed")
    files = _files(entries, plan)
    validate_regular_namespace(root, files, max_files=MAX_FILES, max_bytes=MAX_BYTES)
    raw = _read(root / "parent-scope.json", MAX_METADATA_BYTES)
    if sha256(raw).hexdigest() != control["parent_scope_sha256"]:
        raise ValueError("Context original parent scope identity differs")
    scope = prepare_scope(
        plan,
        context_directory=context_directory,
        native_archive_directory=native_archive_directory,
    )
    if not _same_json(_object(raw), scope):
        raise ValueError("Context original/current parent scope proof differs")
    parents = {row["site_id"]: row for row in scope["requested_sites"]}
    # Gate the complete declared request population before opening even the first body.
    for entry in entries:
        parent = parents[entry["site_id"]]
        if (
            entry.get("scope_status") != parent["scope_status"]
            or not _same_json(
                entry.get("exposure_role"), parent["effective_scope_role"]
            )
            or entry["attempts"]
            and parent["scope_status"] != "eligible_current_scope"
        ):
            raise ValueError(
                "Context protected or unestablished parent forbids source body access"
            )
    maximum_requests = min(limits.max_requests, recorded.max_requests)
    maximum_body = min(limits.max_response_bytes, recorded.max_response_bytes)
    maximum_total = min(limits.max_total_bytes, recorded.max_total_bytes)
    previous_end, end = (
        _utc(manifest["capture_utc_start"]),
        _utc(manifest["capture_utc_end"]),
    )
    if previous_end > end:
        raise ValueError("Context capture timestamps are reversed")
    count = total = 0
    for entry in entries:
        assessed: dict[str, Any] = {
            "terminal_status": "not_attempted_parent_scope"
            if entry["scope_status"] != "eligible_current_scope"
            else "not_attempted_budget"
        }
        if entry["attempts"]:
            count += 1
            if count > maximum_requests or total >= maximum_total:
                raise ValueError("Context source exceeds request or total byte budget")
            request = request_for(
                entry["resource_kind"],
                entry["site_id"],
                dataset_ids=native_dataset_ids(parents[entry["site_id"]])
                if entry["resource_kind"] == "dataset_depositional_environment"
                else None,
            )
            reference = entry["attempts"][0]
            content = _read(root / reference["receipt_file"], 1024 * 1024)
            if sha256(content).hexdigest() != reference["receipt_sha256"]:
                raise ValueError("Context receipt identity differs")
            record = _object(content)
            verify_request_metadata(record, request)
            started, finished = (
                _utc(record.get("utc_start")),
                _utc(record.get("utc_end")),
            )
            if started < previous_end or finished < started or finished > end:
                raise ValueError("Context request timestamps differ")
            previous_end = finished
            if record.get("terminal_status") == "transport_failure":
                if set(reference) != {
                    "request_name",
                    "receipt_file",
                    "receipt_sha256",
                } or set(record) != set(
                    _request_record(request, record["utc_start"])
                ) | {"utc_end", "terminal_status", "error", "body_complete"}:
                    raise ValueError("Context transport failure fields differ")
                _validate_transport_failure(record, request)
                assessed = {
                    "terminal_status": "transport_failure",
                    "reason": record["error"],
                }
            else:
                if (
                    reference.get("body_file") != record.get("body_file")
                    or "body_file" not in reference
                ):
                    raise ValueError("Context literal body pointer differs")
                bound = min(maximum_body, maximum_total - total)
                body = _read(root / reference["body_file"], bound + 1)
                assessed = assess_http(record, request, body, bound)
                total += len(body)
        if set(entry) != _ENTRY | set(assessed) or not _same_json(
            {key: entry[key] for key in assessed}, assessed
        ):
            raise ValueError("Context derived source assessment differs")
    partitions = dict(Counter(row["terminal_status"] for row in entries))
    if (
        type(manifest["request_count"]) is not int
        or type(manifest["response_bytes"]) is not int
        or manifest["request_count"] != count
        or manifest["response_bytes"] != total
        or not _same_json(manifest["partitions"], partitions)
    ):
        raise ValueError("Context source denominator closure differs")
    return NeotomaContextResourceCapture(pin, tuple(entries), count, total, partitions)
