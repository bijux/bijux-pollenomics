"""Close bounded role-admitted facet requests through the existing HTTP owner."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
import time
from typing import Any

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
from ..resources.models import (
    DEFAULT_RESOURCE_LIMITS,
    DEVELOPMENT_ROLES,
    NeotomaResourceLimits,
    NeotomaResourcePlan,
)
from ..transport import NeotomaHttpResponse, _fetch_response
from .assessment import assess_http
from .models import FACET_SCHEMA, NeotomaFacetCapture, NeotomaFacetPlan
from .protocol import facet_identity, request_for, validate_plan
from .replay import SNAPSHOT_CONSISTENCY, replay_neotoma_facet_capture


def capture_neotoma_dataset_facets(
    directory: Path,
    *,
    plan: NeotomaFacetPlan,
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
    staging = build_staging_output_dir(final)
    staging.mkdir(exist_ok=False)
    started = datetime.now(UTC).isoformat()
    wall_start = time.monotonic()
    requests = total = 0
    entries: list[dict[str, Any]] = []
    try:
        plan_digest = _write_json(
            staging / "request-plan.json",
            {
                "schema_version": FACET_SCHEMA,
                "plan": asdict(plan),
                "limits": asdict(limits),
                "policy_sources": NeotomaResourcePlan(
                    plan.resources, plan.roster_sha256
                ).policy_sources,
                "historical_snapshot_replaced": False,
            },
        )
        for resource in sorted(plan.resources, key=lambda row: row.dataset_id):
            for facet in plan.facets:
                entry: dict[str, Any] = {
                    **facet_identity(resource, facet),
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
                assessed: dict[str, Any] = {"terminal_status": "not_attempted_budget"}
                for attempt in range(1, limits.max_attempts + 1):
                    remaining = limits.wall_seconds - (time.monotonic() - wall_start)
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
                            staging, request, request_start, error
                        )
                        assessed = {
                            "terminal_status": "transport_failure",
                            "reason": record["error"],
                        }
                        transient = True
                    else:
                        reference, record = _retain_http_response(
                            staging, request, response, request_start
                        )
                        total += len(response.body)
                        assessed = assess_http(record, request, response.body, bound)
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
        _write_json(
            staging / "capture-manifest.json",
            {
                "schema_version": FACET_SCHEMA,
                "status": "closed",
                "capture_utc_start": started,
                "capture_utc_end": datetime.now(UTC).isoformat(),
                "plan_sha256": plan_digest,
                "facets": entries,
                "request_count": requests,
                "response_bytes": total,
                "partitions": dict(Counter(row["terminal_status"] for row in entries)),
                "scientific_admission": "not_asserted",
                "snapshot_consistency": SNAPSHOT_CONSISTENCY,
            },
        )
        result = replay_neotoma_facet_capture(staging, limits=limits)
        publish_new_output_tree(final_output_root=final, staging_output_root=staging)
        return result
    except Exception as error:
        _write_json(
            staging / "refusal.json",
            {
                "schema_version": FACET_SCHEMA,
                "status": "refused_execution",
                "error": f"{type(error).__name__}: {error}",
                "request_count": requests,
                "response_bytes": total,
            },
        )
        raise
