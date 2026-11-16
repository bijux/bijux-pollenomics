"""Malformed coordinate values cannot acquire a numeric location."""

from __future__ import annotations

from typing import Any

import pytest

from bijux_pollenomics.collection.spatial.representative_points import (
    geometry_to_representative_point,
)
from bijux_pollenomics.core.geospatial.geojson import parse_position


@pytest.mark.parametrize("axis", [0, 1])
@pytest.mark.parametrize(
    "invalid",
    [True, False, float("nan"), float("inf"), float("-inf"), 10**1000, -(10**1000)],
    ids=[
        "true",
        "false",
        "nan",
        "infinity",
        "negative-infinity",
        "huge",
        "negative-huge",
    ],
)
def test_invalid_numeric_coordinate_has_no_map_location(
    axis: int, invalid: Any
) -> None:
    coordinates = [15, 59]
    coordinates[axis] = invalid
    assert parse_position(coordinates) is None
    assert (
        geometry_to_representative_point({"type": "Point", "coordinates": coordinates})
        is None
    )


@pytest.mark.parametrize(
    "coordinates,expected",
    [([0, 0], (0.0, 0.0)), ([15.5, -59], (15.5, -59.0)), ([15, 59, 123], (15.0, 59.0))],
)
def test_finite_positions_keep_zero_sign_precision_and_existing_2d_projection(
    coordinates: list[int | float], expected: tuple[float, float]
) -> None:
    assert parse_position(coordinates) == expected
    assert geometry_to_representative_point(
        {"type": "Point", "coordinates": coordinates}
    ) == (*expected, "Point")
