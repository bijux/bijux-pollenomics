"""Validate the pinned non-outcome inputs needed by declared inclusion."""

from __future__ import annotations

from typing import Any

from .evidence import authenticated_evidence_rows
from .parameters import authenticated_parameter_manifest
from .pollen_index import authenticated_pollen_index
from .taxon_mapping import authenticated_taxon_mapping


def validated_review_inputs(
    *,
    projection: dict[str, Any],
    receipt: dict[str, Any],
    reviewer_id: str,
    decision_date: str,
    evidence_bytes: bytes,
    evidence_sha256: str,
    index_bytes: bytes,
    index_sha256: str,
    attestation_bytes: bytes,
    attestation_sha256: str,
    mapping_bytes: bytes,
    mapping_sha256: str,
    parameter_bytes: bytes,
    parameter_sha256: str,
    nfi_schema_bytes: bytes,
    nfi_schema_sha256: str,
) -> dict[str, dict[str, Any]]:
    """Authenticate source identities without receiving sealed pollen payloads."""
    parameters = authenticated_parameter_manifest(
        parameter_bytes, parameter_sha256, projection, receipt
    )
    mapping = authenticated_taxon_mapping(
        mapping_bytes, mapping_sha256, projection, receipt, parameters
    )
    if not mapping:
        raise ValueError("taxon mapping manifest must not be empty")
    index_rows = authenticated_pollen_index(
        index_bytes,
        index_sha256,
        attestation_bytes,
        attestation_sha256,
        projection,
        mapping_sha256,
        parameter_sha256,
    )
    return authenticated_evidence_rows(
        evidence_bytes,
        evidence_sha256,
        projection,
        reviewer_id,
        decision_date,
        index_rows,
        index_sha256,
        attestation_sha256,
        receipt["accepted_taxon_ids"],
        {taxon: row["accepted_taxon_name"] for taxon, row in parameters.items()},
        nfi_schema_bytes,
        nfi_schema_sha256,
    )
