"""Facade patch seams retained across the package boundary."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import call, patch

from bijux_pollenomics.collection.sources.landclim import time_windows


def test_public_builder_resolves_merge_steps_from_the_facade() -> None:
    raw_paths = {
        "marquer_2017_reveals_taxa_grid_cells.xlsx": Path("marquer.xlsx"),
        "landclim_i_land_cover_types.xlsx": Path("cover.xlsx"),
        "landclim_i_plant_functional_types.xlsx": Path("plants.xlsx"),
        "landclim_ii_grid_cell_quality.xlsx": Path("quality.xlsx"),
        "landclim_ii_reveals_results.zip": Path("reveals.zip"),
    }
    bbox = (10.0, 55.0, 25.0, 70.0)
    boundaries: dict[str, dict[str, object]] = {}
    with (
        patch.object(time_windows, "_merge_marquer_time_windows") as marquer,
        patch.object(time_windows, "_merge_landclim_i_time_windows") as landclim_i,
        patch.object(time_windows, "_merge_landclim_ii_time_windows") as landclim_ii,
        patch.object(time_windows, "landclim_ii_quality_lookup", return_value={}),
    ):
        result = time_windows.build_landclim_temporal_grid_geojson(
            raw_paths, bbox, boundaries
        )

    assert result == {"type": "FeatureCollection", "features": []}
    assert marquer.call_count == 1
    assert landclim_i.call_args_list == [
        call(
            {},
            Path("cover.xlsx"),
            value_group="land_cover_types",
            bbox=bbox,
            country_boundaries=boundaries,
        ),
        call(
            {},
            Path("plants.xlsx"),
            value_group="plant_functional_types",
            bbox=bbox,
            country_boundaries=boundaries,
        ),
    ]
    landclim_ii.assert_called_once()


def test_numeric_helpers_resolve_parser_patch_from_the_facade() -> None:
    with patch.object(time_windows, "parse_float", return_value=1.25) as parser:
        result = time_windows._numeric_mapping(
            {"LCGRID_ID": "GC1", "Picea": "source-value"},
            excluded={"LCGRID_ID"},
        )
    assert result == {"Picea": 1.25}
    parser.assert_called_once_with("source-value")


def test_feature_builder_resolves_temporal_parser_patch_from_facade() -> None:
    with patch.object(time_windows, "parse_bp_window_label", return_value=None):
        try:
            time_windows._temporal_grid_feature(
                dataset_id="937075",
                cell_id="GC1",
                cell_label="Grid one",
                time_window="unknown",
                country="Sweden",
                geometry={},
                provenance_path="source.zip",
                provenance_locator="row:1",
                value_unit="percentage_cover",
            )
        except ValueError as error:
            assert str(error) == "LandClim time window is not numeric: unknown"
        else:
            raise AssertionError("invalid temporal label was not refused")
