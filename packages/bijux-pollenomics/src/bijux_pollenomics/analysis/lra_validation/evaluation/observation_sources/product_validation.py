"""Canonical validation shared by both observation-source product types."""

from __future__ import annotations

from dataclasses import asdict
import json
from typing import Any, cast

from ...contracts import canonical_json, manifest_sha256, required_identity
from ..contracts import digest, refuse
from .closure import validate_source_closure

_PRODUCT_KEYS = frozenset(
    {
        "schema_version",
        "source_kind",
        "source_canonical_json",
        "source_file_sha256",
        "source_payload_sha256",
        "reader_profile",
        "reader_code_sha256",
        "source_reference_id",
        "access_plan_sha256",
        "access_start_receipt_sha256",
        "source_locator_sha256",
        "actual_reads",
        "metadata",
        "taxa",
        "units",
        "requested_units",
        "available_units",
        "missing_units",
        "refused_units",
        "empirical_evaluation_performed",
        "scientific_acceptance",
    }
)
_METADATA_KEYS = frozenset(
    {
        "schema_version",
        "source_kind",
        "evidence_role",
        "reader_profile",
        "reader_code_sha256",
        "provider_id",
        "dataset_id",
        "release_id",
        "source_snapshot_sha256",
        "source_member",
        "source_member_sha256",
        "citation",
        "license",
        "rights_status",
        "rights_evidence_sha256",
        "release_disposition",
        "source_reference_id",
        "taxon_mapping_sha256",
        "taxon_mapping_review_id",
        "normalization_profile",
        "normalization_code_sha256",
    }
)
_READ_KEYS = frozenset({"source_kind", "path", "source_sha256", "bytes"})


def _validate_metadata(
    metadata: object,
    *,
    kind: str,
    source_reference_id: object,
    reader_profile: object,
    reader_code_sha256: object,
) -> None:
    if not isinstance(metadata, dict):
        refuse("Observation source metadata must be an exact object")
    method = (
        "field_method"
        if kind == "independent_measured_vegetation"
        else "counting_method"
    )
    if set(metadata) != _METADATA_KEYS | {method}:
        refuse("Observation source metadata fields differ")
    for field in (
        "provider_id",
        "dataset_id",
        "release_id",
        "source_member",
        "citation",
        "license",
        "taxon_mapping_review_id",
        "normalization_profile",
        method,
    ):
        required_identity(cast(str, metadata.get(field)))
    for field in (
        "reader_code_sha256",
        "source_snapshot_sha256",
        "source_member_sha256",
        "rights_evidence_sha256",
        "taxon_mapping_sha256",
        "normalization_code_sha256",
    ):
        digest(cast(str, metadata.get(field)))
    if (
        metadata.get("schema_version")
        != (
            "pollenomics-measured-vegetation-source.v1"
            if kind == "independent_measured_vegetation"
            else "pollenomics-heldout-pollen-count-source.v1"
        )
        or metadata.get("source_kind") != kind
        or metadata.get("evidence_role") != kind
        or metadata.get("source_reference_id") != source_reference_id
        or metadata.get("reader_profile") != reader_profile
        or metadata.get("reader_code_sha256") != reader_code_sha256
        or metadata.get("rights_status") != "admitted"
        or metadata.get("release_disposition") != "admitted_for_final_evaluation"
    ):
        refuse("Observation source metadata authority or role differs")


def validate_product(
    canonical: str,
    product_sha256: str,
    units: tuple[object, ...],
    *,
    profile: str,
    kind: str,
) -> None:
    try:
        loaded = json.loads(canonical)
    except (json.JSONDecodeError, TypeError) as exc:
        refuse(f"Malformed observation source product: {exc}")
    typed = [cast(Any, unit) for unit in units]
    if (
        not isinstance(loaded, dict)
        or canonical_json(loaded) != canonical
        or manifest_sha256(loaded) != digest(product_sha256)
        or frozenset(loaded) != _PRODUCT_KEYS
        or loaded.get("schema_version") != profile
        or loaded.get("source_kind") != kind
        or loaded.get("empirical_evaluation_performed") is not False
        or loaded.get("scientific_acceptance") != "not_evaluated"
        or canonical_json(loaded.get("units"))
        != canonical_json([asdict(unit) for unit in typed])
    ):
        refuse("Observation source product bytes, units or claim boundary differ")
    taxa = loaded.get("taxa")
    reads = loaded.get("actual_reads")
    if (
        not isinstance(taxa, list)
        or any(not isinstance(value, str) for value in taxa)
        or taxa != sorted(set(taxa))
        or not isinstance(reads, list)
        or len(reads) != 1
        or not isinstance(reads[0], dict)
        or frozenset(reads[0]) != _READ_KEYS
        or loaded.get("requested_units") != len(typed)
        or loaded.get("available_units")
        != sum(unit.status == "available" for unit in typed)
        or loaded.get("missing_units")
        != sum(unit.status == "missing" for unit in typed)
        or loaded.get("refused_units")
        != sum(unit.status == "refused" for unit in typed)
        or len({unit.observation_id for unit in typed}) != len(typed)
        or any(
            tuple(value for value, _ in unit.values) != tuple(taxa) for unit in typed
        )
        or any(
            unit.source_reference_id != loaded.get("source_reference_id")
            for unit in typed
        )
    ):
        refuse("Observation source product denominator, reads or counts differ")
    for field in (
        "source_file_sha256",
        "source_payload_sha256",
        "reader_code_sha256",
        "access_plan_sha256",
        "access_start_receipt_sha256",
        "source_locator_sha256",
    ):
        digest(cast(str, loaded.get(field)))
    required_identity(cast(str, loaded.get("reader_profile")))
    required_identity(cast(str, loaded.get("source_reference_id")))
    _validate_metadata(
        loaded.get("metadata"),
        kind=kind,
        source_reference_id=loaded.get("source_reference_id"),
        reader_profile=loaded.get("reader_profile"),
        reader_code_sha256=loaded.get("reader_code_sha256"),
    )
    validate_source_closure(loaded, units)
