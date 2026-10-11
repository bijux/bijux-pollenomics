"""Authenticate a non-quantitative index of sealed EMPD2 sample payloads."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, cast

from bijux_pollenomics.analysis.lra_validation.contracts import canonical_json

from .projection import digest, identities, identity, sha_identity

_INDEX_KEYS = {
    "schema_version",
    "pollen_source_sha256",
    "taxon_mapping_manifest_sha256",
    "taxon_parameter_binding_sha256",
    "producer_attestation_sha256",
    "sample_count",
    "rows",
}
INDEX_ROW_KEYS = {
    "pollen_sample",
    "pollen_source_sha256",
    "sample_payload_sha256",
    "sample_payload_size",
    "payload_schema_id",
    "taxon_mapping_manifest_sha256",
    "taxon_parameter_binding_sha256",
    "index_row_sha256",
}
_ATTESTATION_KEYS = {
    "schema_version",
    "pollen_source_sha256",
    "sample_count",
    "source_row_count",
    "closure_status",
    "producer_id",
    "evidence_reference_ids",
    "source_table_schema",
    "null_source_row_count",
    "duplicate_source_row_count",
    "noninteger_count_row_count",
    "negative_count_row_count",
    "out_of_mapping_var_row_count",
    "nonpositive_mapped_denominator_sample_count",
    "taxon_mapping_manifest_sha256",
    "ordered_payload_set_sha256",
    "query_contract",
}


def _object(content: bytes, pinned_sha256: str, field: str) -> dict[str, Any]:
    pinned = sha_identity(pinned_sha256, field)
    if sha256(content).hexdigest() != pinned:
        raise ValueError(f"{field} bytes differ from the external trust anchor")
    try:
        raw = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{field} is not canonical JSON") from exc
    if not isinstance(raw, dict) or canonical_json(raw).encode() != content:
        raise ValueError(f"{field} is not a canonical object")
    return cast(dict[str, Any], raw)


def authenticated_pollen_index(
    index_content: bytes,
    index_sha256: str,
    attestation_content: bytes,
    attestation_sha256: str,
    projection: dict[str, Any],
    mapping_sha256: str,
    parameter_sha256: str,
) -> dict[str, dict[str, Any]]:
    """Return sealed payload identities without receiving or opening their bytes."""
    index = _object(index_content, index_sha256, "pollen_count_index_sha256")
    attestation = _object(
        attestation_content,
        attestation_sha256,
        "pollen_count_producer_attestation_sha256",
    )
    source_sha = projection["source_identities"]["empd2_source"]
    if (
        set(index) != _INDEX_KEYS
        or index.get("schema_version") != "empd2-pollen-count-sealed-index.v1"
        or index.get("pollen_source_sha256") != source_sha
        or index.get("taxon_mapping_manifest_sha256") != mapping_sha256
        or index.get("taxon_parameter_binding_sha256") != parameter_sha256
        or index.get("producer_attestation_sha256") != attestation_sha256
        or index.get("sample_count") != 16
    ):
        raise ValueError("pollen count index differs from the exact schema")
    if (
        set(attestation) != _ATTESTATION_KEYS
        or attestation.get("schema_version")
        != "empd2-pollen-count-producer-attestation.v1"
        or attestation.get("pollen_source_sha256") != source_sha
        or attestation.get("sample_count") != 16
        or attestation.get("source_row_count") != 476
        or attestation.get("closure_status")
        != "externally_attested_not_runtime_verified"
        or attestation.get("source_table_schema")
        != {
            "table": "p_counts",
            "columns": [
                {
                    "name": "samplename",
                    "declared_type": "VARCHAR(25)",
                    "not_null": True,
                },
                {"name": "var_", "declared_type": "INTEGER", "not_null": True},
                {
                    "name": "count",
                    "declared_type": "NUMERIC(12,6)",
                    "not_null": False,
                },
            ],
            "primary_key": ["samplename", "var_"],
        }
        or attestation.get("query_contract")
        != {
            "selected_columns": ["samplename", "var_", "count"],
            "sample_denominator": sorted(
                row["pollen_sample"] for row in projection["candidate_rows"]
            ),
            "predicate": {
                "column": "samplename",
                "operator": "in",
                "value_source": "sample_denominator",
            },
            "order_by": ["samplename", "var_"],
        }
        or attestation.get("null_source_row_count") != 0
        or attestation.get("duplicate_source_row_count") != 0
        or attestation.get("noninteger_count_row_count") != 0
        or attestation.get("negative_count_row_count") != 0
        or attestation.get("out_of_mapping_var_row_count") != 0
        or attestation.get("nonpositive_mapped_denominator_sample_count") != 0
        or attestation.get("taxon_mapping_manifest_sha256") != mapping_sha256
    ):
        raise ValueError(
            "pollen count producer attestation differs from the exact claim"
        )
    identity(attestation["producer_id"], "count producer_id")
    identities(attestation["evidence_reference_ids"], "count producer evidence")
    rows = index.get("rows")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("pollen count index rows must be an object array")
    samples = {row["pollen_sample"] for row in projection["candidate_rows"]}
    mapped: dict[str, dict[str, Any]] = {}
    for row in cast(list[dict[str, Any]], rows):
        if set(row) != INDEX_ROW_KEYS:
            raise ValueError(
                "pollen count index row fields differ from the exact schema"
            )
        sample = identity(row["pollen_sample"], "pollen count sample")
        size = row["sample_payload_size"]
        if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
            raise ValueError("sealed pollen payload size must be a positive integer")
        if (
            sample not in samples
            or sample in mapped
            or row["pollen_source_sha256"] != source_sha
            or row["payload_schema_id"] != "empd2-p-counts-sample.v1"
            or row["taxon_mapping_manifest_sha256"] != mapping_sha256
            or row["taxon_parameter_binding_sha256"] != parameter_sha256
        ):
            raise ValueError(
                "pollen count index row differs from its frozen identities"
            )
        sha_identity(row["sample_payload_sha256"], "sample_payload_sha256")
        payload = {key: item for key, item in row.items() if key != "index_row_sha256"}
        if sha_identity(row["index_row_sha256"], "index_row_sha256") != digest(payload):
            raise ValueError(
                "pollen count index row digest differs from its identities"
            )
        mapped[sample] = row
    if list(mapped) != sorted(samples) or set(mapped) != samples:
        raise ValueError("pollen count index does not close all 16 samples")
    payload_set = [
        {
            "pollen_sample": row["pollen_sample"],
            "sample_payload_sha256": row["sample_payload_sha256"],
            "sample_payload_size": row["sample_payload_size"],
            "payload_schema_id": row["payload_schema_id"],
        }
        for row in mapped.values()
    ]
    if attestation.get("ordered_payload_set_sha256") != digest(payload_set):
        raise ValueError("producer attestation differs from the ordered payload set")
    payload_shas = [row["sample_payload_sha256"] for row in mapped.values()]
    if len(payload_shas) != len(set(payload_shas)):
        raise ValueError("sealed pollen payload digests must be unique by sample")
    return mapped
