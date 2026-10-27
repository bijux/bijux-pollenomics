"""Smooth survival and inverse-square responses after exact contact removal."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .arithmetic import Interval, Jet, pi_bounds


@dataclass(frozen=True)
class Geometry:
    """Exact finite parameters of the ideal continuous captured-A law."""

    coefficient: Fraction
    receiver: Fraction
    outer: Fraction
    first: tuple[Fraction, Fraction]
    second: tuple[Fraction, Fraction]

    def __post_init__(self) -> None:
        if (
            type(self.first) is not tuple
            or type(self.second) is not tuple
            or len(self.first) != 2
            or len(self.second) != 2
        ):
            raise ValueError("Two planar coordinates required per anchor")
        values = (
            self.coefficient,
            self.receiver,
            self.outer,
            *self.first,
            *self.second,
        )
        if any(type(value) is not Fraction for value in values):
            raise TypeError("Geometry requires explicit exact Fractions")
        if (
            self.coefficient < 0
            or not 0 < self.receiver < self.outer
            or self.first == self.second
        ):
            raise ValueError("Invalid continuous receiver geometry")

    @property
    def difference(self) -> Fraction:
        return self.outer - self.receiver

    @property
    def delta(self) -> Fraction:
        return sum(
            (b * b - a * a for a, b in zip(self.first, self.second, strict=True)),
            Fraction(0),
        )

    @property
    def norm_sum(self) -> Fraction:
        return sum(
            ((a + b) ** 2 for a, b in zip(self.first, self.second, strict=True)),
            Fraction(0),
        )

    @property
    def norm_difference(self) -> Fraction:
        return sum(
            ((b - a) ** 2 for a, b in zip(self.first, self.second, strict=True)),
            Fraction(0),
        )

    @property
    def dot(self) -> Fraction:
        return sum(
            (a * b for a, b in zip(self.first, self.second, strict=True)), Fraction(0)
        )

    def angular(self, radius: Jet) -> Jet:
        if type(radius) is not Jet or radius.value.lower < 0:
            raise ValueError("Nonnegative exact Taylor radius required")
        if self.delta == 0:
            return Jet.constant(Fraction(1, 2), radius.order)
        u = 2 * (radius**2 - self.dot)
        denominator = (u**2 + self.norm_sum * self.norm_difference).root(2)
        return Fraction(1, 2) + self.delta / (2 * self.norm_sum) * (1 - u / denominator)

    def angular_derivative(self, radius: Jet) -> Jet:
        if type(radius) is not Jet or radius.value.lower < 0:
            raise ValueError("Nonnegative exact Taylor radius required")
        if self.delta == 0:
            return Jet.constant(0, radius.order)
        u = 2 * (radius**2 - self.dot)
        denominator = (u**2 + self.norm_sum * self.norm_difference).root(2)
        # Order-n derivatives of this expression enclose h^(n+1).
        return -2 * self.delta * self.norm_difference * radius / denominator**3

    def contact_survival(self, t: Jet) -> Jet:
        """Q(R); the analytic sinc expression includes the t=0 endpoint."""
        self._unit_coordinate(t)
        phi = t**8 * pi_bounds()
        cosine = phi.sin_cos()[1]
        distance_power = t * ((phi / 2).sinc() * (pi_bounds() * self.receiver)).root(8)
        return 8 * t**7 * (1 + cosine) * (-self.coefficient * distance_power).exp()

    def outer_survival(self, t: Jet) -> Jet:
        """Q(L), with the positive separation L-R kept exact."""
        self._unit_coordinate(t)
        phi = t * pi_bounds()
        sine = phi.sin_cos()[0]
        half_sine = (phi / 2).sin_cos()[0]
        distance_squared = (
            self.difference**2 + 4 * self.receiver * self.outer * half_sine**2
        )
        return (
            2
            * self.outer**2
            * sine**2
            / distance_squared
            * (-self.coefficient * distance_squared.root(16)).exp()
        )

    def triangle(
        self, t: Jet, u: Jet, patch: int, *, contact_outer: Fraction | None = None
    ) -> Jet:
        """Duffy triangles of integral_R^L Q(r)h'(r)dr; no contact collar."""
        self._unit_coordinate(t)
        self._unit_coordinate(u)
        if type(patch) is not int or patch not in (1, 2) or t.order != u.order:
            raise ValueError(
                "Two compatible Duffy coordinates and patch 1 or 2 required"
            )
        if contact_outer is not None and (
            type(contact_outer) is not Fraction
            or not self.receiver < contact_outer <= min(2 * self.receiver, self.outer)
        ):
            raise ValueError(
                "Contact band must use the original receiver and its first radial band"
            )
        v, p, c, r0 = (
            t**8,
            Jet.constant(pi_bounds(), t.order),
            self.difference if contact_outer is None else contact_outer - self.receiver,
            self.receiver,
        )
        if patch == 1:
            radius = r0 + c * v
            half_sinc = (p * v * u / 2).sinc()
            h = c**2 + p**2 * r0 * radius * u**2 * half_sinc**2
            # H1>=C²; this is a proved algebraic lower bound, not clipping.
            h = Jet(
                (Interval(max(h.value.lower, c**2), h.value.upper),)
                + h.coefficients[1:]
            )
            numerator = u**2 * (p * v * u).sinc() ** 2
        else:
            radius = r0 + c * v * u
            half_sinc = (p * v / 2).sinc()
            h = c**2 * u**2 + p**2 * r0 * radius * half_sinc**2
            # sinc(z)>=2/pi on [0,pi/2] proves H2>=4R².
            h = Jet(
                (Interval(max(h.value.lower, 4 * r0**2), h.value.upper),)
                + h.coefficients[1:]
            )
            numerator = (p * v).sinc() ** 2
        weight = 16 * c * p**2 * radius**2 * t**15 * numerator / h
        survival = (-self.coefficient * t * h.root(16)).exp()
        return self.angular_derivative(radius) * survival * weight

    @staticmethod
    def _unit_coordinate(value: Jet) -> None:
        if (
            type(value) is not Jet
            or not 0 <= value.value.lower <= value.value.upper <= 1
        ):
            raise ValueError(
                "Exact Taylor coordinate within the unit interval required"
            )
