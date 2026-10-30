"""Independent angular/area integrals and step bounds for spatial reception."""

from __future__ import annotations

from decimal import Decimal, localcontext
import math
from types import SimpleNamespace
from typing import TypedDict

import numpy as np
from numpy.polynomial.legendre import leggauss
import pytest
from scipy.integrate import IntegrationWarning, quad

from bijux_pollenomics_lra.dispersal import two_anchor_receiver as field
from bijux_pollenomics_lra.dispersal.receiver_annulus import circular_receiver_annulus
from bijux_pollenomics_lra.dispersal.two_anchor_bounds import (
    two_anchor_annulus_step_bounds,
)
from bijux_pollenomics_lra.models.errors import ValidationError


class PhysicalParameters(TypedDict):
    fall_speed_m_s: float
    diffusion_coefficient: float
    turbulence_parameter: float
    wind_speed_m_s: float


PHYSICAL: PhysicalParameters = {
    "fall_speed_m_s": 0.03,
    "diffusion_coefficient": 0.12,
    "turbulence_parameter": 0.25,
    "wind_speed_m_s": 3.0,
}


def _direct_mean(
    radius: float, first: tuple[float, float], second: tuple[float, float]
) -> float:
    scale = max(radius, *map(abs, (*first, *second)))
    r = radius / scale
    a, b = np.array(first) / scale, np.array(second) / scale

    def value(angle: float) -> float:
        x = np.array([r * math.cos(angle), r * math.sin(angle)])
        d1, d2 = float(np.sum((x - a) ** 2)), float(np.sum((x - b) ** 2))
        return d2 / (d1 + d2)

    return float(
        quad(value, 0, 2 * math.pi, epsabs=1e-12, epsrel=1e-12, limit=200)[0]
        / (2 * math.pi)
    )


@pytest.mark.parametrize(
    "radius,first,second",
    [
        (0.0, (2.0, 3.0), (4.0, -1.0)),
        (1.0, (3.0, 1.0), (-2.0, 6.0)),
        (10.0, (3.0, 1.0), (-2.0, 6.0)),
        (100.0, (3.0, 1.0), (-2.0, 6.0)),
        (5.0, (3.0, 4.0), (-3.0, -4.0)),
        (5.0, (3.0, 4.0), (-3.0 + 1e-12, -4.0)),
        (5.0, (3.0, 4.0), (4.0, 3.0)),
        (1e12, (1.0, 2.0), (-3.0, 4.0)),
        (1e-150, (1e-150, 2e-150), (3e-150, -1e-150)),
        (0.0, (0.0, 0.0), (1.0, 0.0)),
        (0.0, (1.0, 0.0), (0.0, 0.0)),
    ],
)
def test_circle_reduction_matches_direct_angular_integral(
    radius: float, first: tuple[float, float], second: tuple[float, float]
) -> None:
    actual = field.two_anchor_inverse_square_angular_mean(radius, first, second)
    assert actual == pytest.approx(_direct_mean(radius, first, second), abs=3e-14)
    assert actual + field.two_anchor_inverse_square_angular_mean(
        radius, second, first
    ) == pytest.approx(1, abs=2e-15)


def test_circle_mean_is_rotation_invariant_and_monotone_toward_half() -> None:
    first, second = (30.0, 40.0), (-60.0, 80.0)
    radii = [0, 10, 30, 50, 80, 100, 200, 1000]
    values = [
        field.two_anchor_inverse_square_angular_mean(r, first, second) for r in radii
    ]
    assert all(a >= b >= 0.5 for a, b in zip(values[:-1], values[1:], strict=True))
    for r, expected in zip(radii, values, strict=True):
        assert field.two_anchor_inverse_square_angular_mean(
            r, (-first[1], first[0]), (-second[1], second[0])
        ) == pytest.approx(expected, abs=2e-15)


def test_almost_coincident_anchor_limit_uses_high_precision_identity() -> None:
    # Ordinary adaptive angular quadrature can miss a feature only 1e-12
    # radians wide. Evaluate the unrearranged angular identity at high
    # precision, independently of the production cancellation-safe form.
    with localcontext() as context:
        context.prec = 96
        radius, first, second = map(Decimal.from_float, (3.0, 3.0, 3.0 + 1e-12))
        total = first + second
        a = 2 * radius**2 + first**2 + second**2
        b = 2 * radius * total
        c = radius**2 + second**2
        t = second / total
        expected = t + (c - t * a) / (a * a - b * b).sqrt()
    actual = field.two_anchor_inverse_square_angular_mean(3, (3, 0), (3 + 1e-12, 0))
    assert actual == pytest.approx(float(expected), abs=2e-16)


def _response(
    receiver: float, inner: float, outer: float
) -> field.TwoAnchorAnnulusResponse:
    return field.two_anchor_circular_receiver_annulus(
        first_anchor_xy_m=(30, 20),
        second_anchor_xy_m=(-200, 80),
        receiver_radius_m=receiver,
        inner_radius_m=inner,
        outer_radius_m=outer,
        **PHYSICAL,
    )


def _area_reference(receiver: float, inner: float, outer: float, order: int) -> float:
    """Integrate source and receiver area plus two numerical angular means.

    This uses the planar displacement density, not the new source-cap/hazard
    integral or its analytical IDW reduction. Receiver rotation symmetry lets
    the independently quadratured source-field angular mean be factored out.
    """
    nodes, weights = leggauss(order)
    z, zw = (nodes + 1) / 2, weights / 2
    r = np.sqrt(inner**2 + (outer**2 - inner**2) * z)
    angles = math.pi * (nodes + 1)
    x, y = r[:, None] * np.cos(angles), r[:, None] * np.sin(angles)
    d1, d2 = (x - 30) ** 2 + (y - 20) ** 2, (x + 200) ** 2 + (y - 80) ** 2
    average = (d2 / (d1 + d2)) @ zw
    exponent = 0.25 / 2
    coefficient = 4 * 0.03 / (0.25 * 3 * math.sqrt(math.pi) * 0.12)
    total = 0.0
    for area, area_weight in zip(z, zw, strict=True):
        offset = receiver * math.sqrt(area)
        distance = np.sqrt(
            r[:, None] ** 2 + offset**2 - 2 * r[:, None] * offset * np.cos(angles)
        )
        density = (
            coefficient
            * exponent
            * distance ** (exponent - 2)
            * np.exp(-coefficient * distance**exponent)
            / (2 * math.pi)
        )
        total += (
            area_weight
            * math.pi
            * (outer**2 - inner**2)
            * float(zw @ (density * average[:, None]) @ zw)
        )
    return total


@pytest.mark.parametrize(
    "receiver,inner,outer", [(10.0, 60.0, 120.0), (80.0, 130.0, 260.0)]
)
def test_weighted_response_matches_independent_area_quadrature(
    receiver: float, inner: float, outer: float
) -> None:
    coarse = _area_reference(receiver, inner, outer, 64)
    fine = _area_reference(receiver, inner, outer, 128)
    assert coarse == pytest.approx(fine, abs=1e-9)
    result = _response(receiver, inner, outer)
    assert result.anchor_factors[0] == pytest.approx(fine, abs=1e-9)
    assert all(x > 0 for x in result.anchor_factors)
    assert abs(result.partition_residual) <= 1e-9 + 1e-8 * result.homogeneous_factor


def test_boundary_receiver_is_enclosed_by_independent_annular_steps() -> None:
    edges = np.geomspace(80, 1000, 9)
    means = [_direct_mean(float(r), (30, 20), (-200, 80)) for r in edges]
    masses = [
        circular_receiver_annulus(
            receiver_radius_m=80,
            inner_radius_m=float(a),
            outer_radius_m=float(b),
            **PHYSICAL,
        )
        for a, b in zip(edges[:-1], edges[1:], strict=True)
    ]
    lower = sum(
        min(a, b) * m.factor
        for a, b, m in zip(means[:-1], means[1:], masses, strict=True)
    )
    upper = sum(
        max(a, b) * m.factor
        for a, b, m in zip(means[:-1], means[1:], masses, strict=True)
    )
    result = _response(80, 80, 1000)
    # Monotonicity gives exact step bounds for exact interval masses. The
    # old consumer's errors are numerical estimates, not rigorous enclosures.
    allowance = sum(m.estimated_absolute_error for m in masses) + 1e-9
    assert lower - allowance <= result.anchor_factors[0] <= upper + allowance
    assert lower < upper
    assert sum(m.factor for m in masses) == pytest.approx(
        result.homogeneous_factor, abs=1e-8
    )


def test_equal_anchor_radius_and_constant_cover_partition() -> None:
    result = field.two_anchor_circular_receiver_annulus(
        first_anchor_xy_m=(30, 40),
        second_anchor_xy_m=(-30, -40),
        receiver_radius_m=10,
        inner_radius_m=60,
        outer_radius_m=120,
        **PHYSICAL,
    )
    assert result.anchor_factors[0] == pytest.approx(
        result.homogeneous_factor / 2, abs=1e-9
    )
    assert result.anchor_factors[1] == pytest.approx(
        result.homogeneous_factor / 2, abs=1e-9
    )
    for constant in (0.0, 0.2, 1.0):
        assert sum(x * constant for x in result.anchor_factors) == pytest.approx(
            constant * result.homogeneous_factor, abs=1e-9
        )


def test_point_receiver_has_an_independent_radial_angular_integral() -> None:
    coefficient = 4 * 0.03 / (0.25 * 3 * math.sqrt(math.pi) * 0.12)
    exponent = 0.25 / 2
    expected = quad(
        lambda r: (
            coefficient
            * exponent
            * r ** (exponent - 1)
            * math.exp(-coefficient * r**exponent)
            * _direct_mean(r, (30, 20), (-200, 80))
        ),
        20,
        80,
        epsabs=1e-11,
        epsrel=1e-11,
    )[0]
    assert _response(0, 20, 80).anchor_factors[0] == pytest.approx(expected, abs=1e-10)


def test_fixed_log_step_record_reconstructs_the_reported_coefficients() -> None:
    result = two_anchor_annulus_step_bounds(
        first_anchor_xy_m=(30, 20),
        second_anchor_xy_m=(-200, 80),
        receiver_radius_m=80,
        inner_radius_m=80,
        outer_radius_m=1000,
        **PHYSICAL,
    )
    assert len(result.annuli) == 8
    lower = [0.0, 0.0]
    upper = [0.0, 0.0]
    for row in result.annuli:
        means = [
            _direct_mean(r, (30, 20), (-200, 80))
            for r in (row.inner_radius_m, row.outer_radius_m)
        ]
        assert row.first_weight_bounds == pytest.approx(
            (min(means), max(means)), abs=3e-14
        )
        lower[0] += min(means) * row.homogeneous_factor
        upper[0] += max(means) * row.homogeneous_factor
        lower[1] += (1 - max(means)) * row.homogeneous_factor
        upper[1] += (1 - min(means)) * row.homogeneous_factor
    for i in range(2):
        assert result.anchor_factor_bounds[i] == pytest.approx(
            (lower[i], upper[i]), abs=1e-14
        )
    assert result.homogeneous_factor == math.fsum(
        r.homogeneous_factor for r in result.annuli
    )
    assert result.homogeneous_estimated_absolute_error == math.fsum(
        r.estimated_absolute_error for r in result.annuli
    )


def test_broad_land_annulus_partitions_without_losing_small_anchor_weight() -> None:
    result = _response(80, 80, 100000)
    assert min(result.anchor_factors) > 0
    assert result.estimated_absolute_error <= 1e-9 + 1e-8 * result.homogeneous_factor
    assert result.homogeneous_estimated_absolute_error >= 0


@pytest.mark.parametrize("annulus_count", [True, 0, 1, 129])
def test_invalid_log_partition_budget_refuses(annulus_count: int) -> None:
    with pytest.raises(ValidationError, match="annulus_count"):
        two_anchor_annulus_step_bounds(
            first_anchor_xy_m=(30, 20),
            second_anchor_xy_m=(-200, 80),
            receiver_radius_m=80,
            inner_radius_m=80,
            outer_radius_m=1000,
            annulus_count=annulus_count,
            **PHYSICAL,
        )


@pytest.mark.parametrize(
    "radius,first,second",
    [
        (-1, (1, 2), (3, 4)),
        (1, (1, 2), (1, 2)),
        (1, (float("nan"), 1), (3, 4)),
        (True, (1, 2), (3, 4)),
    ],
)
def test_invalid_angular_geometry_refuses(
    radius: float, first: tuple[float, float], second: tuple[float, float]
) -> None:
    with pytest.raises(ValidationError):
        field.two_anchor_inverse_square_angular_mean(radius, first, second)


def test_quadrature_failure_refuses_without_a_successful_partition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        field,
        "quad_vec",
        lambda *args, **kwargs: (np.ones(2), 0.0, SimpleNamespace(success=False)),
    )
    with pytest.raises(ValidationError, match="did not converge"):
        _response(10, 60, 120)


def test_failed_partition_does_not_rescale_or_clip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        field,
        "quad_vec",
        lambda *args, **kwargs: (
            np.array([-1e-15, 0.1]),
            0.0,
            SimpleNamespace(success=True),
        ),
    )
    with pytest.raises(ValidationError, match="positivity, partition or error"):
        _response(10, 60, 120)


def test_inner_integration_warning_remains_a_refusal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise IntegrationWarning("controlled unresolved integration")

    monkeypatch.setattr(field, "quad", fail)
    with pytest.raises(ValidationError, match="did not converge"):
        _response(10, 60, 120)
