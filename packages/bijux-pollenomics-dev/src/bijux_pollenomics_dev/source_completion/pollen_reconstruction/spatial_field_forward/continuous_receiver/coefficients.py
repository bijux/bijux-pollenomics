"""Shared finite-work certification of K and complementary anchor responses."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .arithmetic import Interval, Jet
from .kernel import Geometry
from .quadrature import (
    Box,
    IntegralResult,
    Integrand,
    WorkBudget,
    integrate,
    simpson_panel,
)

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


def certify(geometry: Geometry, budget: WorkBudget) -> CoefficientResult:
    """Close all four initial domains before refining any of them.

    Thus a later finite-work refusal retains a quantified complete continuous
    enclosure, rather than losing an unsampled integral or dropping a response.
    Refinement uses no saved responses, forecasts, observed counts or scores.
    """
    functions: tuple[Integrand, ...] = (
        lambda arguments: geometry.contact_survival(arguments[0]),
        lambda arguments: geometry.outer_survival(arguments[0]),
        lambda arguments: geometry.triangle(arguments[0], arguments[1], 1),
        lambda arguments: geometry.triangle(arguments[0], arguments[1], 2),
    )
    dimensions = (1, 1, 2, 2)
    targets = (Q_WIDTH, Q_WIDTH, TRIANGLE_WIDTH, TRIANGLE_WIDTH)
    roots = []
    for function, dimension in zip(functions, dimensions, strict=True):
        budget.add_leaf()
        box: Box = ((Fraction(0), Fraction(1)),) * dimension
        roots.append(simpson_panel(function, box, budget))
    results = tuple(
        integrate(function, dimension, target, budget, initial=root)
        for function, dimension, target, root in zip(
            functions, dimensions, targets, roots, strict=True
        )
    )
    qr, ql, first_triangle, second_triangle = (result.enclosure for result in results)
    hr = geometry.angular(Jet.constant(geometry.receiver, 0)).value
    hl = geometry.angular(Jet.constant(geometry.outer, 0)).value
    products = hr * qr, hl * ql
    homogeneous = qr - ql
    first = products[0] - products[1] + first_triangle + second_triangle
    second = homogeneous - first
    success = (
        all(result.status == "certified_width" for result in results)
        and all(product.width <= PRODUCT_WIDTH for product in products)
        and all(bound.width <= EPSILON for bound in (homogeneous, first, second))
    )
    return CoefficientResult(
        results,
        homogeneous,
        first,
        second,
        products,
        "certified_width" if success else "refuse_unresolved",
    )
