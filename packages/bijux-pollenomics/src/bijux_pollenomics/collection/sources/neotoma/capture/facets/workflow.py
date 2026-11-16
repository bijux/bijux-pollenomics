"""Close bounded role-admitted facet requests through the existing HTTP owner."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
import time
from typing import Any

from bijux_pollenomics.core.filesystem import OwnedTreeWriter
from bijux_pollenomics.core.owned_tree import (
    build_staging_output_dir,
)

from ...publication.ownership import publish_owned_source_tree
from ..receipts import (
    _retain_http_response,
    _retain_transport_failure,
    _safe_root,
    _write_json,
)
from ..resources.models import (
    DEFAULT_RESOURCE_LIMITS,
    DEVELOPMENT_ROLES,
    NeotomaResourceLimits,
    NeotomaResourcePlan,
)
from ..transport import NeotomaHttpResponse, _fetch_response
from .assessment import assess_http
from .models import (
    SCOPED_FACET_SCHEMA,
    NeotomaFacetCapture,
    NeotomaFacetPlan,
    NeotomaFacetScopeInputs,
)
from .protocol import facet_identity, request_for, validate_plan
from .replay import SNAPSHOT_CONSISTENCY, replay_neotoma_facet_capture
from .scope import prepare_facet_parent_scope


def capture_neotoma_dataset_facets(
    directory: Path,
    *,
    plan: NeotomaFacetPlan,
    scope: NeotomaFacetScopeInputs,
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
    fetch: Callable[..., NeotomaHttpResponse] = _fetch_response,
) -> NeotomaFacetCapture:
    """Retain attempts as source evidence, without qualifying a native facet schema.

    Chronology and lithology are numerical source access. Every facet inherits
    the exact parent resource role, including projects/publications/taxa. Injected
    transports are trusted adapter boundaries, not verified HTTP provenance.
    """
    validate_plan(plan, limits)
    final = _safe_root(directory)
    if final.exists():
        raise FileExistsError(f"Neotoma facet output exists: {final}")
    parent_scope = prepare_facet_parent_scope(plan, scope)
    parents = {row["dataset_id"]: row for row in parent_scope["parents"]}
    staging = build_staging_output_dir(final)
    receipt_allowance = limits.max_requests * 64 * 1024
    manifest_allowance = 16 * 1024 * 1024
    parent_scope_allowance = 16 * 1024 * 1024
    with OwnedTreeWriter(
        staging,
        max_bytes=limits.max_total_bytes
        + receipt_allowance
        + manifest_allowance
        + parent_scope_allowance,
        max_files=limits.max_requests * 2 + 4,
    ) as writer:
        started = datetime.now(UTC).isoformat()
        wall_start = time.monotonic()
        requests = total = 0
        entries: list[dict[str, Any]] = []
        try:
            scope_digest = _write_json(
                staging / "parent-scope.json",
                parent_scope,
                writer=writer,
            )
            plan_digest = _write_json(
                staging / "request-plan.json",
                {
                    "schema_version": SCOPED_FACET_SCHEMA,
                    "parent_scope": {
                        "file": "parent-scope.json",
                        "sha256": scope_digest,
                    },
                    "plan": asdict(plan),
                    "limits": asdict(limits),
                    "policy_sources": NeotomaResourcePlan(
                        plan.resources, plan.roster_sha256
                    ).policy_sources,
                    "historical_snapshot_replaced": False,
                },
                writer=writer,
            )
            for resource in sorted(plan.resources, key=lambda row: row.dataset_id):
                for facet in plan.facets:
                    entry: dict[str, Any] = {
                        **facet_identity(resource, facet),
                        "attempts": [],
                        "scientific_admission": "not_asserted",
                        "parent_scope_role": parents[resource.dataset_id][
                            "effective_scope_role"
                        ],
                    }
                    if resource.exposure_role not in DEVELOPMENT_ROLES:
                        entry.update(
                            terminal_status="not_attempted_exposure_role",
                            reason=resource.exposure_role,
                        )
                        entries.append(entry)
                        continue
                    if entry["parent_scope_role"] not in DEVELOPMENT_ROLES:
                        entry.update(
                            terminal_status="not_attempted_parent_scope",
                            reason=entry["parent_scope_role"],
                        )
                        entries.append(entry)
                        continue
                    assessed: dict[str, Any] = {
                        "terminal_status": "not_attempted_budget"
                    }
                    for attempt in range(1, limits.max_attempts + 1):
                        remaining = limits.wall_seconds - (
                            time.monotonic() - wall_start
                        )
                        if (
                            requests >= limits.max_requests
                            or total >= limits.max_total_bytes
                            or remaining <= 0
                        ):
                            break
                        request = request_for(resource, facet, attempt)
                        requests += 1
                        bound = min(
                            limits.max_response_bytes, limits.max_total_bytes - total
                        )
                        request_start = datetime.now(UTC).isoformat()
                        try:
                            response = fetch(
                                request.url,
                                timeout=min(limits.timeout_seconds, remaining),
                                max_bytes=bound,
                            )
                        except Exception as error:
                            reference, record = _retain_transport_failure(
                                staging,
                                request,
                                request_start,
                                error,
                                writer=writer,
                            )
                            assessed = {
                                "terminal_status": "transport_failure",
                                "reason": record["error"],
                            }
                            transient = True
                        else:
                            reference, record = _retain_http_response(
                                staging,
                                request,
                                response,
                                request_start,
                                writer=writer,
                            )
                            total += len(response.body)
                            assessed = assess_http(
                                record, request, response.body, bound
                            )
                            transient = (
                                response.http_status == 429
                                or 500 <= response.http_status <= 599
                            )
                        entry["attempts"].append(reference)
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
                    entry.update(assessed)
                    entries.append(entry)
            manifest_digest = _write_json(
                staging / "capture-manifest.json",
                {
                    "schema_version": SCOPED_FACET_SCHEMA,
                    "status": "closed",
                    "capture_utc_start": started,
                    "capture_utc_end": datetime.now(UTC).isoformat(),
                    "plan_sha256": plan_digest,
                    "facets": entries,
                    "request_count": requests,
                    "response_bytes": total,
                    "partitions": dict(
                        Counter(row["terminal_status"] for row in entries)
                    ),
                    "scientific_admission": "not_asserted",
                    "snapshot_consistency": SNAPSHOT_CONSISTENCY,
                },
                writer=writer,
            )
            return publish_owned_source_tree(
                writer,
                staging=staging,
                final=final,
                validate=lambda location: replay_neotoma_facet_capture(
                    location,
                    expected_manifest_sha256=manifest_digest,
                    limits=limits,
                    scope_inputs={plan.roster_sha256: scope},
                ),
            )
        except Exception as error:
            if staging.exists():
                writer.validate_attachment()
                _write_json(
                    staging / "refusal.json",
                    {
                        "schema_version": SCOPED_FACET_SCHEMA,
                        "status": "refused_execution",
                        "error": f"{type(error).__name__}: {error}",
                        "request_count": requests,
                        "response_bytes": total,
                    },
                    writer=writer,
                )
            raise
