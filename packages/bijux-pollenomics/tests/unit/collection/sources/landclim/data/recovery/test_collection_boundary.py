"""Raw and nested collection recovery never becomes governed collection data."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from bijux_pollenomics.collection.sources.landclim import catalog, collection
from bijux_pollenomics.collection.sources.landclim.collection import surfaces
from bijux_pollenomics.core.filesystem.recovery_storage import (
    resolve_publication_workspace_parent,
)
from tests.unit.collection.sources.landclim.data.test_native_payload_validation import (
    workbook_bytes,
)

FIRST = "landclim_i_land_cover_types.xlsx"


def inventory(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def collection_fixture(root: Path) -> Path:
    (root / "pyproject.toml").write_text('[project]\nname="standalone-landclim"\n')
    public = root / "landclim"
    (public / "raw").mkdir(parents=True)
    (public / "raw" / FIRST).write_bytes(b"previous source")
    (public / "normalized").mkdir()
    (public / "normalized/user.txt").write_bytes(b"user work")
    return public


def assert_no_private_members(root: Path) -> None:
    assert not any(
        path.name.startswith((".bijux-publication-recovery", "capture-"))
        for path in root.rglob("*")
    )


@pytest.mark.parametrize("owner", [catalog, collection])
def test_raw_recollection_recovery_is_outside_the_whole_collection(
    tmp_path: Path, owner: object
) -> None:
    public = collection_fixture(tmp_path)
    with (
        patch.object(
            owner,
            "resolve_landclim_asset_urls",
            return_value={FIRST: "https://example.test/source"},
        ),
        patch.object(owner, "fetch_binary", return_value=workbook_bytes()),
    ):
        owner.download_landclim_raw_assets(public / "raw")
    storage = resolve_publication_workspace_parent(
        public, namespace="landclim-collection"
    )
    records = list(storage.glob("capture-*/published.json"))
    assert len(records) == 1
    assert not storage.is_relative_to(public)
    assert (records[0].parent / "prior" / FIRST).read_bytes() == b"previous source"
    assert (public / "normalized/user.txt").read_bytes() == b"user work"
    assert_no_private_members(public)


@pytest.mark.parametrize("fail_writer", [False, True])
def test_nested_collector_retains_recovery_outside_final_collection(
    tmp_path: Path, fail_writer: bool
) -> None:
    public = collection_fixture(tmp_path)
    prior = inventory(public)
    original = OSError("synthetic normalization failure")
    with (
        patch.object(
            collection,
            "resolve_landclim_asset_urls",
            return_value={FIRST: "https://example.test/source"},
        ),
        patch.object(collection, "fetch_binary", return_value=workbook_bytes()),
        patch.object(
            collection,
            "_build_landclim_raw_receipt",
            return_value={"source": "generated fixture"},
        ),
        patch.object(collection, "validate_landclim_raw_receipt", return_value={}),
        patch.object(surfaces, "build_landclim_site_records", return_value=[]),
        patch.object(
            surfaces,
            "build_landclim_grid_geojson",
            return_value={"type": "FeatureCollection", "features": []},
        ),
        patch.object(
            surfaces,
            "build_landclim_temporal_grid_geojson",
            return_value={"type": "FeatureCollection", "features": []},
        ),
    ):
        if fail_writer:
            with (
                patch.object(
                    surfaces, "write_context_points_geojson", side_effect=original
                ),
                pytest.raises(OSError) as caught,
            ):
                collection.collect_landclim_data(public, {}, (0, 0, 1, 1))
            assert caught.value is original
            assert inventory(public) == prior
        else:
            report = collection.collect_landclim_data(public, {}, (0, 0, 1, 1))
            assert report.raw_manifest_path == public / "raw/landclim_sources.json"
            assert report.summary_path.is_file()
            assert (public / "normalized/user.txt").read_bytes() == b"user work"
    storage = resolve_publication_workspace_parent(
        public, namespace="landclim-collection"
    )
    runs = list(storage.glob("capture-*"))
    assert len(runs) == 1
    assert_no_private_members(public)
    assert not any(
        path.is_relative_to(public) for path in tmp_path.rglob("prepared.json")
    )
    assert (runs[0] / ("refused.json" if fail_writer else "published.json")).is_file()
    assert any(
        path.read_bytes() == b"previous source"
        for path in tmp_path.rglob(FIRST)
        if not path.is_relative_to(public)
    )


def test_download_failure_keeps_all_previous_collection_bytes(tmp_path: Path) -> None:
    public = collection_fixture(tmp_path)
    before = inventory(public)
    failure = OSError("synthetic download failed")
    with (
        patch.object(
            collection,
            "resolve_landclim_asset_urls",
            return_value={FIRST: "https://example.test/source"},
        ),
        patch.object(collection, "fetch_binary", side_effect=failure),
        pytest.raises(OSError) as caught,
    ):
        collection.download_landclim_raw_assets(public / "raw")
    assert caught.value is failure
    assert inventory(public) == before
    assert_no_private_members(public)
    storage = resolve_publication_workspace_parent(
        public, namespace="landclim-collection"
    )
    assert len(list(storage.glob("capture-*/refused.json"))) == 1
