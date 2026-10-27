"""Independent exact identities and small synthetic checks of continuous certificates."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction as Q
import json
from math import comb, factorial, prod
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.arithmetic import (
    Interval,
    Jet,
    cos_bounds,
    exp_bounds,
    pi_bounds,
    sin_bounds,
    sinc_derivative,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.certificates import (
    encoded_certificates,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.coefficients import (
    certify,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.kernel import (
    Geometry,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.quadrature import (
    IntegralResult,
    ResourceRefusal,
    WorkBudget,
    integrate,
    simpson_panel,
)

UNIT = ((Q(0), Q(1)),)


def encloses(actual: Interval, lower: Q, upper: Q | None = None) -> None:
    assert actual.lower <= lower
    assert actual.upper >= (lower if upper is None else upper)


def arctangent_alternating(x: Q) -> tuple[Q, Q]:
    # The two-angle identity below is independent of Machin's 1/5,1/239 identity.
    total = sum(((-1) ** n * x ** (2 * n + 1) / (2 * n + 1) for n in range(120)), Q(0))
    following = x**241 / 241
    return total, total + following


def independent_pi() -> tuple[Q, Q]:
    a, b = arctangent_alternating(Q(1, 2)), arctangent_alternating(Q(1, 3))
    # tan(atan(1/2)+atan(1/3))=1, and both positive angles sum below pi/2.
    return 4 * (a[0] + b[0]), 4 * (a[1] + b[1])


def alternating_trig(x: Q, cosine: bool) -> tuple[Q, Q]:
    offset = 0 if cosine else 1
    total = sum(
        (
            (-1) ** n * x ** (2 * n + offset) / factorial(2 * n + offset)
            for n in range(40)
        ),
        Q(0),
    )
    following = x ** (80 + offset) / factorial(80 + offset)
    return min(total, total + following), max(total, total + following)


def independent_exp(x: Q) -> tuple[Q, Q]:
    total = sum((x**n / factorial(n) for n in range(81)), Q(0))
    # Absolute tail terms decrease geometrically from term81 with ratio <=|x|/82.
    radius = abs(x) ** 81 / factorial(81) / (1 - abs(x) / 82)
    return total - radius, total + radius


@pytest.mark.parametrize("degree", [2, 8, 16])
@pytest.mark.parametrize("number", [Q(0), Q(1, 3), Q(2), Q(65537, 19)])
def test_roots_have_exact_power_certificates(degree: int, number: Q) -> None:
    actual = Interval.point(number).root(degree)
    assert 0 <= actual.lower <= actual.upper
    assert actual.lower**degree <= number <= actual.upper**degree
    interval = Interval(Q(1, 7), Q(9, 4)).root(degree)
    assert interval.lower**degree <= Q(1, 7)
    assert interval.upper**degree >= Q(9, 4)


def test_machin_pi_is_enclosed_by_an_independent_two_angle_identity() -> None:
    reference = independent_pi()
    actual = pi_bounds()
    encloses(actual, *reference)
    assert actual.width < Q(1, 10**27)
    assert Q(3) < reference[0] < reference[1] < Q(22, 7)


@pytest.mark.parametrize("x", [Q(0), Q(1, 3), Q(-1, 3), Q(3, 2), Q(-3, 2)])
def test_trigonometric_bounds_against_signed_alternating_remainders(x: Q) -> None:
    encloses(sin_bounds(Interval.point(x)), *alternating_trig(x, False))
    encloses(cos_bounds(Interval.point(x)), *alternating_trig(x, True))
    assert sin_bounds(Interval.point(x)).width < Q(1, 10**25)


@pytest.mark.parametrize("order", range(5))
def test_sinc_entire_derivatives_and_nonzero_quotient_identity(order: int) -> None:
    origin = Q(0) if order % 2 else Q((-1) ** (order // 2), order + 1)
    encloses(sinc_derivative(Interval.point(0), order), origin)
    x = Q(1, 3)
    # Differentiating sin(x)/x directly gives these independent linear forms.
    coefficients = [
        (1 / x, Q(0)),
        (-1 / x**2, 1 / x),
        (-1 / x + 2 / x**3, -2 / x**2),
        (3 / x**2 - 6 / x**4, -1 / x + 6 / x**3),
        (1 / x - 12 / x**3 + 24 / x**5, 4 / x**2 - 24 / x**4),
    ]
    sine, cosine = alternating_trig(x, False), alternating_trig(x, True)
    a, b = coefficients[order]
    candidates = [a * s + b * c for s in sine for c in cosine]
    encloses(
        sinc_derivative(Interval.point(x), order), min(candidates), max(candidates)
    )


@pytest.mark.parametrize("x", [Q(0), Q(1, 8), Q(-1, 3), Q(2)])
def test_exponential_enclosures_against_geometric_series_tail(x: Q) -> None:
    actual = exp_bounds(Interval.point(x))
    encloses(actual, *independent_exp(x))
    assert actual.lower > 0
    assert actual.width < Q(1, 10**24)


def binomial(alpha: Q, n: int) -> Q:
    result = Q(1)
    for k in range(n):
        result *= (alpha - k) / (k + 1)
    return result


def polynomial_product(a: list[Q], b: list[Q], degree: int) -> list[Q]:
    return [
        sum((a[k] * b[n - k] for k in range(len(a)) if 0 <= n - k < len(b)), Q(0))
        for n in range(degree + 1)
    ]


def test_analytic_jets_against_binomial_and_complex_exponential_coefficients() -> None:
    x = Jet.variable(Interval.point(0))
    root = (1 + x).root(8)
    reciprocal = (1 - x).reciprocal()
    combined = x.exp() * x.sin_cos()[0]
    sine_cardinal = x.sinc()
    real, imaginary = 1, 0
    for n in range(5):
        encloses(root.coefficients[n], binomial(Q(1, 8), n))
        encloses(reciprocal.coefficients[n], Q(1))
        encloses(combined.coefficients[n], Q(imaginary, factorial(n)))
        encloses(
            sine_cardinal.coefficients[n],
            Q(0) if n % 2 else Q((-1) ** (n // 2), factorial(n + 1)),
        )
        real, imaginary = real - imaginary, real + imaginary


def test_jet_bounds_cover_polynomial_derivatives_across_an_interval() -> None:
    actual = Jet.variable(Interval(Q(-1), Q(2))) ** 5
    for n, coefficient in enumerate(actual.coefficients):
        power = 5 - n
        samples = [Q(-1) ** power, Q(2) ** power]
        if power % 2 == 0:
            samples.append(Q(0))
        encloses(coefficient, comb(5, n) * min(samples), comb(5, n) * max(samples))


def test_angular_derivative_jet_encloses_higher_exact_binomial_coefficients() -> None:
    geometry = Geometry(Q(3, 5), Q(1), Q(3), (Q(1), Q(0)), (Q(2), Q(0)))
    encloses(geometry.angular(Jet.constant(2, 0)).value, Q(8, 15))
    actual = geometry.angular_derivative(Jet.variable(Interval.point(2)))
    # At r=2+z, D²=25+64z+80z²+32z³+4z⁴ and h'=-6r/D³.
    w = [Q(0), Q(64, 25), Q(80, 25), Q(32, 25), Q(4, 25)]
    power, series = [Q(1)], [Q(0)] * 5
    for n in range(5):
        coefficient = binomial(Q(-3, 2), n)
        for j, value in enumerate(power):
            series[j] += coefficient * value
        power = polynomial_product(power, w, 4)
    expected = polynomial_product([Q(-12, 125), Q(-6, 125)], series, 4)
    for actual_coefficient, exact in zip(actual.coefficients, expected, strict=True):
        encloses(actual_coefficient, exact)
    assert expected[4] != 0


def test_simpson_error_is_a_radius_and_tensor_requires_both_pure_derivatives() -> None:
    panel = simpson_panel(lambda args: args[0] ** 4, UNIT, WorkBudget())
    assert panel.error_radius == Q(1, 120)
    encloses(panel.node_sum, Q(5, 24))
    encloses(panel.enclosure, Q(1, 5))
    assert panel.enclosure.width >= Q(1, 60)
    tensor = simpson_panel(
        lambda args: args[0] ** 4 + args[1] ** 4, UNIT * 2, WorkBudget()
    )
    assert tensor.directional_radii == (Q(1, 120), Q(1, 120))
    assert tensor.error_radius == Q(1, 60)
    encloses(tensor.node_sum, Q(5, 12))
    encloses(tensor.enclosure, Q(2, 5))
    assert tensor.enclosure.width >= Q(1, 30)


def test_simpson_is_exact_for_separately_cubic_polynomials() -> None:
    univariate = simpson_panel(
        lambda args: args[0] ** 3 - 2 * args[0] + 1,
        ((Q(-1, 2), Q(3, 2)),),
        WorkBudget(),
    )
    assert univariate.error_radius == 0
    encloses(univariate.enclosure, Q(5, 4))
    tensor = simpson_panel(
        lambda args: args[0] ** 3 * args[1] ** 3 + args[0] ** 2 * args[1] - 7,
        UNIT * 2,
        WorkBudget(),
    )
    assert tensor.error_radius == 0
    encloses(tensor.enclosure, Q(-325, 48))


def check_partition(result: IntegralResult, dimensions: int) -> None:
    boxes = [panel.box for panel in result.panels]
    assert boxes
    assert all(
        len(box) == dimensions and all(0 <= a < b <= 1 for a, b in box) for box in boxes
    )
    volume = sum((prod(b - a for a, b in box) for box in boxes), Q(0))
    assert volume == 1
    for i, first in enumerate(boxes):
        for second in boxes[i + 1 :]:
            assert any(
                min(b, d) <= max(a, c)
                for (a, b), (c, d) in zip(first, second, strict=True)
            )
    lower = sum((panel.enclosure.lower for panel in result.panels), Q(0))
    upper = sum((panel.enclosure.upper for panel in result.panels), Q(0))
    assert result.enclosure == Interval(lower, upper)


def test_adaptive_polynomial_leaves_cover_the_whole_domain() -> None:
    result = integrate(
        lambda args: args[0] ** 4 + args[1] ** 4,
        2,
        Q(1, 1000),
        WorkBudget(max_leaves=128),
    )
    assert result.status == "certified_width"
    assert len(result.panels) > 1
    check_partition(result, 2)
    encloses(result.enclosure, Q(2, 5))


def test_second_child_resource_failure_retains_the_complete_parent() -> None:
    budget = WorkBudget(max_attempts=2, max_nodes=6)
    result = integrate(lambda args: args[0] ** 4, 1, Q(1, 10**9), budget)
    assert result.status == "refuse_unresolved"
    assert result.refusal == "attempt_or_node_ceiling"
    assert len(result.panels) == 1 and budget.completed_nodes == 6
    check_partition(result, 1)
    encloses(result.enclosure, Q(1, 5))


def synthetic_geometry() -> Geometry:
    return Geometry(Q(3, 5), Q(1), Q(2), (Q(3), Q(1)), (Q(-5), Q(2)))


def decimal_value(value: Q) -> Decimal:
    return Decimal(value.numerator) / Decimal(value.denominator)


def decimal_sine(value: Decimal) -> Decimal:
    term, total = value, value
    for n in range(1, 100):
        term *= -value * value / Decimal((2 * n) * (2 * n + 1))
        total += term
        if abs(term) < Decimal("1e-85"):
            return total
    raise AssertionError("small diagnostic sine did not terminate")


def test_duffy_patches_match_original_geometry_at_nonzero_a_unequal_anchors() -> None:
    # Decimal comparisons are correspondence diagnostics, not rigorous references.
    geometry = synthetic_geometry()
    for patch in (1, 2):
        for t, u in ((Q(1, 2), Q(1, 3)), (Q(3, 4), Q(2, 5))):
            actual = geometry.triangle(
                Jet.constant(t, 0), Jet.constant(u, 0), patch
            ).value
            assert actual.upper < 0
            with localcontext() as context:
                context.prec = 90
                pi_interval = independent_pi()
                pi = decimal_value(sum(pi_interval, Q(0)) / 2)
                td, ud = decimal_value(t), decimal_value(u)
                r0, c = (
                    decimal_value(geometry.receiver),
                    decimal_value(geometry.difference),
                )
                x, y = (td**8, td**8 * ud) if patch == 1 else (td**8 * ud, td**8)
                r, phi = r0 + c * x, pi * y
                d2 = (r - r0) ** 2 + 4 * r * r0 * decimal_sine(phi / 2) ** 2
                d_power = d2
                for _ in range(4):
                    d_power = d_power.sqrt()
                radial_density = 2 * r * r * decimal_sine(phi) ** 2 / (pi * d2)
                angular_derivative = (
                    -2
                    * decimal_value(geometry.delta * geometry.norm_difference)
                    * r
                    / (
                        4 * (r * r - decimal_value(geometry.dot)) ** 2
                        + decimal_value(geometry.norm_sum * geometry.norm_difference)
                    )
                    ** Decimal("1.5")
                )
                reference = (
                    angular_derivative
                    * (-decimal_value(geometry.coefficient) * d_power).exp()
                    * radial_density
                    * 8
                    * c
                    * pi
                    * td**15
                )
                midpoint = decimal_value((actual.lower + actual.upper) / 2)
                assert abs(midpoint - reference) <= decimal_value(
                    actual.width / 2
                ) + Decimal("1e-60")
    for patch in (1, 2):
        assert geometry.triangle(
            Jet.constant(0, 0), Jet.constant(Q(1, 3), 0), patch
        ).value == Interval.point(0)
    assert geometry.contact_survival(Jet.constant(0, 0)).value == Interval.point(0)
    assert geometry.contact_survival(Jet.constant(Q(1, 2), 0)).value.lower > 0
    assert geometry.outer_survival(Jet.constant(Q(1, 2), 0)).value.lower > 0
    encloses(
        geometry.triangle(Jet.constant(1, 0), Jet.constant(Q(1, 3), 0), 2).value, Q(0)
    )


def check_serialized_certificate(value: dict[str, Any]) -> None:
    for integral in value["integrals"]:
        lower, upper = Q(0), Q(0)
        for leaf in integral["leaves"]:
            radius = Q(leaf["error_radius"])
            assert radius >= 0
            assert sum(map(Q, leaf["directional_radii"]), Q(0)) == radius
            a, b = map(Q, leaf["node_sum"])
            lower += a - radius
            upper += b + radius
        reported_lower, reported_upper = map(Q, integral["bounds"])
        assert reported_lower <= lower <= upper <= reported_upper
    k, b1, b2 = (
        list(map(Q, value["coefficient_bounds"][key])) for key in ("K", "B1", "B2")
    )
    assert b2[0] <= k[0] - b1[1] and b2[1] >= k[1] - b1[0]


def test_four_initial_domains_complementarity_and_aggregate_certificate_cap() -> None:
    budget = WorkBudget(max_leaves=4, max_attempts=4, max_nodes=24, max_queue=4)
    result = certify(synthetic_geometry(), budget)
    assert result.status == "refuse_unresolved"
    assert len(result.integrals) == 4 and budget.completed_nodes == 24
    for dimensions, integral in zip((1, 1, 2, 2), result.integrals, strict=True):
        check_partition(integral, dimensions)
    assert result.second.lower <= result.homogeneous.lower - result.first.upper
    assert result.second.upper >= result.homogeneous.upper - result.first.lower
    encoded = encoded_certificates([result])
    parsed = json.loads(encoded)[0]
    check_serialized_certificate(parsed)
    damaged = deepcopy(parsed)
    damaged["integrals"][0]["bounds"] = ["999999", "999999"]
    with pytest.raises(AssertionError):
        check_serialized_certificate(damaged)
    with pytest.raises(ResourceRefusal, match="certificate_byte_ceiling"):
        encoded_certificates([result, result], maximum_bytes=len(encoded))


@pytest.mark.parametrize("bad", [True, 0.5, float("nan"), float("inf")])
def test_interval_boundary_refuses_inexact_or_boolean_values(bad: object) -> None:
    with pytest.raises(TypeError):
        Interval(cast(Q, bad), Q(1))
    with pytest.raises(TypeError):
        Interval.point(cast(Q, bad))


def test_immutable_exact_jet_anchor_and_singular_boundaries() -> None:
    with pytest.raises(TypeError):
        Jet(cast(tuple[Interval, ...], [Interval.point(0)]))
    with pytest.raises(ValueError):
        Geometry(Q(1), Q(1), Q(2), cast(tuple[Q, Q], [Q(1), Q(0)]), (Q(2), Q(0)))
    with pytest.raises(ValueError):
        Interval(Q(-1), Q(1)).reciprocal()
    with pytest.raises(ValueError):
        Jet.variable(Interval(Q(0), Q(1))).root(8)
    with pytest.raises(ValueError):
        simpson_panel(lambda args: args[0], ((Q(1), Q(0)),), WorkBudget())


@pytest.mark.parametrize(
    "bad", [Interval(Q(-1, 2), Q(1, 2)), Interval(Q(1, 4), Q(5, 4))]
)
def test_unit_coordinate_assumptions_are_enforced_before_kernel_bounds(
    bad: Interval,
) -> None:
    geometry = synthetic_geometry()
    value = Jet.variable(bad)
    with pytest.raises(ValueError):
        geometry.contact_survival(value)
    with pytest.raises(ValueError):
        geometry.outer_survival(value)
    for patch in (1, 2):
        with pytest.raises(ValueError):
            geometry.triangle(value, Jet.constant(Q(1, 2)), patch)
        with pytest.raises(ValueError):
            geometry.triangle(Jet.constant(Q(1, 2)), value, patch)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_leaves": 4097},
        {"max_attempts": 8192},
        {"max_nodes": 73720},
        {"max_queue": 4097},
        {"wall_seconds": 0},
        {"wall_seconds": 181},
        {"max_leaves": True},
    ],
)
def test_work_limits_cannot_exceed_the_prespecified_finite_bounds(
    kwargs: dict[str, Any],
) -> None:
    with pytest.raises((ValueError, TypeError)):
        WorkBudget(**kwargs)


@pytest.mark.parametrize(
    (
        "subintervals",
        "integer_weights",
        "weight_denominator",
        "order",
        "error_denominator",
    ),
    [
        (4, (7, 32, 12, 32, 7), 90, 6, 1935360),
        (6, (41, 216, 27, 272, 27, 216, 41), 840, 8, 1567641600),
    ],
)
def test_positive_closed_rules_have_exact_signed_peano_remainders(
    subintervals: int,
    integer_weights: tuple[int, ...],
    weight_denominator: int,
    order: int,
    error_denominator: int,
) -> None:
    # These prove prospective rules; production remains the existing Simpson method.
    nodes = [Q(j, subintervals) for j in range(subintervals + 1)]
    weights = [Q(value, weight_denominator) for value in integer_weights]
    assert all(weight > 0 for weight in weights) and sum(weights) == 1
    for power in range(order):
        assert sum(
            (weight * node**power for weight, node in zip(weights, nodes, strict=True)),
            Q(0),
        ) == Q(1, power + 1)
    kernel_integral = Q(0)
    for cell in range(subintervals):
        a, length = Q(cell, subintervals), Q(1, subintervals)
        # Q-I Peano kernel: sum w*(node-s)_+^(p-1)/(p-1)! -(1-s)^p/p!.
        power_coefficients = [Q(0)] * (order + 1)
        for node, weight in zip(nodes, weights, strict=True):
            if node > a:
                for power in range(order):
                    power_coefficients[power] += (
                        weight
                        * comb(order - 1, power)
                        * (node - a) ** (order - 1 - power)
                        * (-length) ** power
                        / factorial(order - 1)
                    )
        for power in range(order + 1):
            power_coefficients[power] -= (
                comb(order, power)
                * (1 - a) ** (order - power)
                * (-length) ** power
                / factorial(order)
            )
        bernstein = [
            sum(
                (
                    power_coefficients[j] * Q(comb(k, j), comb(order, j))
                    for j in range(k + 1)
                ),
                Q(0),
            )
            for k in range(order + 1)
        ]
        assert all(coefficient >= 0 for coefficient in bernstein)
        kernel_integral += length * sum(
            (value / (power + 1) for power, value in enumerate(power_coefficients)),
            Q(0),
        )
    assert kernel_integral == Q(1, error_denominator)
    assert (
        sum(
            (weight * node**order for weight, node in zip(weights, nodes, strict=True)),
            Q(0),
        )
        - Q(1, order + 1)
        == factorial(order) * kernel_integral
    )
