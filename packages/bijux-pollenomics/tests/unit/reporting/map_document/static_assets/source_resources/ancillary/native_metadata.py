"""Authenticated finite legacy, scoped and supporting source metadata fixtures."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from bijux_pollenomics.reporting.map_document.source_resources import (
    AtlasResourceCatalogue,
    load_atlas_resource_catalogue,
)

from ....source_resources.ancillary.native_archives import (
    reference_archive as reference_archive,
)
from ....source_resources.ancillary.native_archives import (
    reference_source as reference_source,
)
from ....source_resources.ancillary.native_archives import (
    site_context_products as site_context_products,
)
from ....source_resources.ancillary.native_archives import (
    supporting_sources as supporting_sources,
)
from ....source_resources.ancillary.native_archives import (
    unit_products as unit_products,
)
from ....source_resources.ancillary.native_federations import (
    ancillary_sources as ancillary_sources,
)
from ....source_resources.ancillary.native_federations import (
    capsule_inputs as capsule_inputs,
)
from ....source_resources.ancillary.native_federations import (
    scoped_ancillary_sources as scoped_ancillary_sources,
)
from ....source_resources.ancillary.native_federations import (
    scoped_inputs as scoped_inputs,
)
from ....source_resources.ancillary.native_federations import (
    scoped_selection_products as scoped_selection_products,
)
from ....source_resources.ancillary.native_federations import (
    source_input,
)


@pytest.fixture
def legacy_catalogue(ancillary_sources: dict[str, Any]) -> AtlasResourceCatalogue:
    return load_atlas_resource_catalogue(source_input(ancillary_sources))


@pytest.fixture
def scoped_catalogue(
    scoped_ancillary_sources: dict[str, Any],
) -> AtlasResourceCatalogue:
    return load_atlas_resource_catalogue(source_input(scoped_ancillary_sources))


@pytest.fixture
def supporting_catalogue(
    supporting_sources: Callable[..., dict[str, Any]],
) -> AtlasResourceCatalogue:
    return load_atlas_resource_catalogue(
        supporting_sources("reference_tables")["source"]
    )


def rows(transport: Any, kind: str) -> list[dict[str, Any]]:
    return [
        row
        for part in transport.payloads
        if part["kind"] == kind
        for row in part["records"]
    ]


def rebind_index(transport: Any) -> None:
    """Keep adversarial indexes coherent so source-law refusals are consequential."""
    from bijux_pollenomics.reporting.map_document.static_assets.source_resources.validation import (
        _index_entry,
    )

    parts = [part for part in transport.payloads if part["kind"] == "index"]
    assert len(parts) == 1
    parts[0]["records"] = [
        _index_entry(part["kind"], row, part["part_id"])
        for part in transport.payloads
        if part["kind"] not in {"index", "context"}
        for row in part["records"]
    ]
