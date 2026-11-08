"""Independent polynomial moments, geometric measures and lattice conditioning."""

from __future__ import annotations

from fractions import Fraction as F
from math import comb, isqrt

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.angle_moments.contraction import (
    AngleContraction,
    binomial_coefficients,
    full_moments,
    partial_moments,
    series_remainder,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.angle_moments.domains import (
    AngleDomain,
    AnglePartition,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.arithmetic import (
    Interval,
    Jet,
    pi_bounds,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.kernel import (
    Geometry,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.quadrature import (
    SEVEN_NODE_RULE,
    WorkBudget,
    positive_panel,
)


def geometry(*, coefficient: F = F(1, 2), outer: F = F(4)) -> Geometry:
    return Geometry(coefficient, F(1), outer, (F(1000), F(0)), (F(2000), F(0)))


def sqrt_enclosure(value: F) -> tuple[F, F]:
    scaled = (value.numerator << 256) // value.denominator
    lower = F(isqrt(scaled), 1 << 128)
    upper = lower if lower**2 == value else lower + F(1, 1 << 128)
    assert lower**2 <= value <= upper**2
    return lower, upper


@pytest.mark.parametrize("index", range(11))
def test_full_moments_match_independent_beta_identity(index: int) -> None:
    value = full_moments(8)[index]
    if index % 2:
        assert value.value == Interval.point(0)
    else:
        half = index // 2
        coefficient = F(comb(2 * half, half), 2 * 4**half * (half + 1))
        expected = pi_bounds() * coefficient
        assert (
            value.value.lower <= expected.lower <= expected.upper <= value.value.upper
        )
    assert all(bound == Interval.point(0) for bound in value.coefficients[1:])


@pytest.mark.parametrize("coordinate", [F(0), F(1, 3), F(1)])
def test_partial_moment_derivatives_follow_fundamental_theorem(coordinate: F) -> None:
    theta = Jet.variable(Interval.point(coordinate), 8) * pi_bounds()
    sine, cosine = theta.sin_cos()
    moments = partial_moments(theta, sine, cosine)
    for degree, value in enumerate(moments):
        expected = pi_bounds() * sine.value**2 * cosine.value**degree
        derivative = value.coefficients[1]
        assert derivative.lower <= expected.upper and expected.lower <= derivative.upper
        assert derivative.width < F(1, 10**20)


@pytest.mark.parametrize("q", [F(-1, 2), F(-1, 100), F(0), F(1, 100), F(1, 2)])
def test_binomial_remainder_bounds_independent_exact_root_value(q: F) -> None:
    polynomial = sum(
        (
            coefficient * q**degree
            for degree, coefficient in enumerate(binomial_coefficients())
        ),
        F(0),
    )
    lower, upper = sqrt_enclosure(1 + q)
    truth = (1 / upper**3, 1 / lower**3)
    error = series_remainder(abs(q))
    assert polynomial - error <= truth[0] <= truth[1] <= polynomial + error


@pytest.mark.parametrize("q", [F(-1, 10), F(14, 15), F(1)])
def test_unproved_series_radius_is_refused(q: F) -> None:
    with pytest.raises(ValueError, match="14/15"):
        series_remainder(q)


def test_normalization_retains_precise_values_at_large_physical_anchor_scales() -> None:
    model = Geometry(F(3, 5), F(80), F(100000), (F(20000), F(0)), (F(300000), F(0)))
    contraction = AngleContraction(model)
    distance = F(50000)
    moments = (Jet.constant(1, 0),) + (Jet.constant(0, 0),) * 10
    value = contraction.integrate_angles(Jet.constant(distance, 0), moments).value
    denominator = (
        4 * (distance**2 + model.receiver**2 - model.dot) ** 2
        + model.norm_sum * model.norm_difference
    )
    numerator = -2 * model.delta * model.norm_difference
    lower, upper = sqrt_enclosure(denominator)
    truth = sorted((numerator / lower**3, numerator / upper**3))
    assert value.lower <= truth[0] <= truth[1] <= value.upper
    assert value.width < F(1, 10**24)
    naive = numerator / Interval.point(denominator).root(2) ** 3
    assert value.width * 10**12 < naive.width
    assert value.width * (model.outer + model.receiver) ** 2 < F(1, 10**9) / 256


@pytest.mark.parametrize("antipodal", [False, True])
def test_equal_norm_shortcut_is_exact_only_for_J(antipodal: bool) -> None:
    first = (F(100), F(0))
    second = (F(-100), F(0)) if antipodal else (F(0), F(100))
    model = Geometry(F(1, 2), F(1), F(4), first, second)
    partition = AnglePartition.build(model)
    assert partition.contraction.q_bound == partition.contraction.remainder_radius == 0
    for domain in partition.domains:
        result = domain.evaluate((Jet.variable(Interval(F(0), F(1)), 8),))
        assert all(bound == Interval.point(0) for bound in result.coefficients)
    assert model.contact_survival(Jet.constant(F(1, 2), 0)).value.lower > 0
    with pytest.raises(ValueError, match="geometry"):
        Geometry(F(1, 2), F(1), F(4), first, first)


def test_new_guards_do_not_change_original_geometry_admission() -> None:
    unsupported = geometry(outer=F(3))
    assert unsupported.outer == 3 * unsupported.receiver
    with pytest.raises(ValueError, match="L>3R"):
        AngleContraction(unsupported)
    valid_original = Geometry(F(1), F(1), F(4), (F(1), F(0)), (F(2), F(0)))
    with pytest.raises(ValueError, match="q<14/15"):
        AngleContraction(valid_original)


def test_contact_map_retains_zero_endpoint_through_eighth_derivatives() -> None:
    domain = AnglePartition.build(geometry()).domains[0]
    result = domain.evaluate((Jet.variable(Interval.point(0), 8),))
    assert all(
        bound.lower <= 0 <= bound.upper and bound.width < F(1, 10**20)
        for bound in result.coefficients
    )
    mapped = domain.map(Jet.constant(0, 0))
    assert mapped.distance.value == mapped.distance_power.value == Interval.point(0)


def test_outer_cap_keeps_negative_odd_moments_and_boundary_closure() -> None:
    domain = AnglePartition.build(geometry()).domains[-1]
    mapped = domain.map(Jet.constant(F(1, 2), 0))
    assert all(value.value.upper < 0 for value in mapped.moments[1::2])
    for point in (F(0), F(1)):
        endpoint = domain.map(Jet.constant(point, 0))
        assert endpoint.measure.value.lower <= 0 <= endpoint.measure.value.upper
    result = domain.evaluate((Jet.variable(Interval.point(1), 3),))
    assert all(
        bound.lower <= 0 <= bound.upper and bound.width < F(1, 10**20)
        for bound in result.coefficients
    )


@pytest.mark.parametrize("power", [0, 1, 2])
def test_all_cap_measures_enclose_independent_polynomial_annulus_integral(
    power: int,
) -> None:
    model = geometry(coefficient=F(0))
    partition = AnglePartition.build(model)
    total = Interval.point(0)
    budget = WorkBudget(wall_seconds=180)
    for domain in partition.domains:

        def integrand(
            arguments: tuple[Jet, ...], selected: AngleDomain = domain
        ) -> Jet:
            mapped = selected.map(arguments[0])
            base = model.receiver**2 + mapped.distance**2
            offset = 2 * model.receiver * mapped.distance
            angular = sum(
                (
                    comb(power, degree)
                    * base ** (power - degree)
                    * offset**degree
                    * mapped.moments[degree]
                    for degree in range(power + 1)
                ),
                Jet.constant(0, arguments[0].order),
            )
            return mapped.measure * angular

        for index in range(32):
            panel = positive_panel(
                integrand,
                ((F(index, 32), F(index + 1, 32)),),
                budget,
                rule=SEVEN_NODE_RULE,
            )
            total += panel.enclosure
    exact = (model.outer ** (2 * power + 2) - model.receiver ** (2 * power + 2)) / (
        2 * power + 2
    )
    assert total.lower <= exact <= total.upper
    assert total.width < F(1, 100)


def test_domain_population_cannot_drop_reorder_or_foreign_bind_support() -> None:
    partition = AnglePartition.build(geometry(outer=F(1000)))
    assert (
        partition.domains[0].kind == "inner_cap"
        and partition.domains[-1].kind == "outer_cap"
    )
    bands = [domain.distance_band for domain in partition.domains[1:-1]]
    assert bands[0] is not None and bands[0][0] == 2 * partition.geometry.receiver
    assert (
        bands[-1] is not None
        and bands[-1][1] == partition.geometry.outer - partition.geometry.receiver
    )
    for left, right in zip(bands, bands[1:], strict=False):
        assert left is not None and right is not None and left[1] == right[0]
    with pytest.raises(ValueError, match="incomplete"):
        AnglePartition(partition.contraction, partition.domains[:-1])
    with pytest.raises(ValueError, match="reordered"):
        AnglePartition(partition.contraction, tuple(reversed(partition.domains)))
