from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import cast

from .identity import (
    _canonical,
    _digest,
    _is_sha256_hex,
    _is_sha256_identity,
    _optional_text,
    _required_text,
    _source_taxon_identity,
)
from .models import ClassificationEventContext
from .vocabulary import _ACCEPTED_STATUSES


@dataclass(frozen=True)
class _ClassificationAuthorityReceipt:
    """Product-owned receipt for the only mapping bytes admitted to events."""

    manifest_sha256: str
    source_family: str
    source_snapshot_id: str
    build_id: str
    contract_version: str
    contract_digest: str
    producer_id: str
    producer_version: str
    producer_digest: str
    accepted_mapping_count: int
    accepted_mapping_sha256_by_concept: tuple[tuple[str, str], ...]


_CLASSIFICATION_AUTHORITY = _ClassificationAuthorityReceipt(
    manifest_sha256=(
        "538c3daad922562a172bc578a3b01fffb2020891255f958b060034e0ea072101"
    ),
    source_family="neotoma",
    source_snapshot_id=(
        "sha256:b2bcb99157e10b0c9f13c228acc12eabcb39d96a1f39c86ec25e34aacd78c791"
    ),
    build_id=(
        "sha256:92dd52619837f3641d004a1a5dbe38f9ab6023a79f61989314bb90e612eb58e1"
    ),
    contract_version="1.0.0",
    contract_digest=(
        "sha256:3b61266d52b4a35ad8e808a730b5e433a0bfb37536ef458fb080263b80a5c671"
    ),
    producer_id="bijux-pollenomics.neotoma-classification-audit",
    producer_version="1",
    producer_digest=(
        "sha256:256efdaa6a17978cfcd57e7a561508fb1a9d3d4edc6bd90c9bab30420ba2e015"
    ),
    accepted_mapping_count=0,
    accepted_mapping_sha256_by_concept=(),
)


def _classification_authority_universe_reason(
    mappings: Sequence[Mapping[str, object]],
) -> str | None:
    """Require the caller's accepted mapping universe to equal the authority receipt."""
    authority = _CLASSIFICATION_AUTHORITY
    if not _valid_classification_authority_receipt(authority):
        return "invalid_classification_authority_receipt"
    entries = authority.accepted_mapping_sha256_by_concept

    accepted_by_concept: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for mapping in mappings:
        if _optional_text(mapping.get("mapping_status")) not in _ACCEPTED_STATUSES:
            continue
        concept_id = _optional_text(mapping.get("classification_concept_id"))
        if concept_id is None:
            return "extra_classification_authority_mapping"
        accepted_by_concept[concept_id].append(mapping)

    for rows in accepted_by_concept.values():
        if len(rows) <= 1:
            continue
        if len({_canonical(row) for row in rows}) == 1:
            return "duplicate_classification_authority_mapping"
        return "conflicting_classification_authority_mapping"

    expected = set(entries)
    supplied = {
        (concept_id, f"sha256:{_digest(rows[0])}")
        for concept_id, rows in accepted_by_concept.items()
    }
    if supplied - expected:
        return "extra_classification_authority_mapping"
    if expected - supplied:
        return "incomplete_classification_authority_universe"
    return None


def _ambiguous_authorized_mapping_ids(
    mappings: Sequence[Mapping[str, object]], context: ClassificationEventContext
) -> set[str]:
    """Return authority concepts that share one governed source identity."""
    concepts_by_source_identity: dict[str, set[str]] = defaultdict(set)
    for mapping in mappings:
        concept_id = _optional_text(mapping.get("classification_concept_id"))
        if (
            concept_id is None
            or _optional_text(mapping.get("mapping_status")) not in _ACCEPTED_STATUSES
            or _optional_text(mapping.get("source_family")) != context.source_family
            or _optional_text(mapping.get("classification_contract_version"))
            != context.classification_contract_version
            or _optional_text(mapping.get("mapping_version")) != context.mapping_version
            or not _mapping_is_authorized(mapping, context)
            or _optional_text(mapping.get("source_variable_id")) is None
            or not _source_taxon_identity(mapping.get("source_taxon_id"))
            or _optional_text(mapping.get("source_reported_name")) is None
            or _optional_text(mapping.get("source_element_type")) != "pollen"
        ):
            continue
        source_identity = _canonical(
            {
                "source_family": _required_text(mapping.get("source_family")),
                "source_variable_id": _required_text(mapping.get("source_variable_id")),
                "source_taxon_id": mapping.get("source_taxon_id"),
                "source_reported_name": _required_text(
                    mapping.get("source_reported_name")
                ),
                "source_element_type": _required_text(
                    mapping.get("source_element_type")
                ),
            }
        )
        concepts_by_source_identity[source_identity].add(concept_id)
    return {
        concept_id
        for concept_ids in concepts_by_source_identity.values()
        if len(concept_ids) > 1
        for concept_id in concept_ids
    }


def _mapping_is_authorized(
    mapping: Mapping[str, object], context: ClassificationEventContext
) -> bool:
    authority = _CLASSIFICATION_AUTHORITY
    if not _valid_classification_authority_receipt(authority):
        return False
    entries = authority.accepted_mapping_sha256_by_concept
    if (
        authority.source_family != context.source_family
        or authority.contract_version != context.classification_contract_version
    ):
        return False
    concept_id = _optional_text(mapping.get("classification_concept_id"))
    if concept_id is None:
        return False
    authorized = dict(entries).get(concept_id)
    return authorized == f"sha256:{_digest(mapping)}"


def _valid_classification_authority_receipt(authority: object) -> bool:
    if type(authority) is not _ClassificationAuthorityReceipt:
        return False
    required_text = (
        authority.source_family,
        authority.contract_version,
        authority.producer_id,
        authority.producer_version,
    )
    required_digest_identities = (
        authority.source_snapshot_id,
        authority.build_id,
        authority.contract_digest,
        authority.producer_digest,
    )
    if (
        not _is_sha256_hex(authority.manifest_sha256)
        or any(type(value) is not str or not value.strip() for value in required_text)
        or any(not _is_sha256_identity(value) for value in required_digest_identities)
        or type(authority.accepted_mapping_count) is not int
        or authority.accepted_mapping_count < 0
        or type(authority.accepted_mapping_sha256_by_concept) is not tuple
    ):
        return False
    entries = authority.accepted_mapping_sha256_by_concept
    for entry in entries:
        if type(entry) is not tuple or len(entry) != 2:
            return False
        concept_id = entry[0]
        digest = entry[1]
        if (
            type(concept_id) is not str
            or not concept_id.strip()
            or type(digest) is not str
            or not _is_sha256_identity(digest)
        ):
            return False
    return authority.accepted_mapping_count == len(entries) and len(
        {entry[0] for entry in entries}
    ) == len(entries)


def _classification_authority_manifest_sha256() -> str:
    value = getattr(_CLASSIFICATION_AUTHORITY, "manifest_sha256", None)
    if _is_sha256_hex(value):
        return cast(str, value)
    return "invalid-classification-authority-receipt"
