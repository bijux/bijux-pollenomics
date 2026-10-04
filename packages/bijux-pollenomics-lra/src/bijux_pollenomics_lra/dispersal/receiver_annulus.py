"""A conditional isotropic GPM response for a circular receiving basin."""

from __future__ import annotations

from dataclasses import dataclass
import math
import warnings

from scipy.integrate import IntegrationWarning, quad

from bijux_pollenomics_lra.dispersal.kernels import gpm_values
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import finite_number


@dataclass(frozen=True)
class AnnulusResponse:
    """Disk-averaged factor and a nonrigorous adaptive quadrature error estimate."""

    factor: float
    estimated_absolute_error: float


def _circle_fraction(radius: float, distance: float, receiver_offset: float) -> float:
    if distance + receiver_offset <= radius:
        return 1.0
    if abs(distance - receiver_offset) >= radius:
        return 0.0
    cosine = (
        radius * radius - distance * distance - receiver_offset * receiver_offset
    ) / (2 * distance * receiver_offset)
    return 1.0 - math.acos(max(-1.0, min(1.0, cosine))) / math.pi


def circular_receiver_annulus(
    *,
    receiver_radius_m: float,
    inner_radius_m: float,
    outer_radius_m: float,
    fall_speed_m_s: float,
    diffusion_coefficient: float,
    turbulence_parameter: float,
    wind_speed_m_s: float,
    absolute_tolerance: float = 1e-9,
    relative_tolerance: float = 1e-8,
    quadrature_limit: int = 100,
) -> AnnulusResponse:
    """Integrate a homogeneous land annulus over a uniformly weighted disk.

    This independently declared geometry interprets source GPM survival as a
    stationary isotropic radial displacement law. It does not reproduce the
    historical lake algorithm or establish a physical receiving radius.
    """
    receiver = finite_number(receiver_radius_m, "receiver_radius_m", minimum=0)
    inner = finite_number(inner_radius_m, "inner_radius_m", minimum=0)
    outer = finite_number(outer_radius_m, "outer_radius_m", minimum=0)
    fall = finite_number(
        fall_speed_m_s, "fall_speed_m_s", minimum=0, strict_minimum=True
    )
    diffusion = finite_number(
        diffusion_coefficient, "diffusion_coefficient", minimum=0, strict_minimum=True
    )
    turbulence = finite_number(
        turbulence_parameter, "turbulence_parameter", minimum=0, strict_minimum=True
    )
    wind = finite_number(
        wind_speed_m_s, "wind_speed_m_s", minimum=0, strict_minimum=True
    )
    abs_tol = finite_number(
        absolute_tolerance, "absolute_tolerance", minimum=0, strict_minimum=True
    )
    rel_tol = finite_number(
        relative_tolerance, "relative_tolerance", minimum=0, strict_minimum=True
    )
    if receiver > inner or inner >= outer:
        raise ValidationError("land annulus requires 0 <= receiver <= inner < outer")
    if (
        isinstance(quadrature_limit, bool)
        or not isinstance(quadrature_limit, int)
        or not 20 <= quadrature_limit <= 1000
    ):
        raise ValidationError("quadrature_limit must be an integer from 20 to 1000")

    # The existing GPM kernel owns the survival curve; its value at one metre
    # identifies the exponent coefficient without fitting a second curve.
    survival_one = float(gpm_values(1.0, fall, diffusion, turbulence, wind))
    if not 0.0 < survival_one < 1.0:
        raise ValidationError("GPM survival at one metre is numerically unresolved")
    coefficient = -math.log(survival_one)
    exponent = turbulence / 2.0

    def hazard(distance: float) -> float:
        value = float(coefficient * distance**exponent)
        if not math.isfinite(value):
            raise ValidationError("GPM distance transform is numerically unresolved")
        return value

    if receiver == 0.0:
        inner_survival = float(gpm_values(inner, fall, diffusion, turbulence, wind))
        factor = inner_survival - float(
            gpm_values(outer, fall, diffusion, turbulence, wind)
        )
        if factor == 0.0 and inner_survival > 0.0:
            # Recover equal rounded survivals from the point GPM parameter law,
            # rather than the finite-disk coefficient inferred from exp rounding.
            # Nonzero ordinary subtraction and the disk quadrature stay unchanged.
            point_coefficient = (4 * fall) / (
                turbulence * wind * math.sqrt(math.pi) * diffusion
            )
            inner_hazard = point_coefficient * inner**exponent
            if inner == 0.0 or inner_hazard == 0.0:
                hazard_difference = point_coefficient * outer**exponent
            else:
                relative_increment = (outer - inner) / inner
                # Wide finite radii may overflow their ratio even though both
                # logarithms and the exponent-scaled hazard increment are finite.
                log_ratio = (
                    math.log1p(relative_increment)
                    if math.isfinite(relative_increment)
                    else math.log(outer) - math.log(inner)
                )
                hazard_difference = inner_hazard * math.expm1(exponent * log_ratio)
            factor = math.exp(-inner_hazard) * -math.expm1(-hazard_difference)
        return AnnulusResponse(max(0.0, factor), 0.0)

    largest_inner_error = 0.0

    def at_receiver_area(z: float) -> float:
        nonlocal largest_inner_error
        offset = receiver * math.sqrt(z)
        if offset == 0.0:
            return math.exp(-hazard(inner)) - math.exp(-hazard(outer))
        boundaries = sorted(
            {
                hazard(inner - offset),
                hazard(inner + offset),
                hazard(max(0.0, outer - offset)),
                hazard(outer + offset),
            }
        )
        total = 0.0
        local_error = 0.0
        for left, right in zip(boundaries, boundaries[1:], strict=False):
            if left >= 745.0:
                continue

            def integrand(q: float) -> float:
                distance = (q / coefficient) ** (1.0 / exponent)
                fraction = _circle_fraction(outer, distance, offset) - _circle_fraction(
                    inner, distance, offset
                )
                return math.exp(-q) * fraction

            value, error = quad(
                integrand,
                left,
                min(right, 745.0),
                epsabs=abs_tol / 4.0,
                epsrel=rel_tol,
                limit=quadrature_limit,
            )
            total += value
            local_error += error
        largest_inner_error = max(largest_inner_error, local_error)
        return total

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", IntegrationWarning)
            factor, outer_error = quad(
                at_receiver_area,
                0.0,
                1.0,
                epsabs=abs_tol,
                epsrel=rel_tol,
                limit=quadrature_limit,
            )
    except (IntegrationWarning, OverflowError, ZeroDivisionError) as error:
        raise ValidationError("circular annulus quadrature did not converge") from error
    estimate = outer_error + largest_inner_error
    if (
        not (math.isfinite(factor) and math.isfinite(estimate))
        or not -abs_tol <= factor <= 1.0 + abs_tol
    ):
        raise ValidationError("circular annulus response is numerically invalid")
    return AnnulusResponse(min(1.0, max(0.0, factor)), estimate)
