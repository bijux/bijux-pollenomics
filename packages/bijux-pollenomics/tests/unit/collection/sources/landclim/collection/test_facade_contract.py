from __future__ import annotations

import inspect
from pathlib import Path
from unittest.mock import patch

import pytest
from bijux_pollenomics.collection.sources.landclim import collection

EXPECTED_EXPORTS = [
    "LandClimRawReceiptError",
    "LandClimDataReport",
    "build_landclim_grid_geojson",
    "build_landclim_temporal_grid_geojson",
    "build_landclim_raw_asset_summaries",
    "build_landclim_site_records",
    "collect_landclim_data",
    "download_landclim_raw_assets",
    "feature_key_from_center",
    "feature_key_from_geometry",
    "grid_geometry_from_nw_cell_label",
    "inspect_landclim_ii_archive",
    "landclim_i_site_records",
    "landclim_ii_site_records",
    "materialize_landclim_repository_surfaces",
    "parse_coordinate",
    "resolve_landclim_asset_urls",
    "resolve_landclim_marquer_asset_urls",
    "resolve_landclim_tabular_asset_urls",
    "validate_landclim_raw_receipt",
]


def test_facade_preserves_exports_and_callable_shapes() -> None:
    assert collection.__all__ == EXPECTED_EXPORTS
    assert str(inspect.signature(collection.collect_landclim_data)) == (
        "(output_root: 'Path', country_boundaries: "
        "'dict[str, dict[str, object]]', bbox: "
        "'tuple[float, float, float, float]') -> 'LandClimDataReport'"
    )
    assert str(inspect.signature(collection.download_landclim_raw_assets)) == (
        "(raw_dir: 'Path') -> 'LandClimRawAssets'"
    )
    assert str(inspect.signature(collection._build_landclim_raw_receipt)) == (
        "(raw_paths: 'dict[str, Path]', asset_urls: 'dict[str, str]', "
        "*, generated_on: 'str') -> 'dict[str, object]'"
    )


def test_acquisition_keeps_facade_monkeypatch_seams(tmp_path: Path) -> None:
    with (
        patch.object(
            collection,
            "resolve_landclim_asset_urls",
            return_value={"landclim_i_land_cover_types.xlsx": "https://example.test"},
        ) as resolver,
        patch.object(collection, "fetch_binary", return_value=b"") as fetcher,
        pytest.raises(
            ValueError,
            match=(
                "^LandClim raw asset download was empty for "
                "landclim_i_land_cover_types\\.xlsx$"
            ),
        ),
    ):
        collection.download_landclim_raw_assets(tmp_path)

    resolver.assert_called_once_with()
    fetcher.assert_called_once_with("https://example.test")
