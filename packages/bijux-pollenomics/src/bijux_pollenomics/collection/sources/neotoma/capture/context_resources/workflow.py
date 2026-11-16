"""FD-owned literal HTTP capture after whole-site source-role preflight."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from hashlib import sha256
import json
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
from ..resources.models import NeotomaResourceLimits
from ..transport import NeotomaHttpResponse, _fetch_response
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
    native_dataset_ids,
    request_for,
    validate_new_capture_plan,
    validate_plan,
)
from .replay import replay_neotoma_context_resources
from .scope import prepare_scope


def capture_neotoma_context_resources(
    directory: Path,
    *,
    plan: NeotomaContextResourcePlan,
    context_directory: Path,
    native_archive_directory: Path,
    limits: NeotomaResourceLimits = DEFAULT_CONTEXT_LIMITS,
    fetch: Callable[..., NeotomaHttpResponse] = _fetch_response,
) -> NeotomaContextResourceCapture:
    """Freeze source scope before GET; retain unqualified HTTP entities once.

    The wall budget starts before source scope preparation. Injected fetchers
    are trusted testing/adapter boundaries, not verified network provenance.
    """
    validate_plan(plan, limits)
    final = _safe_root(directory)
    if final.exists():
        raise FileExistsError(f"Context resource output exists: {final}")
    validate_new_capture_plan(plan)
    start, wall_start = datetime.now(UTC).isoformat(), time.monotonic()
    scope = prepare_scope(
        plan,
        context_directory=context_directory,
        native_archive_directory=native_archive_directory,
    )
    scope_bytes = (
        json.dumps(scope, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2)
        + "\n"
    ).encode()
    if len(scope_bytes) > MAX_METADATA_BYTES:
        raise ValueError("Context parent proof exceeds its finite metadata budget")
    staging = build_staging_output_dir(final)
    with OwnedTreeWriter(staging, max_bytes=MAX_BYTES, max_files=MAX_FILES) as writer:
        rows: list[dict[str, Any]] = []
        count = total = 0
        try:
            writer.write_bytes("parent-scope.json", scope_bytes)
            scope_digest = sha256(scope_bytes).hexdigest()
            plan_digest = _write_json(
                staging / "request-plan.json",
                {
                    "schema_version": CONTEXT_SCHEMA,
                    "plan": asdict(plan),
                    "limits": asdict(limits),
                    "parent_scope_sha256": scope_digest,
                    "source_scope": SOURCE_SCOPE,
                    "policy_sources": list(POLICY_SOURCES),
                },
                writer=writer,
            )
            for kind in plan.resource_kinds:
                for parent in scope["requested_sites"]:
                    site_id = parent["site_id"]
                    entry: dict[str, Any] = {
                        "site_id": site_id,
                        "resource_kind": kind,
                        "content_version": "current",
                        "api_version": "v2.0",
                        "scope_status": parent["scope_status"],
                        "exposure_role": parent["effective_scope_role"],
                        "attempts": [],
                        "scientific_admission": "not_asserted",
                    }
                    remaining = limits.wall_seconds - (time.monotonic() - wall_start)
                    if parent["scope_status"] != "eligible_current_scope":
                        entry["terminal_status"] = "not_attempted_parent_scope"
                    elif (
                        count >= limits.max_requests
                        or total >= limits.max_total_bytes
                        or remaining <= 0
                    ):
                        entry["terminal_status"] = "not_attempted_budget"
                    else:
                        request = request_for(
                            kind,
                            site_id,
                            dataset_ids=native_dataset_ids(parent)
                            if kind == "dataset_depositional_environment"
                            else None,
                        )
                        count += 1
                        bound = min(
                            limits.max_response_bytes, limits.max_total_bytes - total
                        )
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
                            assessed = assess_http(
                                record, request, response.body, bound
                            )
                        entry["attempts"].append(reference)
                        entry.update(assessed)
                    rows.append(entry)
            manifest_digest = _write_json(
                staging / "capture-manifest.json",
                {
                    "schema_version": CONTEXT_SCHEMA,
                    "status": "closed",
                    "capture_utc_start": start,
                    "capture_utc_end": datetime.now(UTC).isoformat(),
                    "plan_sha256": plan_digest,
                    "resources": rows,
                    "request_count": count,
                    "response_bytes": total,
                    "partitions": dict(Counter(row["terminal_status"] for row in rows)),
                    "source_scope": SOURCE_SCOPE,
                    "snapshot_consistency": SNAPSHOT_CONSISTENCY,
                    "scientific_admission": "not_asserted",
                },
                writer=writer,
            )
            return publish_owned_source_tree(
                writer,
                staging=staging,
                final=final,
                validate=lambda location: replay_neotoma_context_resources(
                    location,
                    expected_manifest_sha256=manifest_digest,
                    expected_context_sha256=plan.context_manifest_sha256,
                    expected_native_archive_sha256=plan.native_archive_manifest_sha256,
                    context_directory=context_directory,
                    native_archive_directory=native_archive_directory,
                    limits=limits,
                ),
            )
        except Exception as error:
            if staging.exists():
                writer.validate_attachment()
                _write_json(
                    staging / "refusal.json",
                    {
                        "schema_version": CONTEXT_SCHEMA,
                        "status": "refused_execution",
                        "error": f"{type(error).__name__}: {error}",
                        "request_count": count,
                        "response_bytes": total,
                    },
                    writer=writer,
                )
            raise
