"""Reuse qualified original source bytes without inventing fresh HTTP custody."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from ..receipts import _object, _read, _safe_root, _utc
from .models import NeotomaResourceSpec, NeotomaRetainedSource
from .profiles import classify_body
from .protocol import request_for


def read_retained_source(
    resource: NeotomaResourceSpec,
    version: str,
    source: NeotomaRetainedSource,
    maximum_bytes: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return the existing provenance and summary without exposing source bytes."""
    reference, summary, _ = read_retained_source_entity(
        resource, version, source, maximum_bytes
    )
    return reference, summary


def read_retained_source_entity(
    resource: NeotomaResourceSpec,
    version: str,
    source: NeotomaRetainedSource,
    maximum_bytes: int,
) -> tuple[dict[str, Any], dict[str, Any], bytes]:
    """Return the same buffer authenticated and classified for the retained source."""
    provenance_bytes = _read(_safe_root(source.provenance_path), 100000)
    if sha256(provenance_bytes).hexdigest() != source.provenance_sha256:
        raise ValueError("Retained Neotoma provenance identity differs")
    provenance = _object(provenance_bytes)
    if provenance.get("schema_version") != "bokesjon-public-core-sources.v1":
        raise ValueError("Unsupported retained Neotoma provenance schema")
    records = provenance.get("sources")
    if not isinstance(records, list):
        raise ValueError("Retained Neotoma source population is missing")
    url = request_for(resource, version, 1).url
    matching = [
        record
        for record in records
        if isinstance(record, dict) and record.get("source_url") == url
    ]
    if len(matching) != 1:
        raise ValueError("Retained Neotoma request identity differs")
    record = matching[0]
    body = _read(_safe_root(source.body_path), maximum_bytes)
    if (
        record.get("status") != 200
        or record.get("final_url") != url
        or record.get("bytes") != len(body)
        or sha256(body).hexdigest() != source.body_sha256
        or record.get("sha256") != source.body_sha256
    ):
        raise ValueError("Retained Neotoma body/response identity differs")
    _utc(record.get("retrieved_at"))
    status, summary = classify_body(resource, version, body)
    if status != "parsed_native":
        raise ValueError("Retained Neotoma source is not a qualified native hierarchy")
    reference = {
        "provenance_schema": provenance["schema_version"],
        "provenance_sha256": source.provenance_sha256,
        "body_sha256": source.body_sha256,
        "source_url": url,
        "retrieved_at": record["retrieved_at"],
        "http_evidence_scope": "original recorded fields only; no new request, headers or TLS history invented",
    }
    return reference, summary, body
