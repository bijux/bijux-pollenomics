from __future__ import annotations

from math import fsum

import pytest

from bijux_pollenomics.collection.sources.hyde import Bounds, GridSpec
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal
from bijux_pollenomics.core.geospatial.distance import WGS84_GEODESIC


def test_parallel_bounded_area_matches_independent_dense_geodesic_polygon() -> None:
    bounds = Bounds(10, 60, 11, 61)
    bottom = [(10 + i / 1000, 60) for i in range(1001)]
    top = [(11 - i / 1000, 61) for i in range(1001)]
    points = bottom + top
    area, _ = WGS84_GEODESIC.polygon_area_perimeter(
        [p[0] for p in points], [p[1] for p in points]
    )
    assert bounds.area_km2 == pytest.approx(abs(area) / 1e6, rel=1e-9)


def test_area_varies_with_latitude_and_conserves_partition() -> None:
    assert Bounds(0, 60, 1, 61).area_km2 < Bounds(0, 0, 1, 1).area_km2 * 0.51
    parts = [Bounds(x, y, x + 1, y + 1).area_km2 for x in (10, 11) for y in (60, 61)]
    assert fsum(parts) == pytest.approx(Bounds(10, 60, 12, 62).area_km2, rel=1e-12)


def test_row_orientation_edges_and_dateline_refusal() -> None:
    north_first = GridSpec(2, 2, 10, 60, 1, 1, "north_to_south")
    south_first = GridSpec(2, 2, 10, 60, 1, 1, "south_to_north")
    assert north_first.cell_bounds(0, 0) == south_first.cell_bounds(1, 0)
    assert north_first.cell_bounds(0, 0).south == 61
    with pytest.raises(IntakeRefusal, match="bounds_invalid"):
        Bounds(179, 0, -179, 1)
    with pytest.raises(IntakeRefusal, match="grid_dimensions_invalid"):
        GridSpec(True, 1, 10, 60, 1, 1, "north_to_south")
