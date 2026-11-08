"""One-dimensional contact, full-angle and outer-cap displacement maps."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from ..arithmetic import Interval, Jet, pi_bounds
from ..kernel import Geometry
from ..quadrature import ResourceRefusal
from ..radial_partition import MAX_BANDS
from .contraction import AngleContraction, full_moments, partial_moments


def _range(value: Jet, lower: Fraction, upper: Fraction) -> Jet:
    """Intersect a proved real-law value range, leaving all derivative jets intact."""
    return Jet(
        (Interval(max(lower, value.value.lower), min(upper, value.value.upper)),)
        + value.coefficients[1:]
    )


@dataclass(frozen=True)
class MappedAngle:
    """Exact transformed distance, survival argument, measure and angular moments."""

    distance: Jet
    distance_power: Jet
    measure: Jet
    moments: tuple[Jet, ...]


@dataclass(frozen=True)
class AngleDomain:
    """One complete smooth displacement piece of the original source annulus."""

    contraction: AngleContraction
    kind: str
    distance_band: tuple[Fraction, Fraction] | None = None

    def __post_init__(self) -> None:
        """Require an owned cap or a positive, conditioned full-angle band."""
        if type(self.contraction) is not AngleContraction:
            raise TypeError("Exact angle contraction required")
        model = self.contraction.geometry
        if self.kind == "full_angle_band":
            band = self.distance_band
            if (
                type(band) is not tuple
                or len(band) != 2
                or any(type(value) is not Fraction for value in band)
                or not 2 * model.receiver
                <= band[0]
                < band[1]
                <= model.outer - model.receiver
                or band[1] > 2 * band[0]
            ):
                raise ValueError("Invalid conditioned displacement band")
        elif (
            self.kind not in ("inner_cap", "outer_cap")
            or self.distance_band is not None
        ):
            raise ValueError("Unknown receiver-angle domain or unowned cap band")

    def evaluate(self, arguments: tuple[Jet, ...]) -> Jet:
        """Evaluate the finite approximant on one exact unit-coordinate domain."""
        if type(arguments) is not tuple or len(arguments) != 1:
            raise ValueError("One unit-coordinate Taylor jet required")
        coordinate = arguments[0]
        model = self.contraction.geometry
        model._unit_coordinate(coordinate)
        if model.delta == 0:
            return Jet.constant(0, coordinate.order)
        mapped = self.map(coordinate)
        survival = (-model.coefficient * mapped.distance_power).exp()
        contracted = self.contraction.integrate_angles(mapped.distance, mapped.moments)
        return mapped.measure * survival * contracted

    def map(self, coordinate: Jet) -> MappedAngle:
        """Expose the exact geometric map independently of any particular F."""
        model = self.contraction.geometry
        model._unit_coordinate(coordinate)
        if self.kind == "inner_cap":
            return self._inner(coordinate)
        if self.kind == "outer_cap":
            return self._outer(coordinate)
        assert self.distance_band is not None
        lower, upper = self.distance_band
        distance = lower + (upper - lower) * coordinate
        return MappedAngle(
            distance,
            distance.root(8),
            2 * distance * (upper - lower) / pi_bounds(),
            full_moments(coordinate.order),
        )

    def _inner(self, coordinate: Jet) -> MappedAngle:
        model = self.contraction.geometry
        pi = Jet.constant(pi_bounds(), coordinate.order)
        eta = pi / 2 * coordinate**8
        # The true parameter eta=pi*t^8/2 lies in [0,pi/2]. These ranges
        # describe that real law, not every arbitrary member of a pi interval.
        sinc = _range(eta.sinc(), (2 / pi_bounds()).lower, Fraction(1))
        sine = _range(eta * sinc, Fraction(0), Fraction(1))
        cosine = _range(eta.sin_cos()[1], Fraction(0), Fraction(1))
        distance = 2 * model.receiver * sine
        distance_power = coordinate * (pi * model.receiver * sinc).root(8)
        # theta_max=pi/2+eta; use its coupled sine/cosine identities.
        moments = partial_moments(pi / 2 + eta, cosine, -sine)
        # (2d/pi)*(dd/dt)=32R²*t^7*sin(eta)*cos(eta). Factoring
        # sin(eta)=pi*t^8*sinc(eta)/2 retains the exact contact endpoint.
        measure = 16 * pi * model.receiver**2 * coordinate**15 * sinc * cosine
        return MappedAngle(distance, distance_power, measure, moments)

    def _outer(self, coordinate: Jet) -> MappedAngle:
        model = self.contraction.geometry
        pi = Jet.constant(pi_bounds(), coordinate.order)
        theta = pi * coordinate
        sine_raw, cosine = theta.sin_cos()
        sine = _range(sine_raw, Fraction(0), Fraction(1))
        root = (model.outer**2 - model.receiver**2 * sine**2).root(2)
        distance = _range(
            root - model.receiver * cosine,
            model.outer - model.receiver,
            model.outer + model.receiver,
        )
        partial = partial_moments(theta, sine, cosine)
        moments = tuple(
            total - value
            for total, value in zip(
                full_moments(coordinate.order), partial, strict=True
            )
        )
        # The outer angular tails have negative odd moments. No clipping or
        # absolute values may alter that signed polynomial contraction.
        measure = (
            2 * model.receiver * distance * sine * (1 - model.receiver * cosine / root)
        )
        return MappedAngle(distance, distance.root(8), measure, moments)


@dataclass(frozen=True)
class AnglePartition:
    """All three displacement regions, with complete dyadic middle coverage."""

    contraction: AngleContraction
    domains: tuple[AngleDomain, ...]

    def __post_init__(self) -> None:
        """Refuse omitted, reordered or foreign displacement domains."""
        if (
            type(self.contraction) is not AngleContraction
            or type(self.domains) is not tuple
        ):
            raise TypeError("Exact angle contraction and domain tuple required")
        expected = self._domains(self.contraction)
        if self.domains != expected:
            raise ValueError("Receiver-angle support is incomplete or reordered")

    @staticmethod
    def _domains(contraction: AngleContraction) -> tuple[AngleDomain, ...]:
        model = contraction.geometry
        lower, upper = 2 * model.receiver, model.outer - model.receiver
        bands: list[AngleDomain] = []
        while lower < upper:
            if len(bands) >= MAX_BANDS:
                raise ResourceRefusal("displacement_band_ceiling_uncovered_tail")
            end = min(2 * lower, upper)
            bands.append(AngleDomain(contraction, "full_angle_band", (lower, end)))
            lower = end
        return (
            AngleDomain(contraction, "inner_cap"),
            *bands,
            AngleDomain(contraction, "outer_cap"),
        )

    @classmethod
    def build(cls, geometry: Geometry) -> AnglePartition:
        """Validate original geometry and the method's stricter proved guards."""
        contraction = AngleContraction(geometry)
        return cls(contraction, cls._domains(contraction))

    @property
    def geometry(self) -> Geometry:
        """Keep source radius R and annulus [R,L] distinct from displacement d."""
        return self.contraction.geometry
