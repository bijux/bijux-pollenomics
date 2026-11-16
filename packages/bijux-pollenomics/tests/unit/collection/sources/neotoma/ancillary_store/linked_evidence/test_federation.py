"""Shared scoped evidence becomes compact metadata, never copied raw source data."""

import json
from typing import Any

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation import (
    validate_neotoma_ancillary_federation_sources,
)


def test_scoped_federation_retains_pointer_references_and_blocked_contact(
    scoped_selection_products: dict[str, Any],
) -> None:
    products = scoped_selection_products
    view = products["view"]
    assert (
        view.manifest["schema_version"]
        == "neotoma-scoped-ancillary-source-federation.v1"
    )
    assert set(view.manifest["linked_evidence"]) == set(products["evidence_sources"])
    assert len(view.linked_occurrences) == 6
    assert all(
        "source_proof" not in row and "source_proof_pointer" not in row
        for row in view.linked_occurrences
    )
    blocked = next(
        row
        for row in view.observations
        if row["kind"] == "linked" and row["identity"]["kind"] == "contact"
    )
    assert blocked["current_use_role"] == "heldout_no_numerical_access"
    assert blocked["entity_access_status"] == "blocked_current_scope"
    assert blocked["attempts"] == []
    assert not any("proofs/" in path for path in view.manifest["files"])
    assert str(products["directory"].parent) not in json.dumps(view.manifest)


def test_explicit_full_scoped_federation_replay_uses_complete_external_source_closure(
    scoped_selection_products: dict[str, Any],
) -> None:
    products = scoped_selection_products
    result = validate_neotoma_ancillary_federation_sources(
        products["directory"],
        **{
            key: products["kwargs"][key]
            for key in (
                "expected_manifest_sha256",
                "context_directory",
                "native_archive_directory",
                "capsule_sources",
            )
        },
        evidence_sources=products["evidence_sources"],
    )
    assert result["source_assessments_replayed"] is True
    assert result["native_archive_numerical_entities_replayed"] is False
