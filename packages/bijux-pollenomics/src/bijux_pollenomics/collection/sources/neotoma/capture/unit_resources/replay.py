"""Recompute whole-unit scopes and authenticate actual returned HTTP buffers."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
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
from ..resources.models import (
    DEFAULT_RESOURCE_LIMITS,
    DEVELOPMENT_ROLES,
    NeotomaResourceLimits,
)
from ..resources.replay import _same_json
from .assessment import assess_http
from .models import (
    UNIT_SCHEMA,
    NeotomaUnitBody,
    NeotomaUnitResourceCapture,
    NeotomaUnitResourcePlan,
)
from .protocol import plan_from_json, request_for
from .scope import prepare_unit_scopes

SNAPSHOT_CONSISTENCY = (
    "individually timed current unit responses; no transaction or frozen snapshot"
)
_ENTRY_FIELDS = {
    "unit_key",
    "identity",
    "content_version",
    "api_version",
    "attempts",
    "scientific_admission",
}


def _control(
    root: Path, expected: str | None
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    NeotomaUnitResourcePlan,
    NeotomaResourceLimits,
    str,
]:
    raw = _read(root / "capture-manifest.json", 16 * 1024 * 1024)
    digest = sha256(raw).hexdigest()
    if expected is not None and digest != expected:
        raise ValueError("Neotoma unit manifest identity differs")
    manifest = _object(raw)
    if (
        set(manifest)
        != {
            "schema_version",
            "status",
            "capture_utc_start",
            "capture_utc_end",
            "plan_sha256",
            "units",
            "request_count",
            "response_bytes",
            "partitions",
            "scientific_admission",
            "snapshot_consistency",
        }
        or manifest["schema_version"] != UNIT_SCHEMA
        or manifest["status"] != "closed"
        or manifest["scientific_admission"] != "not_asserted"
        or manifest["snapshot_consistency"] != SNAPSHOT_CONSISTENCY
    ):
        raise ValueError("Neotoma unit manifest fields or status differ")
    raw = _read(root / "request-plan.json", 16 * 1024 * 1024)
    if sha256(raw).hexdigest() != manifest["plan_sha256"]:
        raise ValueError("Neotoma unit plan identity differs")
    control = _object(raw)
    if (
        set(control) != {"schema_version", "plan", "limits", "units", "policy_sources"}
        or control["schema_version"] != UNIT_SCHEMA
    ):
        raise ValueError("Neotoma unit control fields differ")
    plan, recorded = plan_from_json(control)
    return manifest, control, plan, recorded, digest


def replay_neotoma_unit_resources(
    directory: Path,
    *,
    roster_path: Path,
    metadata_captures: Mapping[str, Path],
    expected_manifest_sha256: str | None = None,
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
) -> NeotomaUnitResourceCapture:
    """Rebuild native unit membership and role obligations from authenticated sources."""
    root = _safe_root(directory)
    manifest, control, plan, recorded, digest = _control(root, expected_manifest_sha256)
    targets, policies = prepare_unit_scopes(
        plan, roster_path, metadata_captures, limits
    )
    prepare_unit_scopes(plan, roster_path, metadata_captures, recorded)
    if not _same_json(control["units"], targets) or not _same_json(
        control["policy_sources"], policies
    ):
        raise ValueError("Neotoma unit target proof closure differs")
    entries = manifest["units"]
    if not isinstance(entries, list) or len(entries) != len(targets):
        raise ValueError("Neotoma unit target population differs")
    maximum_requests = min(limits.max_requests, recorded.max_requests)
    maximum_attempts = min(limits.max_attempts, recorded.max_attempts)
    maximum_body = min(limits.max_response_bytes, recorded.max_response_bytes)
    maximum_total = min(limits.max_total_bytes, recorded.max_total_bytes)
    previous_end, end = (
        _utc(manifest["capture_utc_start"]),
        _utc(manifest["capture_utc_end"]),
    )
    if previous_end > end:
        raise ValueError("Neotoma unit capture timestamps are reversed")
    count = total = 0
    files = {"capture-manifest.json", "request-plan.json"}
    for entry, target in zip(entries, targets, strict=True):
        if (
            not isinstance(entry, dict)
            or entry.get("unit_key") != target["unit_key"]
            or not _same_json(entry.get("identity"), target)
            or entry.get("content_version") != "current"
            or entry.get("api_version") != "v2.0"
            or entry.get("scientific_admission") != "not_asserted"
            or not isinstance(entry.get("attempts"), list)
            or len(entry["attempts"]) > maximum_attempts
        ):
            raise ValueError("Neotoma unit target identity or attempts differ")
        assessed: dict[str, Any] = {"terminal_status": "not_attempted_budget"}
        if target["exposure_role"] not in DEVELOPMENT_ROLES:
            if entry["attempts"]:
                raise ValueError("Neotoma unit exposure role forbids body access")
            assessed = {
                "terminal_status": "not_attempted_exposure_role",
                "reason": target["exposure_role"],
            }
        for index, reference in enumerate(entry["attempts"], 1):
            count += 1
            if count > maximum_requests or total >= maximum_total:
                raise ValueError(
                    "Neotoma unit capture exceeds caller request or byte limits"
                )
            request = request_for(target, index)
            name = f"{request.name}.receipt.json"
            if (
                not isinstance(reference, dict)
                or reference.get("request_name") != request.name
                or reference.get("receipt_file") != name
            ):
                raise ValueError("Neotoma unit attempt reference differs")
            raw = _read(root / name, 1024 * 1024)
            if sha256(raw).hexdigest() != reference.get("receipt_sha256"):
                raise ValueError("Neotoma unit receipt identity differs")
            record = _object(raw)
            files.add(name)
            started, finished = (
                _utc(record.get("utc_start")),
                _utc(record.get("utc_end")),
            )
            if started < previous_end or finished < started or finished > end:
                raise ValueError("Neotoma unit attempt timestamps differ")
            previous_end = finished
            if record.get("terminal_status") == "transport_failure":
                if set(reference) != {
                    "request_name",
                    "receipt_file",
                    "receipt_sha256",
                } or set(record) != set(
                    _request_record(request, record["utc_start"])
                ) | {"utc_end", "terminal_status", "error", "body_complete"}:
                    raise ValueError("Neotoma unit transport fields differ")
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
                    raise ValueError("Neotoma unit body reference differs")
                bound = min(maximum_body, maximum_total - total)
                body = _read(root / name, bound + 1)
                assessed = assess_http(record, request, body, bound)
                total += len(body)
                files.add(name)
            if index < len(entry["attempts"]) and not (
                record.get("terminal_status") == "transport_failure"
                or record.get("http_status") == 429
                or type(record.get("http_status")) is int
                and 500 <= record["http_status"] <= 599
            ):
                raise ValueError("Neotoma unit retried a nontransient result")
        if set(entry) != _ENTRY_FIELDS | set(assessed) or not _same_json(
            {key: entry[key] for key in assessed}, assessed
        ):
            raise ValueError("Neotoma unit source assessment differs")
    partitions = dict(Counter(row["terminal_status"] for row in entries))
    if (
        type(manifest["request_count"]) is not int
        or type(manifest["response_bytes"]) is not int
        or manifest["request_count"] != count
        or manifest["response_bytes"] != total
        or not _same_json(manifest["partitions"], partitions)
    ):
        raise ValueError("Neotoma unit denominator closure differs")
    if (
        any(path.is_symlink() or not path.is_file() for path in root.iterdir())
        or {path.name for path in root.iterdir()} != files
    ):
        raise ValueError("Neotoma unit file inventory differs")
    return NeotomaUnitResourceCapture(digest, tuple(entries), count, total, partitions)


def read_neotoma_unit_body(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    unit_key: str,
    roster_path: Path,
    metadata_captures: Mapping[str, Path],
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
) -> NeotomaUnitBody:
    """Check inherited roles before body access, then hash the actual returned buffer."""
    root = _safe_root(directory)
    _, _, plan, _, _ = _control(root, expected_manifest_sha256)
    targets, _ = prepare_unit_scopes(plan, roster_path, metadata_captures, limits)
    selected = [target for target in targets if target["unit_key"] == unit_key]
    if len(selected) != 1:
        raise ValueError("Neotoma unit target is absent or ambiguous")
    target = selected[0]
    if target["exposure_role"] not in DEVELOPMENT_ROLES:
        raise ValueError("Neotoma unit exposure role forbids body access")
    capture = replay_neotoma_unit_resources(
        root,
        expected_manifest_sha256=expected_manifest_sha256,
        roster_path=roster_path,
        metadata_captures=metadata_captures,
        limits=limits,
    )
    entry = next(row for row in capture.units if row["unit_key"] == unit_key)
    if entry["terminal_status"] != "received_complete_unqualified_unit_resource":
        raise ValueError("Neotoma complete unit source entity is unavailable")
    reference = entry["attempts"][-1]
    raw = _read(root / reference["receipt_file"], 1024 * 1024)
    if sha256(raw).hexdigest() != reference["receipt_sha256"]:
        raise ValueError("Neotoma unit receipt changed during body access")
    record = _object(raw)
    body = _read(root / reference["body_file"], limits.max_response_bytes)
    _validate_receipt(
        record,
        request_for(target, len(entry["attempts"])),
        body,
        limits.max_response_bytes,
    )
    return NeotomaUnitBody(
        unit_key,
        body,
        sha256(body).hexdigest(),
        reference["receipt_sha256"],
        target,
    )
