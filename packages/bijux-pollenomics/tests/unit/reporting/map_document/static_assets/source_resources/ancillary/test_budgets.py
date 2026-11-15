"""Ancillary source parts obey the existing decoded, script and file budgets."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest

from bijux_pollenomics.reporting.map_document.source_resources import (
    AtlasResourceCatalogue,
)
from bijux_pollenomics.reporting.map_document.static_assets.budgets import (
    ATLAS_CHUNK_MAX_BYTES,
    ATLAS_STATIC_ASSETS_MAX_FILES,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    canonical_json,
)
from bijux_pollenomics.reporting.map_document.static_assets.source_resources import (
    build_source_resource_payloads,
    validate_source_resource_payloads,
)

from .native_metadata import (
    rebind_index,
    rows,
)
from .native_metadata import (
    reference_archive as reference_archive,
)
from .native_metadata import (
    reference_source as reference_source,
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


def test_small_partition_target_retains_every_exact_source_row(
    scoped_catalogue: AtlasResourceCatalogue,
) -> None:
    normal = build_source_resource_payloads(scoped_catalogue)
    small = build_source_resource_payloads(scoped_catalogue, target_bytes=2000)
    assert len(small.payloads) > len(normal.payloads)
    for kind in ("facet_slots", "ancillary_observations", "linked_occurrences"):
        assert rows(normal, kind) == rows(small, kind)
    assert all(
        len(canonical_json(part).encode()) <= ATLAS_CHUNK_MAX_BYTES
        for part in small.payloads
    )
    assert small.domain["record_count"] == normal.domain["record_count"]
    assert small.domain["ancillary_linked_occurrence_count"] == 6


def test_indivisible_ancillary_source_context_still_refuses_the_same_hard_cap(
    scoped_catalogue: AtlasResourceCatalogue,
) -> None:
    source = deepcopy(scoped_catalogue)
    assert source.ancillary is not None
    source.ancillary.source_manifest["unbounded_metadata_note"] = (
        "x" * ATLAS_CHUNK_MAX_BYTES
    )
    with pytest.raises(ValueError, match="chunk.*budget|decoded.*budget"):
        build_source_resource_payloads(source)


def test_ancillary_parts_count_toward_the_existing_512_file_cap(
    scoped_catalogue: AtlasResourceCatalogue,
) -> None:
    source = build_source_resource_payloads(scoped_catalogue)
    oversized = replace(
        source,
        payloads=source.payloads
        + tuple(
            deepcopy(source.payloads[0]) for _ in range(ATLAS_STATIC_ASSETS_MAX_FILES)
        ),
    )
    with pytest.raises(ValueError, match="part count.*budget"):
        validate_source_resource_payloads(
            oversized,
            expected_catalogue_manifest_sha256=scoped_catalogue.provenance[
                "catalogue_manifest_sha256"
            ],
        )


def test_supporting_entry_corruption_refuses_against_original_index_sha(
    supporting_catalogue: AtlasResourceCatalogue,
) -> None:
    transport = build_source_resource_payloads(supporting_catalogue)
    rows(transport, "supporting_entries")[0]["entry"]["terminal_status"] = (
        "invented_admitted_body"
    )
    rebind_index(transport)
    with pytest.raises(ValueError, match="index identity"):
        validate_source_resource_payloads(
            transport,
            expected_catalogue_manifest_sha256=supporting_catalogue.provenance[
                "catalogue_manifest_sha256"
            ],
        )
