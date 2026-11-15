"""Bounded detail capture through verified transport and existing receipt owners."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
import time
from typing import Any

from bijux_pollenomics.core.filesystem import OwnedTreeWriter
from bijux_pollenomics.core.owned_tree import (
    build_staging_output_dir,
    publish_new_output_tree,
)

from ..facets.models import NeotomaFacetScopeInputs
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
)
from ..transport import NeotomaHttpResponse, _fetch_response
from .assessment import assess_http
from .models import (
    SCOPED_LINKED_SCHEMA,
    NeotomaLinkedEvidence,
    NeotomaLinkedResourceCapture,
    NeotomaLinkedResourcePlan,
)
from .protocol import (
    MAX_MANIFEST_BYTES,
    encoded_control,
    prepare_scoped_targets,
    request_for,
    scoped_control,
)
from .replay import SNAPSHOT_CONSISTENCY, replay_neotoma_linked_resources


def capture_neotoma_linked_resources(
    directory: Path,
    *,
    plan: NeotomaLinkedResourcePlan,
    source_facets: Mapping[str, Path],
    evidence: NeotomaLinkedEvidence,
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
    scope_inputs: Mapping[str, NeotomaFacetScopeInputs] | None = None,
    legacy_rosters: Mapping[str, Path] | None = None,
    fetch: Callable[..., NeotomaHttpResponse] = _fetch_response,
) -> NeotomaLinkedResourceCapture:
    """Capture selected direct references; no recursive expansion or schema admission."""
    targets, policies, source_reference = prepare_scoped_targets(
        plan,
        source_facets,
        limits,
        evidence=evidence,
        scope_inputs=scope_inputs,
        legacy_rosters=legacy_rosters,
    )
    final = _safe_root(directory)
    if final.exists():
        raise FileExistsError(f"Neotoma linked output exists: {final}")
    staging = build_staging_output_dir(final)
    receipt_allowance = limits.max_requests * 64 * 1024
    manifest_allowance = 2 * 16 * 1024 * 1024
    with OwnedTreeWriter(
        staging,
        max_bytes=limits.max_total_bytes + receipt_allowance + manifest_allowance,
        max_files=limits.max_requests * 2 + 4,
    ) as writer:
        started = datetime.now(UTC).isoformat()
        wall_start = time.monotonic()
        count = total = 0
        entries: list[dict[str, Any]] = []
        try:
            plan_digest = _write_json(
                staging / "request-plan.json",
                scoped_control(plan, limits, targets, policies, source_reference),
                writer=writer,
            )
            for target in targets:
                entry: dict[str, Any] = {
                    "target_key": target["target_key"],
                    "identity": target,
                    "content_version": "current",
                    "api_version": "v2.0",
                    "attempts": [],
                    "scientific_admission": "not_asserted",
                }
                if target["exposure_role"] not in DEVELOPMENT_ROLES:
                    entry.update(
                        terminal_status="not_attempted_exposure_role",
                        reason=target["exposure_role"],
                    )
                    entries.append(entry)
                    continue
                assessed: dict[str, Any] = {"terminal_status": "not_attempted_budget"}
                for attempt in range(1, limits.max_attempts + 1):
                    remaining = limits.wall_seconds - (time.monotonic() - wall_start)
                    if (
                        count >= limits.max_requests
                        or total >= limits.max_total_bytes
                        or remaining <= 0
                    ):
                        break
                    request = request_for(target, attempt)
                    count += 1
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
            manifest = {
                "schema_version": SCOPED_LINKED_SCHEMA,
                "source_evidence": source_reference,
                "status": "closed",
                "capture_utc_start": started,
                "capture_utc_end": datetime.now(UTC).isoformat(),
                "plan_sha256": plan_digest,
                "resources": entries,
                "request_count": count,
                "response_bytes": total,
                "partitions": dict(Counter(row["terminal_status"] for row in entries)),
                "scientific_admission": "not_asserted",
                "snapshot_consistency": SNAPSHOT_CONSISTENCY,
            }
            if len(encoded_control(manifest)) > MAX_MANIFEST_BYTES:
                raise ValueError(
                    "Linked capture manifest exceeds finite metadata byte budget"
                )
            _write_json(staging / "capture-manifest.json", manifest, writer=writer)
            verified = replay_neotoma_linked_resources(
                staging,
                source_facets=source_facets,
                limits=limits,
                scope_inputs=scope_inputs,
                evidence=evidence,
                legacy_rosters=legacy_rosters,
            )
            writer.validate_attachment()
            publish_new_output_tree(
                final_output_root=final, staging_output_root=staging
            )
            return replay_neotoma_linked_resources(
                final,
                expected_manifest_sha256=verified.manifest_sha256,
                source_facets=source_facets,
                scope_inputs=scope_inputs,
                evidence=evidence,
                legacy_rosters=legacy_rosters,
                limits=limits,
            )
        except Exception as error:
            if staging.exists():
                writer.validate_attachment()
                _write_json(
                    staging / "refusal.json",
                    {
                        "schema_version": SCOPED_LINKED_SCHEMA,
                        "status": "refused_execution",
                        "error": f"{type(error).__name__}: {error}",
                        "request_count": count,
                        "response_bytes": total,
                    },
                    writer=writer,
                )
            raise
