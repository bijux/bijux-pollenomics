"""Logical resource parts preserve complete metadata without Atlas activation."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import importlib
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import (
    build_neotoma_resource_catalogue,
    write_neotoma_resource_catalogue,
)
from bijux_pollenomics.reporting.map_document.source_resources import (
    AtlasResourceArchiveInput,
    AtlasResourceCatalogue,
    AtlasResourceCatalogueInput,
    load_atlas_resource_catalogue,
)
from bijux_pollenomics.reporting.map_document.static_assets.budgets import (
    ATLAS_CHUNK_MAX_BYTES,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    canonical_json,
)

from .....collection.sources.neotoma.resource_catalogue.test_current_profiles import (
    inputs as current_profile_inputs,
)
from ...source_resources.archive_reference.native_archives import (
    archive_inputs as archive_inputs,
)
from ...source_resources.archive_reference.native_archives import (
    publish_catalogue as publish_catalogue,
)
from ...source_resources.catalogue_inputs import (
    atlas_catalogue as atlas_catalogue,
)
from ...source_resources.catalogue_inputs import (
    catalogue_sources as catalogue_sources,
)


def resource_transport_api() -> ModuleType:
    return importlib.import_module(
        "bijux_pollenomics.reporting.map_document.static_assets.source_resources"
    )


@pytest.fixture
def projected_catalogue(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]],
) -> AtlasResourceCatalogue:
    root, digest, _ = atlas_catalogue()
    return load_atlas_resource_catalogue(AtlasResourceCatalogueInput(root, digest))


def rows_of(transport: Any, kind: str) -> list[dict[str, Any]]:
    return [
        row
        for part in transport.payloads
        if part["kind"] == kind
        for row in part["records"]
    ]


def test_finite_source_metadata_is_retained_once_with_exact_population(
    projected_catalogue: AtlasResourceCatalogue,
) -> None:
    api = resource_transport_api()
    transport = api.build_source_resource_payloads(projected_catalogue)
    assert rows_of(transport, "resources") == list(projected_catalogue.resource_records)
    assert rows_of(transport, "sites") == list(projected_catalogue.site_records)
    assert {
        row["record_id"]: row["descriptor"] for row in rows_of(transport, "descriptors")
    } == projected_catalogue.source_descriptors
    context = rows_of(transport, "context")
    assert len(context) == 1
    assert context[0]["provenance"] == projected_catalogue.provenance
    assert context[0]["summary"] == projected_catalogue.summary
    assert context[0]["legacy_site_references"] == list(
        projected_catalogue.legacy_site_references
    )
    assert transport.domain["record_count"] == 4
    assert transport.domain["site_count"] == 3
    assert transport.domain["version_status_count"] == 8
    assert transport.domain["source_descriptor_count"] == 1
    assert transport.domain["scientific_admission"] == "not_asserted"
    assert transport.domain["numerical_atlas_denominator_changed"] is False
    assert transport.domain["initial_load"] is False
    assert (
        api.validate_source_resource_payloads(
            transport,
            expected_catalogue_manifest_sha256=projected_catalogue.provenance[
                "catalogue_manifest_sha256"
            ],
        )
        is None
    )


def test_partitions_and_lightweight_index_preserve_exact_record_links(
    projected_catalogue: AtlasResourceCatalogue,
) -> None:
    api = resource_transport_api()
    transport = api.build_source_resource_payloads(
        projected_catalogue, target_bytes=1000
    )
    assert sum(part["kind"] == "resources" for part in transport.payloads) > 1
    index = rows_of(transport, "index")
    assert len(index) == 8
    parts = {part["part_id"]: part for part in transport.payloads}
    for entry in index:
        target = parts[entry["part_id"]]
        assert target["kind"] == entry["entity_type"]
        field = {
            "resources": "dataset_id",
            "sites": "site_id",
            "descriptors": "record_id",
        }[entry["entity_type"]]
        assert sum(row[field] == entry["record_id"] for row in target["records"]) == 1
        assert "versions" not in entry and "native_site_variants" not in entry
    assert all(
        len(canonical_json(part).encode()) <= ATLAS_CHUNK_MAX_BYTES
        for part in transport.payloads
    )


def test_source_order_does_not_change_transport_and_outputs_are_detached(
    projected_catalogue: AtlasResourceCatalogue,
) -> None:
    api = resource_transport_api()
    before = deepcopy(projected_catalogue)
    first = api.build_source_resource_payloads(projected_catalogue)
    second = api.build_source_resource_payloads(
        replace(
            projected_catalogue,
            resource_records=tuple(reversed(projected_catalogue.resource_records)),
            site_records=tuple(reversed(projected_catalogue.site_records)),
        )
    )
    assert first == second
    rows_of(first, "resources")[0]["versions"]["current"]["future_qualification"] = {
        "status": None
    }
    assert projected_catalogue == before


@pytest.mark.parametrize("target", [False, 0, -1, ATLAS_CHUNK_MAX_BYTES, "1000"])
def test_invalid_partition_target_refuses(
    projected_catalogue: AtlasResourceCatalogue, target: Any
) -> None:
    with pytest.raises(ValueError, match="target"):
        resource_transport_api().build_source_resource_payloads(
            projected_catalogue, target_bytes=target
        )


def test_indivisible_metadata_record_exceeding_hard_cap_refuses(
    projected_catalogue: AtlasResourceCatalogue,
) -> None:
    source = deepcopy(projected_catalogue)
    source.site_records[0]["native_site_variants"][0]["native_site"]["raw_note"] = (
        "x" * ATLAS_CHUNK_MAX_BYTES
    )
    with pytest.raises(ValueError, match="chunk.*budget|decoded.*budget"):
        resource_transport_api().build_source_resource_payloads(source)


def test_derived_current_profile_retains_original_capture_status(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    inputs = current_profile_inputs(catalogue_sources)
    native = build_neotoma_resource_catalogue(
        **inputs, qualify_current_source_profiles=True
    )
    public = tmp_path / "qualified-catalogue"
    write_neotoma_resource_catalogue(
        public,
        catalogue=native,
        roster_path=inputs["roster_path"],
        capture_sources={**inputs["metadata_captures"], **inputs["resource_captures"]},
    )
    source = load_atlas_resource_catalogue(
        AtlasResourceCatalogueInput(
            public, sha256((public / "manifest.json").read_bytes()).hexdigest()
        )
    )
    transport = resource_transport_api().build_source_resource_payloads(source)
    resource = next(
        row for row in rows_of(transport, "resources") if row["dataset_id"] == "202"
    )
    current = resource["versions"]["current"]
    assert current == source.resource_records[1]["versions"]["current"]
    assert current["acquisition_status"] == "unsupported_dataset_type"
    assert current["qualification_status"] == "not_qualified"
    assert current["current_source_qualification_status"] == "parsed_current_source"
    context = rows_of(transport, "context")[0]
    assert (
        context["provenance"]["current_source_profile_schema"]
        == native["current_source_profile_schema"]
    )
    index = next(
        row
        for row in rows_of(transport, "index")
        if row["entity_type"] == "resources" and row["record_id"] == "202"
    )
    assert (
        index["version_statuses"]["current"]["acquisition_status"]
        == "unsupported_dataset_type"
    )
    assert (
        index["version_statuses"]["current"]["current_source_qualification_status"]
        == "parsed_current_source"
    )


def test_prepared_metadata_needs_no_files_or_resolvers(
    projected_catalogue: AtlasResourceCatalogue, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = resource_transport_api()

    def forbidden(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("Metadata transport attempted file access")

    with monkeypatch.context() as local:
        local.setattr(Path, "open", forbidden)
        result = api.build_source_resource_payloads(projected_catalogue)
    assert result.domain["record_count"] == 4


@pytest.mark.parametrize("field", ["native_body", "native_payload"])
def test_native_reader_outputs_cannot_be_embedded_as_resource_metadata(
    projected_catalogue: AtlasResourceCatalogue, field: str
) -> None:
    source = deepcopy(projected_catalogue)
    source.resource_records[0][field] = (
        b"original HTTP body" if field == "native_body" else {"samples": []}
    )
    with pytest.raises(ValueError, match="native body|native reader"):
        resource_transport_api().build_source_resource_payloads(source)


def test_archive_reference_occurs_only_once_in_lazy_catalogue_context(
    archive_inputs: tuple[Path, str, Path, str],
) -> None:
    root, digest, archive, archive_pin = archive_inputs
    projected = load_atlas_resource_catalogue(
        AtlasResourceCatalogueInput(
            root,
            digest,
            archive=AtlasResourceArchiveInput(
                archive, archive_pin, "/data/neotoma/source-resources/"
            ),
        )
    )
    api = resource_transport_api()
    transport = api.build_source_resource_payloads(projected)
    context = rows_of(transport, "context")[0]
    assert (
        context["provenance"]["source_archive"]
        == projected.provenance["source_archive"]
    )
    assert transport.domain["context_part_id"] == "context:0"
    assert transport.domain["initial_load"] is False
    assert "files" not in context["provenance"]["source_archive"]
    assert all("source_archive" not in row for row in rows_of(transport, "resources"))
    corrupt = deepcopy(projected.provenance)
    corrupt["source_archive"]["published_base_url"] = "https://foreign.invalid/"
    with pytest.raises(ValueError, match="public URL prefix"):
        api.build_source_resource_payloads(replace(projected, provenance=corrupt))
