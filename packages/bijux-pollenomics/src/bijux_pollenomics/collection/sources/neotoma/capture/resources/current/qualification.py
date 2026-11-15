"""Authenticate a separate current-source profile without changing capture ledgers."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from typing import Any

from ...receipts import _object, _read, _safe_root, _validate_receipt
from ..models import (
    DEFAULT_RESOURCE_LIMITS,
    DEVELOPMENT_ROLES,
    NeotomaResourceLimits,
    NeotomaRetainedSource,
)
from ..profiles import _TYPES as LEGACY_CURRENT_TYPES
from ..protocol import identity, plan_from_json, request_for, resource_key
from ..replay import replay_neotoma_resource_capture
from .profiles import (
    CURRENT_SOURCE_TYPES,
    _UnavailableCurrentSource,
    parse_neotoma_current_source,
    summarize_current_source,
)


def _pinned(path: Path, digest: str, bound: int) -> dict[str, Any]:
    content = _read(path, bound)
    if sha256(content).hexdigest() != digest:
        raise ValueError("Current source qualification metadata identity differs")
    return _object(content)


def qualify_neotoma_current_capture(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    source_captures: Mapping[str, Path] | None = None,
    retained_sources: Mapping[str, NeotomaRetainedSource] | None = None,
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
) -> dict[str, Any]:
    """Qualify the five observed proxy types separately from original v1 results.

    Replay authenticates the original acquisition and reuse graph. The exact
    selected HTTP buffer is authenticated again before decoding; an unsupported
    v1 result remains unsupported in that original ledger. Frozen responses and
    existing v1 profiles retain their independent qualification owners.
    """
    sources = source_captures or {}
    captured = replay_neotoma_resource_capture(
        directory,
        expected_manifest_sha256=expected_manifest_sha256,
        source_captures=sources,
        retained_sources=retained_sources,
        limits=limits,
    )
    root = _safe_root(directory)
    manifest = _pinned(
        root / "capture-manifest.json", captured.manifest_sha256, 16 * 1024 * 1024
    )
    control = _pinned(
        root / "request-plan.json", manifest["plan_sha256"], 4 * 1024 * 1024
    )
    plan, recorded = plan_from_json(control)
    specs = {spec.dataset_id: spec for spec in plan.resources}
    rows = []
    for entry in captured.resources:
        if entry["version"] != "current":
            continue
        spec = specs[entry["dataset_id"]]
        row: dict[str, Any] = {
            "resource_key": resource_key(spec, "current"),
            "dataset_id": spec.dataset_id,
            "root_identity": identity(spec),
            "source_terminal_status": entry["terminal_status"],
            "scientific_admission": "not_asserted",
        }
        rows.append(row)
        if spec.exposure_role not in DEVELOPMENT_ROLES:
            row["qualification_status"] = "not_qualified_exposure_role"
            continue
        if spec.dataset_type not in CURRENT_SOURCE_TYPES:
            row["qualification_status"] = (
                "not_applicable_existing_native_profile"
                if spec.dataset_type in LEGACY_CURRENT_TYPES
                else "not_qualified_dataset_type"
            )
            continue
        if entry["terminal_status"] != "unsupported_dataset_type":
            row["qualification_status"] = "not_qualified_source_result"
            continue
        source_root, source_digest, source_entry = root, captured.manifest_sha256, entry
        while "reused_from" in source_entry:
            source_digest = source_entry["reused_from"]["manifest_sha256"]
            source_root = _safe_root(sources[source_digest])
            previous = _pinned(
                source_root / "capture-manifest.json", source_digest, 16 * 1024 * 1024
            )
            source_entry = next(
                item
                for item in previous["resources"]
                if item["resource_key"] == row["resource_key"]
            )
        reference = source_entry["attempts"][-1]
        receipt = _pinned(
            source_root / reference["receipt_file"], reference["receipt_sha256"], 65536
        )
        bound = min(limits.max_response_bytes, recorded.max_response_bytes)
        body = _read(source_root / reference["body_file"], bound)
        if sha256(body).hexdigest() != receipt["retained_body_sha256"]:
            raise ValueError(
                "Current qualification actual source buffer identity differs"
            )
        _validate_receipt(
            receipt,
            request_for(spec, "current", len(source_entry["attempts"])),
            body,
            bound,
        )
        row["source"] = {
            "capture_manifest_sha256": source_digest,
            "resource_key": row["resource_key"],
            "content_version": "current",
            "api_version": "v2.0",
            "receipt_file": reference["receipt_file"],
            "receipt_sha256": reference["receipt_sha256"],
            "body_file": reference["body_file"],
            "body_sha256": receipt["retained_body_sha256"],
            "utc_start": receipt["utc_start"],
            "utc_end": receipt["utc_end"],
            "requested_url": receipt["requested_url"],
            "tls_mode": receipt["tls_mode"],
        }
        try:
            parsed = parse_neotoma_current_source(
                spec, body, expected_body_sha256=receipt["retained_body_sha256"]
            )
            row.update(
                qualification_status="parsed_current_source",
                summary=summarize_current_source(parsed),
            )
        except _UnavailableCurrentSource as error:
            row.update(
                qualification_status="unavailable_current_api_empty",
                reason=str(error),
                absence_certified=False,
            )
        except ValueError as error:
            row.update(qualification_status="refused_current_source", reason=str(error))
    return {
        "schema_version": "neotoma-current-source-qualification.v1",
        "source_capture_manifest_sha256": captured.manifest_sha256,
        "source_capture_relabelled": False,
        "resources": rows,
        "scientific_admission": "not_asserted",
    }
