"""Resource publication does not retain redundant complete encoded buffers."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.reporting.map_document.source_resources import (
    AtlasResourceCatalogue,
)
from bijux_pollenomics.reporting.map_document.static_assets import writer
from bijux_pollenomics.reporting.map_document.static_assets.budgets import (
    ATLAS_CHUNK_MAX_BYTES,
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
    original = writer.hashlib.sha256
    largest = 0

    def bounded_hash(data: Any = b"", **kwargs: Any) -> Any:
        nonlocal largest
        largest = max(largest, len(data))
        assert len(data) <= ATLAS_CHUNK_MAX_BYTES, (
            "Build identity materialized the complete resource encoding"
        )
        return original(data, **kwargs)

    monkeypatch.setattr(writer.hashlib, "sha256", bounded_hash)
    assets = writer.write_static_atlas_assets(
        tmp_path,
        slug="generated-memory",
        version="generated",
        point_layers=[],
        polygon_layers=[],
        source_resources=catalogue,
    )
    assert (
        assets.manifest["domains"]["resources"]["ancillary_linked_occurrence_count"]
        == 2000
    )
    assert 0 < largest <= ATLAS_CHUNK_MAX_BYTES
    assert catalogue == before
