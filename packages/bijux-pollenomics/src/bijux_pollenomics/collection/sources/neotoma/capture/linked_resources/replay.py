"""Recompute exact source proof closure and authenticate returned detail buffers."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from typing import Any

from ..facets.models import NeotomaFacetScopeInputs
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
from .evidence import read_neotoma_linked_evidence_target
from .models import (
    EVIDENCE_SCHEMA,
    LINKED_SCHEMA,
    SCOPED_LINKED_SCHEMA,
    NeotomaLinkedBody,
    NeotomaLinkedEvidence,
    NeotomaLinkedResourceCapture,
    NeotomaLinkedResourcePlan,
)
from .protocol import (
    _prepare_scoped_targets,
    plan_from_json,
    prepare_scoped_targets,
    prepare_targets,
    request_for,
    validate_scoped_limits,
)

SNAPSHOT_CONSISTENCY = (
    "individually timed current linked responses; no transaction or frozen snapshot"
)
_ENTRY_FIELDS = {
    "target_key",
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
    NeotomaLinkedResourcePlan,
    NeotomaResourceLimits,
    str,
]:
    raw = _read(root / "capture-manifest.json", 16 * 1024 * 1024)
    digest = sha256(raw).hexdigest()
    if expected is not None and digest != expected:
        raise ValueError("Neotoma linked manifest identity differs")
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
            "scientific_admission",
            "snapshot_consistency",
        }
        | (
            {"source_evidence"}
            if manifest.get("schema_version") == SCOPED_LINKED_SCHEMA
            else set()
        )
        or manifest["schema_version"] not in {LINKED_SCHEMA, SCOPED_LINKED_SCHEMA}
        or manifest["status"] != "closed"
        or manifest["scientific_admission"] != "not_asserted"
        or manifest["snapshot_consistency"] != SNAPSHOT_CONSISTENCY
    ):
        raise ValueError("Neotoma linked manifest fields or status differ")
    raw = _read(root / "request-plan.json", 16 * 1024 * 1024)
    if sha256(raw).hexdigest() != manifest["plan_sha256"]:
        raise ValueError("Neotoma linked plan identity differs")
    control = _object(raw)
    if (
        set(control)
        != {"schema_version", "plan", "limits", "targets", "policy_sources"}
        | (
            {"source_evidence"}
            if manifest["schema_version"] == SCOPED_LINKED_SCHEMA
            else set()
        )
        or control["schema_version"] != manifest["schema_version"]
    ):
        raise ValueError("Neotoma linked control fields differ")
    plan, recorded = plan_from_json(control)
    return manifest, control, plan, recorded, digest


def _targets_for_control(
    manifest: dict[str, Any],
    control: dict[str, Any],
    plan: NeotomaLinkedResourcePlan,
    source_facets: Mapping[str, Path],
    limits: NeotomaResourceLimits,
    *,
    scope_inputs: Mapping[str, NeotomaFacetScopeInputs] | None,
    evidence: NeotomaLinkedEvidence | None,
    legacy_rosters: Mapping[str, Path] | None,
    _session: Any = None,
    _operation: object | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    if manifest["schema_version"] == LINKED_SCHEMA:
        return prepare_targets(plan, source_facets, limits, scope_inputs=scope_inputs)
    if not isinstance(evidence, NeotomaLinkedEvidence):
        raise ValueError(
            "Scoped linked replay requires an externally anchored evidence resolver"
        )
    reference = {
        "schema_version": EVIDENCE_SCHEMA,
        "manifest_sha256": evidence.manifest_sha256,
    }
    if not _same_json(manifest["source_evidence"], reference) or not _same_json(
        control["source_evidence"], reference
    ):
        raise ValueError(
            "Scoped linked evidence reference differs from external anchor"
        )
    prepare = prepare_scoped_targets if _session is None else _prepare_scoped_targets
    session_options = (
        {} if _session is None else {"_session": _session, "_operation": _operation}
    )
    targets, policies, _ = prepare(
        plan,
        source_facets,
        limits,
        evidence=evidence,
        scope_inputs=scope_inputs,
        legacy_rosters=legacy_rosters,
        **session_options,
    )
    return targets, policies


def replay_neotoma_linked_resources(
    directory: Path,
    *,
    source_facets: Mapping[str, Path],
    expected_manifest_sha256: str | None = None,
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
    scope_inputs: Mapping[str, NeotomaFacetScopeInputs] | None = None,
    evidence: NeotomaLinkedEvidence | None = None,
    legacy_rosters: Mapping[str, Path] | None = None,
) -> NeotomaLinkedResourceCapture:
    """Original facet identities and every occurrence are recomputed, never trusted."""
    return _replay_linked_resources(
        directory,
        source_facets=source_facets,
        expected_manifest_sha256=expected_manifest_sha256,
        limits=limits,
        scope_inputs=scope_inputs,
        evidence=evidence,
        legacy_rosters=legacy_rosters,
    )


def _replay_linked_resources(
    directory: Path,
    *,
    source_facets: Mapping[str, Path],
    expected_manifest_sha256: str | None = None,
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
    scope_inputs: Mapping[str, NeotomaFacetScopeInputs] | None = None,
    evidence: NeotomaLinkedEvidence | None = None,
    legacy_rosters: Mapping[str, Path] | None = None,
    _session: Any = None,
    _operation: object | None = None,
) -> NeotomaLinkedResourceCapture:
    """Original facet identities and every occurrence are recomputed, never trusted."""
    from .evidence_parts.session import _check_session

    session_inputs = {
        "capture_directory": directory,
        "capture_manifest_sha256": expected_manifest_sha256,
        "operation": _operation,
        "evidence": evidence,
        "source_facets": source_facets,
        "scope_inputs": scope_inputs,
        "legacy_rosters": legacy_rosters,
    }
    if _session is not None:
        _check_session(_session, **session_inputs, full=True)
    root = _safe_root(directory)
    manifest, control, plan, recorded, digest = _control(root, expected_manifest_sha256)
    targets, policies = _targets_for_control(
        manifest,
        control,
        plan,
        source_facets,
        limits,
        scope_inputs=scope_inputs,
        evidence=evidence,
        legacy_rosters=legacy_rosters,
        _session=_session,
        _operation=_operation,
    )
    if manifest["schema_version"] == SCOPED_LINKED_SCHEMA:
        assert evidence is not None
        validate_scoped_limits(evidence, recorded)
    else:
        prepare_targets(plan, source_facets, recorded, scope_inputs=scope_inputs)
    if not _same_json(control["targets"], targets) or not _same_json(
        control["policy_sources"], policies
    ):
        raise ValueError("Neotoma linked target proof closure differs")
    entries = manifest["resources"]
    if not isinstance(entries, list) or len(entries) != len(targets):
        raise ValueError("Neotoma linked target population differs")
    maximum_requests = min(limits.max_requests, recorded.max_requests)
    maximum_attempts = min(limits.max_attempts, recorded.max_attempts)
    maximum_body = min(limits.max_response_bytes, recorded.max_response_bytes)
    maximum_total = min(limits.max_total_bytes, recorded.max_total_bytes)
    previous_end, end = (
        _utc(manifest["capture_utc_start"]),
        _utc(manifest["capture_utc_end"]),
    )
    if previous_end > end:
        raise ValueError("Neotoma linked capture timestamps are reversed")
    count = total = 0
    files = {"capture-manifest.json", "request-plan.json"}
    for entry, target in zip(entries, targets, strict=True):
        if _session is not None:
            _check_session(_session, **session_inputs)
        if (
            not isinstance(entry, dict)
            or entry.get("target_key") != target["target_key"]
            or not _same_json(entry.get("identity"), target)
            or entry.get("content_version") != "current"
            or entry.get("api_version") != "v2.0"
            or entry.get("scientific_admission") != "not_asserted"
            or not isinstance(entry.get("attempts"), list)
            or len(entry["attempts"]) > maximum_attempts
        ):
            raise ValueError("Neotoma linked target identity or attempts differ")
        assessed: dict[str, Any] = {"terminal_status": "not_attempted_budget"}
        if target["exposure_role"] not in DEVELOPMENT_ROLES:
            if entry["attempts"]:
                raise ValueError("Neotoma linked exposure role forbids body access")
            assessed = {
                "terminal_status": "not_attempted_exposure_role",
                "reason": target["exposure_role"],
            }
        for index, reference in enumerate(entry["attempts"], 1):
            if _session is not None:
                _check_session(_session, **session_inputs)
            count += 1
            if count > maximum_requests or total >= maximum_total:
                raise ValueError(
                    "Neotoma linked capture exceeds caller request or byte limits"
                )
            request = request_for(target, index)
            name = f"{request.name}.receipt.json"
            if (
                not isinstance(reference, dict)
                or reference.get("request_name") != request.name
                or reference.get("receipt_file") != name
            ):
                raise ValueError("Neotoma linked attempt reference differs")
            raw = _read(root / name, 1024 * 1024)
            if sha256(raw).hexdigest() != reference.get("receipt_sha256"):
                raise ValueError("Neotoma linked receipt identity differs")
            record = _object(raw)
            files.add(name)
            started, finished = (
                _utc(record.get("utc_start")),
                _utc(record.get("utc_end")),
            )
            if started < previous_end or finished < started or finished > end:
                raise ValueError("Neotoma linked attempt timestamps differ")
            previous_end = finished
            if record.get("terminal_status") == "transport_failure":
                if set(reference) != {
                    "request_name",
                    "receipt_file",
                    "receipt_sha256",
                } or set(record) != set(
                    _request_record(request, record["utc_start"])
                ) | {"utc_end", "terminal_status", "error", "body_complete"}:
                    raise ValueError("Neotoma linked transport fields differ")
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
                    raise ValueError("Neotoma linked body reference differs")
                bound = min(maximum_body, maximum_total - total)
                if _session is not None:
                    _check_session(_session, **session_inputs)
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
                raise ValueError("Neotoma linked retried a nontransient result")
        if set(entry) != _ENTRY_FIELDS | set(assessed) or not _same_json(
            {key: entry[key] for key in assessed}, assessed
        ):
            raise ValueError("Neotoma linked source assessment differs")
    partitions = dict(Counter(row["terminal_status"] for row in entries))
    if (
        type(manifest["request_count"]) is not int
        or type(manifest["response_bytes"]) is not int
        or manifest["request_count"] != count
        or manifest["response_bytes"] != total
        or not _same_json(manifest["partitions"], partitions)
    ):
        raise ValueError("Neotoma linked denominator closure differs")
    if (
        any(path.is_symlink() or not path.is_file() for path in root.iterdir())
        or {path.name for path in root.iterdir()} != files
    ):
        raise ValueError("Neotoma linked file inventory differs")
    if _session is not None:
        _check_session(_session, **session_inputs, full=True)
    return NeotomaLinkedResourceCapture(
        digest, tuple(entries), count, total, partitions
    )


def read_neotoma_linked_body(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    target_key: str,
    source_facets: Mapping[str, Path],
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
    scope_inputs: Mapping[str, NeotomaFacetScopeInputs] | None = None,
    evidence: NeotomaLinkedEvidence | None = None,
    legacy_rosters: Mapping[str, Path] | None = None,
) -> NeotomaLinkedBody:
    """Check inherited roles before body access, then hash the actual returned buffer."""
    root = _safe_root(directory)
    manifest, control, plan, _, _ = _control(root, expected_manifest_sha256)
    targets, _ = _targets_for_control(
        manifest,
        control,
        plan,
        source_facets,
        limits,
        scope_inputs=scope_inputs,
        evidence=evidence,
        legacy_rosters=legacy_rosters,
    )
    selected = [target for target in targets if target["target_key"] == target_key]
    if len(selected) != 1:
        raise ValueError("Neotoma linked target is absent or ambiguous")
    target = selected[0]
    if target["exposure_role"] not in DEVELOPMENT_ROLES:
        raise ValueError("Neotoma linked exposure role forbids body access")
    capture = replay_neotoma_linked_resources(
        root,
        expected_manifest_sha256=expected_manifest_sha256,
        source_facets=source_facets,
        scope_inputs=scope_inputs,
        evidence=evidence,
        legacy_rosters=legacy_rosters,
        limits=limits,
    )
    entry = next(row for row in capture.resources if row["target_key"] == target_key)
    return _read_linked_entry_body(root, entry, limits, evidence=evidence)


def _read_linked_entry_body(
    root: Path,
    entry: dict[str, Any],
    limits: NeotomaResourceLimits,
    *,
    evidence: NeotomaLinkedEvidence | None = None,
) -> NeotomaLinkedBody:
    target = entry["identity"]
    target_key = entry["target_key"]
    if target["exposure_role"] not in DEVELOPMENT_ROLES:
        raise ValueError("Neotoma linked exposure role forbids body access")
    if entry["terminal_status"] != "received_complete_unqualified_linked_resource":
        raise ValueError("Neotoma complete linked source entity is unavailable")
    proofs = target.get("source_proofs")
    if "source_proof_reference" in target:
        if not isinstance(evidence, NeotomaLinkedEvidence):
            raise ValueError("Scoped linked body requires its evidence resolver")
        proofs = read_neotoma_linked_evidence_target(
            evidence.directory,
            expected_manifest_sha256=evidence.manifest_sha256,
            kind=target["kind"],
            native_id=target["native_id"],
        )["source_proofs"]
    reference = entry["attempts"][-1]
    raw = _read(root / reference["receipt_file"], 1024 * 1024)
    if sha256(raw).hexdigest() != reference["receipt_sha256"]:
        raise ValueError("Neotoma linked receipt changed during body access")
    record = _object(raw)
    body = _read(root / reference["body_file"], limits.max_response_bytes)
    _validate_receipt(
        record,
        request_for(target, len(entry["attempts"])),
        body,
        limits.max_response_bytes,
    )
    return NeotomaLinkedBody(
        target_key,
        body,
        sha256(body).hexdigest(),
        reference["receipt_sha256"],
        tuple(proofs),
    )
