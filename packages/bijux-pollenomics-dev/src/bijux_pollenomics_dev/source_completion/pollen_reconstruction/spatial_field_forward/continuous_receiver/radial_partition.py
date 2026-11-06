"""Exact radial coverage with one contact band and scaled regular bands.

Band metadata owns the unchanged global geometry. A regular band's scale is
its source-radius lower bound, never a replacement receiving-disk radius.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .arithmetic import Interval, Jet, pi_bounds
from .kernel import Geometry
from .quadrature import ResourceRefusal

WHOLE_ANNULUS = "whole_annulus"
DYADIC_RADIAL = "dyadic_radial"
MAX_BANDS = 11


def validate_partition_option(partition: str) -> None:
    """Require one of the two named radial partition strategies."""
    if type(partition) is not str or partition not in (WHOLE_ANNULUS, DYADIC_RADIAL):
        raise ValueError("Unknown continuous-receiver radial partition")


@dataclass(frozen=True)
class Band:
    """Bind one exact radial band to its unchanged original geometry."""

    geometry: Geometry
    index: int
    lower: Fraction
    upper: Fraction

    def __post_init__(self) -> None:
        """Require the band index and endpoints to match original radial ownership."""
        if (
            type(self.geometry) is not Geometry
            or type(self.index) is not int
            or not 0 <= self.index < MAX_BANDS
        ):
            raise ValueError("Exact original geometry and bounded band index required")
        if type(self.lower) is not Fraction or type(self.upper) is not Fraction:
            raise TypeError("Exact radial-band boundaries required")
        expected_lower = self.geometry.receiver * 2**self.index
        expected_upper = min(2 * expected_lower, self.geometry.outer)
        if (
            self.lower != expected_lower
            or self.upper != expected_upper
            or not self.lower < self.upper
        ):
            raise ValueError(
                "Radial band differs from its exact original-geometry ownership"
            )


def radial_bands(geometry: Geometry) -> tuple[Band, ...]:
    """Partition the full radial span into bounded dyadic bands."""
    if type(geometry) is not Geometry:
        raise TypeError("Exact original geometry required")
    bands: list[Band] = []
    lower = geometry.receiver
    while lower < geometry.outer:
        if len(bands) >= MAX_BANDS:
            raise ResourceRefusal("radial_band_ceiling_uncovered_tail")
        upper = min(2 * lower, geometry.outer)
        bands.append(Band(geometry, len(bands), lower, upper))
        lower = upper
    return tuple(bands)


def validate_bands(geometry: Geometry, bands: tuple[Band, ...]) -> None:
    """Require exactly the complete ordered bands of the declared geometry."""
    if type(bands) is not tuple or bands != radial_bands(geometry):
        raise ValueError("Missing, overlapping, reordered or foreign radial bands")


@dataclass(frozen=True)
class RadialDomain:
    """Describe a contact-triangle or regular-band integration domain."""

    band: Band
    kind: str
    patch: int | None = None

    def __post_init__(self) -> None:
        """Require the domain kind and patch to match their source-owned band."""
        if type(self.band) is not Band:
            raise TypeError("Source-owned radial band required")
        if self.kind == "contact_triangle":
            if (
                self.band.index != 0
                or type(self.patch) is not int
                or self.patch not in (1, 2)
            ):
                raise ValueError(
                    "Contact triangle must own the first original-receiver band"
                )
        elif self.kind == "regular_band":
            if self.band.index == 0 or self.patch is not None:
                raise ValueError("Regular domain must own a noncontact radial band")
        else:
            raise ValueError("Unknown radial domain kind")

    def evaluate(self, arguments: tuple[Jet, ...]) -> Jet:
        """Evaluate the transformed integrand on its declared radial domain."""
        if len(arguments) != 2:
            raise ValueError("Two radial integration coordinates required")
        first, second = arguments
        model = self.band.geometry
        model._unit_coordinate(first)
        model._unit_coordinate(second)
        if first.order != second.order:
            raise ValueError("Radial coordinate Taylor orders differ")
        if self.kind == "contact_triangle":
            assert self.patch is not None
            return model.triangle(
                first, second, self.patch, contact_outer=self.band.upper
            )
        a, b = self.band.lower, self.band.upper
        if not 2 * model.receiver <= a < b <= min(2 * a, model.outer):
            raise ValueError(
                "Regular-band scale does not belong to the original receiver"
            )
        radius = a + (b - a) * first
        x, rho = 1 + ((b - a) / a) * first, model.receiver / a
        phi = second * pi_bounds()
        sine = phi.sin_cos()[0]
        half_sine = (phi / 2).sin_cos()[0]
        scaled_distance = (x - rho) ** 2 + 4 * rho * x * half_sine**2
        # Unit coordinates and R/a<=1/2 prove these bounds before intersection.
        # The exact underlying distance remains a²*scaled_distance.
        scaled_distance = Jet(
            (
                Interval(
                    max(Fraction(1, 4), scaled_distance.value.lower),
                    min(Fraction(25, 4), scaled_distance.value.upper),
                ),
            )
            + scaled_distance.coefficients[1:]
        )
        distance_power = scaled_distance.root(16) * Interval.point(a).root(8)
        survival = (-model.coefficient * distance_power).exp()
        return (
            2
            * (b - a)
            * x**2
            * model.angular_derivative(radius)
            * sine**2
            / scaled_distance
            * survival
        )


@dataclass(frozen=True)
class RadialPartition:
    """Group exact radial bands and their complete transformed domains."""

    geometry: Geometry
    bands: tuple[Band, ...]
    domains: tuple[RadialDomain, ...]

    def __post_init__(self) -> None:
        """Require the exact ordered domain population for the original geometry."""
        validate_bands(self.geometry, self.bands)
        expected = (
            RadialDomain(self.bands[0], "contact_triangle", 1),
            RadialDomain(self.bands[0], "contact_triangle", 2),
        ) + tuple(RadialDomain(band, "regular_band") for band in self.bands[1:])
        if type(self.domains) is not tuple or self.domains != expected:
            raise ValueError(
                "Missing, overlapping, reordered or foreign radial domains"
            )

    @classmethod
    def build(cls, geometry: Geometry) -> RadialPartition:
        """Construct all contact and regular domains for an exact geometry."""
        bands = radial_bands(geometry)
        domains = (
            RadialDomain(bands[0], "contact_triangle", 1),
            RadialDomain(bands[0], "contact_triangle", 2),
        ) + tuple(RadialDomain(band, "regular_band") for band in bands[1:])
        return cls(geometry, bands, domains)
