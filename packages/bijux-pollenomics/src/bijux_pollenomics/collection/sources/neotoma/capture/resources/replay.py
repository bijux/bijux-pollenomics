"""Authenticate finite resource ledgers and original failed/reused HTTP evidence."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from ..receipts import (
    _object,
    _read,
    _safe_root,
    _utc,
    _validate_transport_failure,
)
from .assessment import ASSESSMENT_FIELDS, QUALIFIED_STATUSES, assess_http
from .models import (
    DEFAULT_RESOURCE_LIMITS,
    DEVELOPMENT_ROLES,
    RESOURCE_SCHEMA,
    NeotomaResourceCapture,
    NeotomaResourceLimits,
    NeotomaRetainedSource,
)
from .protocol import identity, plan_from_json, request_for, resource_key, validate_plan
from .retained import read_retained_source

_ENTRY_FIELDS = {
    "resource_key",
    "dataset_id",
    "version",
    "identity",
    "attempts",
    "scientific_admission",
    "terminal_status",
}


def _same_json(left: object, right: object) -> bool:
    """Compare owned JSON while retaining boolean, integer and float distinctions."""
    try:
        return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(
            right, sort_keys=True, allow_nan=False
        )
    except (ValueError, TypeError, RecursionError) as error:
        raise ValueError("Neotoma resource assessment is not canonical JSON") from error


def _entry_fields(entry: dict[str, Any], fields: set[str]) -> None:
    if set(entry) != _ENTRY_FIELDS | fields:
        raise ValueError(
            "Neotoma resource assessment fields differ from its owned branch"
        )


def replay_neotoma_resource_capture(
    directory: Path,
    *,
    expected_manifest_sha256: str | None = None,
    source_captures: Mapping[str, Path] | None = None,
    retained_sources: Mapping[str, NeotomaRetainedSource] | None = None,
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
    _visited: frozenset[str] = frozenset(),
) -> NeotomaResourceCapture:
    """Verify plans, receipts and one body at a time without any network access."""
    root = _safe_root(directory)
    content = _read(root / "capture-manifest.json", 16 * 1024 * 1024)
    digest = sha256(content).hexdigest()
    if expected_manifest_sha256 is not None and digest != expected_manifest_sha256:
        raise ValueError("Neotoma resource manifest identity differs")
    if digest in _visited:
        raise ValueError("Cyclic Neotoma resource reuse")
    manifest = _object(content)
    if set(manifest) != {
        "schema_version",
        "status",
        "capture_utc_start",
        "capture_utc_end",
        "plan_sha256",
        "resources",
        "request_count",
        "response_bytes",
        "partitions",
        "all_resources_parsed",
        "scientific_admission",
        "snapshot_consistency",
    }:
        raise ValueError("Neotoma resource manifest fields differ")
    if (
        manifest.get("schema_version") != RESOURCE_SCHEMA
        or manifest.get("status") != "closed"
    ):
        raise ValueError("Unclosed or unsupported Neotoma resource capture")
    plan_bytes = _read(root / "request-plan.json", 4 * 1024 * 1024)
    if sha256(plan_bytes).hexdigest() != manifest.get("plan_sha256"):
        raise ValueError("Neotoma resource plan identity differs")
    control = _object(plan_bytes)
    if set(control) != {
        "schema_version",
        "plan",
        "limits",
        "input_captures",
        "retry_failed",
        "historical_snapshot_replaced",
    }:
        raise ValueError("Neotoma resource plan fields differ")
    if (
        control.get("schema_version") != RESOURCE_SCHEMA
        or control.get("historical_snapshot_replaced") is not False
    ):
        raise ValueError("Neotoma resource source role differs")
    plan, recorded_limits = plan_from_json(control)
    validate_plan(plan, limits)
    maximum_requests = min(limits.max_requests, recorded_limits.max_requests)
    maximum_body = min(limits.max_response_bytes, recorded_limits.max_response_bytes)
    maximum_total = min(limits.max_total_bytes, recorded_limits.max_total_bytes)
    sources = source_captures or {}
    retained = retained_sources or {}
    prior = {}
    selected_resources: dict[str, tuple[str, dict[str, Any]]] = {}
    requested_keys = {
        resource_key(resource, version)
        for resource in plan.resources
        for version in resource.versions
    }
    for source_digest in control.get("input_captures", []):
        if source_digest not in sources:
            raise ValueError("Neotoma resource reuse source is unavailable")
        result = replay_neotoma_resource_capture(
            sources[source_digest],
            expected_manifest_sha256=source_digest,
            source_captures=sources,
            retained_sources=retained_sources,
            limits=limits,
            _visited=_visited | {digest},
        )
        if not any(row["resource_key"] in requested_keys for row in result.resources):
            raise ValueError("Selected Neotoma input capture has no requested resource")
        prior[source_digest] = {row["resource_key"]: row for row in result.resources}
        for row in result.resources:
            if row["resource_key"] in selected_resources:
                raise ValueError("Ambiguous prior Neotoma resource result")
            selected_resources[row["resource_key"]] = (source_digest, row)
    resources = manifest.get("resources")
    if not isinstance(resources, list):
        raise ValueError("Neotoma resource ledger is malformed")
    expected = [
        (resource, version)
        for resource in sorted(plan.resources, key=lambda row: row.dataset_id)
        for version in resource.versions
    ]
    if len(resources) != len(expected):
        raise ValueError("Neotoma resource request closure differs")
    files = {"request-plan.json", "capture-manifest.json"}
    count = 0
    total = 0
    previous_end = _utc(manifest.get("capture_utc_start"))
    capture_end = _utc(manifest.get("capture_utc_end"))
    if previous_end > capture_end:
        raise ValueError("Neotoma resource capture timestamps are reversed")
    for entry, (resource, version) in zip(resources, expected, strict=True):
        key = resource_key(resource, version)
        if (
            not isinstance(entry, dict)
            or entry.get("resource_key") != key
            or entry.get("dataset_id") != resource.dataset_id
            or type(entry.get("dataset_id")) is not int
            or not _same_json(entry.get("identity"), identity(resource))
            or entry.get("version") != version
            or entry.get("scientific_admission") != "not_asserted"
        ):
            raise ValueError("Neotoma resource identity or role differs")
        attempts = entry.get("attempts")
        if not isinstance(attempts, list):
            raise ValueError("Neotoma resource attempt list is malformed")
        previous = selected_resources.get(key)
        if previous is not None and previous[1]["identity"] != entry["identity"]:
            raise ValueError("Prior Neotoma resource request identity differs")
        if "predecessor_result" in entry and (
            "reused_from" not in entry
            and (
                "retained_source" in entry
                or resource.exposure_role not in DEVELOPMENT_ROLES
            )
        ):
            raise ValueError("Neotoma predecessor requires a declared retry result")
        if "reused_from" in entry:
            reused = entry["reused_from"]
            if (
                not isinstance(reused, dict)
                or set(reused) != {"manifest_sha256", "resource_key"}
                or reused.get("manifest_sha256") not in prior
                or key != reused.get("resource_key")
                or attempts
            ):
                raise ValueError("Neotoma reused resource reference differs")
            original = prior[reused["manifest_sha256"]].get(key)
            if original is None or (
                control["retry_failed"]
                and original["terminal_status"] not in QUALIFIED_STATUSES
            ):
                raise ValueError("Neotoma reused result was relabelled")
            expected_copy = deepcopy(original)
            expected_copy["attempts"] = []
            expected_copy["reused_from"] = {
                "manifest_sha256": reused["manifest_sha256"],
                "resource_key": key,
            }
            if not _same_json(entry, expected_copy):
                raise ValueError("Neotoma reused result was relabelled")
            continue
        if resource.exposure_role not in DEVELOPMENT_ROLES:
            _entry_fields(entry, {"reason"})
            if (
                attempts
                or entry.get("terminal_status") != "not_attempted_exposure_role"
                or entry.get("reason") != resource.exposure_role
            ):
                raise ValueError(
                    "Reserved Neotoma resource contains numerical attempts"
                )
            continue
        if "retained_source" in entry:
            _entry_fields(entry, {"retained_source", "summary"})
            if attempts or key not in retained:
                raise ValueError("Retained Neotoma source resolver is missing")
            reference, summary = read_retained_source(
                resource, version, retained[key], maximum_body
            )
            if (
                entry.get("terminal_status") != "reused_qualified_native"
                or not _same_json(entry["retained_source"], reference)
                or not _same_json(entry.get("summary"), summary)
            ):
                raise ValueError("Retained Neotoma source assessment identity differs")
            continue
        if previous is None:
            if "predecessor_result" in entry:
                raise ValueError("Neotoma predecessor has no selected input result")
        elif (
            not control["retry_failed"]
            or previous[1]["terminal_status"] in QUALIFIED_STATUSES
            or entry.get("predecessor_result")
            != {
                "manifest_sha256": previous[0],
                "resource_key": key,
                "terminal_status": previous[1]["terminal_status"],
            }
        ):
            raise ValueError(
                "Neotoma retry predecessor differs from authenticated input"
            )
        if not attempts:
            _entry_fields(
                entry, {"predecessor_result"} if previous is not None else set()
            )
            if entry.get("terminal_status") != "not_attempted_budget":
                raise ValueError("Neotoma resource has no accounted attempt")
            continue
        if len(attempts) > min(limits.max_attempts, recorded_limits.max_attempts):
            raise ValueError("Neotoma resource attempt budget exceeded")
        assessment: dict[str, Any] = {}
        for index, reference in enumerate(attempts, start=1):
            request = request_for(resource, version, index)
            if (
                not isinstance(reference, dict)
                or reference.get("request_name") != request.name
                or reference.get("receipt_file") != f"{request.name}.receipt.json"
            ):
                raise ValueError("Neotoma HTTP request reference differs")
            receipt_bytes = _read(root / reference["receipt_file"], 65536)
            if sha256(receipt_bytes).hexdigest() != reference.get("receipt_sha256"):
                raise ValueError("Neotoma resource receipt identity differs")
            record = _object(receipt_bytes)
            reference_fields = {"request_name", "receipt_file", "receipt_sha256"}
            if record.get("terminal_status") != "transport_failure":
                reference_fields.add("body_file")
            if set(reference) != reference_fields:
                raise ValueError("Neotoma resource attempt reference fields differ")
            files.add(reference["receipt_file"])
            count += 1
            if (
                not previous_end
                <= _utc(record.get("utc_start"))
                <= _utc(record.get("utc_end"))
                <= capture_end
            ):
                raise ValueError("Neotoma resource request time differs")
            previous_end = _utc(record["utc_end"])
            if record.get("terminal_status") == "transport_failure":
                _validate_transport_failure(record, request)
                assessment = {
                    "terminal_status": "transport_failure",
                    "reason": record["error"],
                }
                continue
            name = f"{request.name}.body"
            if record.get("body_file") != name or reference.get("body_file") != name:
                raise ValueError("Neotoma resource body path differs")
            body = _read(root / name, maximum_body + 1)
            files.add(name)
            total += len(body)
            assessment = assess_http(
                resource, version, record, request, body, maximum_body
            )
            del body
        _entry_fields(
            entry,
            set(assessment)
            | ({"predecessor_result"} if previous is not None else set()),
        )
        if not _same_json(
            {
                field: entry.get(field)
                for field in ASSESSMENT_FIELDS
                if field in assessment
            },
            assessment,
        ):
            raise ValueError("Neotoma resource assessment differs from retained body")
    if (
        count > maximum_requests
        or total > maximum_total + 1
        or not _same_json(manifest.get("request_count"), count)
        or not _same_json(manifest.get("response_bytes"), total)
    ):
        raise ValueError("Neotoma resource aggregate budget/identity differs")
    partitions = dict(Counter(row["terminal_status"] for row in resources))
    if (
        not _same_json(manifest.get("partitions"), partitions)
        or manifest.get("all_resources_parsed")
        != all(row["terminal_status"] == "parsed_native" for row in resources)
        or manifest.get("scientific_admission") != "not_asserted"
        or manifest.get("snapshot_consistency")
        != "individually timed live or explicitly reused responses; no transaction snapshot"
        or {path.name for path in root.iterdir()} != files
    ):
        raise ValueError("Neotoma resource ledger/file population differs")
    return NeotomaResourceCapture(digest, tuple(resources), count, total, partitions)
