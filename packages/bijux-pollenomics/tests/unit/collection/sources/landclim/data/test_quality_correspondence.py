"""Native quality rows must own the exact physical result cell."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.collection.sources.landclim.grid import (
    landclim_ii_quality_lookup,
    merge_landclim_ii_grid_features,
)
from bijux_pollenomics.collection.sources.landclim.time_windows import (
    time_window_from_tw_filename,
)
from bijux_pollenomics.collection.sources.landclim.time_windows.landclim_ii import (
    _merge_landclim_ii_time_windows,
)
from tests.support.geography import NORDIC_TEST_BBOX, SWEDEN_BOUNDARIES
from tests.support.workbooks import write_landclim_ii_zip, write_xlsx


def _quality(path: Path, longitude: str, latitude: str) -> dict[str, dict[str, str]]:
    windows = [
        time_window_from_tw_filename(f"TW{index}.csv").removesuffix(" BP")
        for index in range(1, 26)
    ]
    write_xlsx(
        path,
        {
            "GC_quality_by_TW": [
                ["LCGRID_ID", "lonDD", "latDD", *windows],
                ["GC001", longitude, latitude, *(["1"] * 25)],
            ]
        },
    )
    return landclim_ii_quality_lookup(path)


def _project(
    path: Path, quality: dict[str, dict[str, str]], projection: str
) -> dict[Any, dict[str, Any]]:
    features: dict[Any, dict[str, Any]] = {}
    merge = (
        _merge_landclim_ii_time_windows
        if projection == "temporal"
        else merge_landclim_ii_grid_features
    )
    merge(
        features,
        path,
        quality_by_grid=quality,
        bbox=NORDIC_TEST_BBOX,
        country_boundaries=cast(Mapping[str, Mapping[str, object]], SWEDEN_BOUNDARIES),
    )
    return features


@pytest.mark.parametrize("projection", ["temporal", "aggregate"])
def test_quality_coordinates_must_match_the_physical_result_cell(
    tmp_path: Path, projection: str
) -> None:
    path = tmp_path / "results.zip"
    write_landclim_ii_zip(
        path,
        [{"LCGRID_ID": "GC001", "lonDD": "17.5", "latDD": "59.5", "PICEA": "0.12"}],
    )
    quality = _quality(tmp_path / "quality.xlsx", "18.5", "60.5")
    with pytest.raises(ValueError, match="quality physical cell differs"):
        _project(path, quality, projection)


@pytest.mark.parametrize("projection", ["temporal", "aggregate"])
def test_decimal_spelling_aliases_preserve_the_same_source_cell(
    tmp_path: Path, projection: str
) -> None:
    path = tmp_path / "results.zip"
    write_landclim_ii_zip(
        path,
        [{"LCGRID_ID": "GC001", "lonDD": "17.5", "latDD": "59.5", "PICEA": "0.12"}],
    )
    quality = _quality(tmp_path / "quality.xlsx", "17.5000", "5.95e1")
    features = _project(path, quality, projection)
    assert len(features) == 1
    if projection == "temporal":
        properties = next(iter(features.values()))["properties"]
        assert properties["reconstruction_values"] == {"PICEA": 0.12}
        assert properties["standard_errors"] == {"PICEA": 0.01}


def test_quality_coordinate_precision_cannot_alias_a_distinct_native_cell(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="coordinate precision is unsupported"):
        _quality(tmp_path / "quality.xlsx", "17.500000000000000001", "59.5")
