"""Original coefficients assembled from finite-polynomial integrals plus one tail."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from ..arithmetic import Interval, Jet
from ..coefficients import EPSILON, TRIANGLE_WIDTH
from ..quadrature import SEVEN_NODE_RULE, IntegralResult, ResourceRefusal
from .domains import AnglePartition


def radial_target(partition: AnglePartition) -> Fraction:
    """Reserve the global two-sided series width inside the original epsilon/8."""
    available = 2 * TRIANGLE_WIDTH - 2 * partition.contraction.remainder_radius
    if available <= 0:
        raise ResourceRefusal("angular_remainder_exceeds_radial_allocation")
    return available / len(partition.domains)


@dataclass(frozen=True)
class MomentCoefficient:
    """Keep finite quadrature and the exact-law whole-J allowance separately."""

    partition: AnglePartition
    integrals: tuple[IntegralResult, ...]
    homogeneous: Interval
    first: Interval
    second: Interval
    endpoint_products: tuple[Interval, Interval]
    finite_radial_sum: Interval
    radial_sum: Interval
    status: str
    rule: str = SEVEN_NODE_RULE

    def __post_init__(self) -> None:
        """Refuse incomplete domains, mixed rules or repeated/omitted global tails."""
        if (
            type(self.partition) is not AnglePartition
            or len(self.integrals) != len(self.partition.domains) + 2
            or self.rule != SEVEN_NODE_RULE
            or any(row.rule != self.rule for row in self.integrals)
        ):
            raise ValueError(
                "Complete original-geometry angle integral population required"
            )
        finite = sum((row.enclosure for row in self.integrals[2:]), Interval.point(0))
        if self.finite_radial_sum != finite or self.radial_sum != finite.expanded(
            self.partition.contraction.remainder_radius
        ):
            raise ValueError(
                "Global angle remainder must widen the whole J exactly once"
            )
        expected_k = self.integrals[0].enclosure - self.integrals[1].enclosure
        expected_first = (
            self.endpoint_products[0] - self.endpoint_products[1] + self.radial_sum
        )
        if (
            self.homogeneous != expected_k
            or self.first != expected_first
            or self.second != expected_k - expected_first
        ):
            raise ValueError("Original complementary coefficient assembly differs")
        status = (
            "certified_width"
            if all(
                value.width <= EPSILON
                for value in (self.homogeneous, self.first, self.second)
            )
            else "refuse_unresolved"
        )
        if self.status != status:
            raise ValueError("Original epsilon coefficient status differs")


def assemble(
    partition: AnglePartition, integrals: tuple[IntegralResult, ...]
) -> MomentCoefficient:
    """Enclose the same K,B1,B2 after adding the finite-series tail only to J."""
    if len(integrals) != len(partition.domains) + 2:
        raise ValueError("Complete angle domains required before coefficient assembly")
    radial_target(partition)
    model = partition.geometry
    qr, ql = integrals[0].enclosure, integrals[1].enclosure
    products = (
        model.angular(Jet.constant(model.receiver, 0)).value * qr,
        model.angular(Jet.constant(model.outer, 0)).value * ql,
    )
    finite = sum((row.enclosure for row in integrals[2:]), Interval.point(0))
    radial = finite.expanded(partition.contraction.remainder_radius)
    k = qr - ql
    first = products[0] - products[1] + radial
    second = k - first
    status = (
        "certified_width"
        if all(value.width <= EPSILON for value in (k, first, second))
        else "refuse_unresolved"
    )
    return MomentCoefficient(
        partition, integrals, k, first, second, products, finite, radial, status
    )
