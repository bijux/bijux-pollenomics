"""Finite angular polynomials and a separate uniform original-integral remainder."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import cached_property
import math

from ..arithmetic import Interval, Jet, pi_bounds
from ..kernel import Geometry

DEGREE = 5
MOMENTS = 2 * DEGREE + 1


def binomial_coefficients() -> tuple[Fraction, ...]:
    """Coefficients of (1+q)^(-3/2), through the fixed fifth power."""
    values = [Fraction(1)]
    for degree in range(1, DEGREE + 1):
        values.append(-values[-1] * Fraction(2 * degree + 1, 2 * degree))
    return tuple(values)


def series_remainder(q_bound: Fraction) -> Fraction:
    """Bound the absolute k>=6 tail by its first term and a geometric majorant."""
    if type(q_bound) is not Fraction or not 0 <= q_bound < Fraction(14, 15):
        raise ValueError("Exact expansion bound must satisfy 0<=q<14/15")
    return Fraction(3003, 1024) * q_bound**6 / (1 - Fraction(15, 14) * q_bound)


def full_moments(order: int) -> tuple[Jet, ...]:
    """Integrals of sin²(theta)cos^m(theta) on [0,pi], including signed odd zero."""
    values = [Jet.constant(pi_bounds() / 2, order), Jet.constant(0, order)]
    for degree in range(2, MOMENTS):
        values.append(values[degree - 2] * Fraction(degree - 1, degree + 2))
    return tuple(values)


def partial_moments(theta: Jet, sine: Jet, cosine: Jet) -> tuple[Jet, ...]:
    """Exact primitives from zero to theta; supplied trigonometric jets share theta."""
    if theta.order != sine.order or theta.order != cosine.order:
        raise ValueError("Angular moment Taylor orders differ")
    sine_cube = sine**3
    values = [(theta - sine * cosine) / 2, sine_cube / 3]
    for degree in range(2, MOMENTS):
        values.append(
            (sine_cube * cosine ** (degree - 1) + (degree - 1) * values[degree - 2])
            / (degree + 2)
        )
    return tuple(values)


@dataclass(frozen=True)
class AngleContraction:
    """Keep a finite angular approximant distinct from its exact-law tail bound."""

    geometry: Geometry

    def __post_init__(self) -> None:
        """Preserve original Geometry admission and refuse unsupported cap geometry."""
        if type(self.geometry) is not Geometry:
            raise TypeError("Validated original Geometry required")
        if self.geometry.outer <= 3 * self.geometry.receiver:
            raise ValueError("Receiver-angle cap partition requires L>3R")
        # Equal-norm anchors have exactly h=1/2 and J=0, including the
        # noncoincident antipodal case N=0. Only J uses this shortcut.
        if self.geometry.delta != 0:
            if self.denominator_root_lower <= 0:
                raise ValueError(
                    "Receiver-angle normalization needs a positive root bound"
                )
            if self.q_bound >= Fraction(14, 15):
                raise ValueError("Receiver-angle expansion requires q<14/15")

    @cached_property
    def denominator_floor(self) -> Fraction:
        """Positive ND of the nonconstant original two-anchor angular mean."""
        return self.geometry.norm_sum * self.geometry.norm_difference

    @cached_property
    def denominator_root_lower(self) -> Fraction:
        """Use the certified existing root lower bound, never a rounded float."""
        if self.geometry.delta == 0:
            return Fraction(0)
        return Interval.point(self.denominator_floor).root(2).lower

    @cached_property
    def normalization(self) -> Interval:
        """Scale before inversion so the absolute lattice never inverts ND^(3/2)."""
        model = self.geometry
        if model.delta == 0:
            return Interval.point(0)
        ratio = -2 * model.delta * model.norm_difference / self.denominator_floor
        return ratio / Interval.point(self.denominator_floor).root(2)

    @cached_property
    def q_bound(self) -> Fraction:
        """Uniform bound over all displacement distances through L+R."""
        model = self.geometry
        if model.delta == 0:
            return Fraction(0)
        beta = 2 * model.receiver * (model.outer + model.receiver)
        return (
            2 * beta / self.denominator_root_lower
            + 4 * beta**2 / self.denominator_floor
        )

    @cached_property
    def remainder_radius(self) -> Fraction:
        """Absolute WHOLE-J remainder; add both ways once after 1D integration."""
        model = self.geometry
        if model.delta == 0:
            return Fraction(0)
        magnitude = (
            2
            * abs(model.delta)
            * model.norm_difference
            / (self.denominator_floor * self.denominator_root_lower)
        )
        # S<=1 and integral_0^pi sin²(theta)dtheta=pi/2 bound the full
        # translated support, even where only a cap of angles is present.
        bound = (
            (model.outer + model.receiver) ** 2
            * magnitude
            * series_remainder(self.q_bound)
            / 2
        )
        return Interval.outward(Fraction(0), bound).upper

    def integrate_angles(self, distance: Jet, moments: tuple[Jet, ...]) -> Jet:
        """Integrate ONLY the finite k0..5 polynomial; its jets omit the tail.

        These are derivatives of the approximant, never asserted derivatives
        of the exact original F. The separate whole-integral radius closes that
        approximation after the one-dimensional quadrature is enclosed.
        """
        if (
            type(distance) is not Jet
            or distance.value.lower < 0
            or type(moments) is not tuple
            or len(moments) != MOMENTS
            or any(
                type(value) is not Jet or value.order != distance.order
                for value in moments
            )
        ):
            raise ValueError("Nonnegative distance and eleven aligned moments required")
        model = self.geometry
        if model.delta == 0:
            return Jet.constant(0, distance.order)
        centered = distance**2 + model.receiver**2 - model.dot
        # Multiplying by the exact scalar 1/ND normalizes before any
        # reciprocal. Inverting a dimensional ND^(3/2) around 1e33 would
        # lose all relative precision on the fixed absolute 96-bit lattice.
        inverse_scale = 1 / self.denominator_floor
        denominator = 1 + (4 * centered**2) * inverse_scale
        first = (
            (16 * model.receiver * distance * centered) * inverse_scale / denominator
        )
        second = (16 * model.receiver**2 * distance**2) * inverse_scale / denominator
        first_powers = tuple(first**degree for degree in range(DEGREE + 1))
        second_powers = tuple(second**degree for degree in range(DEGREE + 1))
        total = Jet.constant(0, distance.order)
        for degree, coefficient in enumerate(binomial_coefficients()):
            for second_degree in range(degree + 1):
                total += (
                    coefficient
                    * math.comb(degree, second_degree)
                    * first_powers[degree - second_degree]
                    * second_powers[second_degree]
                    * moments[degree + second_degree]
                )
        return total * self.normalization / denominator.root(2) ** 3
