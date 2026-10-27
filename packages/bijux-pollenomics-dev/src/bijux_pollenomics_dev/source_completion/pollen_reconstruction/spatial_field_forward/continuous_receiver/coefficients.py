"""Shared finite-work certification of K and complementary anchor responses."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .arithmetic import Interval, Jet
from .kernel import Geometry
from .quadrature import (
    SIMPSON_RULE,
    Box,
    IntegralResult,
    Integrand,
    WorkBudget,
    integrate,
    positive_panel,
    rule_definition,
)
from .radial_partition import WHOLE_ANNULUS, RadialPartition, validate_partition_option

EPSILON = Fraction(1, 10**9)
Q_WIDTH = EPSILON / 32
PRODUCT_WIDTH = EPSILON / 16
TRIANGLE_WIDTH = EPSILON / 16


@dataclass(frozen=True)
class CoefficientResult:
    integrals: tuple[IntegralResult, ...]
    homogeneous: Interval
    first: Interval
    second: Interval
    endpoint_products: tuple[Interval, Interval]
    status: str
    rule: str = SIMPSON_RULE
    conditioning: RadialPartition | None = None
    radial_sum: Interval | None = None

    def __post_init__(self) -> None:
        rule_definition(self.rule)
        if any(integral.rule != self.rule for integral in self.integrals):
            raise ValueError("Mixed quadrature rules in coefficient certificate")
        if self.conditioning is None:
            if self.radial_sum is not None:
                raise ValueError("Radial-sum ownership requires the declared partition")
        elif (
            type(self.conditioning) is not RadialPartition
            or len(self.integrals) != len(self.conditioning.domains) + 2
            or self.radial_sum
            != sum((row.enclosure for row in self.integrals[2:]), Interval.point(0))
        ):
            raise ValueError("Conditioned certificate population or radial sum differs")


def certify(
    geometry: Geometry,
    budget: WorkBudget,
    *,
    rule: str = SIMPSON_RULE,
    partition: str = WHOLE_ANNULUS,
) -> CoefficientResult:
    """Close every initial domain before refining any of them.

    Thus a later finite-work refusal retains a quantified complete continuous
    enclosure, rather than losing an unsampled integral or dropping a response.
    Refinement uses no saved responses, forecasts, observed counts or scores.
    """
    rule_definition(rule)
    validate_partition_option(partition)
    conditioning = (
        None if partition == WHOLE_ANNULUS else RadialPartition.build(geometry)
    )
    endpoints: tuple[Integrand, ...] = (
        lambda arguments: geometry.contact_survival(arguments[0]),
        lambda arguments: geometry.outer_survival(arguments[0]),
    )
    radial: tuple[Integrand, ...] = (
        (
            lambda arguments: geometry.triangle(arguments[0], arguments[1], 1),
            lambda arguments: geometry.triangle(arguments[0], arguments[1], 2),
        )
        if conditioning is None
        else tuple(domain.evaluate for domain in conditioning.domains)
    )
    functions = endpoints + radial
    dimensions = (1, 1) + (2,) * len(radial)
    # Fix the same TOTAL radial full-width budget before any observations.
    local_width = 2 * TRIANGLE_WIDTH / len(radial)
    targets = (Q_WIDTH, Q_WIDTH) + (local_width,) * len(radial)
    roots = []
    for function, dimension in zip(functions, dimensions, strict=True):
        budget.add_leaf()
        box: Box = ((Fraction(0), Fraction(1)),) * dimension
        roots.append(positive_panel(function, box, budget, rule=rule))
    results = tuple(
        integrate(function, dimension, target, budget, initial=root, rule=rule)
        for function, dimension, target, root in zip(
            functions, dimensions, targets, roots, strict=True
        )
    )
    return assemble_coefficients(
        geometry, results, rule=rule, conditioning=conditioning
    )


def assemble_coefficients(
    geometry: Geometry,
    results: tuple[IntegralResult, ...],
    *,
    rule: str = SIMPSON_RULE,
    conditioning: RadialPartition | None = None,
    require_local_allocations: bool = True,
) -> CoefficientResult:
    """Assemble complete coverage; population stopping may use final widths alone.

    The default keeps the single-case local-allocation and product gates. The
    explicit population option retains those diagnostics without imposing them
    after all three mathematically valid final coefficient widths already close.
    """
    rule_definition(rule)
    if type(require_local_allocations) is not bool:
        raise TypeError("Explicit Boolean allocation policy required")
    expected = 4 if conditioning is None else len(conditioning.domains) + 2
    if len(results) != expected or (
        conditioning is not None and conditioning.geometry != geometry
    ):
        raise ValueError("Coefficient assembly requires complete owned domains")
    qr, ql = results[0].enclosure, results[1].enclosure
    hr = geometry.angular(Jet.constant(geometry.receiver, 0)).value
    hl = geometry.angular(Jet.constant(geometry.outer, 0)).value
    products = hr * qr, hl * ql
    homogeneous = qr - ql
    radial_sum = None
    if conditioning is None:
        # Retain the existing unbanded operation order and certificate bytes.
        first = products[0] - products[1] + results[2].enclosure + results[3].enclosure
    else:
        radial_sum = sum(
            (result.enclosure for result in results[2:]), Interval.point(0)
        )
        first = products[0] - products[1] + radial_sum
    second = homogeneous - first
    success = all(bound.width <= EPSILON for bound in (homogeneous, first, second))
    if require_local_allocations:
        success = (
            all(result.status == "certified_width" for result in results)
            and all(product.width <= PRODUCT_WIDTH for product in products)
            and success
        )
    return CoefficientResult(
        results,
        homogeneous,
        first,
        second,
        products,
        "certified_width" if success else "refuse_unresolved",
        rule,
        conditioning,
        radial_sum,
    )
