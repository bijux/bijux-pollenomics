"""Capture fixed reference prefixes through existing verified HTTP/receipt owners."""

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
    publish_new_output_tree,
)

from ..receipts import (
    _retain_http_response,
    _retain_transport_failure,
    _safe_root,
    _write_json,
)
from ..resources.models import NeotomaResourceLimits
from ..transport import NeotomaHttpResponse, _fetch_response
from .models import (
    DEFAULT_REFERENCE_LIMITS,
    METADATA_SCOPE,
    POLICY_SOURCES,
    REFERENCE_SCHEMA,
    NeotomaReferenceTableCapture,
    NeotomaReferenceTablePlan,
)
from .protocol import assess_http, request_for, validate_plan
from .replay import SNAPSHOT_CONSISTENCY, replay_neotoma_reference_tables


def capture_neotoma_reference_tables(
    directory: Path,
    *,
    plan: NeotomaReferenceTablePlan,
    limits: NeotomaResourceLimits = DEFAULT_REFERENCE_LIMITS,
    fetch: Callable[..., NeotomaHttpResponse] = _fetch_response,
) -> NeotomaReferenceTableCapture:
    """Fetch at most two single prefixes; no retries, pagination or table expansion.

    Injected callbacks are trusted test/adapter boundaries. Actual source HTTP
    provenance requires the maintained default verified transport.
    """
    validate_plan(plan, limits)
    final = _safe_root(directory)
    if final.exists():
        raise FileExistsError(f"Neotoma reference output exists: {final}")
    staging = build_staging_output_dir(final)
    receipt_allowance = limits.max_requests * 64 * 1024
    manifest_allowance = 16 * 1024 * 1024
    with OwnedTreeWriter(
        staging,
        max_bytes=limits.max_total_bytes + receipt_allowance + manifest_allowance,
        max_files=limits.max_requests * 2 + 4,
    ) as writer:
        start = datetime.now(UTC).isoformat()
        wall_start = time.monotonic()
        count = total = 0
        rows: list[dict[str, Any]] = []
        try:
            plan_digest = _write_json(
                staging / "request-plan.json",
                {
                    "schema_version": REFERENCE_SCHEMA,
                    "plan": asdict(plan),
                    "limits": asdict(limits),
                    "metadata_scope": METADATA_SCOPE,
                    "policy_sources": list(POLICY_SOURCES),
                },
                writer=writer,
            )
            for table in plan.tables:
                entry: dict[str, Any] = {
                    "table": table,
                    "content_version": "current",
                    "api_version": "v2.0",
                    "metadata_role": "reference_metadata",
                    "attempts": [],
                    "scientific_admission": "not_asserted",
                }
                remaining = limits.wall_seconds - (time.monotonic() - wall_start)
                if (
                    count >= limits.max_requests
                    or total >= limits.max_total_bytes
                    or remaining <= 0
                ):
                    entry["terminal_status"] = "not_attempted_budget"
                    rows.append(entry)
                    continue
                request = request_for(table)
                count += 1
                bound = min(limits.max_response_bytes, limits.max_total_bytes - total)
                started = datetime.now(UTC).isoformat()
                try:
                    response = fetch(
                        request.url,
                        timeout=min(limits.timeout_seconds, remaining),
                        max_bytes=bound,
                    )
                except Exception as error:
                    reference, record = _retain_transport_failure(
                        staging, request, started, error, writer=writer
                    )
                    assessed = {
                        "terminal_status": "transport_failure",
                        "reason": record["error"],
                    }
                else:
                    reference, record = _retain_http_response(
                        staging, request, response, started, writer=writer
                    )
                    total += len(response.body)
                    assessed = assess_http(record, request, response.body, bound)
                entry["attempts"].append(reference)
                entry.update(assessed)
                rows.append(entry)
            _write_json(
                staging / "capture-manifest.json",
                {
                    "schema_version": REFERENCE_SCHEMA,
                    "status": "closed",
                    "capture_utc_start": start,
                    "capture_utc_end": datetime.now(UTC).isoformat(),
                    "plan_sha256": plan_digest,
                    "tables": rows,
                    "request_count": count,
                    "response_bytes": total,
                    "partitions": dict(Counter(row["terminal_status"] for row in rows)),
                    "metadata_scope": METADATA_SCOPE,
                    "snapshot_consistency": SNAPSHOT_CONSISTENCY,
                    "scientific_admission": "not_asserted",
                },
                writer=writer,
            )
            verified = replay_neotoma_reference_tables(staging, limits=limits)
            writer.validate_attachment()
            publish_new_output_tree(
                final_output_root=final, staging_output_root=staging
            )
            return replay_neotoma_reference_tables(
                final, expected_manifest_sha256=verified.manifest_sha256, limits=limits
            )
        except Exception as error:
            if staging.exists():
                writer.validate_attachment()
                _write_json(
                    staging / "refusal.json",
                    {
                        "schema_version": REFERENCE_SCHEMA,
                        "status": "refused_execution",
                        "error": f"{type(error).__name__}: {error}",
                        "request_count": count,
                        "response_bytes": total,
                    },
                    writer=writer,
                )
            raise
