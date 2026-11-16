"""Ancillary source closure refuses coherent index forgeries and elevated claims."""

from __future__ import annotations

from typing import Any

import pytest

from bijux_pollenomics.reporting.map_document.source_resources import (
    AtlasResourceCatalogue,
)
from bijux_pollenomics.reporting.map_document.static_assets.source_resources import (
    build_source_resource_payloads,
    validate_source_resource_payloads,
)

from .native_metadata import (
    ancillary_sources as ancillary_sources,
)
from .native_metadata import (
    capsule_inputs as capsule_inputs,
)
from .native_metadata import (
    legacy_catalogue as legacy_catalogue,
)
from .native_metadata import (
    rebind_index,
    rows,
)
from .native_metadata import (
    scoped_ancillary_sources as scoped_ancillary_sources,
)
from .native_metadata import (
    scoped_catalogue as scoped_catalogue,
)
from .native_metadata import (
    scoped_inputs as scoped_inputs,
)
from .native_metadata import (
    scoped_selection_products as scoped_selection_products,
)


def validate(transport: Any, catalogue: AtlasResourceCatalogue) -> None:
    validate_source_resource_payloads(
        transport,
        expected_catalogue_manifest_sha256=catalogue.provenance[
            "catalogue_manifest_sha256"
        ],
    )


@pytest.mark.parametrize(
    "field",
    [
        "ancillary_slot_count",
        "ancillary_observation_count",
        "ancillary_facet_observation_count",
        "ancillary_linked_observation_count",
        "ancillary_linked_occurrence_count",
        "supporting_archive_count",
        "supporting_entry_count",
    ],
)
@pytest.mark.parametrize("invalid", [True, -1, "1"])
def test_separate_ancillary_denominators_are_literal_and_rederived(
    scoped_catalogue: AtlasResourceCatalogue, field: str, invalid: Any
) -> None:
    transport = build_source_resource_payloads(scoped_catalogue)
    validate(transport, scoped_catalogue)
    transport.domain[field] = invalid
    with pytest.raises(ValueError, match="count|population"):
        validate(transport, scoped_catalogue)


@pytest.mark.parametrize(
    "mutation",
    [
        "slot_omitted",
        "foreign_site",
        "missing_observation",
        "missing_occurrence_owner",
        "selected",
        "body_verified",
        "scoped_part",
        "capture_owner",
        "slot_role",
        "summary_boolean",
        "source_schema",
        "guard_alias",
        "guard_size_boolean",
    ],
)
def test_source_relationships_refuse_even_with_coherent_transport_index(
    scoped_catalogue: AtlasResourceCatalogue, mutation: str
) -> None:
    transport = build_source_resource_payloads(scoped_catalogue)
    validate(transport, scoped_catalogue)
    slot = rows(transport, "facet_slots")[0]
    observations = rows(transport, "ancillary_observations")
    occurrence = rows(transport, "linked_occurrences")[0]
    if mutation == "slot_omitted":
        next(part for part in transport.payloads if part["kind"] == "facet_slots")[
            "records"
        ].pop()
    elif mutation == "foreign_site":
        slot["root_identity"]["site_id"] = 999
    elif mutation == "missing_observation":
        slot["observation_ids"] = ["missing:source"]
    elif mutation == "missing_occurrence_owner":
        occurrence["observation_id"] = "missing:source"
    elif mutation == "selected":
        observations[0]["selected_by_default"] = True
    elif mutation == "body_verified":
        occurrence["native_field_value_verified"] = True
    elif mutation == "capture_owner":
        observations[0]["source_capture_manifest_sha256"] = "0" * 64
        observations[0]["observation_id"] = (
            "0" * 64 + ":" + observations[0]["source_entry_pointer"]
        )
    elif mutation == "slot_role":
        slot["current_use_role"] = "invented_independent_evidence"
    elif mutation == "source_schema":
        rows(transport, "ancillary_context")[0]["source_manifest"]["schema_version"] = (
            "unowned-source-schema"
        )
    elif mutation == "guard_alias":
        rows(transport, "ancillary_context")[0]["source_manifest"][
            "current_use_parent_obligations"
        ]["path"] = "/unowned/source-proof.json"
    elif mutation == "guard_size_boolean":
        rows(transport, "ancillary_context")[0]["source_manifest"][
            "current_use_parent_obligations"
        ]["bytes"] = True
    elif mutation == "summary_boolean":
        context = rows(transport, "ancillary_context")[0]
        key = next(iter(context["summary"]["source_terminal_counts"]))
        context["summary"]["source_terminal_counts"][key] = True
        context["source_manifest"]["summary"]["source_terminal_counts"][key] = True
    else:
        locator = occurrence["evidence_locator"]
        locator["part_sha256"] = "0" * 64
        occurrence["occurrence_id"] = (
            occurrence["observation_id"]
            + ":evidence:"
            + locator["evidence_manifest_sha256"]
            + ":"
            + locator["part_sha256"]
            + ":"
            + str(locator["row_offset"])
        )
    # An index repair must not become a source-identity/relationship waiver.
    with pytest.raises(ValueError):
        rebind_index(transport)
        validate(transport, scoped_catalogue)


@pytest.mark.parametrize(
    "field,value",
    [
        ("native_payload", {"samples": []}),
        ("native_body", b"HTTP entity"),
        ("href", "/unchecked/source.body"),
        ("native_profiles_verified", True),
        ("source_assessments_replayed", True),
    ],
)
def test_nested_entity_outputs_hrefs_and_verification_claims_are_refused(
    scoped_catalogue: AtlasResourceCatalogue, field: str, value: Any
) -> None:
    transport = build_source_resource_payloads(scoped_catalogue)
    observation = rows(transport, "ancillary_observations")[0]
    observation["unexpected_reader_result"] = {field: value}
    with pytest.raises(ValueError, match="body|reader|href|verification"):
        validate(transport, scoped_catalogue)


def test_v1_cannot_silently_transport_ancillary_records(
    scoped_catalogue: AtlasResourceCatalogue,
) -> None:
    transport = build_source_resource_payloads(scoped_catalogue)
    transport.domain["schema_version"] = "atlas-source-resources.v1"
    with pytest.raises(ValueError, match="part identity"):
        validate(transport, scoped_catalogue)


def test_legacy_source_pointer_stays_bound_to_exact_captured_occurrence(
    legacy_catalogue: AtlasResourceCatalogue,
) -> None:
    transport = build_source_resource_payloads(legacy_catalogue)
    occurrences = rows(transport, "linked_occurrences")
    assert occurrences and "source_proof_pointer" in occurrences[0]
    validate(transport, legacy_catalogue)
    occurrences[0]["source_proof_pointer"] = "/resources/999/identity/source_proofs/999"
    with pytest.raises(ValueError, match="pointer"):
        validate(transport, legacy_catalogue)
