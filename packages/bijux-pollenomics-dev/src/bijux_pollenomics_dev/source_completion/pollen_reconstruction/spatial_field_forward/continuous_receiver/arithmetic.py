"""Outward rational intervals and analytic Taylor coefficients through order eight.

All arithmetic bounds use the existing radial-envelope 96-bit lattice. Elementary
functions use rational Taylor remainders, rather than machine transcendental
rounding. Taylor coefficients enclose derivatives divided by their factorials
at every point of the supplied base interval.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
import math

from ..radial_envelope import lattice_bounds, root_bounds

Scalar = Fraction | int
ORDER = 4
MAX_ORDER = 8
SERIES_DEGREE = 64


@dataclass(frozen=True)
class Interval:
    lower: Fraction
    upper: Fraction

    def __post_init__(self) -> None:
        if type(self.lower) not in (int, Fraction) or type(self.upper) not in (
            int,
            Fraction,
        ):
            raise TypeError("Exact rational interval endpoints required")
        object.__setattr__(self, "lower", Fraction(self.lower))
        object.__setattr__(self, "upper", Fraction(self.upper))
        if self.lower > self.upper:
            raise ValueError("Reversed interval")

    @classmethod
    def point(cls, value: Scalar) -> Interval:
        if type(value) not in (int, Fraction):
            raise TypeError("Exact rational input required")
        return cls(Fraction(value), Fraction(value))

    @classmethod
    def outward(cls, lower: Fraction, upper: Fraction) -> Interval:
        return cls(*lattice_bounds((lower, upper)))

    @property
    def width(self) -> Fraction:
        return self.upper - self.lower

    @property
    def magnitude(self) -> Fraction:
        return max(abs(self.lower), abs(self.upper))

    def __add__(self, other: Interval | Scalar) -> Interval:
        rhs = interval(other)
        return self.outward(self.lower + rhs.lower, self.upper + rhs.upper)

    __radd__ = __add__

    def __neg__(self) -> Interval:
        return Interval(-self.upper, -self.lower)

    def __sub__(self, other: Interval | Scalar) -> Interval:
        return self + -interval(other)

    def __rsub__(self, other: Interval | Scalar) -> Interval:
        return interval(other) + -self

    def __mul__(self, other: Interval | Scalar) -> Interval:
        rhs = interval(other)
        products = [
            a * b for a in (self.lower, self.upper) for b in (rhs.lower, rhs.upper)
        ]
        return self.outward(min(products), max(products))

    __rmul__ = __mul__

    def reciprocal(self) -> Interval:
        if self.lower <= 0 <= self.upper:
            raise ValueError("Reciprocal interval includes zero")
        return self.outward(1 / self.upper, 1 / self.lower)

    def __truediv__(self, other: Interval | Scalar) -> Interval:
        return self * interval(other).reciprocal()

    def __rtruediv__(self, other: Interval | Scalar) -> Interval:
        return interval(other) / self

    def __pow__(self, exponent: int) -> Interval:
        if type(exponent) is not int:
            raise TypeError("Exact integer exponent required")
        if exponent < 0:
            return (self**-exponent).reciprocal()
        if exponent == 0:
            return Interval.point(1)
        if exponent % 2 == 0:
            values = (self.lower**exponent, self.upper**exponent)
            return self.outward(
                Fraction(0) if self.lower <= 0 <= self.upper else min(values),
                max(values),
            )
        return self.outward(self.lower**exponent, self.upper**exponent)

    def root(self, degree: int) -> Interval:
        if type(degree) is not int or degree not in (2, 8, 16) or self.lower < 0:
            raise ValueError("Nonnegative power-of-two root domain required")
        result = self
        for _ in range(degree.bit_length() - 1):
            result = Interval(
                root_bounds(result.lower)[0], root_bounds(result.upper)[1]
            )
        return result

    def expanded(self, radius: Fraction) -> Interval:
        if radius < 0:
            raise ValueError("Nonnegative error radius required")
        return self.outward(self.lower - radius, self.upper + radius)

    def encoded(self) -> list[str]:
        return [str(self.lower), str(self.upper)]


def interval(value: Interval | Scalar) -> Interval:
    return value if isinstance(value, Interval) else Interval.point(value)


@lru_cache(maxsize=1)
def pi_bounds() -> Interval:
    """Machin's identity with signed alternating-series remainder."""

    def atan_inverse(denominator: int) -> Interval:
        x = Fraction(1, denominator)
        value = sum(
            ((-1) ** n * x ** (2 * n + 1) / (2 * n + 1) for n in range(40)), Fraction(0)
        )
        following = x**81 / 81
        return Interval(value, value + following)

    return 16 * atan_inverse(5) - 4 * atan_inverse(239)


def _trigonometric_derivative(value: Interval, derivative: int) -> Interval:
    """Enclose sin derivatives by a midpoint polynomial and |next derivative|<=1."""
    midpoint = (value.lower + value.upper) / 2
    if abs(midpoint) > 4:
        raise ValueError("Certified trigonometric domain is [-4,4]")
    polynomial = Fraction(0)
    for power in range(SERIES_DEGREE + 1):
        phase = (derivative + power) % 4
        coefficient = (0, 1, 0, -1)[phase]
        if coefficient:
            polynomial += coefficient * midpoint**power / math.factorial(power)
    remainder = abs(midpoint) ** (SERIES_DEGREE + 1) / math.factorial(SERIES_DEGREE + 1)
    radius = remainder + value.width / 2
    return Interval.outward(polynomial - radius, polynomial + radius)


def sin_bounds(value: Interval) -> Interval:
    return _trigonometric_derivative(value, 0)


def cos_bounds(value: Interval) -> Interval:
    return _trigonometric_derivative(value, 1)


def sinc_derivative(value: Interval, derivative: int) -> Interval:
    """Differentiate sinc(z)=integral_0^1 cos(t*z)dt, including z=0."""
    if type(derivative) is not int or not 0 <= derivative <= MAX_ORDER:
        raise ValueError("Sinc derivative order exceeds certificate order")
    midpoint = (value.lower + value.upper) / 2
    if abs(midpoint) > 4:
        raise ValueError("Certified sinc domain is [-4,4]")
    polynomial = Fraction(0)
    for power in range(SERIES_DEGREE + 1):
        phase = (derivative + power) % 4
        coefficient = (1, 0, -1, 0)[phase]
        if coefficient:
            polynomial += (
                coefficient
                * midpoint**power
                / (math.factorial(power) * (derivative + power + 1))
            )
    remainder = abs(midpoint) ** (SERIES_DEGREE + 1) / (
        math.factorial(SERIES_DEGREE + 1) * (derivative + SERIES_DEGREE + 2)
    )
    radius = remainder + value.width / (2 * (derivative + 2))
    return Interval.outward(polynomial - radius, polynomial + radius)


def exp_bounds(value: Interval) -> Interval:
    def at_point(x: Fraction) -> Interval:
        if abs(x) > 1024:
            raise ValueError(
                "Certified exponential argument exceeds finite work domain"
            )
        reductions = 0
        while abs(x) > Fraction(1, 8):
            x /= 2
            reductions += 1
        polynomial = sum((x**n / math.factorial(n) for n in range(33)), Fraction(0))
        # exp(|x|)<2 for |x|<=1/8 gives an elementary Lagrange bound.
        remainder = 2 * abs(x) ** 33 / math.factorial(33)
        result = Interval.outward(polynomial - remainder, polynomial + remainder)
        for _ in range(reductions):
            result = result**2
        return result

    return Interval(at_point(value.lower).lower, at_point(value.upper).upper)


@dataclass(frozen=True)
class Jet:
    coefficients: tuple[Interval, ...]

    def __post_init__(self) -> None:
        if (
            type(self.coefficients) is not tuple
            or not 1 <= len(self.coefficients) <= MAX_ORDER + 1
            or any(type(value) is not Interval for value in self.coefficients)
        ):
            raise TypeError(
                "One through nine exact interval Taylor coefficients required"
            )

    @classmethod
    def constant(cls, value: Interval | Scalar, order: int = ORDER) -> Jet:
        if type(order) is not int or not 0 <= order <= MAX_ORDER:
            raise ValueError("Invalid Taylor order")
        return cls((interval(value),) + (Interval.point(0),) * order)

    @classmethod
    def variable(cls, value: Interval, order: int = ORDER) -> Jet:
        if type(order) is not int or not 0 <= order <= MAX_ORDER:
            raise ValueError("Invalid Taylor order")
        if order == 0:
            return cls.constant(value, 0)
        return cls((value, Interval.point(1)) + (Interval.point(0),) * (order - 1))

    @property
    def order(self) -> int:
        return len(self.coefficients) - 1

    @property
    def value(self) -> Interval:
        return self.coefficients[0]

    def _other(self, value: Jet | Interval | Scalar) -> Jet:
        result = value if isinstance(value, Jet) else Jet.constant(value, self.order)
        if result.order != self.order:
            raise ValueError("Taylor orders differ")
        return result

    def __add__(self, other: Jet | Interval | Scalar) -> Jet:
        rhs = self._other(other)
        return Jet(
            tuple(
                a + b for a, b in zip(self.coefficients, rhs.coefficients, strict=True)
            )
        )

    __radd__ = __add__

    def __neg__(self) -> Jet:
        return Jet(tuple(-value for value in self.coefficients))

    def __sub__(self, other: Jet | Interval | Scalar) -> Jet:
        return self + -self._other(other)

    def __rsub__(self, other: Jet | Interval | Scalar) -> Jet:
        return self._other(other) + -self

    def __mul__(self, other: Jet | Interval | Scalar) -> Jet:
        rhs = self._other(other)
        return Jet(
            tuple(
                sum(
                    (
                        self.coefficients[k] * rhs.coefficients[n - k]
                        for k in range(n + 1)
                    ),
                    Interval.point(0),
                )
                for n in range(self.order + 1)
            )
        )

    __rmul__ = __mul__

    def reciprocal(self) -> Jet:
        coefficients = [self.value.reciprocal()]
        for n in range(1, self.order + 1):
            coefficients.append(
                -coefficients[0]
                * sum(
                    (
                        self.coefficients[k] * coefficients[n - k]
                        for k in range(1, n + 1)
                    ),
                    Interval.point(0),
                )
            )
        return Jet(tuple(coefficients))

    def __truediv__(self, other: Jet | Interval | Scalar) -> Jet:
        return self * self._other(other).reciprocal()

    def __rtruediv__(self, other: Jet | Interval | Scalar) -> Jet:
        return self._other(other) / self

    def __pow__(self, exponent: int) -> Jet:
        if type(exponent) is not int:
            raise TypeError("Exact integer exponent required")
        if exponent < 0:
            return (self**-exponent).reciprocal()
        original_exponent = exponent
        result = Jet.constant(1, self.order)
        factor = self
        while exponent:
            if exponent & 1:
                result = result * factor
            factor = factor * factor
            exponent //= 2
        # Direct powers preserve shared-sign information when an even-power
        # base interval crosses zero. Higher Taylor coefficients stay outward.
        return Jet((self.value**original_exponent,) + result.coefficients[1:])

    def root(self, degree: int) -> Jet:
        if self.value.lower <= 0:
            raise ValueError("Taylor root requires strictly positive base interval")
        alpha = Fraction(1, degree)
        coefficients = [self.value.root(degree)]
        for n in range(self.order):
            right = alpha * sum(
                (
                    coefficients[k] * (n - k + 1) * self.coefficients[n - k + 1]
                    for k in range(n + 1)
                ),
                Interval.point(0),
            )
            left = sum(
                (
                    self.coefficients[k] * (n - k + 1) * coefficients[n - k + 1]
                    for k in range(1, n + 1)
                ),
                Interval.point(0),
            )
            coefficients.append((right - left) / ((n + 1) * self.value))
        return Jet(tuple(coefficients))

    def exp(self) -> Jet:
        coefficients = [exp_bounds(self.value)]
        for n in range(self.order):
            coefficients.append(
                sum(
                    (
                        (k + 1) * self.coefficients[k + 1] * coefficients[n - k]
                        for k in range(n + 1)
                    ),
                    Interval.point(0),
                )
                / (n + 1)
            )
        return Jet(tuple(coefficients))

    def sin_cos(self) -> tuple[Jet, Jet]:
        sine, cosine = [sin_bounds(self.value)], [cos_bounds(self.value)]
        for n in range(self.order):
            sine.append(
                sum(
                    (
                        (k + 1) * self.coefficients[k + 1] * cosine[n - k]
                        for k in range(n + 1)
                    ),
                    Interval.point(0),
                )
                / (n + 1)
            )
            cosine.append(
                -sum(
                    (
                        (k + 1) * self.coefficients[k + 1] * sine[n - k]
                        for k in range(n + 1)
                    ),
                    Interval.point(0),
                )
                / (n + 1)
            )
        return Jet(tuple(sine)), Jet(tuple(cosine))

    def sinc(self) -> Jet:
        difference = Jet((Interval.point(0),) + self.coefficients[1:])
        result = Jet.constant(0, self.order)
        power = Jet.constant(1, self.order)
        for n in range(self.order + 1):
            result += power * (sinc_derivative(self.value, n) / math.factorial(n))
            power *= difference
        return result
