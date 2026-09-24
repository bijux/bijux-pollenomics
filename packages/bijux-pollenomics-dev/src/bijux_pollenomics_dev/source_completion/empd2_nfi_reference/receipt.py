"""Validate the externally pinned taxon-parameter review receipt."""

from __future__ import annotations

from typing import Any, cast

from .projection import digest, identities, identity, iso_date, sha_identity

_RECEIPT_KEYS = {
    "schema_version",
    "pollen_source_sha256",
    "accepted_taxon_ids",
    "parameter_binding_sha256",
    "reviewer_id",
    "reviewer_authority",
    "decision_date",
    "evidence_reference_ids",
    "disposition",
    "scientific_acceptance",
    "release_acceptance",
}


def validated_taxon_receipt(
    value: object, projection: dict[str, Any], pinned_sha256: str | None
) -> tuple[dict[str, Any], str]:
    """Validate exact receipt content without authenticating its reviewer."""
    if pinned_sha256 is None:
        raise ValueError("admission requires an externally pinned taxon/PPE receipt")
    pinned = sha_identity(pinned_sha256, "taxon_ppe_receipt_sha256")
    if not isinstance(value, dict) or set(value) != _RECEIPT_KEYS:
        raise ValueError("accepted taxon/PPE receipt fields differ from the schema")
    receipt = cast(dict[str, Any], value)
    taxa = identities(receipt.get("accepted_taxon_ids"), "accepted_taxon_ids")
    if (
        digest(receipt) != pinned
        or receipt.get("schema_version") != "empd2-nfi-taxon-ppe-admission.v1"
        or receipt.get("pollen_source_sha256")
        != projection["source_identities"]["empd2_source"]
        or receipt.get("reviewer_authority") != "declared_not_authenticated"
        or receipt.get("disposition") != "accepted_for_reference_contract"
        or receipt.get("scientific_acceptance") != "not_evaluated"
        or receipt.get("release_acceptance") != "not_evaluated"
    ):
        raise ValueError("taxon/PPE receipt differs from its external trust anchor")
    sha_identity(receipt.get("parameter_binding_sha256"), "parameter_binding_sha256")
    identity(receipt.get("reviewer_id"), "taxon/PPE reviewer_id")
    iso_date(receipt.get("decision_date"), "taxon/PPE decision_date")
    identities(receipt.get("evidence_reference_ids"), "taxon/PPE evidence")
    receipt["accepted_taxon_ids"] = taxa
    return receipt, pinned
