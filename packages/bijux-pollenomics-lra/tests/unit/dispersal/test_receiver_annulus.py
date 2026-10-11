"""Independent geometry and numerical guards for a conditional ring response."""

from __future__ import annotations

import math

import numpy as np
from numpy.polynomial.legendre import leggauss
import pytest

from bijux_pollenomics_lra.dispersal.kernels import gpm_values
from bijux_pollenomics_lra.dispersal.receiver_annulus import circular_receiver_annulus
from bijux_pollenomics_lra.models.errors import ValidationError


def _factor(receiver: float, inner: float, outer: float, fall: float = 0.03) -> float:
    response = circular_receiver_annulus(
        receiver_radius_m=receiver,
        inner_radius_m=inner,
        outer_radius_m=outer,
        fall_speed_m_s=fall,
        diffusion_coefficient=0.12,
        turbulence_parameter=0.25,
        wind_speed_m_s=3.0,
    )
    assert response.estimated_absolute_error >= 0
    return response.factor


def _source_area(
    receiver: float, inner: float, outer: float, fall: float, order: int
) -> float:
    """Integrate emitting area and receiving area, without angular ring fractions."""
    nodes, weights = leggauss(order)
    z = (nodes + 1) / 2
    z_weights = weights / 2
    source_radii = np.sqrt(inner**2 + (outer**2 - inner**2) * z)
    angles = math.pi * (nodes + 1)
    exponent = 0.25 / 2
    coefficient = 4 * fall / (0.25 * 3 * math.sqrt(math.pi) * 0.12)
    total = 0.0
    for area, area_weight in zip(z, z_weights, strict=True):
        offset = receiver * math.sqrt(area)
        distance = np.sqrt(
            source_radii[:, None] ** 2
            + offset**2
            - 2 * source_radii[:, None] * offset * np.cos(angles)[None, :]
        )
        planar_density = (
            coefficient
            * exponent
            * distance ** (exponent - 2)
            * np.exp(-coefficient * distance**exponent)
            / (2 * math.pi)
        )
        source_integral = (
            math.pi
            * (outer**2 - inner**2)
            * float(z_weights @ planar_density @ z_weights)
        )
        total += area_weight * source_integral
    return total


@pytest.mark.parametrize("fall", [0.003, 0.03, 0.12])
def test_point_receiver_matches_source_survival(fall: float) -> None:
    expected = float(gpm_values(81, fall, 0.12, 0.25, 3)) - float(
        gpm_values(500, fall, 0.12, 0.25, 3)
    )
    assert _factor(0, 81, 500, fall) == pytest.approx(expected, abs=1e-15)


@pytest.mark.parametrize(
    "receiver,first,middle,last",
    [(10, 11, 60, 120), (80, 81, 500, 1000), (150, 151, 300, 500)],
)
def test_land_annuli_are_positive_and_telescope(
    receiver: float, first: float, middle: float, last: float
) -> None:
    left = _factor(receiver, first, middle)
    right = _factor(receiver, middle, last)
    whole = _factor(receiver, first, last)
    assert 0 < left < 1
    assert 0 < right < 1
    assert left + right == pytest.approx(whole, abs=1e-8)


def test_exposed_english_geometry_matches_independent_derivation() -> None:
    assert _factor(80, 81, 500, 0.03) == pytest.approx(0.09730993326551013, abs=1e-8)
    assert _factor(80, 500, 1000, 0.03) == pytest.approx(0.027010985523778817, abs=1e-8)


@pytest.mark.parametrize(
    "receiver,inner,outer,fall",
    [(10, 60, 120, 0.003), (80, 130, 260, 0.03), (150, 200, 400, 0.12)],
)
def test_independent_source_area_quadrature(
    receiver: float, inner: float, outer: float, fall: float
) -> None:
    angular = _factor(receiver, inner, outer, fall)
    coarse = _source_area(receiver, inner, outer, fall, 64)
    fine = _source_area(receiver, inner, outer, fall, 128)
    assert coarse == pytest.approx(fine, abs=1e-8)
    assert angular == pytest.approx(fine, abs=1e-8)


@pytest.mark.parametrize(
    "receiver,inner,outer",
    [(-1, 1, 2), (80, 79, 500), (80, 80, 80), (80, 500, float("inf"))],
)
def test_invalid_receiver_geometry_refused(
    receiver: float, inner: float, outer: float
) -> None:
    with pytest.raises(ValidationError):
        _factor(receiver, inner, outer)


def test_invalid_numerical_budget_refused() -> None:
    with pytest.raises(ValidationError, match="quadrature_limit"):
        circular_receiver_annulus(
            receiver_radius_m=80,
            inner_radius_m=81,
            outer_radius_m=500,
            fall_speed_m_s=0.03,
            diffusion_coefficient=0.12,
            turbulence_parameter=0.25,
            wind_speed_m_s=3,
            quadrature_limit=1,
        )
