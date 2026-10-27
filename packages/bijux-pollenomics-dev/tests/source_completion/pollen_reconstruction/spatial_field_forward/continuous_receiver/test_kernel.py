"""Nonzero-decay unequal-anchor Duffy contact and source-radius identities."""

from __future__ import annotations

from fractions import Fraction
import math

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.arithmetic import (
    Interval,
    Jet,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.kernel import (
    Geometry,
)


def geometry() -> Geometry:
    return Geometry(
        Fraction(1, 2),
        Fraction(1),
        Fraction(20),
        (Fraction(4), Fraction(1)),
        (Fraction(-7), Fraction(3)),
    )


def sinc(value: float) -> float:
    return math.sin(value) / value if value else 1.0


@pytest.mark.parametrize("patch", [1, 2])
@pytest.mark.parametrize("other", [Fraction(0), Fraction(1, 7), Fraction(1)])
def test_contact_corner_is_an_entire_zero_through_four_derivatives(
    patch: int, other: Fraction
) -> None:
    result = geometry().triangle(
        Jet.variable(Interval.point(0)), Jet.constant(other), patch
    )
    assert all(bound.lower <= 0 <= bound.upper for bound in result.coefficients)
    assert all(bound.width < Fraction(1, 10**20) for bound in result.coefficients)


@pytest.mark.parametrize("patch", [1, 2])
def test_transformed_measure_matches_independent_original_integrand(patch: int) -> None:
    model = geometry()
    t, u = Fraction(3, 4), Fraction(2, 5)
    v, c, r0 = float(t) ** 8, float(model.difference), float(model.receiver)
    x, y = (v, v * float(u)) if patch == 1 else (v * float(u), v)
    radius, phi = r0 + c * x, math.pi * y
    distance_squared = (radius - r0) ** 2 + 4 * r0 * radius * math.sin(phi / 2) ** 2
    derivative = (
        -2
        * radius
        * float(model.delta * model.norm_difference)
        / (
            4 * (radius**2 - float(model.dot)) ** 2
            + float(model.norm_sum * model.norm_difference)
        )
        ** 1.5
    )
    original = (
        derivative
        * math.exp(-float(model.coefficient) * distance_squared ** (1 / 16))
        * 2
        * radius**2
        * math.sin(phi) ** 2
        / (math.pi * distance_squared)
    )
    jacobian = 8 * c * math.pi * float(t) ** 15
    result = model.triangle(Jet.constant(t, 0), Jet.constant(u, 0), patch).value
    assert math.isclose(
        float((result.lower + result.upper) / 2),
        original * jacobian,
        abs_tol=1e-13,
        rel_tol=1e-12,
    )
    assert result.upper < 0
    assert result.width < Fraction(1, 10**20)


def test_contact_endpoint_formula_and_h_prime_composition() -> None:
    model, value = geometry(), Fraction(2, 3)
    t = float(value)
    expected = (
        8
        * t**7
        * (1 + math.cos(math.pi * t**8))
        * math.exp(
            -float(model.coefficient)
            * t
            * (math.pi * float(model.receiver) * sinc(math.pi * t**8 / 2)) ** (1 / 8)
        )
    )
    actual = model.contact_survival(Jet.constant(value, 0)).value
    assert math.isclose(
        float((actual.lower + actual.upper) / 2), expected, rel_tol=1e-13
    )
    radius = Jet.variable(Interval.point(Fraction(3)))
    weight, derivative = model.angular(radius), model.angular_derivative(radius)
    for n in range(4):
        left, right = weight.coefficients[n + 1] * (n + 1), derivative.coefficients[n]
        assert max(left.lower, right.lower) <= min(left.upper, right.upper)


@pytest.mark.parametrize("axis", [0, 1])
@pytest.mark.parametrize("patch", [1, 2])
def test_near_contact_nonzero_decay_derivative_boxes_are_finite(
    axis: int, patch: int
) -> None:
    box = Interval(Fraction(0), Fraction(1, 16))
    other = Interval(Fraction(0), Fraction(1))
    arguments = (
        (Jet.variable(box), Jet.constant(other))
        if axis == 0
        else (Jet.constant(box), Jet.variable(other))
    )
    result = geometry().triangle(*arguments, patch)
    assert len(result.coefficients) == 5
    assert result.coefficients[4].magnitude > 0


def test_equal_radius_symmetry_and_invalid_native_domains() -> None:
    model = Geometry(
        Fraction(1),
        Fraction(1),
        Fraction(2),
        (Fraction(2), Fraction(1)),
        (Fraction(-1), Fraction(2)),
    )
    assert model.angular(Jet.constant(3, 0)).value == Interval.point(Fraction(1, 2))
    assert model.angular_derivative(
        Jet.variable(Interval(Fraction(1), Fraction(2)))
    ).value == Interval.point(0)
    with pytest.raises(ValueError, match="geometry"):
        Geometry(Fraction(-1), Fraction(1), Fraction(2), model.first, model.second)


@pytest.mark.parametrize(
    "bounds",
    [
        (Fraction(-1, 100), Fraction(0)),
        (Fraction(0), Fraction(101, 100)),
        (Fraction(2), Fraction(3)),
    ],
)
def test_contact_proofs_refuse_coordinate_extrapolation(
    bounds: tuple[Fraction, Fraction],
) -> None:
    argument = Jet.variable(Interval(*bounds))
    model = geometry()
    with pytest.raises(ValueError, match="unit interval"):
        model.contact_survival(argument)
    with pytest.raises(ValueError, match="unit interval"):
        model.outer_survival(argument)
    with pytest.raises(ValueError, match="unit interval"):
        model.triangle(argument, Jet.constant(Fraction(1, 2)), 1)
    with pytest.raises(ValueError, match="unit interval"):
        model.triangle(Jet.constant(Fraction(1, 2)), argument, 2)
