"""Adding ancillary source metadata preserves the original native Atlas population."""

from __future__ import annotations

from dataclasses import fields, replace
from typing import Any

from bijux_pollenomics.reporting.map_document import source_resources as owner
from bijux_pollenomics.reporting.map_document.static_assets.source_resources import (
    build_source_resource_payloads,
)

from .native_federations import (
    ancillary_sources as ancillary_sources,
)
from .native_federations import (
    capsule_inputs as capsule_inputs,
)
from .native_federations import (
    source_input,
)


def test_native_projection_and_existing_transport_remain_identical(
    ancillary_sources: dict[str, Any],
) -> None:
    configured = source_input(ancillary_sources)
    original = owner.load_atlas_resource_catalogue(replace(configured, ancillary=None))
    joined = owner.load_atlas_resource_catalogue(configured)
    assert original.ancillary is None
    assert joined.ancillary is not None
    for field in fields(original):
        if field.name != "ancillary":
            assert getattr(original, field.name) == getattr(joined, field.name)
    before = build_source_resource_payloads(original)
    after = build_source_resource_payloads(joined)
    assert before == after
    assert all(
        site["legacy_numerical_membership"] == "not_joined"
        for site in joined.site_records
    )
    assert joined.legacy_site_references == ()
