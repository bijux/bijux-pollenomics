"""Content-addressed manifests for classification-audit bundles."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from typing import cast

from .models import ClassificationAuditRefusalError
from .values import refuse


def canonical_json_bytes(payload: object) -> bytes:
    try:
        rendered = json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
    except (TypeError, ValueError) as error:
        raise ClassificationAuditRefusalError(
            "invalid_output_serialization",
            "classification audit must be finite canonical JSON",
        ) from error
    return f"{rendered}\n".encode()


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def build_manifest(
    *,
    accounting: Mapping[str, object],
    serialized_payloads: Mapping[str, bytes],
    classification_contract_version: str,
    classification_contract_digest: str,
    classification_producer_id: str,
    classification_producer_version: str,
    classification_producer_digest: str,
) -> dict[str, object]:
    entries = tuple(
        {
            "path": name,
            "sha256": sha256(serialized_payloads[name]),
            "record_count": payload_record_count(serialized_payloads[name]),
        }
        for name in sorted(serialized_payloads)
    )
    digest_input = "".join(
        f"{entry['path']}\0{entry['sha256']}\0{entry['record_count']}\n"
        for entry in entries
    ).encode("utf-8")
    return {
        "schema_version": "classification-audit-manifest.v1",
        "source_family": accounting["source_family"],
        "source_snapshot_id": accounting["source_snapshot_id"],
        "build_id": accounting["build_id"],
        "classification_contract_version": classification_contract_version,
        "classification_contract_digest": classification_contract_digest,
        "classification_producer_id": classification_producer_id,
        "classification_producer_version": classification_producer_version,
        "classification_producer_digest": classification_producer_digest,
        "input_accounting_sha256": sha256(canonical_json_bytes(accounting)),
        "bundle_digest": sha256(digest_input),
        "payload_file_count": len(entries),
        "files": entries,
    }


def payload_record_count(payload_bytes: bytes) -> int:
    payload: object = json.loads(payload_bytes)
    if not isinstance(payload, dict):
        refuse("invalid_output_reconciliation", "audit payload must be an object")
    payload = cast(dict[str, object], payload)
    count = payload.get("record_count")
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        refuse(
            "invalid_output_reconciliation",
            "audit payload requires a non-negative record_count",
        )
    return cast(int, count)
