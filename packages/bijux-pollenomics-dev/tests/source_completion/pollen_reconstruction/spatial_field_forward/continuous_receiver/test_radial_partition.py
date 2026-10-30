"""Exact coverage, unchanged receiver ownership and conditioned integral controls."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import json
import math

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver import (
    coefficients,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.arithmetic import (
    Interval,
    Jet,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.certificates import (
    encoded_certificates,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.coefficients import (
    Q_WIDTH,
    TRIANGLE_WIDTH,
    certify,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.kernel import (
    Geometry,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.quadrature import (
    SEVEN_NODE_RULE,
    SIMPSON_RULE,
    IntegralResult,
    Integrand,
    Panel,
    ResourceRefusal,
    WorkBudget,
    integrate,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.radial_partition import (
    DYADIC_RADIAL,
    WHOLE_ANNULUS,
    Band,
    RadialDomain,
    RadialPartition,
    radial_bands,
    validate_bands,
)


def geometry(
    outer: Fraction = Fraction(17), coefficient: Fraction = Fraction(3, 5)
) -> Geometry:
    return Geometry(
        coefficient,
        Fraction(1),
        outer,
        (Fraction(4), Fraction(1)),
        (Fraction(-7), Fraction(3)),
    )


@pytest.mark.parametrize(
    "outer,expected",
    [
        (Fraction(2), ((Fraction(1), Fraction(2)),)),
        (Fraction(5, 2), ((Fraction(1), Fraction(2)), (Fraction(2), Fraction(5, 2)))),
        (
            Fraction(4) + Fraction(1, 2**40),
            (
                (Fraction(1), Fraction(2)),
                (Fraction(2), Fraction(4)),
                (Fraction(4), Fraction(4) + Fraction(1, 2**40)),
            ),
        ),
    ],
)
def test_exact_band_boundaries_and_tiny_final_band_are_never_rounded_away(
    outer: Fraction, expected: tuple[tuple[Fraction, Fraction], ...]
) -> None:
    model = geometry(outer)
    bands = radial_bands(model)
    assert tuple((band.lower, band.upper) for band in bands) == expected
    assert bands[0].lower == model.receiver and bands[-1].upper == model.outer
    assert all(
        left.upper == right.lower
        for left, right in zip(bands[:-1], bands[1:], strict=True)
    )
    assert (
        sum((band.upper - band.lower for band in bands), Fraction(0))
        == model.outer - model.receiver
    )
    assert all(band.geometry is model for band in bands)


def test_maximum_band_count_refuses_uncovered_tail_before_any_integrand_work() -> None:
    assert len(radial_bands(geometry(Fraction(2048)))) == 11
    model = geometry(Fraction(2048) + Fraction(1, 2**40))
    budget = WorkBudget()
    with pytest.raises(ResourceRefusal, match="uncovered_tail"):
        certify(model, budget, rule=SEVEN_NODE_RULE, partition=DYADIC_RADIAL)
    assert budget.nodes == budget.attempts == budget.leaves == 0


def test_missing_overlap_reordering_and_foreign_ownership_are_closed_failures() -> None:
    model = geometry()
    bands = radial_bands(model)
    foreign = replace(model, coefficient=Fraction(4, 5))
    for damaged in (
        bands[:-1],
        bands + (bands[-1],),
        tuple(reversed(bands)),
        radial_bands(foreign),
    ):
        with pytest.raises(ValueError, match="radial bands"):
            validate_bands(model, damaged)
    with pytest.raises(ValueError, match="ownership"):
        Band(model, 1, Fraction(1), Fraction(4))
    with pytest.raises(ValueError, match="first"):
        RadialDomain(bands[1], "contact_triangle", 1)
    with pytest.raises(ValueError, match="noncontact"):
        RadialDomain(bands[0], "regular_band")
    partition = RadialPartition.build(model)
    with pytest.raises(ValueError, match="radial domains"):
        replace(partition, domains=partition.domains[:-1])


@pytest.mark.parametrize("index", [1, 2, 3])
def test_scaled_regular_kernel_matches_literal_unscaled_and_duffy_diagnostics(
    index: int,
) -> None:
    # Binary64 evaluations below are numerical correspondence diagnostics,
    # separate from the exact interval/analytic enclosure claims.
    model = geometry()
    band = radial_bands(model)[index]
    domain = RadialDomain(band, "regular_band")
    s, u = Fraction(1, 3), Fraction(2, 5)
    result = domain.evaluate((Jet.constant(s, 0), Jet.constant(u, 0))).value
    a, b, r0 = float(band.lower), float(band.upper), float(model.receiver)
    radius, phi = a + (b - a) * float(s), math.pi * float(u)
    distance = (radius - r0) ** 2 + 4 * r0 * radius * math.sin(phi / 2) ** 2
    hprime = (
        -2
        * radius
        * float(model.delta * model.norm_difference)
        / (
            4 * (radius**2 - float(model.dot)) ** 2
            + float(model.norm_sum * model.norm_difference)
        )
        ** 1.5
    )
    literal = (
        2
        * (b - a)
        * radius**2
        * hprime
        * math.sin(phi) ** 2
        / distance
        * math.exp(-float(model.coefficient) * distance ** (1 / 16))
    )
    actual = float((result.lower + result.upper) / 2)
    assert math.isclose(actual, literal, abs_tol=1e-13, rel_tol=1e-12)
    x, y = (radius - r0) / float(model.difference), float(u)
    v = max(x, y)
    t, other = Fraction.from_float(v ** (1 / 8)), Fraction.from_float(min(x, y) / v)
    patch = 1 if x >= y else 2
    duffy = model.triangle(Jet.constant(t, 0), Jet.constant(other, 0), patch).value
    diagnostic = (
        float((duffy.lower + duffy.upper) / 2)
        * (b - a)
        / (8 * float(model.difference) * float(t) ** 15)
    )
    assert math.isclose(actual, diagnostic, abs_tol=1e-13, rel_tol=2e-12)


def test_zero_decay_endpoints_and_each_owned_band_match_exact_antiderivative() -> None:
    model = geometry(Fraction(5), Fraction(0))
    result = certify(
        model, WorkBudget(max_attempts=6), rule=SEVEN_NODE_RULE, partition=DYADIC_RADIAL
    )
    assert result.conditioning is not None
    assert all(
        row.enclosure.lower <= 1 <= row.enclosure.upper for row in result.integrals[:2]
    )
    for band in result.conditioning.bands:
        indices = [
            i + 2
            for i, domain in enumerate(result.conditioning.domains)
            if domain.band == band
        ]
        integral = sum(
            (result.integrals[i].enclosure for i in indices), Interval.point(0)
        )
        right = model.angular(Jet.constant(band.upper, 0)).value
        left = model.angular(Jet.constant(band.lower, 0)).value
        difference = right - left
        assert integral.lower <= difference.lower <= difference.upper <= integral.upper
    assert result.homogeneous.lower <= 0 <= result.homogeneous.upper


def test_symmetric_anchors_keep_radial_sum_zero_and_complementary_half_responses() -> (
    None
):
    model = Geometry(
        Fraction(3, 5),
        Fraction(1),
        Fraction(5),
        (Fraction(2), Fraction(1)),
        (Fraction(1), Fraction(2)),
    )
    result = certify(
        model, WorkBudget(max_attempts=6), rule=SEVEN_NODE_RULE, partition=DYADIC_RADIAL
    )
    assert result.radial_sum == Interval.point(0)
    for response in (result.first, result.second):
        half = result.homogeneous / 2
        assert response.lower <= half.lower <= half.upper <= response.upper


def test_all_initial_domains_share_one_global_budget_and_original_receiver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = geometry(Fraction(1025))
    contact_calls: list[Geometry] = []
    outer_calls: list[Geometry] = []
    allocations: list[tuple[int, Fraction]] = []
    contact, outer = Geometry.contact_survival, Geometry.outer_survival
    existing_integrate = integrate

    def tracked_contact(owner: Geometry, argument: Jet) -> Jet:
        contact_calls.append(owner)
        return contact(owner, argument)

    def tracked_outer(owner: Geometry, argument: Jet) -> Jet:
        outer_calls.append(owner)
        return outer(owner, argument)

    def tracked_integrate(
        function: Integrand,
        dimensions: int,
        target_width: Fraction,
        budget: WorkBudget,
        *,
        initial: Panel | None = None,
        rule: str = SIMPSON_RULE,
    ) -> IntegralResult:
        assert budget.attempts == 14 and initial is not None
        allocations.append((dimensions, target_width))
        return existing_integrate(
            function, dimensions, target_width, budget, initial=initial, rule=rule
        )

    monkeypatch.setattr(Geometry, "contact_survival", tracked_contact)
    monkeypatch.setattr(Geometry, "outer_survival", tracked_outer)
    monkeypatch.setattr(coefficients, "integrate", tracked_integrate)
    budget = WorkBudget(max_attempts=14, max_queue=1)
    result = certify(model, budget, rule=SEVEN_NODE_RULE, partition=DYADIC_RADIAL)
    assert result.conditioning is not None
    assert len(result.integrals) == 14
    assert len(result.conditioning.bands) == 11
    assert budget.attempts == budget.leaves == 14
    assert budget.nodes == budget.completed_nodes == 602
    assert budget.derivative_boxes == 26
    assert allocations == [(1, Q_WIDTH)] * 2 + [(2, 2 * TRIANGLE_WIDTH / 12)] * 12
    assert len(contact_calls) == len(outer_calls) == 8
    assert all(
        owner is model and owner.receiver == 1 and owner.outer == 1025
        for owner in contact_calls + outer_calls
    )
    assert all(domain.band.geometry is model for domain in result.conditioning.domains)
    payload = json.loads(encoded_certificates([result]))[0]
    assert payload["schema_version"] == "continuous-receiver-coefficient-certificate.v3"
    assert payload["geometry"]["receiver_radius_m"] == "1"
    assert payload["geometry"]["outer_radius_m"] == "1025"
    assert len(payload["radial_domains"]) == 12
    widths = [
        Fraction(domain["target_full_width"]) for domain in payload["radial_domains"]
    ]
    assert sum(widths, Fraction(0)) == 2 * TRIANGLE_WIDTH
    assert all(width == 2 * TRIANGLE_WIDTH / 12 for width in widths)
    assert Fraction(1, 32_000_000_000) == Q_WIDTH
    assert result.radial_sum is not None
    assert payload["radial_sum_bounds"] == result.radial_sum.encoded()


@pytest.mark.parametrize("rule", [SIMPSON_RULE, SEVEN_NODE_RULE])
def test_default_unbanded_certificates_remain_byte_identical(rule: str) -> None:
    model = geometry(Fraction(2))
    old_default = certify(model, WorkBudget(max_attempts=4), rule=rule)
    explicit = certify(
        model, WorkBudget(max_attempts=4), rule=rule, partition=WHOLE_ANNULUS
    )
    assert encoded_certificates([old_default]) == encoded_certificates([explicit])
    assert old_default.conditioning is None
    assert old_default.radial_sum is None


def test_unit_and_contact_band_proofs_refuse_extrapolation_before_intersection() -> (
    None
):
    model = geometry()
    domain = RadialDomain(radial_bands(model)[1], "regular_band")
    outside = Jet.variable(Interval(Fraction(-1, 10), Fraction(1)))
    with pytest.raises(ValueError, match="unit interval"):
        domain.evaluate((outside, Jet.constant(Fraction(1, 2))))
    with pytest.raises(ValueError, match="Contact band"):
        model.triangle(
            Jet.constant(Fraction(1, 2)),
            Jet.constant(Fraction(1, 2)),
            1,
            contact_outer=Fraction(3),
        )
    budget = WorkBudget()
    with pytest.raises(ValueError, match="Unknown"):
        certify(model, budget, partition="undocumented")
    assert budget.nodes == budget.leaves == 0


def test_global_node_refusal_before_complete_initial_population_never_returns_partial_sum() -> (
    None
):
    model = geometry(Fraction(1025))
    with pytest.raises(ResourceRefusal, match="node_ceiling"):
        certify(
            model,
            WorkBudget(max_nodes=601),
            rule=SEVEN_NODE_RULE,
            partition=DYADIC_RADIAL,
        )
