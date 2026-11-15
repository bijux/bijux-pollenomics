"""Exclusive metadata attempts and atomic publication of complete captures."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from bijux_pollenomics.core.filesystem import OwnedTreeWriter
from bijux_pollenomics.core.owned_tree import (
    build_staging_output_dir,
)

from ..publication.ownership import publish_owned_source_tree
from .models import (
    _SCHEMA,
    DEFAULT_METADATA_LIMITS,
    NeotomaMetadataCapture,
    NeotomaMetadataLimits,
    NeotomaMetadataPlan,
    NeotomaMetadataResponse,
    _Request,
)
from .protocol import _validate_plan, _walk_plan
from .receipts import (
    _retain_http_response,
    _retain_transport_failure,
    _safe_root,
    _validate_receipt,
    _write_json,
)
from .replay import replay_neotoma_metadata_capture
from .transport import _fetch_response


def capture_neotoma_metadata(
    directory: Path,
    *,
    plan: NeotomaMetadataPlan,
    limits: NeotomaMetadataLimits = DEFAULT_METADATA_LIMITS,
    fetch: Callable[..., NeotomaMetadataResponse] = _fetch_response,
) -> NeotomaMetadataCapture:
    """Publish complete metadata, retaining refused attempts in exclusive staging.

    The default transport sends the recorded fixed headers with verified TLS.
    An injected fetch callback is a trusted test/adapter boundary responsible for
    that same HTTP contract; its provenance cannot be authenticated by parsing
    the returned bytes. Actual provider captures must pin the transport used.
    Replay requires UTC request intervals to follow their declared serial order.
    """
    _validate_plan(plan, limits)
    final = _safe_root(directory)
    if final.exists():
        raise FileExistsError(f"Neotoma metadata output already exists: {final}")
    staging = build_staging_output_dir(final)
    receipt_allowance = limits.max_requests * 64 * 1024
    manifest_allowance = 16 * 1024 * 1024
    with OwnedTreeWriter(
        staging,
        max_bytes=limits.max_total_bytes + receipt_allowance + manifest_allowance,
        max_files=limits.max_requests * 2 + 4,
    ) as writer:
        started = datetime.now(UTC).isoformat()
        declared_plan = asdict(plan)
        if not plan.geopolitical_unit_ids:
            del declared_plan["geopolitical_unit_ids"]
        plan_digest = _write_json(
            staging / "request-plan.json",
            {
                "schema_version": _SCHEMA,
                "plan": declared_plan,
                "limits": asdict(limits),
                "exposure_role": "metadata_only; no samples or observation outcomes",
                "historical_capture_replaced": False,
            },
            writer=writer,
        )
        records: list[dict[str, object]] = []
        total = 0

        def consume(request: _Request) -> bytes:
            nonlocal total
            if len(records) >= limits.max_requests or total >= limits.max_total_bytes:
                raise ValueError(
                    "Neotoma metadata request or total-byte budget exhausted"
                )
            bound = min(limits.max_response_bytes, limits.max_total_bytes - total)
            request_started = datetime.now(UTC).isoformat()
            try:
                response = fetch(
                    request.url, timeout=limits.timeout_seconds, max_bytes=bound
                )
            except Exception as error:
                _retain_transport_failure(
                    staging, request, request_started, error, writer=writer
                )
                raise
            reference, record = _retain_http_response(
                staging, request, response, request_started, writer=writer
            )
            records.append(
                {key: value for key, value in reference.items() if key != "body_file"}
            )
            total += len(response.body)
            _validate_receipt(record, request, response.body, bound)
            return response.body

        try:
            _walk_plan(plan, limits, consume)
            manifest_digest = _write_json(
                staging / "capture-manifest.json",
                {
                    "schema_version": _SCHEMA,
                    "status": "complete",
                    "capture_utc_start": started,
                    "capture_utc_end": datetime.now(UTC).isoformat(),
                    "plan_file": "request-plan.json",
                    "plan_sha256": plan_digest,
                    "records": records,
                    "request_count": len(records),
                    "response_bytes": total,
                    "snapshot_consistency": "sequential_live_responses; no transaction snapshot",
                    "scientific_admission": "not_asserted",
                },
                writer=writer,
            )
            return publish_owned_source_tree(
                writer,
                staging=staging,
                final=final,
                validate=lambda location: replay_neotoma_metadata_capture(
                    location, expected_manifest_sha256=manifest_digest, limits=limits
                ),
            )
        except Exception as error:
            if staging.exists():
                writer.validate_attachment()
                _write_json(
                    staging / "refusal.json",
                    {
                        "schema_version": _SCHEMA,
                        "status": "refused",
                        "utc_end": datetime.now(UTC).isoformat(),
                        "error": f"{type(error).__name__}: {error}",
                        "completed_http_request_count": len(records),
                        "response_bytes": total,
                    },
                    writer=writer,
                )
            raise
