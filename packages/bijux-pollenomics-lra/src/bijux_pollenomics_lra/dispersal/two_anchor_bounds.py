"""Fixed radial-step enclosures for two-anchor disk-reception coefficients."""

from __future__ import annotations

from dataclasses import dataclass
import math

from bijux_pollenomics_lra.dispersal.receiver_annulus import circular_receiver_annulus
from bijux_pollenomics_lra.dispersal.two_anchor_receiver import (
    Coordinate,
    two_anchor_inverse_square_angular_mean,
)
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import finite_number


@dataclass(frozen=True)
class AnnulusStep:
    """One ring's computed mass and extrema of its radial angular-mean weight."""

    inner_radius_m: float
    outer_radius_m: float
    first_weight_bounds: tuple[float, float]
    homogeneous_factor: float
    estimated_absolute_error: float


@dataclass(frozen=True)
class TwoAnchorAnnulusBounds:
    """Step bounds conditional on computed ring masses, not exact quadrature.

    Factor bounds concern the first and second anchor, in that order. Their
    extrema are coupled by complementary weights and need not occur together.
    Numerical ring-mass errors remain separate, nonrigorous estimates.
    """

    anchor_factor_bounds: tuple[tuple[float, float], tuple[float, float]]
    homogeneous_factor: float
    homogeneous_estimated_absolute_error: float
    annuli: tuple[AnnulusStep, ...]


def two_anchor_annulus_step_bounds(
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
    annulus_count: int = 8,
) -> TwoAnchorAnnulusBounds:
    """Use endpoint circle means and unchanged homogeneous ring responses.

    With Delta=|a2|²-|a1|², d=a1-a2 and the positive angular denominator D,
    the radial derivative of the first mean is -2*r*Delta*|d|²/D³. It is
    monotone toward one half, so endpoint minima/maxima enclose its value
    throughout each radial ring. Integrating against a positive radial
    measure preserves those inequalities for exact ring masses.

    These bounds instead condition on the returned numerical ring factors.
    Adaptive quadrature error estimates do not turn them into guaranteed
    true-integral or directed floating-point intervals. The fixed logarithmic
    partition is never refined to meet a target score or desired bound width.
    """
    receiver = finite_number(receiver_radius_m, "receiver_radius_m", minimum=0)
    inner = finite_number(
        inner_radius_m, "inner_radius_m", minimum=0, strict_minimum=True
    )
    outer = finite_number(
        outer_radius_m, "outer_radius_m", minimum=0, strict_minimum=True
    )
    abs_tol = finite_number(
        absolute_tolerance, "absolute_tolerance", minimum=0, strict_minimum=True
    )
    rel_tol = finite_number(
        relative_tolerance, "relative_tolerance", minimum=0, strict_minimum=True
    )
    if receiver > inner or inner >= outer:
        raise ValidationError("Log annuli require 0 <= receiver <= inner < outer")
    if type(annulus_count) is not int or not 2 <= annulus_count <= 128:
        raise ValidationError("annulus_count must be an integer from 2 to 128")
    width = math.log(outer) - math.log(inner)
    edges = [
        inner,
        *(
            math.exp(math.log(inner) + width * i / annulus_count)
            for i in range(1, annulus_count)
        ),
        outer,
    ]
    if any(a >= b for a, b in zip(edges[:-1], edges[1:], strict=True)):
        raise ValidationError("Distinct logarithmic annuli are not representable")
    means = [
        two_anchor_inverse_square_angular_mean(r, first_anchor_xy_m, second_anchor_xy_m)
        for r in edges
    ]
    rows = []
    for a, b, left, right in zip(
        edges[:-1], edges[1:], means[:-1], means[1:], strict=True
    ):
        mass = circular_receiver_annulus(
            receiver_radius_m=receiver,
            inner_radius_m=a,
            outer_radius_m=b,
            fall_speed_m_s=fall_speed_m_s,
            diffusion_coefficient=diffusion_coefficient,
            turbulence_parameter=turbulence_parameter,
            wind_speed_m_s=wind_speed_m_s,
            absolute_tolerance=abs_tol / annulus_count,
            relative_tolerance=rel_tol,
            quadrature_limit=quadrature_limit,
        )
        rows.append(
            AnnulusStep(
                a,
                b,
                (min(left, right), max(left, right)),
                mass.factor,
                mass.estimated_absolute_error,
            )
        )
    first_lower = math.fsum(
        row.first_weight_bounds[0] * row.homogeneous_factor for row in rows
    )
    first_upper = math.fsum(
        row.first_weight_bounds[1] * row.homogeneous_factor for row in rows
    )
    second_lower = math.fsum(
        (1 - row.first_weight_bounds[1]) * row.homogeneous_factor for row in rows
    )
    second_upper = math.fsum(
        (1 - row.first_weight_bounds[0]) * row.homogeneous_factor for row in rows
    )
    return TwoAnchorAnnulusBounds(
        ((first_lower, first_upper), (second_lower, second_upper)),
        math.fsum(row.homogeneous_factor for row in rows),
        math.fsum(row.estimated_absolute_error for row in rows),
        tuple(rows),
    )
