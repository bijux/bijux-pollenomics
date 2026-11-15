"""Authenticate finite facet ledgers and expose only role-admitted source buffers."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from typing import Any

from ..receipts import (
    _object,
    _read,
    _safe_root,
    _utc,
    _validate_receipt,
    _validate_transport_failure,
)
from ..resources.models import (
    DEFAULT_RESOURCE_LIMITS,
    DEVELOPMENT_ROLES,
    NeotomaResourceLimits,
    NeotomaResourcePlan,
)
from ..resources.replay import _same_json
from .assessment import assess_http
from .models import (
    FACET_SCHEMA,
    SCOPED_FACET_SCHEMA,
    NeotomaFacetBody,
    NeotomaFacetCapture,
    NeotomaFacetPlan,
    NeotomaFacetScopeInputs,
)
from .protocol import facet_identity, plan_from_json, request_for, validate_plan
from .scope import authenticate_parent_scope

_MANIFEST_FIELDS = {
    "schema_version",
    "status",
    "capture_utc_start",
    "capture_utc_end",
    "plan_sha256",
    "facets",
    "request_count",
    "response_bytes",
    "partitions",
    "scientific_admission",
    "snapshot_consistency",
}
_ENTRY_FIELDS = {
    "facet_key",
    "root_identity",
    "facet",
    "content_version",
    "api_version",
    "attempts",
    "scientific_admission",
}
SNAPSHOT_CONSISTENCY = (
    "individually timed current facet responses; no transaction or frozen snapshot"
)


def _control(
    root: Path, expected: str | None
) -> tuple[dict[str, Any], NeotomaFacetPlan, NeotomaResourceLimits, str]:
    content = _read(root / "capture-manifest.json", 16 * 1024 * 1024)
    digest = sha256(content).hexdigest()
    if expected is not None and digest != expected:
        raise ValueError("Neotoma facet manifest identity differs")
    manifest = _object(content)
    if (
        set(manifest) != _MANIFEST_FIELDS
        or manifest["schema_version"] not in {FACET_SCHEMA, SCOPED_FACET_SCHEMA}
        or manifest["status"] != "closed"
        or manifest["scientific_admission"] != "not_asserted"
        or manifest["snapshot_consistency"] != SNAPSHOT_CONSISTENCY
    ):
        raise ValueError("Neotoma facet manifest fields or status differ")
    raw = _read(root / "request-plan.json", 4 * 1024 * 1024)
    if sha256(raw).hexdigest() != manifest["plan_sha256"]:
        raise ValueError("Neotoma facet plan identity differs")
    control = _object(raw)
    if (
        set(control)
        != {
            "schema_version",
            "plan",
            "limits",
            "policy_sources",
            "historical_snapshot_replaced",
        }
        | (
            {"parent_scope"}
            if manifest["schema_version"] == SCOPED_FACET_SCHEMA
            else set()
        )
        or control["schema_version"] != manifest["schema_version"]
        or control["historical_snapshot_replaced"] is not False
    ):
        raise ValueError("Neotoma facet plan fields differ")
    plan, limits = plan_from_json(control)
    if not _same_json(
        control["policy_sources"],
        list(NeotomaResourcePlan(plan.resources, plan.roster_sha256).policy_sources),
    ):
        raise ValueError("Neotoma facet policy references differ")
    return manifest, plan, limits, digest


def replay_neotoma_facet_capture(
    directory: Path,
    *,
    expected_manifest_sha256: str | None = None,
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
    scope_inputs: Mapping[str, NeotomaFacetScopeInputs] | None = None,
) -> NeotomaFacetCapture:
    """Recompute each status from authenticated attempts, without any network access."""
    root = _safe_root(directory)
    manifest, plan, recorded, digest = _control(root, expected_manifest_sha256)
    validate_plan(plan, limits)
    maximum_requests = min(limits.max_requests, recorded.max_requests)
    maximum_attempts = min(limits.max_attempts, recorded.max_attempts)
    maximum_body = min(limits.max_response_bytes, recorded.max_response_bytes)
    maximum_total = min(limits.max_total_bytes, recorded.max_total_bytes)
    expected = [
        (resource, facet)
        for resource in sorted(plan.resources, key=lambda item: item.dataset_id)
        for facet in plan.facets
    ]
    entries = manifest["facets"]
    if not isinstance(entries, list) or len(entries) != len(expected):
        raise ValueError("Neotoma facet request closure differs")
    files = {"capture-manifest.json", "request-plan.json"}
    parents = {}
    scoped = manifest["schema_version"] == SCOPED_FACET_SCHEMA
    if scoped:
        control = _object(_read(root / "request-plan.json", 4 * 1024 * 1024))
        proof = authenticate_parent_scope(root, control, plan, scope_inputs)
        parents = {row["dataset_id"]: row for row in proof["parents"]}
        files.add("parent-scope.json")
    count = total = 0
    previous_end, end = (
        _utc(manifest["capture_utc_start"]),
        _utc(manifest["capture_utc_end"]),
    )
    if previous_end > end:
        raise ValueError("Neotoma facet capture timestamps are reversed")
    for entry, (resource, facet) in zip(entries, expected, strict=True):
        expected_identity = facet_identity(resource, facet)
        if (
            not isinstance(entry, dict)
            or not _same_json(
                {key: entry.get(key) for key in expected_identity}, expected_identity
            )
            or entry.get("scientific_admission") != "not_asserted"
            or not isinstance(entry.get("attempts"), list)
            or len(entry["attempts"]) > maximum_attempts
        ):
            raise ValueError("Neotoma facet root or request identity differs")
        assessed: dict[str, Any] = {"terminal_status": "not_attempted_budget"}
        scope_role = (
            parents[resource.dataset_id]["effective_scope_role"]
            if scoped
            else resource.exposure_role
        )
        if scoped and entry.get("parent_scope_role") != scope_role:
            raise ValueError("Facet parent scope role differs")
        if resource.exposure_role not in DEVELOPMENT_ROLES:
            if entry["attempts"]:
                raise ValueError("Neotoma facet exposure role forbids body access")
            assessed = {
                "terminal_status": "not_attempted_exposure_role",
                "reason": resource.exposure_role,
            }
        elif scope_role not in DEVELOPMENT_ROLES:
            if entry["attempts"]:
                raise ValueError("Facet parent scope forbids body access")
            assessed = {
                "terminal_status": "not_attempted_parent_scope",
                "reason": scope_role,
            }
        for index, reference in enumerate(entry["attempts"], 1):
            count += 1
            if count > maximum_requests or total >= maximum_total:
                raise ValueError(
                    "Neotoma facet capture exceeds caller request or byte limits"
                )
            request = request_for(resource, facet, index)
            if (
                not isinstance(reference, dict)
                or reference.get("request_name") != request.name
                or reference.get("receipt_file") != f"{request.name}.receipt.json"
            ):
                raise ValueError("Neotoma facet attempt reference differs")
            receipt_path = reference["receipt_file"]
            receipt_bytes = _read(root / receipt_path, 1024 * 1024)
            if sha256(receipt_bytes).hexdigest() != reference.get("receipt_sha256"):
                raise ValueError("Neotoma facet receipt identity differs")
            record = _object(receipt_bytes)
            files.add(receipt_path)
            started, finished = (
                _utc(record.get("utc_start")),
                _utc(record.get("utc_end")),
            )
            if started < previous_end or finished < started or finished > end:
                raise ValueError("Neotoma facet attempt timestamps differ")
            previous_end = finished
            if record.get("terminal_status") == "transport_failure":
                if set(reference) != {"request_name", "receipt_file", "receipt_sha256"}:
                    raise ValueError("Neotoma facet transport reference fields differ")
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
                    raise ValueError("Neotoma facet body reference fields differ")
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
                raise ValueError("Neotoma facet retried a nontransient response")
        if set(entry) != _ENTRY_FIELDS | set(assessed) | (
            {"parent_scope_role"} if scoped else set()
        ) or not _same_json({key: entry[key] for key in assessed}, assessed):
            raise ValueError("Neotoma facet derived assessment differs")
    partitions = dict(Counter(entry["terminal_status"] for entry in entries))
    if (
        type(manifest["request_count"]) is not int
        or type(manifest["response_bytes"]) is not int
        or manifest["request_count"] != count
        or manifest["response_bytes"] != total
        or not _same_json(manifest["partitions"], partitions)
    ):
        raise ValueError("Neotoma facet denominator closure differs")
    if (
        any(path.is_symlink() or not path.is_file() for path in root.iterdir())
        or {path.name for path in root.iterdir()} != files
    ):
        raise ValueError("Neotoma facet file inventory differs")
    return NeotomaFacetCapture(digest, tuple(entries), count, total, partitions)


def read_neotoma_facet_body(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    facet_key: str,
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
    scope_inputs: Mapping[str, NeotomaFacetScopeInputs] | None = None,
) -> NeotomaFacetBody:
    """Gate the root role, replay custody, then authenticate the actual returned buffer."""
    root = _safe_root(directory)
    manifest, plan, _, _ = _control(root, expected_manifest_sha256)
    selected = [
        (resource, facet)
        for resource in plan.resources
        for facet in plan.facets
        if facet_identity(resource, facet)["facet_key"] == facet_key
    ]
    if len(selected) != 1:
        raise ValueError("Neotoma facet key is absent or ambiguous")
    resource, facet = selected[0]
    if resource.exposure_role not in DEVELOPMENT_ROLES:
        raise ValueError("Neotoma facet exposure role forbids body access")
    if manifest["schema_version"] == SCOPED_FACET_SCHEMA:
        control = _object(_read(root / "request-plan.json", 4 * 1024 * 1024))
        proof = authenticate_parent_scope(root, control, plan, scope_inputs)
        parent = next(
            row for row in proof["parents"] if row["dataset_id"] == resource.dataset_id
        )
        if parent["effective_scope_role"] not in DEVELOPMENT_ROLES:
            raise ValueError("Facet parent scope forbids body access")
    capture = replay_neotoma_facet_capture(
        root,
        expected_manifest_sha256=expected_manifest_sha256,
        limits=limits,
        scope_inputs=scope_inputs,
    )
    entry = next(row for row in capture.facets if row["facet_key"] == facet_key)
    if entry["terminal_status"] != "received_complete_unqualified_facet":
        raise ValueError("Neotoma facet complete source entity is unavailable")
    return _read_authenticated_facet_body(root, resource, facet, entry, limits)


def _read_authenticated_facet_body(
    root: Path,
    resource: Any,
    facet: str,
    entry: dict[str, Any],
    limits: NeotomaResourceLimits,
) -> NeotomaFacetBody:
    """Recheck the same returned receipt/body buffer after its enclosing replay."""
    facet_key = entry["facet_key"]
    reference = entry["attempts"][-1]
    receipt = _read(root / reference["receipt_file"], 1024 * 1024)
    if sha256(receipt).hexdigest() != reference["receipt_sha256"]:
        raise ValueError("Neotoma facet receipt changed during body access")
    body = _read(root / reference["body_file"], limits.max_response_bytes)
    record = _object(receipt)
    _validate_receipt(
        record,
        request_for(resource, facet, len(entry["attempts"])),
        body,
        limits.max_response_bytes,
    )
    return NeotomaFacetBody(
        facet_key,
        entry["root_identity"],
        body,
        sha256(body).hexdigest(),
        reference["receipt_sha256"],
    )
