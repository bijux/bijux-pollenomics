from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.collection.sources.landclim.grid import (
    build_landclim_grid_geojson,
    feature_key_from_center,
    feature_key_from_geometry,
    grid_geometry_from_center,
    landclim_ii_quality_lookup,
)
from bijux_pollenomics.collection.sources.landclim.time_windows import (
    time_window_from_tw_filename,
)
from bijux_pollenomics.collection.sources.landclim.time_windows.landclim_ii import (
    _merge_landclim_ii_time_windows,
)
from tests.support.geography import NORDIC_TEST_BBOX, SWEDEN_BOUNDARIES
from tests.support.workbooks import write_landclim_ii_zip, write_xlsx


@pytest.mark.parametrize(
    "second,expected_count", [("17.5000002", 2), ("17.5000001", 1)]
)
def test_aggregate_groups_only_equal_source_cell_geometry(
    tmp_path: Path,
    second: str,
    expected_count: int,
) -> None:
    workbook_a = tmp_path / "cover.xlsx"
    workbook_b = tmp_path / "pft.xlsx"
    quality = tmp_path / "quality.xlsx"
    archive = tmp_path / "results.zip"
    for path in (workbook_a, workbook_b):
        write_xlsx(path, {"empty": [["no grid rows"]]})
    windows = [
        time_window_from_tw_filename(f"TW{i}.csv").removesuffix(" BP")
        for i in range(1, 26)
    ]
    write_xlsx(
        quality,
        {
            "GC_quality_by_TW": [
                ["LCGRID_ID", "lonDD", "latDD", *windows],
                ["A", "17.5000001", "59.5", *(["1"] * 25)],
                ["B", second, "59.5", *(["1"] * 25)],
            ]
        },
    )
    write_landclim_ii_zip(
        archive,
        [
            {"LCGRID_ID": "A", "lonDD": "17.5000001", "latDD": "59.5", "PICEA": "0.2"},
            {"LCGRID_ID": "B", "lonDD": second, "latDD": "59.5", "PICEA": "0.8"},
        ],
        time_window_count=1,
    )
    paths = {
        "landclim_i_land_cover_types.xlsx": workbook_a,
        "landclim_i_plant_functional_types.xlsx": workbook_b,
        "landclim_ii_grid_cell_quality.xlsx": quality,
        "landclim_ii_reveals_results.zip": archive,
    }
    boundaries = cast(dict[str, dict[str, object]], SWEDEN_BOUNDARIES)
    result = build_landclim_grid_geojson(paths, NORDIC_TEST_BBOX, boundaries)
    features = result["features"]
    assert isinstance(features, list)
    assert len(features) == expected_count
    ids = {feature["properties"]["record_id"] for feature in features}
    assert len(ids) == expected_count
    assert ids == {
        feature_key_from_center(17.5000001, 59.5),
        feature_key_from_center(float(second), 59.5),
    }
    temporal: dict[tuple[str, str, str], dict[str, object]] = {}
    _merge_landclim_ii_time_windows(
        temporal,
        archive,
        quality_by_grid=landclim_ii_quality_lookup(quality),
        bbox=NORDIC_TEST_BBOX,
        country_boundaries=boundaries,
    )
    assert {key[1] for key in temporal} == {"A", "B"}


def test_geometry_and_center_key_preserve_precise_edges() -> None:
    left = feature_key_from_center(17.5000001, 59.5)
    right = feature_key_from_center(17.5000002, 59.5)
    assert left != right
    assert left == feature_key_from_geometry(
        grid_geometry_from_center(17.5000001, 59.5)
    )
    assert right == feature_key_from_geometry(
        grid_geometry_from_center(17.5000002, 59.5)
    )
    assert (
        feature_key_from_center(17.5, 59.5) == "17.000000,59.000000,18.000000,60.000000"
    )


@pytest.mark.parametrize(
    "longitude,latitude",
    [
        (float("nan"), 59.5),
        (float("inf"), 59.5),
        (10**1000, 59.5),
        (180, 59.5),
        (17.5, 90),
        (5e-324, 59.5),
    ],
)
def test_invalid_or_unrepresentable_center_is_refused(
    longitude: float, latitude: float
) -> None:
    with pytest.raises(ValueError):
        feature_key_from_center(longitude, latitude)


def test_signed_zero_in_edges_has_one_key() -> None:
    assert feature_key_from_center(-0.0, 0.5) == feature_key_from_center(0.0, 0.5)
    geometry = grid_geometry_from_center(0.5, 0.5)
    negative = {
        "type": "Polygon",
        "coordinates": [
            [[-0.0, -0.0], [1.0, -0.0], [1.0, 1.0], [-0.0, 1.0], [-0.0, -0.0]]
        ],
    }
    assert feature_key_from_geometry(geometry) == feature_key_from_geometry(negative)
