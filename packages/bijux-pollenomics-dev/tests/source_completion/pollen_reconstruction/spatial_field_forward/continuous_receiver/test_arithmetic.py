"""Independent exact and high-precision checks on primitive proof obligations."""

from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction
import math

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.arithmetic import (
    Interval,
    Jet,
    cos_bounds,
    exp_bounds,
    pi_bounds,
    sin_bounds,
    sinc_derivative,
)


def decimal(value: Fraction) -> Decimal:
    return Decimal(value.numerator) / Decimal(value.denominator)


@pytest.mark.parametrize(
    "value", [Fraction(0), Fraction(1, 7), Fraction(2), Fraction(13, 3)]
)
@pytest.mark.parametrize("degree", [2, 8, 16])
def test_roots_have_exact_outward_power_proof(value: Fraction, degree: int) -> None:
    result = Interval.point(value).root(degree)
    assert result.lower**degree <= value <= result.upper**degree


@pytest.mark.parametrize(
    "value", [Fraction(-12), Fraction(-1, 7), Fraction(0), Fraction(3, 4), Fraction(10)]
)
def test_exp_contains_independent_decimal(value: Fraction) -> None:
    bounds = exp_bounds(Interval.point(value))
    with localcontext() as context:
        context.prec = 120
        expected = decimal(value).exp()
        assert decimal(bounds.lower) <= expected <= decimal(bounds.upper)
    assert bounds.width < Fraction(1, 10**20)


def test_pi_signed_machin_remainders_and_trigonometric_endpoints() -> None:
    bounds = pi_bounds()
    literal = Fraction(
        "3.14159265358979323846264338327950288419716939937510582097494459230781640628620899"
    )
    assert bounds.lower < literal < bounds.upper
    assert sin_bounds(bounds).lower <= 0 <= sin_bounds(bounds).upper
    assert cos_bounds(bounds).lower <= -1 <= cos_bounds(bounds).upper
    assert sinc_derivative(bounds, 0).lower <= 0 <= sinc_derivative(bounds, 0).upper


@pytest.mark.parametrize(
    "derivative,expected",
    [
        (0, Fraction(1)),
        (1, Fraction(0)),
        (2, Fraction(-1, 3)),
        (3, Fraction(0)),
        (4, Fraction(1, 5)),
    ],
)
def test_sinc_derivatives_are_entire_at_zero(
    derivative: int, expected: Fraction
) -> None:
    bounds = sinc_derivative(Interval.point(0), derivative)
    assert bounds.lower <= expected <= bounds.upper
    assert bounds.width <= Fraction(2, 2**96)


def test_jet_polynomial_derivatives_and_root_composition() -> None:
    x = Jet.variable(Interval(Fraction(2), Fraction(3)))
    polynomial = x**5
    assert (
        polynomial.coefficients[4].lower <= 10 <= 15 <= polynomial.coefficients[4].upper
    )
    root = (x**2).root(2)
    assert root.coefficients[1].lower <= 1 <= root.coefficients[1].upper
    point = Jet.variable(Interval.point(Fraction(3, 2)))
    restored = point.root(16) ** 16
    for n, exact_coefficient in enumerate(
        (Fraction(3, 2), Fraction(1), Fraction(0), Fraction(0), Fraction(0))
    ):
        assert (
            restored.coefficients[n].lower
            <= exact_coefficient
            <= restored.coefficients[n].upper
        )


def test_analytic_jets_match_independent_derivative_identities() -> None:
    x = Jet.variable(Interval.point(1))
    exponential = x.exp()
    with localcontext() as context:
        context.prec = 100
        for n, bound in enumerate(exponential.coefficients):
            expected = Decimal(1).exp() / math.factorial(n)
            assert decimal(bound.lower) <= expected <= decimal(bound.upper)
    sinc = Jet.variable(Interval.point(0)).sinc()
    for n, exact_coefficient in enumerate(
        (Fraction(1), Fraction(0), Fraction(-1, 6), Fraction(0), Fraction(1, 120))
    ):
        assert (
            sinc.coefficients[n].lower
            <= exact_coefficient
            <= sinc.coefficients[n].upper
        )


def test_domain_failures_refuse_without_clipping() -> None:
    with pytest.raises(ValueError, match="zero"):
        Interval(Fraction(-1), Fraction(1)).reciprocal()
    with pytest.raises(ValueError, match="positive"):
        Jet.variable(Interval.point(0)).root(8)
    with pytest.raises(ValueError, match="domain"):
        sin_bounds(Interval.point(5))
    with pytest.raises(TypeError, match="Exact"):
        Interval.point(0.5)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [float("nan"), float("inf"), 0.5, True])
def test_direct_interval_constructor_cannot_bypass_exact_endpoint_contract(
    value: float | bool,
) -> None:
    with pytest.raises(TypeError, match="Exact"):
        Interval(value, Fraction(1))  # type: ignore[arg-type]


def test_orders_exponents_and_reserved_derivatives_are_strict_integers() -> None:
    with pytest.raises(TypeError, match="integer"):
        Interval.point(1) ** True
    with pytest.raises(ValueError, match="order"):
        Jet.constant(1, True)
    with pytest.raises(ValueError, match="order"):
        sinc_derivative(Interval.point(0), True)
