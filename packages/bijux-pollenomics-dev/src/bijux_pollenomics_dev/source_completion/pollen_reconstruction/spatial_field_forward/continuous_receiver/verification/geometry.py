"""Independent original-disk, Duffy and scaled-band receiver equations."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from ..arithmetic import Interval, Jet, pi_bounds
from .contracts import Function, require


@dataclass(frozen=True)
class Geometry:
    coefficient: Fraction
    receiver: Fraction
    outer: Fraction
    first: tuple[Fraction, Fraction]
    second: tuple[Fraction, Fraction]

    def __post_init__(self) -> None:
        require(
            all(
                type(x) is Fraction
                for x in (
                    self.coefficient,
                    self.receiver,
                    self.outer,
                    *self.first,
                    *self.second,
                )
            ),
            "Exact geometry required",
        )
        require(
            self.coefficient > 0
            and 0 < self.receiver < self.outer
            and self.first != self.second,
            "Invalid declared geometry",
        )

    def encoded(self) -> dict[str, Any]:
        return {
            "coefficient_A": str(self.coefficient),
            "receiver_radius_m": str(self.receiver),
            "outer_radius_m": str(self.outer),
            "first_anchor_xy_m": [str(x) for x in self.first],
            "second_anchor_xy_m": [str(x) for x in self.second],
        }

    def anchors(self) -> tuple[Fraction, Fraction, Fraction, Fraction, Fraction]:
        aa = sum((x * x for x in self.first), Fraction(0))
        bb = sum((x * x for x in self.second), Fraction(0))
        dot = sum(
            (a * b for a, b in zip(self.first, self.second, strict=True)), Fraction(0)
        )
        return aa, bb, dot, aa + bb + 2 * dot, aa + bb - 2 * dot

    def distance_polynomial(self, radius: Jet) -> Jet:
        aa, bb, dot, s, t = self.anchors()
        result = 4 * radius**4 - 8 * dot * radius**2 + (aa + bb) ** 2
        lower = max(s * t, result.value.lower)
        require(
            lower > 0 and lower <= result.value.upper,
            "Anchor denominator not certified positive",
        )
        return Jet((Interval(lower, result.value.upper),) + result.coefficients[1:])

    def mean(self, radius: Fraction) -> Interval:
        aa, bb, dot, s, t = self.anchors()
        if aa == bb:
            return Interval.point(Fraction(1, 2))
        denominator = self.distance_polynomial(Jet.constant(radius, 0)).root(2).value
        u = 2 * (radius**2 - dot)
        if u >= 0:
            return Fraction(1, 2) + (bb - aa) * t / (
                2 * denominator * (denominator + u)
            )
        return Fraction(1, 2) + (bb - aa) / (2 * s) * (1 - u / denominator)

    def derivative(self, radius: Jet) -> Jet:
        aa, bb, _, _, t = self.anchors()
        if aa == bb:
            return Jet.constant(0, radius.order)
        return (
            -2 * (bb - aa) * t * radius / self.distance_polynomial(radius).root(2) ** 3
        )

    def bands(self) -> tuple[tuple[Fraction, Fraction], ...]:
        result: list[tuple[Fraction, Fraction]] = []
        a = self.receiver
        while a < self.outer:
            require(len(result) < 11, "Uncovered radial tail")
            b = min(2 * a, self.outer)
            result.append((a, b))
            a = b
        return tuple(result)

    def function(self, index: int) -> Function:
        if index == 0:

            def contact(arguments: tuple[Jet, ...]) -> Jet:
                t = arguments[0]
                phi = t**8 * pi_bounds()
                cosine = (phi / 2).sin_cos()[1]
                power = t * ((phi / 2).sinc() * (pi_bounds() * self.receiver)).root(8)
                return 16 * t**7 * cosine**2 * (-self.coefficient * power).exp()

            return contact
        if index == 1:

            def outer(arguments: tuple[Jet, ...]) -> Jet:
                phi = arguments[0] * pi_bounds()
                sine, cosine = phi.sin_cos()
                squared = (
                    self.outer - self.receiver
                ) ** 2 + 2 * self.receiver * self.outer * (1 - cosine)
                squared = Jet(
                    (
                        Interval(
                            max((self.outer - self.receiver) ** 2, squared.value.lower),
                            squared.value.upper,
                        ),
                    )
                    + squared.coefficients[1:]
                )
                return (
                    2
                    * self.outer**2
                    * sine**2
                    / squared
                    * (-self.coefficient * squared.root(16)).exp()
                )

            return outer
        band_index = 0 if index < 4 else index - 3
        a, b = self.bands()[band_index]
        if band_index == 0:
            patch = index - 1

            def duffy(arguments: tuple[Jet, ...]) -> Jet:
                t, u = arguments
                v = t**8
                c = b - self.receiver
                p = Jet.constant(pi_bounds(), t.order)
                radius = self.receiver + c * v * (1 if patch == 1 else u)
                z = p * v * (u if patch == 1 else 1)
                h = (
                    c**2 * (1 if patch == 1 else u**2)
                    + self.receiver
                    * radius
                    * (p * (u if patch == 1 else 1) * (z / 2).sinc()) ** 2
                )
                proved = c**2 if patch == 1 else 4 * self.receiver**2
                h = Jet(
                    (Interval(max(proved, h.value.lower), h.value.upper),)
                    + h.coefficients[1:]
                )
                density = (
                    2
                    * radius**2
                    / pi_bounds()
                    * (p * (u if patch == 1 else 1) * z.sinc()) ** 2
                    / h
                )
                jacobian = t**15 * p * (8 * c)
                return (
                    self.derivative(radius)
                    * (-self.coefficient * t * h.root(16)).exp()
                    * density
                    * jacobian
                )

            return duffy

        def regular(arguments: tuple[Jet, ...]) -> Jet:
            s, u = arguments
            radius = a + (b - a) * s
            x = 1 + (b - a) / a * s
            rho = self.receiver / a
            phi = u * pi_bounds()
            sine, cosine = phi.sin_cos()
            dhat = x**2 + rho**2 - 2 * rho * x * cosine
            dhat = Jet(
                (
                    Interval(
                        max(Fraction(1, 4), dhat.value.lower),
                        min(Fraction(25, 4), dhat.value.upper),
                    ),
                )
                + dhat.coefficients[1:]
            )
            power = dhat.root(16) * Interval.point(a).root(8)
            return (
                2
                * (b - a)
                * x**2
                * self.derivative(radius)
                * sine**2
                / dhat
                * (-self.coefficient * power).exp()
            )

        return regular
