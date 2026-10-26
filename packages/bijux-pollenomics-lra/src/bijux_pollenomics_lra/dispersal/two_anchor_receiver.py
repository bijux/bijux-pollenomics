"""Disk reception of a two-anchor inverse-square composition field."""

from __future__ import annotations

from dataclasses import dataclass
import math
import warnings

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import IntegrationWarning, quad, quad_vec

from bijux_pollenomics_lra.dispersal.kernels import gpm_values
from bijux_pollenomics_lra.dispersal.receiver_annulus import circular_receiver_annulus
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import finite_number

Coordinate = tuple[float, float]


@dataclass(frozen=True)
class TwoAnchorAnnulusResponse:
    """Two nonnegative field factors, homogeneous mass and numerical diagnostics.

    Error estimates are adaptive quadrature diagnostics, not rigorous bounds.
    Each factor multiplies its source anchor's cover and the target taxon's PPE.
    The two factors partition the independently computed homogeneous response.
    """

    anchor_factors: tuple[float, float]
    homogeneous_factor: float
    estimated_absolute_error: float
    partition_residual: float
    homogeneous_estimated_absolute_error: float


def _anchors(first: Coordinate, second: Coordinate) -> tuple[Coordinate, Coordinate]:
    coordinates = []
    for point in (first, second):
        if not isinstance(point, (tuple, list)) or len(point) != 2:
            raise ValidationError("Each planar anchor requires two metre coordinates")
        coordinates.append(tuple(finite_number(x, "anchor coordinate") for x in point))
    a, b = coordinates
    if a == b:
        raise ValidationError("The two source anchors must have distinct coordinates")
    return (a[0], a[1]), (b[0], b[1])


def _angular_mean(radius: float, a: Coordinate, b: Coordinate) -> float:
    scale = max(radius, *(abs(x) for x in (*a, *b)))
    ax, ay, bx, by, r = (*(x / scale for x in (*a, *b)), radius / scale)
    sx, sy, dx, dy = ax + bx, ay + by, bx - ax, by - ay
    difference = math.hypot(dx, dy)
    if difference == 0:
        raise ValidationError("Distinct anchor separation is numerically unresolved")
    delta = math.fsum((dx * sx, dy * sy))
    if delta == 0:
        # Equal-radius and opposite anchors have exactly symmetric circle means.
        return 0.5
    sum_norm = math.hypot(sx, sy)
    u = 2 * math.fsum((r * r, -ax * bx, -ay * by))
    denominator = math.hypot(u, sum_norm * difference)
    if denominator == 0:
        raise ValidationError("Two-anchor angular denominator is unresolved")
    if u >= 0:
        # Rationalize 1-u/D: direct subtraction loses the far-field limit and
        # is especially unstable for almost opposite anchors.
        correction = (delta / denominator) * (
            difference * difference / (2 * (denominator + u))
        )
    else:
        correction = delta / (2 * sum_norm * sum_norm) * (1 - u / denominator)
    value = 0.5 + correction
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValidationError("Two-anchor angular mean is numerically unresolved")
    return value


def two_anchor_inverse_square_angular_mean(
    radius_m: float, first_anchor_xy_m: Coordinate, second_anchor_xy_m: Coordinate
) -> float:
    """Average the first IDW weight over a target-centred source circle.

    The literal field is |x-a2|²/(|x-a1|²+|x-a2|²), including weight one at
    the first anchor. Coordinates and radius share one declared planar metre
    system. Distinct anchors keep the field denominator positive everywhere.
    Equal-radius anchors have mean one half. Coincident coordinates refuse;
    their limiting mean is one half away from the common anchor point.
    No projection, geodesic interpretation or field calibration is inferred.
    """
    radius = finite_number(radius_m, "radius_m", minimum=0)
    first, second = _anchors(first_anchor_xy_m, second_anchor_xy_m)
    return _angular_mean(radius, first, second)


def _receiver_fraction(
    receiver: float, distance: float, radius: float, gap: float
) -> float:
    """Source-centred angular fraction intercepting the receiver disk.

    Factoring the triangle altitude avoids subtracting nearly equal squared
    distances. At a boundary source and vanishing displacement the limit is
    one half, rather than a rounded zero from subtracting receiver-distance.
    """
    if distance <= gap or distance >= radius + receiver:
        return 0.0
    cosine = (gap / distance) * ((radius + receiver) / (2 * radius)) + distance / (
        2 * radius
    )
    if cosine <= 0.5:
        return math.acos(cosine) / math.pi
    side = max(radius, distance, receiver)
    terms = (
        (distance - gap) / side,
        (distance + gap) / side,
        (radius + receiver - distance) / side,
        (radius + receiver + distance) / side,
    )
    altitude = math.sqrt(math.prod(terms))
    horizontal = (gap / side) * ((radius + receiver) / side) + (distance / side) ** 2
    return math.atan2(altitude, horizontal) / math.pi


def two_anchor_circular_receiver_annulus(
    *,
    first_anchor_xy_m: Coordinate,
    second_anchor_xy_m: Coordinate,
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
) -> TwoAnchorAnnulusResponse:
    """Integrate a varying two-anchor field over a land annulus and receiver.

    Reuse the declared isotropic GPM and uniformly weighted disk, with land
    outside the receiving disk. Disk symmetry makes the effective source
    kernel radial. For source radius r and displacement d, its radial density
    is 2r/R² times the integral of the GPM displacement density against the
    source-centred fraction of directions intercepting the disk. Hazard q
    gives displacement mass exp(-q)dq. The remaining source-angle integral
    is the analytical two-anchor circle mean. Thus only two quadratures remain.

    Inner and outer quadratures receive fixed sub-budgets. Warnings, invalid
    values, nonpositive components at positive total mass, or a partition gap
    exceeding abs_tol+rel_tol*homogeneous_mass refuse without clipping or
    rescaling. Numerical errors do not establish a rigorous enclosure.
    """
    first, second = _anchors(first_anchor_xy_m, second_anchor_xy_m)
    abs_tol = finite_number(
        absolute_tolerance, "absolute_tolerance", minimum=0, strict_minimum=True
    )
    rel_tol = finite_number(
        relative_tolerance, "relative_tolerance", minimum=0, strict_minimum=True
    )
    # The existing consumer owns the physical parameter and annulus domain.
    homogeneous = circular_receiver_annulus(
        receiver_radius_m=receiver_radius_m,
        inner_radius_m=inner_radius_m,
        outer_radius_m=outer_radius_m,
        fall_speed_m_s=fall_speed_m_s,
        diffusion_coefficient=diffusion_coefficient,
        turbulence_parameter=turbulence_parameter,
        wind_speed_m_s=wind_speed_m_s,
        absolute_tolerance=abs_tol / 4,
        relative_tolerance=rel_tol / 4,
        quadrature_limit=quadrature_limit,
    )
    receiver, inner, outer = map(
        float, (receiver_radius_m, inner_radius_m, outer_radius_m)
    )
    fall, diffusion, turbulence, wind = map(
        float,
        (fall_speed_m_s, diffusion_coefficient, turbulence_parameter, wind_speed_m_s),
    )
    survival = float(gpm_values(1.0, fall, diffusion, turbulence, wind))
    coefficient = -math.log(survival)
    power = turbulence / 2
    largest_inner_error = 0.0

    def weight(radius: float) -> NDArray[np.float64]:
        first_weight = _angular_mean(radius, first, second)
        return np.array([first_weight, 1 - first_weight])

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", IntegrationWarning)
            if receiver == 0:
                coefficient = (4 * fall) / (
                    turbulence * wind * math.sqrt(math.pi) * diffusion
                )
                left, right = coefficient * inner**power, coefficient * outer**power
                if left >= 745:
                    factors, error = np.zeros(2), 0.0
                else:

                    def point_integrand(q: float) -> NDArray[np.float64]:
                        return np.asarray(
                            math.exp(-q) * weight((q / coefficient) ** (1 / power)),
                            dtype=float,
                        )

                    factors, error, info = quad_vec(
                        point_integrand,
                        left,
                        min(right, 745.0),
                        epsabs=abs_tol / 4,
                        epsrel=rel_tol / 4,
                        limit=quadrature_limit,
                        full_output=True,
                    )
                    if not info.success:
                        raise ValidationError(
                            "Two-anchor point quadrature did not converge"
                        )
            else:
                relative_width = (outer - inner) / inner
                log_width = (
                    math.log1p(relative_width)
                    if math.isfinite(relative_width)
                    else math.log(outer) - math.log(inner)
                )
                flatten = max(1.0, 1 / power)

                def integrand(t: float) -> NDArray[np.float64]:
                    nonlocal largest_inner_error
                    growth = math.expm1(log_width * t**flatten)
                    radius = inner * (1 + growth)
                    gap = (inner - receiver) + inner * growth
                    jacobian = log_width * flatten * t ** (flatten - 1)
                    scale = 2 * (radius / receiver) ** 2 * jacobian
                    if not math.isfinite(scale):
                        raise ValidationError("Receiver radial measure is unresolved")
                    left = coefficient * gap**power
                    right = coefficient * (radius + receiver) ** power
                    if left >= 745:
                        return np.zeros(2)

                    def displacement(q: float) -> float:
                        distance = (q / coefficient) ** (1 / power)
                        return math.exp(-q) * _receiver_fraction(
                            receiver, distance, radius, gap
                        )

                    value, local_error = quad(
                        displacement,
                        left,
                        min(right, 745.0),
                        epsabs=abs_tol / (64 * max(1.0, scale)),
                        epsrel=rel_tol / 16,
                        limit=quadrature_limit,
                    )
                    largest_inner_error = max(largest_inner_error, scale * local_error)
                    return np.asarray(
                        scale * float(value) * weight(radius), dtype=float
                    )

                factors, error, info = quad_vec(
                    integrand,
                    0.0,
                    1.0,
                    epsabs=abs_tol / 4,
                    epsrel=rel_tol / 4,
                    limit=quadrature_limit,
                    full_output=True,
                )
                if not info.success:
                    raise ValidationError("Two-anchor disk quadrature did not converge")
    except (IntegrationWarning, OverflowError, ZeroDivisionError, ValueError) as exc:
        raise ValidationError(
            "Two-anchor receiver quadrature did not converge"
        ) from exc
    first_factor, second_factor = map(float, factors)
    weighted_error = float(error) + largest_inner_error
    residual = first_factor + second_factor - homogeneous.factor
    tolerance = abs_tol + rel_tol * homogeneous.factor
    if (
        not all(
            math.isfinite(v)
            for v in (first_factor, second_factor, weighted_error, residual)
        )
        or min(first_factor, second_factor) < 0
        or (homogeneous.factor > 0 and min(first_factor, second_factor) <= 0)
        or abs(residual) > tolerance
        or weighted_error > tolerance
    ):
        raise ValidationError(
            "Two-anchor response failed positivity, partition or error criterion"
        )
    return TwoAnchorAnnulusResponse(
        (first_factor, second_factor),
        homogeneous.factor,
        weighted_error,
        residual,
        homogeneous.estimated_absolute_error,
    )
