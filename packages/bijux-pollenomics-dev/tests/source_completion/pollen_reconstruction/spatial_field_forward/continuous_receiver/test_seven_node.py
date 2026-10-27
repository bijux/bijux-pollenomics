"""Reviewed positive seven-node moments, eighth-order error and rule identity."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction
import json
import math

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.arithmetic import (
    MAX_ORDER,
    ORDER,
    Interval,
    Jet,
    sinc_derivative,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.certificates import (
    certificate,
    encoded_certificates,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.coefficients import (
    CoefficientResult,
    certify,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.kernel import (
    Geometry,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.quadrature import (
    SEVEN_NODE_RULE,
    SIMPSON_RULE,
    IntegralResult,
    ResourceRefusal,
    WorkBudget,
    integrate,
    positive_panel,
    rule_definition,
    simpson_panel,
)

UNIT = ((Fraction(0), Fraction(1)),)


def decimal(value: Fraction) -> Decimal:
    return Decimal(value.numerator) / Decimal(value.denominator)


@pytest.mark.parametrize("degree", range(8))
def test_seven_positive_moments_and_actual_panels_are_exact_through_degree_seven(
    degree: int,
) -> None:
    _, weights, divisor, _ = rule_definition(SEVEN_NODE_RULE)
    assert all(weight > 0 for weight in weights)
    assert sum(weights) == divisor
    exact = sum(
        (
            Fraction(weight, divisor) * Fraction(j, 6) ** degree
            for j, weight in enumerate(weights)
        ),
        Fraction(0),
    )
    assert exact == Fraction(1, degree + 1)
    budget = WorkBudget()
    panel = positive_panel(
        lambda arguments: arguments[0] ** degree, UNIT, budget, rule=SEVEN_NODE_RULE
    )
    assert panel.error_radius == 0
    assert panel.enclosure.lower <= exact <= panel.enclosure.upper
    assert panel.enclosure.width < Fraction(1, 10**23)
    assert budget.nodes == budget.completed_nodes == 7
    assert panel.rule == SEVEN_NODE_RULE


def test_eighth_degree_error_is_radius_and_complete_width_contains_twice_it() -> None:
    panel = positive_panel(
        lambda arguments: arguments[0] ** 8, UNIT, WorkBudget(), rule=SEVEN_NODE_RULE
    )
    radius = Fraction(math.factorial(8), 1567641600)
    assert radius == Fraction(1, 38880)
    assert panel.error_radius == radius
    assert panel.node_sum.lower <= Fraction(1, 9) + radius <= panel.node_sum.upper
    assert panel.enclosure.lower <= Fraction(1, 9) <= panel.enclosure.upper
    assert panel.enclosure.width >= 2 * radius


def test_tensor_positive_error_sums_both_pure_eighth_derivatives() -> None:
    budget = WorkBudget()
    panel = positive_panel(
        lambda arguments: arguments[0] ** 8 + arguments[1] ** 8,
        UNIT * 2,
        budget,
        rule=SEVEN_NODE_RULE,
    )
    assert panel.directional_radii == (Fraction(1, 38880),) * 2
    assert panel.error_radius == Fraction(1, 19440)
    assert panel.enclosure.width >= Fraction(1, 9720)
    assert panel.enclosure.lower <= Fraction(2, 9) <= panel.enclosure.upper
    assert budget.nodes == budget.completed_nodes == 49


def test_separately_seventh_degree_tensor_needs_no_mixed_derivative_error() -> None:
    panel = positive_panel(
        lambda arguments: arguments[0] ** 7 * arguments[1] ** 7,
        UNIT * 2,
        WorkBudget(),
        rule=SEVEN_NODE_RULE,
    )
    assert panel.error_radius == 0
    assert panel.enclosure.lower <= Fraction(1, 64) <= panel.enclosure.upper


def test_nonunit_tensor_lengths_scale_ninth_order_directional_error() -> None:
    box = ((Fraction(2), Fraction(4)), (Fraction(-1), Fraction(2)))
    panel = positive_panel(
        lambda arguments: arguments[0] ** 8 + arguments[1] ** 8,
        box,
        WorkBudget(),
        rule=SEVEN_NODE_RULE,
    )
    factor = Fraction(math.factorial(8), 1567641600)
    assert panel.directional_radii == (2**9 * 3 * factor, 2 * 3**9 * factor)


def test_default_simpson_panel_and_legacy_certificate_bytes_keep_their_contract() -> (
    None
):
    panel = simpson_panel(lambda arguments: arguments[0] ** 4, UNIT, WorkBudget())
    assert panel.rule == SIMPSON_RULE
    assert panel.node_sum == Interval.outward(Fraction(5, 24), Fraction(5, 24))
    assert panel.error_radius == Fraction(1, 120)
    assert Jet.variable(Interval.point(1)).order == ORDER == 4
    assert MAX_ORDER == 8
    zero = Interval.point(0)
    integral = IntegralResult(zero, (), "controlled", None)
    result = CoefficientResult(
        (integral,) * 4, zero, zero, zero, (zero, zero), "controlled"
    )
    legacy = {
        "schema_version": "continuous-receiver-coefficient-certificate.v1",
        "status": "controlled",
        "coefficient_bounds": {"K": ["0", "0"], "B1": ["0", "0"], "B2": ["0", "0"]},
        "endpoint_products": [["0", "0"], ["0", "0"]],
        "integrals": [
            {
                "status": "controlled",
                "refusal": None,
                "bounds": ["0", "0"],
                "leaves": [],
            }
        ]
        * 4,
    }
    assert encoded_certificates([result]) == json.dumps(
        [legacy], sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def test_new_rule_certificate_is_explicit_at_result_integral_and_leaf() -> None:
    panel = positive_panel(
        lambda arguments: arguments[0], UNIT, WorkBudget(), rule=SEVEN_NODE_RULE
    )
    integral = IntegralResult(
        panel.enclosure, (panel,), "controlled", None, SEVEN_NODE_RULE
    )
    zero = Interval.point(0)
    result = CoefficientResult(
        (integral,) * 4, zero, zero, zero, (zero, zero), "controlled", SEVEN_NODE_RULE
    )
    payload = json.loads(encoded_certificates([result]))[0]
    assert payload["schema_version"] == "continuous-receiver-coefficient-certificate.v2"
    assert payload["quadrature_rule"] == SEVEN_NODE_RULE
    assert all(
        row["quadrature_rule"] == SEVEN_NODE_RULE
        and row["leaves"][0]["quadrature_rule"] == SEVEN_NODE_RULE
        for row in payload["integrals"]
    )


def test_unknown_mixed_rules_and_wrong_derivative_order_fail_before_admission() -> None:
    budget = WorkBudget()
    with pytest.raises(ValueError, match="Unknown"):
        positive_panel(lambda arguments: arguments[0], UNIT, budget, rule="unreviewed")
    assert budget.attempts == budget.nodes == 0
    panel = positive_panel(
        lambda arguments: arguments[0], UNIT, WorkBudget(), rule=SEVEN_NODE_RULE
    )
    with pytest.raises(ValueError, match="Mixed"):
        integrate(
            lambda arguments: arguments[0], 1, Fraction(1, 100), budget, initial=panel
        )
    with pytest.raises(ValueError, match="Mixed"):
        IntegralResult(panel.enclosure, (panel,), "controlled", None)
    with pytest.raises(ValueError, match="Unknown"):
        replace(panel, rule="unreviewed")
    integral = IntegralResult(
        panel.enclosure, (panel,), "controlled", None, SEVEN_NODE_RULE
    )
    zero = Interval.point(0)
    with pytest.raises(ValueError, match="Mixed"):
        CoefficientResult((integral,), zero, zero, zero, (zero, zero), "controlled")
    with pytest.raises(ValueError, match="derivative order"):
        positive_panel(
            lambda arguments: Jet.constant(1), UNIT, WorkBudget(), rule=SEVEN_NODE_RULE
        )


def test_same_node_ceiling_refuses_seven_by_seven_before_any_evaluation() -> None:
    budget = WorkBudget(max_nodes=48)
    with pytest.raises(ResourceRefusal, match="node_ceiling"):
        positive_panel(
            lambda arguments: arguments[0], UNIT * 2, budget, rule=SEVEN_NODE_RULE
        )
    assert budget.nodes == budget.completed_nodes == budget.attempts == 0
    budget = WorkBudget(max_attempts=2)
    result = integrate(
        lambda arguments: arguments[0] ** 8,
        1,
        Fraction(1, 10**15),
        budget,
        rule=SEVEN_NODE_RULE,
    )
    assert result.status == "refuse_unresolved" and len(result.panels) == 1
    assert result.rule == SEVEN_NODE_RULE
    assert budget.nodes == budget.completed_nodes == 14
    assert result.enclosure.lower <= Fraction(1, 9) <= result.enclosure.upper


def test_eighth_order_primitives_and_entire_sinc_coefficients() -> None:
    variable = Jet.variable(Interval.point(1), 8)
    root, exponential = variable.root(16), variable.exp()
    coefficient = Fraction(1)
    with localcontext() as context:
        context.prec = 100
        for n in range(9):
            if n:
                coefficient *= (Fraction(1, 16) - (n - 1)) / n
            assert (
                root.coefficients[n].lower <= coefficient <= root.coefficients[n].upper
            )
            expected = Decimal(1).exp() / math.factorial(n)
            assert (
                decimal(exponential.coefficients[n].lower)
                <= expected
                <= decimal(exponential.coefficients[n].upper)
            )
    sinc = Jet.variable(Interval.point(0), 8).sinc()
    for n, bounds in enumerate(sinc.coefficients):
        exact_coefficient = (
            Fraction((-1) ** (n // 2), math.factorial(n + 1))
            if n % 2 == 0
            else Fraction(0)
        )
        assert bounds.lower <= exact_coefficient <= bounds.upper
    for n in (5, 6, 7, 8):
        expected_derivative = (
            Fraction((-1) ** (n // 2), n + 1) if n % 2 == 0 else Fraction(0)
        )
        direct = sinc_derivative(Interval.point(0), n)
        assert direct.lower <= expected_derivative <= direct.upper
    with pytest.raises(ValueError, match="order"):
        Jet.constant(1, 9)
    with pytest.raises(ValueError, match="order"):
        sinc_derivative(Interval.point(0), 9)


def test_h_prime_eighth_jet_matches_independent_underlying_ninth_series() -> None:
    # For anchors (0,0),(2,0), h(r)=1-r²/(2*sqrt(r^4+4)). Expand
    # (1+z)^4+4 around r=1 by exact formal binomial products, not Jets.
    polynomial = [
        Fraction(0),
        Fraction(4, 5),
        Fraction(6, 5),
        Fraction(4, 5),
        Fraction(1, 5),
    ]
    power = [Fraction(1)] + [Fraction(0)] * 9
    series = [Fraction(0)] * 10
    binomial = Fraction(1)
    for k in range(10):
        for n in range(10):
            series[n] += binomial * power[n]
        power = [
            sum(
                (
                    power[j] * polynomial[n - j]
                    for j in range(n + 1)
                    if n - j < len(polynomial)
                ),
                Fraction(0),
            )
            for n in range(10)
        ]
        binomial *= (Fraction(-1, 2) - k) / (k + 1)
    factor = -Fraction(9, 2) * (series[9] + 2 * series[8] + series[7])
    model = Geometry(
        Fraction(3, 5),
        Fraction(1),
        Fraction(17),
        (Fraction(0), Fraction(0)),
        (Fraction(2), Fraction(0)),
    )
    derivative = model.angular_derivative(
        Jet.variable(Interval.point(1), 8)
    ).coefficients[8]
    with localcontext() as context:
        context.prec = 100
        expected = decimal(factor) / Decimal(5).sqrt()
        assert decimal(derivative.lower) <= expected <= decimal(derivative.upper)


def test_source_free_four_domain_new_rule_refusal_keeps_all_cases_and_node_charge() -> (
    None
):
    model = Geometry(
        Fraction(3, 5),
        Fraction(1),
        Fraction(17),
        (Fraction(4), Fraction(1)),
        (Fraction(-7), Fraction(3)),
    )
    budget = WorkBudget(max_attempts=4)
    result = certify(model, budget, rule=SEVEN_NODE_RULE)
    assert result.status == "refuse_unresolved"
    assert result.rule == SEVEN_NODE_RULE
    assert len(result.integrals) == 4
    assert all(len(integral.panels) == 1 for integral in result.integrals)
    assert budget.nodes == budget.completed_nodes == 7 + 7 + 49 + 49
    assert certificate(result)["quadrature_rule"] == SEVEN_NODE_RULE
