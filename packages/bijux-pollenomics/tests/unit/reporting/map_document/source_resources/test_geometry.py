"""All resource-owned native points must agree before offering a metadata marker."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.reporting.map_document.source_resources import (
    AtlasResourceCatalogueInput,
    load_atlas_resource_catalogue,
)

from .catalogue_inputs import pin_compact_extension


@pytest.mark.parametrize(
    ("geography", "status", "coordinates"),
    [
        (
            '{"type":"Point","coordinates":[13,61.5]}',
            "conflicting_native_point_geographies",
            None,
        ),
        (
            {"type": "Point", "coordinates": [12.0, 61.5]},
            "native_point_consensus",
            [12, 61.5],
        ),
        (None, "native_point_unavailable", None),
        ("missing", "native_point_unavailable", None),
        ("malformed", "native_point_unavailable", None),
        ({"type": "Polygon", "coordinates": []}, "native_point_unavailable", None),
        (
            {"type": "Point", "coordinates": [True, 61.5]},
            "native_point_unavailable",
            None,
        ),
        (
            {"type": "Point", "coordinates": [181, 61.5]},
            "native_point_unavailable",
            None,
        ),
        (
            {"type": "Point", "coordinates": [12, 61.5, 3]},
            "native_point_unavailable",
            None,
        ),
        (
            {"type": "Point", "coordinates": ["12", 61.5]},
            "native_point_unavailable",
            None,
        ),
    ],
)
def test_marker_uses_every_native_site_geography(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]],
    geography: object,
    status: str,
    coordinates: object,
) -> None:
    root, digest, raw = atlas_catalogue(geography=geography)
    # The catalogue's representative still has the first point in adverse cases.
    assert raw["sites"][0]["native_site_metadata"]["geography"] == (
        '{"type":"Point","coordinates":[12,61.5]}'
    )
    result = load_atlas_resource_catalogue(AtlasResourceCatalogueInput(root, digest))
    site = result.site_records[0]
    assert site["site_id"] == "12"
    assert site["geometry_status"] == status
    assert site["marker_geometry"] == (
        {"type": "Point", "coordinates": coordinates} if coordinates else None
    )
    assert len(site["native_site_variants"]) == 2
    assert sorted(
        identity
        for variant in site["native_site_variants"]
        for identity in variant["dataset_ids"]
    ) == ["201", "202"]
    assert site["country_code"] == "UNASSIGNED"
    assert site["legacy_numerical_membership"] == "not_joined"


def test_agreeing_metadata_deduplicates_site_payload_without_losing_resource_links(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]],
) -> None:
    root, digest, _ = atlas_catalogue()
    result = load_atlas_resource_catalogue(AtlasResourceCatalogueInput(root, digest))
    site = result.site_records[0]
    assert len(site["native_site_variants"]) == 1
    variant = site["native_site_variants"][0]
    assert variant["dataset_ids"] == ["201", "202"]
    assert len(variant["metadata_sources"]) == 2
    assert {row["native_site_variant_id"] for row in result.resource_records[:2]} == {
        variant["variant_id"]
    }


@pytest.mark.parametrize("foreign_identity", [13, "12", True, None])
def test_foreign_native_site_metadata_cannot_supply_a_marker(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]],
    foreign_identity: object,
) -> None:
    root, _, native = atlas_catalogue()
    native["resources"][1]["metadata"]["native_site"]["siteid"] = foreign_identity
    anchor = pin_compact_extension(root, native)
    with pytest.raises(ValueError, match="native site identity|native ID"):
        load_atlas_resource_catalogue(AtlasResourceCatalogueInput(root, anchor))


@pytest.mark.parametrize(
    "geography",
    [
        '{"type":"Point","coordinates":[12,61.5],"coordinates":[13,61.5]}',
        '{"type":"Point","coordinates":[1e-9999,61.5]}',
    ],
)
def test_encoded_geography_cannot_silently_change_native_coordinates(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]], geography: str
) -> None:
    root, digest, raw = atlas_catalogue(geography=geography, all_site_resources=True)
    assert all(
        row["metadata"]["native_site"]["geography"] == geography
        for row in raw["resources"][:2]
    )
    result = load_atlas_resource_catalogue(AtlasResourceCatalogueInput(root, digest))
    site = result.site_records[0]
    assert site["geometry_status"] == "native_point_unavailable"
    assert site["marker_geometry"] is None
    assert len(site["native_site_variants"]) == 1
    variant = site["native_site_variants"][0]
    assert variant["native_site"]["geography"] == geography
    assert variant["dataset_ids"] == ["201", "202"]
    assert len(variant["metadata_sources"]) == 2
    assert variant["geography_status"] == "native_geography_invalid_json"
