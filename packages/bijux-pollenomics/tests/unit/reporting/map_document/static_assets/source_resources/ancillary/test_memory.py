"""Resource publication does not retain redundant complete encoded buffers."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import gc
import hashlib
from pathlib import Path
from typing import Any
import weakref

import pytest

from bijux_pollenomics.reporting.map_document.source_resources import (
    AtlasResourceCatalogue,
)
from bijux_pollenomics.reporting.map_document.static_assets import writer
from bijux_pollenomics.reporting.map_document.static_assets.budgets import (
    ATLAS_CHUNK_MAX_BYTES,
)
from bijux_pollenomics.reporting.map_document.static_assets.models import (
    StaticAtlasAssets,
)
from bijux_pollenomics.reporting.map_document.static_assets.source_resources.publication import (
    SourceResourcePayloads,
    build_source_resource_payloads,
)
from bijux_pollenomics.reporting.map_document.static_assets.validation import (
    validate_static_atlas_assets,
)

from .native_metadata import ancillary_sources as ancillary_sources
from .native_metadata import capsule_inputs as capsule_inputs
from .native_metadata import legacy_catalogue as legacy_catalogue
from .native_metadata import unit_products as unit_products


def test_build_identity_does_not_hash_a_complete_resource_buffer(
    legacy_catalogue: AtlasResourceCatalogue,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = legacy_catalogue.ancillary
    assert source is not None
    rows = []
    for number in range(2000):
        row = deepcopy(source.linked_occurrences[0])
        row["occurrence_id"] = row["observation_id"] + ":proof:" + str(number)
        row["source_proof_pointer"] = (
            row["source_proof_pointer"].rsplit("/", 1)[0] + "/" + str(number)
        )
        row["source_proof"]["generated_marker"] = "x" * 760 + str(number)
        rows.append(row)
    summary = {**deepcopy(source.summary), "linked_occurrence_count": len(rows)}
    manifest = {**deepcopy(source.source_manifest), "summary": summary}
    catalogue = replace(
        legacy_catalogue,
        ancillary=replace(
            source,
            linked_occurrences=tuple(rows),
            summary=summary,
            source_manifest=manifest,
        ),
    )
    before = deepcopy(catalogue)
    original = hashlib.sha256
    largest = 0

    def bounded_hash(data: bytes = b"", *, usedforsecurity: bool = True) -> Any:
        nonlocal largest
        largest = max(largest, len(data))
        assert len(data) <= ATLAS_CHUNK_MAX_BYTES, (
            "Build identity materialized the complete resource encoding"
        )
        return original(data, usedforsecurity=usedforsecurity)

    monkeypatch.setattr(hashlib, "sha256", bounded_hash)
    assets = writer.write_static_atlas_assets(
        tmp_path,
        slug="generated-memory",
        version="generated",
        point_layers=[],
        polygon_layers=[],
        source_resources=catalogue,
    )
    domains = assets.manifest["domains"]
    assert isinstance(domains, dict)
    resources = domains["resources"]
    assert isinstance(resources, dict)
    assert resources["ancillary_linked_occurrence_count"] == 2000
    assert 0 < largest <= ATLAS_CHUNK_MAX_BYTES
    assert catalogue == before


def test_owned_resource_graph_is_released_before_authenticated_readback(
    legacy_catalogue: AtlasResourceCatalogue,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class TrackedRecords(list[Any]):
        pass

    original_builder = build_source_resource_payloads
    original_validator = validate_static_atlas_assets
    references: list[weakref.ReferenceType[Any]] = []
    validated = False
    before = deepcopy(legacy_catalogue)

    def tracked_builder(catalogue: AtlasResourceCatalogue) -> SourceResourcePayloads:
        transport = original_builder(catalogue)
        parts = []
        for part in transport.payloads:
            records = TrackedRecords(part["records"])
            references.append(weakref.ref(records))
            parts.append({**part, "records": records})
        detached = SourceResourcePayloads(
            domain=transport.domain, payloads=tuple(parts)
        )
        references.append(weakref.ref(detached))
        return detached

    def authenticated_readback(assets: StaticAtlasAssets) -> None:
        nonlocal validated
        assert references
        gc.collect()
        assert all(reference() is None for reference in references), (
            "Owned resource graph overlaps final decoded validation"
        )
        original_validator(assets)
        validated = True

    monkeypatch.setattr(writer, "build_source_resource_payloads", tracked_builder)
    monkeypatch.setattr(writer, "validate_static_atlas_assets", authenticated_readback)
    writer.write_static_atlas_assets(
        tmp_path,
        slug="generated-lifetimes",
        version="generated",
        point_layers=[],
        polygon_layers=[],
        source_resources=legacy_catalogue,
    )
    assert validated
    assert legacy_catalogue == before


def test_streamed_build_identity_preserves_complete_asset_bytes(
    legacy_catalogue: AtlasResourceCatalogue,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
        canonical_json,
    )

    streamed = tmp_path / "streamed"
    original = tmp_path / "original"
    streamed.mkdir()
    original.mkdir()

    def publish(directory: Path) -> None:
        writer.write_static_atlas_assets(
            directory,
            slug="generated-identical",
            version="generated",
            point_layers=[],
            polygon_layers=[],
            source_resources=legacy_catalogue,
        )

    before = deepcopy(legacy_catalogue)
    publish(streamed)
    monkeypatch.setattr(
        writer,
        "_canonical_json_sha256",
        lambda value: hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest(),
    )
    publish(original)
    assert {path.name: path.read_bytes() for path in streamed.iterdir()} == {
        path.name: path.read_bytes() for path in original.iterdir()
    }
    assert legacy_catalogue == before
