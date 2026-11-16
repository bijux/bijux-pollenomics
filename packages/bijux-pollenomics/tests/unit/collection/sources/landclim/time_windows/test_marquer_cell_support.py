"""Every source contributor must remain inside its inferred model cell."""

import math
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.collection.sources.landclim.time_windows.marquer import (
    _marquer_cell_geometries,
)
from tests.support.workbooks import write_xlsx


def _metadata(path: Path, points: tuple[tuple[float, float], ...]) -> None:
    rows: list[list[object]] = [["grid", "site", "source", "latitude", "longitude"]]
    for lon, lat in points:
        rows.append(["GC1", "generated", "fixture", str(lat), str(lon)])
    write_xlsx(path, {"Metadata": rows})


@pytest.mark.parametrize(
    "point",
    [
        (17.995, 59.5),
        (17.5, 59.995),
        (-0.005, 59.5),
        (17.5, -0.005),
        (17.5, 59.5),
        (18.0, 60.0),
    ],
)
def test_near_integer_coordinates_never_move_support_past_a_contributor(
    tmp_path: Path, point: tuple[float, float]
) -> None:
    path = tmp_path / "marquer.xlsx"
    _metadata(path, (point,))
    geometry = _marquer_cell_geometries(path)["1"]
    ring = cast(list[list[list[float]]], geometry["coordinates"])[0]
    assert min(p[0] for p in ring) <= point[0] <= max(p[0] for p in ring)
    assert min(p[1] for p in ring) <= point[1] <= max(p[1] for p in ring)


@pytest.mark.parametrize(
    "points",
    [
        ((17.995, 59.5), (18.2, 59.5)),
        ((17.5, 59.995), (17.5, 60.2)),
        ((17.0, 59.0), (18.1, 59.0)),
    ],
)
def test_contributors_without_one_consistent_integer_grid_cell_are_refused(
    tmp_path: Path, points: tuple[tuple[float, float], ...]
) -> None:
    path = tmp_path / "marquer.xlsx"
    _metadata(path, points)
    with pytest.raises(
        ValueError, match="grid 1 site coordinates exceed one-degree support"
    ):
        _marquer_cell_geometries(path)


@pytest.mark.parametrize(
    "point",
    [
        (180.0, 90.0),
        (-180.0, -90.0),
        (180.0, -90.0),
        (-180.0, 90.0),
    ],
)
def test_geographic_boundary_points_keep_their_whole_cell_inside_the_world(
    tmp_path: Path, point: tuple[float, float]
) -> None:
    path = tmp_path / "marquer.xlsx"
    _metadata(path, (point,))
    geometry = _marquer_cell_geometries(path)["1"]
    ring = cast(list[list[list[float]]], geometry["coordinates"])[0]
    assert all(-180 <= lon <= 180 and -90 <= lat <= 90 for lon, lat in ring)
    assert min(p[0] for p in ring) <= point[0] <= max(p[0] for p in ring)
    assert min(p[1] for p in ring) <= point[1] <= max(p[1] for p in ring)


@pytest.mark.parametrize(
    "point",
    [
        (180.1, 0.0),
        (-180.1, 0.0),
        (0.0, 90.1),
        (0.0, -90.1),
        (math.nan, 0.0),
        (0.0, math.inf),
    ],
)
def test_invalid_geographic_support_refuses_with_the_native_cell_identity(
    tmp_path: Path, point: tuple[float, float]
) -> None:
    path = tmp_path / "marquer.xlsx"
    _metadata(path, (point,))
    with pytest.raises(ValueError, match="Marquer grid 1 coordinates"):
        _marquer_cell_geometries(path)
