"""Atlas source metadata retains every declared epoch without selecting evidence."""

from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.reporting.map_document import source_resources as owner

from .native_federations import (
    ancillary_sources as ancillary_sources,
)
from .native_federations import (
    capsule_inputs as capsule_inputs,
)
from .native_federations import (
    source_input,
)


def test_all_federation_metadata_is_detached_and_preserved(
    ancillary_sources: dict[str, Any],
) -> None:
    view = owner.load_atlas_resource_catalogue(source_input(ancillary_sources))
    extra = view.ancillary
    assert extra is not None
    source = ancillary_sources["view"]
    assert list(extra.slots) == source.slots
    assert list(extra.observations) == source.observations
    assert list(extra.linked_occurrences) == source.linked_occurrences
    assert extra.summary == source.summary
    assert extra.source_manifest == source.manifest
    assert extra.entity_body_hashes_verified is False
    assert extra.source_assessments_replayed is False
    assert extra.integrity_scope == "current_context_and_capsule_metadata"
    assert all(row["selected_observation_id"] is None for row in extra.slots)
    assert all(row["selected_by_default"] is False for row in extra.observations)
    assert len(extra.slots) == len(view.resource_records) * 8
    extra.slots[0]["observation_ids"].append("detached metadata mutation")
    assert extra.slots[0] != source.slots[0]


def test_original_and_current_scope_are_not_conflated(
    ancillary_sources: dict[str, Any],
) -> None:
    extra = owner.load_atlas_resource_catalogue(
        source_input(ancillary_sources)
    ).ancillary
    assert extra is not None
    assert {row["coverage_status"] for row in extra.slots} >= {
        "protected_current_scope",
        "pending_capture",
        "complete_source_entity",
    }
    assert any(
        row["capture_parent_scope_verification"] == "not_recorded_legacy_capture"
        for row in extra.observations
        if row["kind"] == "facet"
    )
    assert all("current_use_scope_verification" in row for row in extra.observations)
    assert extra.provenance["scientific_admission"] == "not_asserted"
    assert extra.provenance["original_preget_scope_reconstructed"] is False
    assert extra.provenance["related_resource_graph_complete"] is False


def test_v1_none_and_unused_evidence_resolvers_preserve_exact_metadata_bytes(
    ancillary_sources: dict[str, Any], tmp_path: Path
) -> None:
    source = source_input(ancillary_sources)
    baseline = owner.load_atlas_resource_catalogue(source)
    assert baseline.ancillary is not None
    assert (
        baseline.ancillary.source_manifest["schema_version"]
        == "neotoma-ancillary-source-federation.v1"
    )
    encoded = json.dumps(asdict(baseline), sort_keys=True, separators=(",", ":"))
    dependency = source.ancillary
    assert dependency is not None and dependency.evidence_sources is None
    for resolver in (None, {}, {"7" * 64: tmp_path / "unused-evidence"}):
        current = owner.load_atlas_resource_catalogue(
            replace(source, ancillary=replace(dependency, evidence_sources=resolver))
        )
        assert (
            json.dumps(asdict(current), sort_keys=True, separators=(",", ":"))
            == encoded
        )
        assert current.ancillary is not None
        assert "linked_evidence" not in current.ancillary.source_manifest
