"""Versioned ancillary transport retains source identities without native promotion."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.reporting.map_document.source_resources import (
    AtlasAncillarySupportingMetadata,
    AtlasResourceCatalogue,
)
from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    canonical_json,
)
from bijux_pollenomics.reporting.map_document.static_assets.source_resources import (
    build_source_resource_payloads,
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
    reference_archive as reference_archive,
)
from .native_metadata import (
    reference_source as reference_source,
)
from .native_metadata import (
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
from .native_metadata import (
    site_context_products as site_context_products,
)
from .native_metadata import (
    supporting_catalogue as supporting_catalogue,
)
from .native_metadata import (
    supporting_sources as supporting_sources,
)
from .native_metadata import (
    unit_products as unit_products,
)


@pytest.mark.parametrize("fixture", ["legacy_catalogue", "scoped_catalogue"])
def test_each_source_population_and_locator_is_retained_once_with_separate_counts(
    request: pytest.FixtureRequest, fixture: str
) -> None:
    catalogue = request.getfixturevalue(fixture)
    source = catalogue.ancillary
    transport = build_source_resource_payloads(catalogue)
    assert transport.domain["schema_version"] == "atlas-source-resources.v2"
    assert all(
        part["schema_version"] == "atlas-source-resource-chunk.v1"
        for part in transport.payloads
    )
    assert rows(transport, "facet_slots") == sorted(
        source.slots, key=lambda row: row["slot_key"]
    )
    assert rows(transport, "ancillary_observations") == sorted(
        source.observations, key=lambda row: row["observation_id"]
    )
    assert rows(transport, "linked_occurrences") == sorted(
        source.linked_occurrences, key=lambda row: row["occurrence_id"]
    )
    assert transport.domain["record_count"] == len(catalogue.resource_records)
    assert transport.domain["version_status_count"] == 2 * len(
        catalogue.resource_records
    )
    assert transport.domain["ancillary_slot_count"] == len(source.slots)
    assert transport.domain["ancillary_observation_count"] == len(source.observations)
    assert transport.domain["ancillary_linked_occurrence_count"] == len(
        source.linked_occurrences
    )
    context = rows(transport, "ancillary_context")[0]
    assert context["source_manifest"] == source.source_manifest
    assert context["provenance"] == source.provenance
    assert context["summary"] == source.summary
    assert context["entity_body_hashes_verified"] is False
    assert context["source_assessments_replayed"] is False
    assert (
        context["provenance"]["selection_authority"]
        == "not_provided_by_metadata_projection"
    )
    assert context["source_manifest"]["current_use_parent_obligations"]["bytes"] > 0
    assert "current_parent_proof" not in context
    assert all(
        row["native_field_value_verified"] is False
        for row in rows(transport, "linked_occurrences")
    )


def test_supporting_index_rows_reconstruct_exact_source_metadata(
    supporting_catalogue: AtlasResourceCatalogue,
) -> None:
    transport = build_source_resource_payloads(supporting_catalogue)
    assert isinstance(supporting_catalogue.ancillary, AtlasAncillarySupportingMetadata)
    source = supporting_catalogue.ancillary.supporting_archives[0]
    headers, entries = (
        rows(transport, "supporting_archives"),
        rows(transport, "supporting_entries"),
    )
    assert len(headers) == transport.domain["supporting_archive_count"] == 1
    assert (
        len(entries)
        == transport.domain["supporting_entry_count"]
        == len(source["index"]["tables"])
    )
    header = headers[0]
    assert "tables" not in header["index_metadata"]
    assert header["manifest"] == source["manifest"]
    assert {
        **header["index_metadata"],
        "tables": [
            row["entry"] for row in sorted(entries, key=lambda row: row["row_index"])
        ],
    } == source["index"]
    assert all(
        row["archive_manifest_sha256"] == source["archive_manifest_sha256"]
        for row in entries
    )
    assert header["entity_body_hashes_verified"] is False
    assert header["native_profiles_verified"] is False


def test_default_v1_parts_are_unchanged_when_ancillary_is_absent(
    scoped_catalogue: AtlasResourceCatalogue,
) -> None:
    native = replace(scoped_catalogue, ancillary=None)
    plain = build_source_resource_payloads(native)
    extended = build_source_resource_payloads(scoped_catalogue)
    assert plain.domain["schema_version"] == "atlas-source-resources.v1"
    assert not any(
        key.startswith(("ancillary_", "supporting_")) for key in plain.domain
    )
    assert [
        part
        for part in extended.payloads
        if part["kind"] in {"context", "sites", "resources", "descriptors"}
    ] == [part for part in plain.payloads if part["kind"] != "index"]
    assert rows(extended, "resources") == rows(plain, "resources")
    assert rows(extended, "sites") == rows(plain, "sites")


def test_prepared_ancillary_metadata_needs_no_entity_or_resolver_reads(
    scoped_catalogue: AtlasResourceCatalogue, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refused(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("Transport attempted source I/O")

    with monkeypatch.context() as local:
        local.setattr(Path, "open", refused)
        prepared = build_source_resource_payloads(scoped_catalogue)
    assert prepared.domain["ancillary_linked_occurrence_count"] == 6


def test_common_writer_publishes_v2_as_lazy_same_envelope_with_integrity(
    scoped_catalogue: AtlasResourceCatalogue, tmp_path: Path
) -> None:
    written = write_static_atlas_assets(
        tmp_path,
        slug="ancillary",
        version="source-metadata",
        point_layers=[],
        polygon_layers=[],
        source_resources=scoped_catalogue,
    )
    domains = written.manifest["domains"]
    compatibility = written.manifest["compatibility"]
    assert isinstance(domains, dict) and isinstance(compatibility, dict)
    assert domains["resources"]["schema_version"] == "atlas-source-resources.v2"
    assert compatibility["resource_schema"] == "atlas-source-resource-chunk.v1"
    inventory = normalize_asset_inventory(written.manifest["assets"])
    assert all(
        row["initial_load"] is False
        for row in inventory
        if row["domain"] == "resources"
    )
    assert all(
        isinstance(row["integrity"], str) and row["integrity"].startswith("sha256-")
        for row in inventory
    )
    assert len(canonical_json(written.manifest)) > 0


def test_prepared_body_buffer_is_refused_before_partition_serialization(
    scoped_catalogue: AtlasResourceCatalogue,
) -> None:
    from copy import deepcopy

    source = deepcopy(scoped_catalogue)
    assert source.ancillary is not None
    source.ancillary.observations[0]["native_body"] = b"original source entity"
    with pytest.raises(ValueError, match="body|reader"):
        build_source_resource_payloads(source)
