"""Close a finite resource ledger without confusing source failures with admission."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
import time
from typing import Any

from bijux_pollenomics.core.filesystem import OwnedTreeWriter
from bijux_pollenomics.core.owned_tree import (
    build_staging_output_dir,
    publish_new_output_tree,
)

from ..receipts import (
    _retain_http_response,
    _retain_transport_failure,
    _safe_root,
    _write_json,
)
from ..transport import NeotomaHttpResponse, _fetch_response
from .assessment import ASSESSMENT_FIELDS, QUALIFIED_STATUSES, assess_http
from .models import (
    DEFAULT_RESOURCE_LIMITS,
    DEVELOPMENT_ROLES,
    RESOURCE_SCHEMA,
    NeotomaResourceCapture,
    NeotomaResourceLimits,
    NeotomaResourcePlan,
    NeotomaRetainedSource,
)
from .protocol import identity, request_for, resource_key, validate_plan
from .replay import replay_neotoma_resource_capture
from .retained import read_retained_source


def capture_neotoma_resources(
    directory: Path,
    *,
    plan: NeotomaResourcePlan,
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
    reuse_from: Mapping[str, Path] | None = None,
    source_captures: Mapping[str, Path] | None = None,
    retained_sources: Mapping[str, NeotomaRetainedSource] | None = None,
    retry_failed: bool = False,
    fetch: Callable[..., NeotomaHttpResponse] = _fetch_response,
) -> NeotomaResourceCapture:
    """Retain each attempt and close every requested version, one body at a time.

    Injected fetch callbacks are trusted test/adapter boundaries; actual source
    provenance requires the pinned default transport. Reuse authenticates a
    prior closed ledger and retains its original statuses and request times.
    ``reuse_from`` selects direct prior results; ``source_captures`` supplies
    their ancestor resolvers without selecting those ancestors as competitors.
    """
    validate_plan(plan, limits)
    if type(retry_failed) is not bool:
        raise ValueError("Neotoma resource retry control must be boolean")
    final = _safe_root(directory)
    if final.exists():
        raise FileExistsError(f"Neotoma resource output already exists: {final}")
    selected = dict(reuse_from or {})
    sources = {**(source_captures or {}), **selected}
    retained = dict(retained_sources or {})
    previous = {}
    requested_keys = {
        resource_key(resource, version)
        for resource in plan.resources
        for version in resource.versions
    }
    for digest, source in selected.items():
        result = replay_neotoma_resource_capture(
            source,
            expected_manifest_sha256=digest,
            source_captures=sources,
            retained_sources=retained_sources,
            limits=limits,
        )
        if not any(row["resource_key"] in requested_keys for row in result.resources):
            raise ValueError("Selected Neotoma input capture has no requested resource")
        for row in result.resources:
            if row["resource_key"] in previous:
                raise ValueError("Ambiguous prior Neotoma resource result")
            previous[row["resource_key"]] = (digest, row)
    for resource in plan.resources:
        for version in resource.versions:
            prior = previous.get(resource_key(resource, version))
            if prior is not None and prior[1]["identity"] != identity(resource):
                raise ValueError("Prior Neotoma resource request identity differs")
    staging = build_staging_output_dir(final)
    receipt_allowance = limits.max_requests * 64 * 1024
    manifest_allowance = 16 * 1024 * 1024
    with OwnedTreeWriter(
        staging,
        max_bytes=limits.max_total_bytes + receipt_allowance + manifest_allowance,
        max_files=limits.max_requests * 2 + 4,
    ) as writer:
        started = datetime.now(UTC).isoformat()
        wall_start = time.monotonic()
        request_count = 0
        total = 0
        entries = []
        plan_digest = _write_json(
            staging / "request-plan.json",
            {
                "schema_version": RESOURCE_SCHEMA,
                "plan": asdict(plan),
                "limits": asdict(limits),
                "input_captures": sorted(selected),
                "retry_failed": retry_failed,
                "historical_snapshot_replaced": False,
            },
            writer=writer,
        )
        try:
            for resource in sorted(plan.resources, key=lambda row: row.dataset_id):
                for version in resource.versions:
                    key = resource_key(resource, version)
                    entry: dict[str, Any] = {
                        "resource_key": key,
                        "dataset_id": resource.dataset_id,
                        "version": version,
                        "identity": identity(resource),
                        "attempts": [],
                        "scientific_admission": "not_asserted",
                    }
                    if resource.exposure_role not in DEVELOPMENT_ROLES:
                        entry.update(
                            terminal_status="not_attempted_exposure_role",
                            reason=resource.exposure_role,
                        )
                        entries.append(entry)
                        continue
                    if key in retained:
                        reference, summary = read_retained_source(
                            resource,
                            version,
                            retained[key],
                            limits.max_response_bytes,
                        )
                        entry.update(
                            terminal_status="reused_qualified_native",
                            retained_source=reference,
                            summary=summary,
                        )
                        entries.append(entry)
                        continue
                    prior = previous.get(key)
                    if prior is not None and (
                        not retry_failed
                        or prior[1]["terminal_status"] in QUALIFIED_STATUSES
                    ):
                        entry = deepcopy(prior[1])
                        entry["attempts"] = []
                        entry["reused_from"] = {
                            "manifest_sha256": prior[0],
                            "resource_key": key,
                        }
                        entries.append(entry)
                        continue
                    if prior is not None:
                        entry["predecessor_result"] = {
                            "manifest_sha256": prior[0],
                            "resource_key": key,
                            "terminal_status": prior[1]["terminal_status"],
                        }
                    entry["terminal_status"] = "not_attempted_budget"
                    for attempt in range(1, limits.max_attempts + 1):
                        if (
                            request_count >= limits.max_requests
                            or total >= limits.max_total_bytes
                            or time.monotonic() - wall_start >= limits.wall_seconds
                        ):
                            break
                        for field in ASSESSMENT_FIELDS:
                            entry.pop(field, None)
                        request = request_for(resource, version, attempt)
                        request_count += 1
                        bound = min(
                            limits.max_response_bytes, limits.max_total_bytes - total
                        )
                        request_start = datetime.now(UTC).isoformat()
                        transient = False
                        try:
                            response = fetch(
                                request.url,
                                timeout=min(
                                    limits.timeout_seconds,
                                    max(
                                        0.001,
                                        limits.wall_seconds
                                        - (time.monotonic() - wall_start),
                                    ),
                                ),
                                max_bytes=bound,
                            )
                        except Exception as error:
                            reference, record = _retain_transport_failure(
                                staging, request, request_start, error, writer=writer
                            )
                            entry["attempts"].append(reference)
                            entry.update(
                                terminal_status="transport_failure",
                                reason=record["error"],
                            )
                            transient = True
                        else:
                            reference, record = _retain_http_response(
                                staging, request, response, request_start, writer=writer
                            )
                            entry["attempts"].append(reference)
                            total += len(response.body)
                            entry.update(
                                assess_http(
                                    resource,
                                    version,
                                    record,
                                    request,
                                    response.body,
                                    bound,
                                )
                            )
                            transient = (
                                response.http_status == 429
                                or 500 <= response.http_status <= 599
                            )
                            del response
                        if not transient or attempt == limits.max_attempts:
                            break
                        if limits.retry_delay_seconds:
                            time.sleep(
                                min(
                                    limits.retry_delay_seconds,
                                    max(
                                        0.0,
                                        limits.wall_seconds
                                        - (time.monotonic() - wall_start),
                                    ),
                                )
                            )
                    entries.append(entry)
            partitions = dict(Counter(row["terminal_status"] for row in entries))
            _write_json(
                staging / "capture-manifest.json",
                {
                    "schema_version": RESOURCE_SCHEMA,
                    "status": "closed",
                    "capture_utc_start": started,
                    "capture_utc_end": datetime.now(UTC).isoformat(),
                    "plan_sha256": plan_digest,
                    "resources": entries,
                    "request_count": request_count,
                    "response_bytes": total,
                    "partitions": partitions,
                    "all_resources_parsed": all(
                        row["terminal_status"] == "parsed_native" for row in entries
                    ),
                    "scientific_admission": "not_asserted",
                    "snapshot_consistency": "individually timed live or explicitly reused responses; no transaction snapshot",
                },
                writer=writer,
            )
            result = replay_neotoma_resource_capture(
                staging,
                source_captures=sources,
                retained_sources=retained_sources,
                limits=limits,
            )
            writer.validate_attachment()
            publish_new_output_tree(
                final_output_root=final, staging_output_root=staging
            )
            return replay_neotoma_resource_capture(
                final,
                expected_manifest_sha256=result.manifest_sha256,
                source_captures=sources,
                retained_sources=retained_sources,
                limits=limits,
            )
        except Exception as error:
            if staging.exists():
                writer.validate_attachment()
                _write_json(
                    staging / "refusal.json",
                    {
                        "schema_version": RESOURCE_SCHEMA,
                        "status": "refused_execution",
                        "error": f"{type(error).__name__}: {error}",
                        "request_count": request_count,
                        "response_bytes": total,
                    },
                    writer=writer,
                )
            raise
