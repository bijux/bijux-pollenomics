"""Chronology claim indexing and entity-link reconciliation."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping

from ..io import _identifier_text, _mapping, _required_text
from .admission import object_rows
from .models import ClaimIndex, EvidenceBundle, RelationIndex


def index_claims(bundle: EvidenceBundle) -> ClaimIndex:
    """Validate claim identities and group all claims by governed site."""
    rows = object_rows(bundle.claims, "claims", "SEAD chronology claims")
    if bundle.claims.get("claim_count") != len(rows):
        raise ValueError("SEAD chronology claim count does not reconcile")
    by_site: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    claim_ids: set[str] = set()
    country_counts: Counter[str] = Counter()
    for row in rows:
        claim_id = _required_text(
            row.get("chronology_claim_id"), "SEAD chronology claim ID"
        )
        if claim_id in claim_ids:
            raise ValueError(f"SEAD chronology claim ID is duplicated: {claim_id}")
        claim_ids.add(claim_id)
        site_id = _required_text(row.get("source_site_id"), "SEAD claim site ID")
        if row.get("build_id") != bundle.claims.get("source_build_id"):
            raise ValueError("SEAD claim build identity changed")
        if row.get("acquisition_manifest_sha256") != bundle.claims.get(
            "acquisition_manifest_sha256"
        ):
            raise ValueError("SEAD claim acquisition identity changed")
        by_site[site_id].append(row)
        country_counts[
            _required_text(row.get("country_code"), "SEAD claim country")
        ] += 1
    if dict(sorted(country_counts.items())) != bundle.claims.get("country_counts"):
        raise ValueError("SEAD claim country counts do not reconcile")
    return ClaimIndex(rows=rows, by_site=by_site, country_counts=country_counts)


def reconcile_claim_entity_links(
    claims: ClaimIndex,
    relations: RelationIndex,
    observation_count_by_entity: Counter[str],
) -> None:
    """Prove that every claim remains linked within its governed site."""
    for claim in claims.rows:
        relation_id = _required_text(
            claim.get("observation_relation_id"),
            "SEAD claim observation relation ID",
        )
        entity = relations.entity_by_id.get(relation_id)
        if entity is None:
            raise ValueError("SEAD claim references unknown observation relation")
        if _identifier_text(entity.get("site_id"), "SEAD claim relation site") != (
            _required_text(claim.get("source_site_id"), "SEAD claim site")
        ):
            raise ValueError("SEAD claim observation relation crosses sites")
        if (
            claim.get("linked_source_native_observation_count")
            != (observation_count_by_entity[relation_id])
        ):
            raise ValueError("SEAD claim observation count does not reconcile")
        chronology = _mapping(entity.get("chronology_link"), "SEAD entity chronology")
        entity_claim_ids = chronology.get("claim_ids")
        if (
            not isinstance(entity_claim_ids, list)
            or claim.get("chronology_claim_id") not in entity_claim_ids
        ):
            raise ValueError("SEAD claim is absent from its entity chronology relation")
