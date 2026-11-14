"""Exclusive metadata attempts and atomic publication of complete captures."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from bijux_pollenomics.core.owned_tree import (
    build_staging_output_dir,
    publish_new_output_tree,
)

from .models import (
    _HEADERS,
    _SCHEMA,
    DEFAULT_METADATA_LIMITS,
    NeotomaMetadataCapture,
    NeotomaMetadataLimits,
    NeotomaMetadataPlan,
    NeotomaMetadataResponse,
    _Request,
)
from .protocol import _validate_plan, _walk_plan
from .receipts import _safe_root, _validate_receipt, _write_json
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
    staging.mkdir(exist_ok=False)
    started = datetime.now(UTC).isoformat()
    plan_digest = _write_json(
        staging / "request-plan.json",
        {
            "schema_version": _SCHEMA,
            "plan": asdict(plan),
            "limits": asdict(limits),
            "exposure_role": "metadata_only; no samples or observation outcomes",
            "historical_capture_replaced": False,
        },
    )
    records: list[dict[str, object]] = []
    total = 0

    def consume(request: _Request) -> bytes:
        nonlocal total
        if len(records) >= limits.max_requests or total >= limits.max_total_bytes:
            raise ValueError("Neotoma metadata request or total-byte budget exhausted")
        bound = min(limits.max_response_bytes, limits.max_total_bytes - total)
        parts = urlsplit(request.url)
        record: dict[str, Any] = {
            "requested_url": request.url,
            "request_method": "GET",
            "request_target": parts.path + ("?" + parts.query if parts.query else ""),
            "parameters": request.parameters,
            "role": request.role,
            "expected_site_id": request.site_id,
            "request_headers": [list(pair) for pair in _HEADERS],
            "tls_mode": "verified_no_insecure_fallback",
            "utc_start": datetime.now(UTC).isoformat(),
        }
        if request.dataset_id is not None:
            record["expected_dataset_id"] = request.dataset_id
        try:
            response = fetch(
                request.url, timeout=limits.timeout_seconds, max_bytes=bound
            )
        except Exception as error:
            record.update(
                {
                    "utc_end": datetime.now(UTC).isoformat(),
                    "terminal_status": "transport_failure",
                    "error": f"{type(error).__name__}: {error}",
                    "body_complete": False,
                }
            )
            _write_json(staging / f"{request.name}.receipt.json", record)
            raise
        record.update(
            {
                "utc_end": datetime.now(UTC).isoformat(),
                "final_url": response.final_url,
                "http_status": response.http_status,
                "response_headers": [list(pair) for pair in response.headers],
                "body_file": f"{request.name}.body",
                "body_complete": response.body_complete,
                "retained_body_bytes": len(response.body),
                "retained_body_sha256": sha256(response.body).hexdigest(),
                "terminal_status": "complete_http_200"
                if response.http_status == 200 and response.body_complete
                else "refused_http_response",
            }
        )
        with (staging / record["body_file"]).open("xb") as stream:
            stream.write(response.body)
        receipt_name = f"{request.name}.receipt.json"
        receipt_digest = _write_json(staging / receipt_name, record)
        records.append(
            {
                "request_name": request.name,
                "receipt_file": receipt_name,
                "receipt_sha256": receipt_digest,
            }
        )
        total += len(response.body)
        _validate_receipt(record, request, response.body, bound)
        return response.body

    try:
        _walk_plan(plan, limits, consume)
        _write_json(
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
        )
        result = replay_neotoma_metadata_capture(staging, limits=limits)
        publish_new_output_tree(final_output_root=final, staging_output_root=staging)
        return result
    except Exception as error:
        if staging.exists():
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
            )
        raise
