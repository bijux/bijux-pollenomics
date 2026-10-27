"""Two closed positive rules, deterministic partitions and finite work caps."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from fractions import Fraction
import heapq
import math
import time

from .arithmetic import Interval, Jet

Integrand = Callable[[tuple[Jet, ...]], Jet]
Box = tuple[tuple[Fraction, Fraction], ...]
SIMPSON_RULE = "simpson-positive.v1"
SEVEN_NODE_RULE = "closed-newton-cotes-seven.v1"


def rule_definition(identity: str) -> tuple[int, tuple[int, ...], int, int]:
    """Closed reviewed rules: derivative order, positive weights, two divisors."""
    if type(identity) is not str:
        raise ValueError("Unknown positive quadrature rule")
    if identity == SIMPSON_RULE:
        return 4, (1, 4, 1), 6, 2880
    if identity == SEVEN_NODE_RULE:
        return 8, (41, 216, 27, 272, 27, 216, 41), 840, 1567641600
    raise ValueError("Unknown positive quadrature rule")


class ResourceRefusal(RuntimeError):
    """A declared work limit stopped certification without changing tolerance."""


@dataclass
class WorkBudget:
    """One geometry's shared four-integral budget; limits may only be lowered."""

    max_leaves: int = 4096
    max_attempts: int = 8191
    max_nodes: int = 73719
    max_queue: int = 4096
    wall_seconds: float = 180
    attempts: int = 0
    nodes: int = 0
    completed_nodes: int = 0
    leaves: int = 0
    derivative_boxes: int = 0
    started: float = field(default_factory=time.monotonic)

    def __post_init__(self) -> None:
        if any(
            type(value) is not int
            for value in (
                self.max_leaves,
                self.max_attempts,
                self.max_nodes,
                self.max_queue,
            )
        ):
            raise TypeError("Integer work ceilings required")
        if not (
            1 <= self.max_leaves <= 4096
            and 1 <= self.max_attempts <= 8191
            and 1 <= self.max_nodes <= 73719
            and 1 <= self.max_queue <= 4096
            and 0 < self.wall_seconds <= 180
        ):
            raise ValueError("Work limits exceed the declared finite ceilings")

    def check(self) -> None:
        if time.monotonic() - self.started >= self.wall_seconds:
            raise ResourceRefusal("wall_seconds")

    def panel(self, dimensions: int, *, nodes_per_axis: int = 3) -> None:
        self.check()
        if (
            type(dimensions) is not int
            or dimensions not in (1, 2)
            or type(nodes_per_axis) is not int
            or nodes_per_axis not in (3, 7)
        ):
            raise ValueError("Unknown positive quadrature node population")
        nodes = nodes_per_axis**dimensions
        if self.attempts >= self.max_attempts or self.nodes + nodes > self.max_nodes:
            raise ResourceRefusal("attempt_or_node_ceiling")
        self.attempts += 1
        self.nodes += nodes

    def add_leaf(self) -> None:
        self.check()
        if self.leaves >= self.max_leaves:
            raise ResourceRefusal("leaf_ceiling")
        self.leaves += 1


@dataclass(frozen=True)
class Panel:
    box: Box
    node_sum: Interval
    error_radius: Fraction
    directional_radii: tuple[Fraction, ...]
    rule: str = SIMPSON_RULE

    def __post_init__(self) -> None:
        rule_definition(self.rule)

    @property
    def enclosure(self) -> Interval:
        # Both rules give |error|<=E: this adds FULL width 2E.
        return self.node_sum.expanded(self.error_radius)


def simpson_panel(function: Integrand, box: Box, budget: WorkBudget) -> Panel:
    """Preserve the default fourth-order rule and its exact arithmetic order."""
    return positive_panel(function, box, budget, rule=SIMPSON_RULE)


def positive_panel(
    function: Integrand, box: Box, budget: WorkBudget, *, rule: str = SIMPSON_RULE
) -> Panel:
    order, weights, weight_divisor, error_divisor = rule_definition(rule)
    node_count = len(weights)
    dimensions = len(box)
    if dimensions not in (1, 2) or any(not a < b for a, b in box):
        raise ValueError("One or two positive integration intervals required")
    budget.panel(dimensions, nodes_per_axis=node_count)
    lengths = tuple(b - a for a, b in box)
    volume = math.prod(lengths)
    radii = []
    for axis in range(dimensions):
        arguments = tuple(
            Jet.variable(Interval(a, b), order)
            if axis == j
            else Jet.constant(Interval(a, b), order)
            for j, (a, b) in enumerate(box)
        )
        budget.derivative_boxes += 1
        evaluated = function(arguments)
        if evaluated.order != order:
            raise ValueError(
                "Integrand returned the wrong derivative order for the rule"
            )
        derivative = evaluated.coefficients[order].magnitude * math.factorial(order)
        radii.append(volume * lengths[axis] ** order * derivative / error_divisor)
        budget.check()
    coordinates = tuple(
        tuple(a + (b - a) * j / (node_count - 1) for j in range(node_count))
        for a, b in box
    )
    total = Interval.point(0)
    for first in range(node_count):
        for second in range(node_count if dimensions == 2 else 1):
            indices = (first, second)[:dimensions]
            point = tuple(
                Jet.constant(coordinates[j][index], 0)
                for j, index in enumerate(indices)
            )
            weight = math.prod(weights[index] for index in indices)
            total += function(point).value * weight
            budget.completed_nodes += 1
            budget.check()
    node_sum = total * (volume / (weight_divisor**dimensions))
    return Panel(box, node_sum, sum(radii, Fraction(0)), tuple(radii), rule)


@dataclass(frozen=True)
class IntegralResult:
    enclosure: Interval
    panels: tuple[Panel, ...]
    status: str
    refusal: str | None
    rule: str = SIMPSON_RULE

    def __post_init__(self) -> None:
        rule_definition(self.rule)
        if any(panel.rule != self.rule for panel in self.panels):
            raise ValueError("Mixed quadrature rules in integral certificate")


def integrate(
    function: Integrand,
    dimensions: int,
    target_width: Fraction,
    budget: WorkBudget,
    *,
    initial: Panel | None = None,
    rule: str = SIMPSON_RULE,
) -> IntegralResult:
    """Bisect the widest-error leaf, then its largest directional error (ties first)."""
    rule_definition(rule)
    if (
        type(dimensions) is not int
        or dimensions not in (1, 2)
        or type(target_width) not in (int, Fraction)
        or target_width <= 0
    ):
        raise ValueError("Invalid integration design")
    if initial is None:
        budget.add_leaf()
        root = positive_panel(
            function, ((Fraction(0), Fraction(1)),) * dimensions, budget, rule=rule
        )
    else:
        root = initial
        if root.rule != rule:
            raise ValueError("Mixed quadrature rules in initial certificate")
        if root.box != ((Fraction(0), Fraction(1)),) * dimensions:
            raise ValueError("Initial certificate does not cover the unit domain")
    queue: list[tuple[Fraction, int, Panel]] = [(-root.enclosure.width, 0, root)]
    lower, upper, sequence = root.enclosure.lower, root.enclosure.upper, 0
    refusal = None
    while upper - lower > target_width:
        try:
            budget.check()
            if len(queue) + 1 > budget.max_queue:
                raise ResourceRefusal("queue_ceiling")
            budget.add_leaf()
            _, _, parent = queue[0]
            axis = max(
                range(dimensions), key=lambda j: (parent.directional_radii[j], -j)
            )
            a, b = parent.box[axis]
            midpoint = (a + b) / 2
            boxes = []
            for interval in ((a, midpoint), (midpoint, b)):
                coordinates = list(parent.box)
                coordinates[axis] = interval
                boxes.append(tuple(coordinates))
            # Publish neither child unless BOTH are closed. On refusal retain
            # the valid parent partition and its certified wide enclosure.
            children = [
                positive_panel(function, box, budget, rule=rule) for box in boxes
            ]
            heapq.heappop(queue)
            lower -= parent.enclosure.lower
            upper -= parent.enclosure.upper
            for child in children:
                sequence += 1
                heapq.heappush(queue, (-child.enclosure.width, sequence, child))
                lower += child.enclosure.lower
                upper += child.enclosure.upper
        except ResourceRefusal as error:
            refusal = str(error)
            break
    panels = tuple(item[2] for item in sorted(queue, key=lambda item: item[1]))
    status = "certified_width" if upper - lower <= target_width else "refuse_unresolved"
    return IntegralResult(Interval(lower, upper), panels, status, refusal, rule)
