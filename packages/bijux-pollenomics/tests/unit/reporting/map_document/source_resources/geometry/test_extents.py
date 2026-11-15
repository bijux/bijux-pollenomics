"""A native extent is a source boundary, never an inferred sample location."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.reporting.map_document.source_resources import (
    AtlasResourceCatalogueInput,
    load_atlas_resource_catalogue,
)

_RING = [[179, 60], [-179, 60], [-179, 62], [179, 60]]
_HOLE = [[179.2, 60.2], [179.5, 60.2], [179.4, 60.4], [179.2, 60.2]]


@pytest.mark.parametrize(
    "geometry",
    [
        {"type": "Polygon", "coordinates": [_RING, _HOLE]},
        {"type": "MultiPolygon", "coordinates": [[_RING, _HOLE], [_RING]]},
    ],
)
def test_native_rings_holes_and_dateline_coordinates_remain_exact_extents(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]],
    geometry: dict[str, Any],
) -> None:
    root, digest, raw = atlas_catalogue(geography=geometry, all_site_resources=True)
    result = load_atlas_resource_catalogue(AtlasResourceCatalogueInput(root, digest))
    site = result.site_records[0]
    assert site["marker_geometry"] is None
    assert site["geometry_status"] == "native_point_unavailable"
    variant = site["native_site_variants"][0]
    assert variant["extent_geometry"] == geometry
    assert variant["extent_status"] == "explicit_native_extent"
    assert variant["dataset_ids"] == ["201", "202"]
    assert len(variant["metadata_sources"]) == 2
    assert variant["native_site"]["geography"] == geometry
    assert raw["resources"][0]["metadata"]["native_site"]["geography"] == geometry


@pytest.mark.parametrize(
    "geometry",
    [
        {"type": "Polygon", "coordinates": []},
        {"type": "Polygon", "coordinates": [[[12, 61], [13, 61], [13, 62]]]},
        {"type": "Polygon", "coordinates": [[[12, 61], [13, 61], [13, 62], [12, 62]]]},
        {"type": "Polygon", "coordinates": [[[12, 61, 1]] * 4]},
        {"type": "Polygon", "coordinates": [[[True, 61]] * 4]},
        {"type": "MultiPolygon", "coordinates": [[[[181, 61]] * 4]]},
        '{"type":"Polygon","coordinates":[],"coordinates":[[[12,61],[13,61],[13,62],[12,61]]]}',
        '{"type":"Polygon","coordinates":[[[1e-9999,61],[13,61],[13,62],[1e-9999,61]]]}',
    ],
)
def test_invalid_extents_stay_raw_and_list_only(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]], geometry: object
) -> None:
    root, digest, _ = atlas_catalogue(geography=geometry, all_site_resources=True)
    result = load_atlas_resource_catalogue(AtlasResourceCatalogueInput(root, digest))
    site = result.site_records[0]
    assert site["marker_geometry"] is None
    variant = site["native_site_variants"][0]
    assert variant["extent_geometry"] is None
    assert variant["extent_status"] != "explicit_native_extent"
    assert variant["native_site"]["geography"] == geometry


def test_extent_display_budget_retains_every_raw_variant_without_partial_admission(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.reporting.map_document.source_resources import geometry

    polygon = {"type": "Polygon", "coordinates": [_RING]}
    root, digest, _ = atlas_catalogue(geography=polygon)
    monkeypatch.setattr(geometry, "MAX_SITE_EXTENT_VARIANTS", 1)
    actual_extent = geometry.native_extent

    def bounded_site(native: Any) -> Any:
        if native.get("siteid") == 12:
            pytest.fail("Over-budget site parsed extents")
        return actual_extent(native)

    monkeypatch.setattr(geometry, "native_extent", bounded_site)
    result = load_atlas_resource_catalogue(AtlasResourceCatalogueInput(root, digest))
    variants = result.site_records[0]["native_site_variants"]
    assert len(variants) == 2
    assert all(variant["extent_geometry"] is None for variant in variants)
    assert {variant["extent_status"] for variant in variants} == {
        "native_extent_site_display_budget_exceeded"
    }
    assert sorted(
        member for variant in variants for member in variant["dataset_ids"]
    ) == ["201", "202"]
    assert any(variant["native_site"]["geography"] == polygon for variant in variants)


def test_extent_coordinate_budget_refuses_the_whole_native_geometry(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.reporting.map_document.source_resources import geometry

    polygon = {"type": "Polygon", "coordinates": [_RING, _HOLE]}
    root, digest, _ = atlas_catalogue(geography=polygon, all_site_resources=True)
    monkeypatch.setattr(geometry, "MAX_EXTENT_POSITIONS", 6)
    result = load_atlas_resource_catalogue(AtlasResourceCatalogueInput(root, digest))
    variant = result.site_records[0]["native_site_variants"][0]
    assert variant["extent_geometry"] is None
    assert variant["extent_status"] == "native_extent_coordinate_budget_exceeded"
    assert variant["native_site"]["geography"] == polygon
