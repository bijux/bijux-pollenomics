"""External scoped evidence is explicit metadata, not inferred capture authority."""

from __future__ import annotations

from typing import Any

from bijux_pollenomics.reporting.map_document import source_resources as owner

from .native_federations import (
    scoped_ancillary_sources as scoped_ancillary_sources,
)
from .native_federations import (
    scoped_inputs as scoped_inputs,
)
from .native_federations import (
    scoped_selection_products as scoped_selection_products,
)
from .native_federations import (
    source_input,
)


def test_scoped_federation_preserves_exact_native_occurrences_and_source_flags(
    scoped_ancillary_sources: dict[str, Any],
) -> None:
    sources = scoped_ancillary_sources
    projected = owner.load_atlas_resource_catalogue(source_input(sources)).ancillary
    assert projected is not None
    raw = sources["view"]
    assert projected.source_manifest == raw.manifest
    assert (
        projected.source_manifest["schema_version"]
        == "neotoma-scoped-ancillary-source-federation.v1"
    )
    assert list(projected.slots) == raw.slots
    assert list(projected.observations) == raw.observations
    assert list(projected.linked_occurrences) == raw.linked_occurrences
    assert len(projected.linked_occurrences) == 6
    assert all(
        "source_proof" not in row and "source_proof_pointer" not in row
        for row in projected.linked_occurrences
    )
    assert all(
        row["native_field_value_verified"] is False
        for row in projected.linked_occurrences
    )
    assert all("evidence_locator" in row for row in projected.linked_occurrences)
    assert projected.entity_body_hashes_verified is False
    assert projected.source_assessments_replayed is False
    assert projected.provenance["scientific_admission"] == "not_asserted"
    assert projected.provenance["related_resource_graph_complete"] is False
    blocked = next(
        row
        for row in projected.observations
        if row["kind"] == "linked" and row["identity"]["kind"] == "contact"
    )
    assert blocked["current_use_role"] == "heldout_no_numerical_access"
    assert blocked["entity_access_status"] == "blocked_current_scope"
    assert blocked["attempts"] == []
