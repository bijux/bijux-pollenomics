"""Official same-frame controls are separate from exact mathematical grid edges."""

from __future__ import annotations

import csv
import importlib
import math
from pathlib import Path
from typing import Any

from pyproj import Transformer
import pytest

from .test_service import producer


def projection_module() -> Any:
    module, _ = producer()
    return importlib.import_module(module.__name__ + ".projection")


def test_all_fifteen_official_controls_verify_both_directions_and_axes() -> None:
    module = projection_module()
    projection = module.NativePointProjection()
    forward = Transformer.from_crs(4619, 3006, always_xy=True, allow_ballpark=False)
    path = Path(__file__).parent / "reference/sweref99tm-controls.csv"
    with path.open() as stream:
        controls = list(csv.DictReader(stream))
    assert len(controls) == 15 and [int(r["control_id"]) for r in controls] == list(
        range(1, 16)
    )
    for row in controls:
        lon = float(row["longitude_degrees"])
        lat = float(row["latitude_degrees"])
        east = float(row["easting_metres"])
        north = float(row["northing_metres"])
        actual_east, actual_north = forward.transform(lon, lat, errcheck=True)
        assert (
            abs(actual_east - east) <= 0.000501
            and abs(actual_north - north) <= 0.000501
        )
        inverse = projection.inverse_point(east, north)
        assert inverse is not None
        assert abs(inverse[0] - lon) <= 2e-8 and abs(inverse[1] - lat) <= 1e-8
        assert projection.inverse_point(north, east) is None
    assert projection.source.to_epsg() == 3006 and projection.target.to_epsg() == 4619
    identity = projection.identity()
    assert (
        identity["always_xy"] is True
        and identity["reported_accuracy_is_not_native_coordinate_accuracy"] is True
    )
    assert (
        identity["location_support"]
        == "EPSG3006_area_of_use_rectangle_not_country_containment"
    )


@pytest.mark.parametrize(
    "longitude,latitude,expected",
    [
        (15.0, 60.0, (15, 60)),
        (math.nextafter(15.0, -math.inf), math.nextafter(60.0, -math.inf), (14, 59)),
        (math.nextafter(15.0, math.inf), math.nextafter(60.0, math.inf), (15, 60)),
        (0.0, 0.0, (0, 0)),
        (-0.000001, -0.000001, (-1, -1)),
        (-180.0, -90.0, (-180, -90)),
    ],
)
def test_grid_edges_have_exact_half_open_ownership_without_snapping(
    longitude: float, latitude: float, expected: tuple[int, int]
) -> None:
    assert projection_module().grid_cell(longitude, latitude) == expected


@pytest.mark.parametrize(
    "longitude,latitude", [(180, 60), (15, 90), (float("nan"), 60), (15, float("inf"))]
)
def test_outside_global_grid_domain_is_refused(
    longitude: float, latitude: float
) -> None:
    with pytest.raises(ValueError):
        projection_module().grid_cell(longitude, latitude)
