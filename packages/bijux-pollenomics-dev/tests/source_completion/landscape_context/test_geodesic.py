"""Challenge spatial units, reference accuracy and threshold comparisons."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.landscape_context.geodesic import (
    WGS84,
    inside,
    point,
    spherical_km,
    wgs84_km,
)
from bijux_pollenomics_dev.source_completion.landscape_context.source import overlap


@pytest.mark.parametrize("value", [True, False, None, "55", float("nan"), float("inf")])
def test_invalid_coordinate_values_refused(value: object) -> None:
    with pytest.raises(ValueError):
        point(value, 13)


@pytest.mark.parametrize("lat,lon", [(91, 13), (-91, 13), (55, 181), (55, -181)])
def test_coordinate_axis_domain_refused(lat: float, lon: float) -> None:
    with pytest.raises(ValueError):
        point(lat, lon)


def test_true_zero_coordinate_and_distance() -> None:
    assert point(0, 0) == (0, 0)
    assert wgs84_km((0, 0), (0, 0)) == spherical_km((0, 0), (0, 0)) == 0


@pytest.mark.parametrize("radius", [10, 20])
def test_full_computational_threshold_is_not_display_rounding(radius: int) -> None:
    assert inside(float(radius), radius)
    assert inside(math.nextafter(float(radius), -math.inf), radius)
    assert not inside(math.nextafter(float(radius), math.inf), radius)
    assert not inside(radius + 0.000001, radius)
    assert round(radius + 0.000001, 3) == radius


@pytest.mark.parametrize("radius", [10, 20])
@pytest.mark.parametrize(
    "latitude,longitude", [(0, 0), (55, 13), (89, 0), (55, 179.99)]
)
@pytest.mark.parametrize("azimuth", [0, 90, 180, 270])
def test_direct_inverse_resolves_one_millimetre_boundary_sides(
    radius: int, latitude: float, longitude: float, azimuth: float
) -> None:
    for side in [-1, 1]:
        expected = radius * 1000 + side * 0.001
        lon, lat, _ = WGS84.fwd(longitude, latitude, azimuth, expected)
        computed = wgs84_km((latitude, longitude), (lat, lon))
        assert abs(computed * 1000 - expected) < 1e-5
        assert inside(computed, radius) == (side < 0)


def test_twenty_published_geographiclib_inverse_distances() -> None:
    reference = json.loads(
        (Path(__file__).parent / "fixtures/inverse-vectors.json").read_bytes()
    )
    assert len(reference["vectors"]) == 20
    assert WGS84.a == 6378137 and abs(WGS84.f - 1 / 298.257223563) < 1e-18
    for row in reference["vectors"]:
        # Published vectors use unrolled longitudes; canonicalize equivalent
        # meridians only for this fixture, preserving source coordinate refusal.
        a = (row["latitude_1"], (row["longitude_1"] + 180) % 360 - 180)
        b = (row["latitude_2"], (row["longitude_2"] + 180) % 360 - 180)
        forward = wgs84_km(a, b) * 1000
        reverse = wgs84_km(b, a) * 1000
        assert abs(forward - row["expected_metres"]) < reference["tolerance_metres"]
        assert abs(forward - reverse) < 1e-7


@pytest.mark.parametrize(
    "lower,upper,start,end,expected",
    [
        (0, 0, 0, 500, True),
        (500, 500, 0, 500, False),
        (500, 500, 500, 1000, True),
        (0, 500, 500, 1000, False),
        (None, 500, 0, 500, False),
        (0, None, 0, 500, False),
        (500, 0, 0, 500, False),
        (-1, -1, -500, 0, True),
        (82, 83, 84, 105, False),
        (105, 107, 84, 105, False),
    ],
)
def test_original_half_open_point_and_disjoint_interval_semantics(
    lower: float | None, upper: float | None, start: int, end: int, expected: bool
) -> None:
    assert overlap(lower, upper, start, end) is expected
