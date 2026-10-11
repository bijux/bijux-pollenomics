"""Full precision bounded-footprint separation, shared with final evaluation."""

from dataclasses import dataclass, replace
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.spatial.support import (
    support_distance_lower_bound_m,
    support_separation,
)
from bijux_pollenomics.core.geospatial.distance import wgs84_inverse_geodesic


@dataclass(frozen=True)
class Footprint:
    latitude: float
    longitude: float
    radius_m: float = 0
    coordinate_uncertainty_m: float = 0


@pytest.mark.parametrize(
    "coordinates",
    [(0, 0, 0, 1), (57, 15, 57.1, 15.1), (0, 179.99, 0, -179.99), (89, 0, 89, 180)],
)
def test_exact_evaluator_formula_includes_both_radii_and_uncertainties(
    coordinates: tuple[float, float, float, float],
) -> None:
    a, b, c, d = coordinates
    left, right = Footprint(a, b, 13, 2), Footprint(c, d, 17, 3)
    centre = (
        wgs84_inverse_geodesic(
            latitude_a=a, longitude_a=b, latitude_b=c, longitude_b=d
        ).distance_km_unrounded
        * 1000
    )
    expected = max(0.0, centre - 13 - 17 - 2 - 3)
    result = support_separation(left, right)
    assert result.centre_distance_m == centre and result.lower_bound_m == expected
    assert support_distance_lower_bound_m(left, right) == expected
    assert result.target_radius_m == 13 and result.training_radius_m == 17
    assert (
        result.target_coordinate_uncertainty_m == 2
        and result.training_coordinate_uncertainty_m == 3
    )


def test_overlapping_footprints_have_zero_lower_bound() -> None:
    assert (
        support_distance_lower_bound_m(Footprint(0, 0, 200000), Footprint(0, 1, 1)) == 0
    )


@pytest.mark.parametrize("value", [-1, True, float("nan"), float("inf"), "1"])
def test_invalid_support_measurement_is_not_coerced(value: Any) -> None:
    with pytest.raises(ValidationRefusal):
        support_separation(replace(Footprint(0, 0), radius_m=value), Footprint(0, 1))


@pytest.mark.parametrize("side", ["target", "training"])
@pytest.mark.parametrize("field", ["latitude", "longitude"])
@pytest.mark.parametrize("value", [10**400, True, float("nan"), float("inf"), "1"])
def test_invalid_coordinate_is_refused_before_geodesic(
    side: str, field: str, value: Any
) -> None:
    target, training = Footprint(0, 0), Footprint(0, 1)
    if side == "target":
        target = replace(target, **{field: value})
    else:
        training = replace(training, **{field: value})
    with pytest.raises(ValidationRefusal) as error:
        support_separation(target, training)
    assert error.value.reason_code == "invalid_number"
