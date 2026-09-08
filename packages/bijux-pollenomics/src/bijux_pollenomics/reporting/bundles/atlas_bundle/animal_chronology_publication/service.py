"""Coordinate fail-closed animal sample chronology publication."""

from __future__ import annotations

from typing import Any

from .contract_values import mapping, mapping_rows
from .corpus_reconciliation import validate_counts, validate_refusals
from .feature_reconciliation import validate_projected_features
from .geography_reconciliation import validate_country_accountability
from .identity import (
    canonical_sha256,
    validate_corpus_identity,
    validate_input_identity,
)


def build_animal_chronology_publication(
    projection: Any, *, artifact_name: str
) -> tuple[dict[str, object], dict[str, object]]:
    """Reconcile projected nodes and refusals before emitting their contract."""
    input_identity = dict(
        mapping(projection.input_identity.as_dict(), "input identity")
    )
    accountability = dict(mapping(projection.accountability, "accountability"))
    corpus_identity = dict(mapping(projection.corpus_identity, "corpus identity"))
    refusals = [
        dict(mapping(refusal.as_dict(), "refusal")) for refusal in projection.refusals
    ]
    layers = mapping_rows(projection.point_layers, "point layers")
    validate_input_identity(accountability, input_identity)
    validate_corpus_identity(accountability, input_identity, corpus_identity)
    validate_refusals(accountability, refusals)
    validate_counts(accountability, refusals, layers)
    validate_projected_features(accountability, refusals, layers, artifact_name)
    validate_country_accountability(accountability, layers)
    content: dict[str, object] = {
        "schema_version": "animal-sample-chronology-context-publication.v1",
        "accountability": accountability,
        "refusals": refusals,
        "input_identity": input_identity,
        "corpus_identity": corpus_identity,
    }
    content_sha256 = canonical_sha256(content)
    payload = {**content, "content_sha256": content_sha256}
    return payload, {
        "artifact": artifact_name,
        "content_sha256": content_sha256,
        "input_identity_sha256": input_identity["combined_sha256"],
        "corpus_identity_sha256": corpus_identity["content_sha256"],
        "scope": accountability["scope"],
        "global_admitted_node_count": accountability["global_admitted_node_count"],
        "projected_node_count": accountability["projected_node_count"],
        "excluded_by_scope_count": accountability["excluded_by_scope_count"],
        "refusal_count": accountability["refusal_count"],
        "governed_country_rows": accountability["governed_country_rows"],
    }


__all__ = ["build_animal_chronology_publication"]
