"""Independent radial coverage, original-disk identities and certificate accounting."""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal, localcontext
from fractions import Fraction as Q
import json
from math import isqrt
from typing import cast

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver import (
    coefficients,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.arithmetic import (
    Interval,
    Jet,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.certificates import (
    certificate,
    encoded_certificates,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.coefficients import (
    CoefficientResult,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.kernel import (
    Geometry,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.quadrature import (
    SEVEN_NODE_RULE,
    SIMPSON_RULE,
    Box,
    IntegralResult,
    Integrand,
    Panel,
    ResourceRefusal,
    WorkBudget,
    integrate,
    positive_panel,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.radial_partition import (
    DYADIC_RADIAL,
    Band,
    RadialDomain,
    RadialPartition,
    radial_bands,
    validate_bands,
)

from .test_independent_certificates import (
    decimal_sine,
    decimal_value,
    encloses,
    independent_pi,
)

UNIT = ((Q(0), Q(1)),)


def model(coefficient: Q = Q(3, 5), receiver: Q = Q(1), outer: Q = Q(1025)) -> Geometry:
    return Geometry(coefficient, receiver, outer, (Q(137), Q(41)), (Q(-293), Q(107)))


@pytest.mark.parametrize("outer", [Q(3, 2), Q(2), Q(17, 3), Q(1025), Q(2048)])
def test_exact_dyadic_bands_cover_the_entire_original_annulus(outer: Q) -> None:
    geometry = model(outer=outer)
    bands = radial_bands(geometry)
    expected = [Q(1)]
    while expected[-1] < outer:
        expected.append(min(2 * expected[-1], outer))
    assert [(band.lower, band.upper) for band in bands] == list(
        zip(expected, expected[1:], strict=False)
    )
    assert (
        len(bands) <= 11
        and bands[0].lower == geometry.receiver
        and bands[-1].upper == outer
    )
    assert (
        sum((band.upper - band.lower for band in bands), Q(0))
        == outer - geometry.receiver
    )
    assert all(
        band.geometry is geometry and band.index == i for i, band in enumerate(bands)
    )
    assert all(
        first.upper == second.lower
        for first, second in zip(bands[:-1], bands[1:], strict=True)
    )
    partition = RadialPartition.build(geometry)
    assert len(partition.domains) == len(bands) + 1
    assert [
        (domain.kind, domain.patch, domain.band.index) for domain in partition.domains
    ] == [("contact_triangle", 1, 0), ("contact_triangle", 2, 0)] + [
        ("regular_band", None, i) for i in range(1, len(bands))
    ]


def test_noninteger_receiver_and_uncovered_tail_are_never_rounded_or_truncated() -> (
    None
):
    receiver = Q(3, 5)
    geometry = model(receiver=receiver, outer=receiver * 2048)
    bands = radial_bands(geometry)
    assert len(bands) == 11 and bands[-1].upper == Q(6144, 5)
    assert [band.lower for band in bands] == [receiver * 2**i for i in range(11)]
    with pytest.raises(ResourceRefusal, match="uncovered_tail"):
        radial_bands(replace(geometry, outer=geometry.outer + Q(1, 7)))


@pytest.mark.parametrize("damage", ["missing", "duplicate", "reordered", "foreign"])
def test_band_and_domain_ownership_refuse_incomplete_or_foreign_partitions(
    damage: str,
) -> None:
    geometry = model()
    partition = RadialPartition.build(geometry)
    bands = partition.bands
    if damage == "missing":
        damaged = bands[:-1]
    elif damage == "duplicate":
        damaged = bands[:2] + (bands[1],) + bands[3:]
    elif damage == "reordered":
        damaged = (bands[1], bands[0]) + bands[2:]
    else:
        foreign = replace(geometry, coefficient=Q(2, 5))
        damaged = radial_bands(foreign)
    with pytest.raises(ValueError):
        validate_bands(geometry, damaged)
    with pytest.raises(ValueError):
        RadialPartition(geometry, damaged, partition.domains)
    domains = partition.domains
    if damage == "missing":
        wrong_domains = domains[:-1]
    elif damage == "duplicate":
        wrong_domains = domains[:2] + (domains[1],) + domains[3:]
    elif damage == "reordered":
        wrong_domains = (domains[1], domains[0]) + domains[2:]
    else:
        wrong_domains = RadialPartition.build(
            replace(geometry, coefficient=Q(2, 5))
        ).domains
    with pytest.raises(ValueError):
        RadialPartition(geometry, bands, wrong_domains)


def test_band_boundary_and_contact_domain_restrictions_are_literal() -> None:
    geometry = model()
    bands = radial_bands(geometry)
    with pytest.raises(ValueError):
        Band(geometry, 0, Q(1), Q(3))
    with pytest.raises(ValueError):
        Band(geometry, True, Q(1), Q(2))
    with pytest.raises(TypeError):
        Band(geometry, 0, cast(Q, 1.0), Q(2))
    with pytest.raises(ValueError):
        RadialDomain(bands[0], "regular_band")
    with pytest.raises(ValueError):
        RadialDomain(bands[1], "contact_triangle", 1)
    with pytest.raises(ValueError):
        RadialDomain(bands[0], "contact_triangle", True)
    with pytest.raises(ValueError):
        geometry.triangle(
            Jet.constant(Q(1, 2), 0), Jet.constant(Q(1, 3), 0), 1, contact_outer=Q(3)
        )


@pytest.mark.parametrize("index", [1, 5, 10])
def test_scaled_band_matches_original_disk_formula_with_nonzero_survival(
    index: int,
) -> None:
    geometry = model()
    band = radial_bands(geometry)[index]
    domain = RadialDomain(band, "regular_band")
    first, second = Q(2, 5), Q(3, 7)
    actual = domain.evaluate((Jet.constant(first, 0), Jet.constant(second, 0))).value
    assert actual.upper < 0
    # High-precision direct original geometry is a diagnostic, not a rigorous oracle.
    with localcontext() as context:
        context.prec = 90
        p_bounds = independent_pi()
        pi = decimal_value((p_bounds[0] + p_bounds[1]) / 2)
        a, b, r0 = map(decimal_value, (band.lower, band.upper, geometry.receiver))
        s, u = decimal_value(first), decimal_value(second)
        radius, phi = a + (b - a) * s, pi * u
        d2 = (radius - r0) ** 2 + 4 * radius * r0 * decimal_sine(phi / 2) ** 2
        displacement_power = d2
        for _ in range(4):
            displacement_power = displacement_power.sqrt()
        delta = decimal_value(geometry.delta)
        separation = decimal_value(geometry.norm_difference)
        denominator = 4 * (
            radius * radius - decimal_value(geometry.dot)
        ) ** 2 + decimal_value(geometry.norm_sum * geometry.norm_difference)
        derivative = -2 * delta * separation * radius / (denominator.sqrt() ** 3)
        expected = (
            derivative
            * (-decimal_value(geometry.coefficient) * displacement_power).exp()
            * 2
            * radius**2
            * decimal_sine(phi) ** 2
            / (pi * d2)
            * (b - a)
            * pi
        )
        midpoint = decimal_value((actual.lower + actual.upper) / 2)
        assert abs(midpoint - expected) <= decimal_value(actual.width / 2) + Decimal(
            "1e-60"
        )
    assert domain.band.geometry.receiver == 1 and domain.band.lower != 1


def test_zero_survival_coefficient_band_integral_has_known_angular_antiderivative() -> (
    None
):
    geometry = Geometry(Q(0), Q(1, 2), Q(2), (Q(0), Q(0)), (Q(2), Q(0)))
    domain = RadialPartition.build(geometry).domains[-1]
    assert (domain.band.lower, domain.band.upper) == (Q(1), Q(2))
    panel = positive_panel(
        domain.evaluate, UNIT * 2, WorkBudget(), rule=SEVEN_NODE_RULE
    )
    # Q(r)=1. For these anchors h(r)=1-r²/(2sqrt(r⁴+4)); h(2)-h(1)=-1/(2sqrt5).
    scale = 2**160
    root = isqrt(5 * scale**2)
    lower_root, upper_root = Q(root, scale), Q(root + 1, scale)
    assert lower_root**2 <= 5 <= upper_root**2
    encloses(panel.enclosure, -1 / (2 * lower_root), -1 / (2 * upper_root))


def test_equal_radius_anchor_symmetry_annuls_every_radial_domain() -> None:
    geometry = Geometry(Q(3, 5), Q(1), Q(8), (Q(3), Q(4)), (Q(-4), Q(3)))
    assert geometry.delta == 0
    for domain in RadialPartition.build(geometry).domains:
        actual = domain.evaluate((Jet.constant(Q(2, 5), 0), Jet.constant(Q(3, 7), 0)))
        assert actual.value == Interval.point(0)
    assert geometry.angular(
        Jet.variable(Interval(Q(1), Q(8)), 8)
    ).value == Interval.point(Q(1, 2))


@dataclass(frozen=True)
class ClosedPartition:
    geometry: Geometry
    result: CoefficientResult
    budget: WorkBudget
    targets: tuple[Q, ...]
    endpoint_calls: tuple[tuple[str, Q, Q, int], ...]
    initial_counts: tuple[tuple[int, int, int], ...]


@pytest.fixture(scope="module")
def closed_partition() -> ClosedPartition:
    geometry = model()
    budget = WorkBudget(max_leaves=14, max_attempts=14, max_nodes=602, max_queue=14)
    started = budget.started
    targets: list[Q] = []
    endpoints: list[tuple[str, Q, Q, int]] = []
    initial_counts: list[tuple[int, int, int]] = []
    actual_panel, actual_integrate = positive_panel, integrate
    contact, outer = Geometry.contact_survival, Geometry.outer_survival

    def tracked_panel(
        function: Integrand, box: Box, owned: WorkBudget, *, rule: str = SIMPSON_RULE
    ) -> Panel:
        assert owned is budget and owned.started == started
        result = actual_panel(function, box, owned, rule=rule)
        initial_counts.append(
            (owned.attempts, owned.completed_nodes, owned.derivative_boxes)
        )
        return result

    def tracked_integrate(
        function: Integrand,
        dimensions: int,
        target_width: Q,
        owned: WorkBudget,
        *,
        initial: Panel | None = None,
        rule: str = SIMPSON_RULE,
    ) -> IntegralResult:
        # This assertion executes before EVERY adaptation, including the first.
        assert (
            owned is budget and owned.started == started and len(initial_counts) == 14
        )
        assert (
            owned.attempts,
            owned.nodes,
            owned.completed_nodes,
            owned.derivative_boxes,
        ) == (14, 602, 602, 26)
        targets.append(target_width)
        return actual_integrate(
            function, dimensions, target_width, owned, initial=initial, rule=rule
        )

    def tracked_contact(self: Geometry, coordinate: Jet) -> Jet:
        assert self is geometry
        endpoints.append(("contact", self.receiver, self.outer, coordinate.order))
        return contact(self, coordinate)

    def tracked_outer(self: Geometry, coordinate: Jet) -> Jet:
        assert self is geometry
        endpoints.append(("outer", self.receiver, self.outer, coordinate.order))
        return outer(self, coordinate)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(coefficients, "positive_panel", tracked_panel)
        patch.setattr(coefficients, "integrate", tracked_integrate)
        patch.setattr(Geometry, "contact_survival", tracked_contact)
        patch.setattr(Geometry, "outer_survival", tracked_outer)
        result = coefficients.certify(
            geometry, budget, rule=SEVEN_NODE_RULE, partition=DYADIC_RADIAL
        )
    return ClosedPartition(
        geometry,
        result,
        budget,
        tuple(targets),
        tuple(endpoints),
        tuple(initial_counts),
    )


def test_every_initial_domain_closes_once_before_refinement_with_one_shared_budget(
    closed_partition: ClosedPartition,
) -> None:
    record = closed_partition
    assert record.initial_counts == ((1, 7, 1), (2, 14, 2)) + tuple(
        (i + 3, 14 + 49 * (i + 1), 4 + 2 * i) for i in range(12)
    )
    assert (
        record.budget.attempts,
        record.budget.nodes,
        record.budget.completed_nodes,
        record.budget.leaves,
    ) == (14, 602, 602, 14)
    assert (
        len(record.result.integrals) == 14
        and record.result.status == "refuse_unresolved"
    )
    assert len(record.endpoint_calls) == 16
    for kind in ("contact", "outer"):
        calls = [row for row in record.endpoint_calls if row[0] == kind]
        assert calls == [(kind, Q(1), Q(1025), 8)] + [(kind, Q(1), Q(1025), 0)] * 7
    assert record.targets[:2] == (Q(1, 32 * 10**9),) * 2
    assert record.targets[2:] == (Q(1, 96 * 10**9),) * 12
    assert sum(record.targets[2:], Q(0)) == Q(1, 8 * 10**9)
    for index, integral in enumerate(record.result.integrals):
        assert len(integral.panels) == 1
        assert integral.panels[0].box == UNIT * (1 if index < 2 else 2)
        assert integral.enclosure == integral.panels[0].enclosure


def test_global_radial_sum_and_complementary_coefficients_keep_every_band(
    closed_partition: ClosedPartition,
) -> None:
    result = closed_partition.result
    assert result.conditioning is not None and len(result.conditioning.bands) == 11
    lower = sum((row.enclosure.lower for row in result.integrals[2:]), Q(0))
    upper = sum((row.enclosure.upper for row in result.integrals[2:]), Q(0))
    assert result.radial_sum == Interval(lower, upper)
    a, b = result.endpoint_products
    assert result.first == Interval(
        a.lower - b.upper + lower, a.upper - b.lower + upper
    )
    qr, ql = result.integrals[:2]
    assert result.homogeneous == Interval(
        qr.enclosure.lower - ql.enclosure.upper, qr.enclosure.upper - ql.enclosure.lower
    )
    assert result.second == Interval(
        result.homogeneous.lower - result.first.upper,
        result.homogeneous.upper - result.first.lower,
    )
    with pytest.raises(ValueError):
        replace(result, integrals=result.integrals[:-1])
    with pytest.raises(ValueError):
        replace(result, radial_sum=Interval.point(0))
    with pytest.raises(ValueError, match="Mixed"):
        replace(result, rule=SIMPSON_RULE)


def test_certificate_binds_exact_original_geometry_domains_rule_and_width_budget(
    closed_partition: ClosedPartition,
) -> None:
    result = closed_partition.result
    assert result.radial_sum is not None
    payload = json.loads(encoded_certificates([result]))[0]
    assert payload["schema_version"] == "continuous-receiver-coefficient-certificate.v3"
    assert payload["partition_schema"] == "continuous-receiver-dyadic-radial.v1"
    assert payload["geometry"] == {
        "coefficient_A": "3/5",
        "receiver_radius_m": "1",
        "outer_radius_m": "1025",
        "first_anchor_xy_m": ["137", "41"],
        "second_anchor_xy_m": ["-293", "107"],
    }
    edges = [2**i for i in range(11)] + [1025]
    assert payload["radial_bands"] == [
        {"index": i, "bounds_m": [str(a), str(b)]}
        for i, (a, b) in enumerate(zip(edges[:-1], edges[1:], strict=True))
    ]
    assert payload["quadrature_rule"] == "closed-newton-cotes-seven.v1"
    assert payload["radial_full_width_budget"] == "1/8000000000"
    assert payload["radial_sum_bounds"] == [
        str(result.radial_sum.lower),
        str(result.radial_sum.upper),
    ]
    for index, domain in enumerate(payload["radial_domains"]):
        band_index = 0 if index < 2 else index - 1
        assert domain == {
            "kind": "contact_triangle" if index < 2 else "regular_band",
            "patch": index + 1 if index < 2 else None,
            "band_index": band_index,
            "band_bounds_m": [str(edges[band_index]), str(edges[band_index + 1])],
            "original_receiver_radius_m": "1",
            "integral_index": index + 2,
            "quadrature_rule": SEVEN_NODE_RULE,
            "target_full_width": "1/96000000000",
            "bounds": [
                str(result.integrals[index + 2].enclosure.lower),
                str(result.integrals[index + 2].enclosure.upper),
            ],
        }
    assert all(
        row["quadrature_rule"] == SEVEN_NODE_RULE
        and all(leaf["quadrature_rule"] == SEVEN_NODE_RULE for leaf in row["leaves"])
        for row in payload["integrals"]
    )


@pytest.mark.parametrize("bad", [None, True, "partial_annulus"])
def test_unknown_partition_or_rule_refuses_before_any_work(bad: object) -> None:
    budget = WorkBudget()
    with pytest.raises(ValueError):
        coefficients.certify(
            model(), budget, partition=cast(str, bad), rule=SEVEN_NODE_RULE
        )
    with pytest.raises(ValueError):
        coefficients.certify(
            model(), budget, partition=DYADIC_RADIAL, rule=cast(str, bad)
        )
    assert (
        budget.attempts == budget.nodes == budget.completed_nodes == budget.leaves == 0
    )


@pytest.mark.parametrize(
    "rule,schema",
    [
        (SIMPSON_RULE, "continuous-receiver-coefficient-certificate.v1"),
        (SEVEN_NODE_RULE, "continuous-receiver-coefficient-certificate.v2"),
    ],
)
def test_unconditioned_literal_certificate_contracts_stay_exact(
    rule: str, schema: str
) -> None:
    zero = Interval.point(0)
    integral = IntegralResult(zero, (), "controlled", None, rule)
    result = CoefficientResult(
        (integral,) * 4, zero, zero, zero, (zero, zero), "controlled", rule
    )
    expected = {
        "schema_version": schema,
        "status": "controlled",
        "coefficient_bounds": {"K": ["0", "0"], "B1": ["0", "0"], "B2": ["0", "0"]},
        "endpoint_products": [["0", "0"], ["0", "0"]],
        "integrals": [
            {
                "status": "controlled",
                "refusal": None,
                "bounds": ["0", "0"],
                "leaves": [],
                **({"quadrature_rule": rule} if rule == SEVEN_NODE_RULE else {}),
            }
        ]
        * 4,
        **({"quadrature_rule": rule} if rule == SEVEN_NODE_RULE else {}),
    }
    assert (
        encoded_certificates([result])
        == json.dumps(
            [expected], sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    )
    assert "geometry" not in certificate(result) and result.conditioning is None
