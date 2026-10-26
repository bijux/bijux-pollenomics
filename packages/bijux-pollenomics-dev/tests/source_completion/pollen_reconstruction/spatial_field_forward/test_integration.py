"""Check the new angular reduction against literal spatial angular quadrature."""

from __future__ import annotations

import pytest

from bijux_pollenomics_lra.dispersal.two_anchor_receiver import (
    two_anchor_inverse_square_angular_mean,
)

from .integration import circle_weights, normalized_first_bounds


@pytest.mark.parametrize("radius", [0.0, 20.0, 100.0, 500.0, 100_000.0])
@pytest.mark.parametrize(
    ("first", "second"),
    [
        ((100.0, 0.0), (0.0, 200.0)),
        ((-100.0, 50.0), (250.0, -50.0)),
        ((250.0, -50.0), (-100.0, 50.0)),
    ],
)
def test_production_angular_mean_matches_literal_quadrature(
    radius: float, first: tuple[float, float], second: tuple[float, float]
) -> None:
    coarse = circle_weights(radius, first, second)
    fine = circle_weights(radius, first, second, 512)
    assert sum(coarse) == pytest.approx(1, abs=2e-14, rel=0)
    assert coarse == pytest.approx(fine, abs=2e-12, rel=0)
    assert two_anchor_inverse_square_angular_mean(radius, first, second) == (
        pytest.approx(fine[0], abs=2e-12, rel=0)
    )


def test_direct_quadrature_has_exact_origin_swap_and_equal_radius_controls() -> None:
    assert circle_weights(0, (100, 0), (0, 200)) == pytest.approx(
        (0.8, 0.2), abs=2e-14, rel=0
    )
    for radius in (0, 20, 100, 250):
        assert circle_weights(radius, (100, 0), (-100, 0)) == pytest.approx(
            (0.5, 0.5), abs=2e-14, rel=0
        )
        assert (
            two_anchor_inverse_square_angular_mean(radius, (100, 0), (-100, 0)) == 0.5
        )
        forward = circle_weights(radius, (100, 20), (-300, 80))
        reverse = circle_weights(radius, (-300, 80), (100, 20))
        assert forward == pytest.approx(reverse[::-1], abs=2e-14, rel=0)


def test_positive_normalization_bounds_cover_all_component_corners() -> None:
    assert normalized_first_bounds((1, 2), (1, 2)) == pytest.approx(
        (1 / 3, 1 / 3), abs=2e-14, rel=0
    )
    low, high = normalized_first_bounds((1, 2), (3, 5))
    assert (low, high) == pytest.approx((1 / 6, 3 / 5), abs=2e-14, rel=0)
    for first in (1, 3):
        for second in (2, 5):
            assert low <= first / (first + second) <= high
    with pytest.raises(ValueError):
        normalized_first_bounds((0, 0), (0, 0))
