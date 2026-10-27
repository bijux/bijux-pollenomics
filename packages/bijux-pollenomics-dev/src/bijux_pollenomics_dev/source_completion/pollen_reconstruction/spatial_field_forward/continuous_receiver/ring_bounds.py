"""True cumulative-survival certificates and shared-mass radial field bounds.

For t=R/r, w_t(phi)=2*sin(phi)^2/(1-2*t*cos(phi)+t^2) integrates
into pi. At contact its removable limit is 1+cos(phi). For t2>t1 the
ratio w_t2/w_t1 increases with cos(phi), since its derivative is
2*(t2-t1)*(1-t1*t2)/(1-2*t2*cos(phi)+t2^2)^2. Increasing r decreases t
and increases distance pointwise. The attenuation increases with cos(phi)
and decreases with r. Thus Q(r) is nonincreasing, strictly for A>0;
Q lies in [0,1] and true differences Q(a)-Q(b) are nonnegative masses.
These analytic constraints tighten enclosures, never the raw precision flag.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from fractions import Fraction
import heapq
import math
import time

from .arithmetic import Interval, Jet
from .coefficients import EPSILON
from .kernel import Geometry
from .quadrature import (
    SEVEN_NODE_RULE,
    Box,
    IntegralResult,
    Integrand,
    Panel,
    ResourceRefusal,
    WorkBudget,
    positive_panel,
)

Q_TARGET = Fraction(1, 10**10)


def _edges(geometry: Geometry, edges: tuple[Fraction, ...]) -> None:
    if (
        type(geometry) is not Geometry
        or type(edges) is not tuple
        or not 2 <= len(edges) <= 129
        or any(type(value) is not Fraction for value in edges)
        or edges[0] != geometry.receiver
        or edges[-1] != geometry.outer
        or any(a >= b for a, b in zip(edges[:-1], edges[1:], strict=True))
    ):
        raise ValueError("Two to 129 exact ordered original-radius edges required")


def _q_operator(geometry: Geometry, radius: Fraction) -> Callable[[Jet], Jet]:
    if (
        type(geometry) is not Geometry
        or type(radius) is not Fraction
        or not geometry.receiver <= radius <= geometry.outer
    ):
        raise ValueError("Exact endpoint radius within the original geometry required")
    return (
        geometry.contact_survival
        if radius == geometry.receiver
        else replace(geometry, outer=radius).outer_survival
    )


def _integrand(operator: Callable[[Jet], Jet]) -> Integrand:
    return lambda arguments: operator(arguments[0])


def evaluate_q(geometry: Geometry, radius: Fraction, coordinate: Jet) -> Jet:
    """Retain original R/A/anchors; only the survival evaluation radius changes."""
    return _q_operator(geometry, radius)(coordinate)


def _intersect(value: Interval, lower: Fraction, upper: Fraction) -> Interval:
    return Interval(max(value.lower, lower), min(value.upper, upper))


def _constrained_q(values: tuple[Interval, ...]) -> tuple[Interval, ...]:
    bounded = tuple(_intersect(value, Fraction(0), Fraction(1)) for value in values)
    lower: list[Fraction] = []
    suffix = Fraction(0)
    for value in reversed(bounded):
        suffix = max(suffix, value.lower)
        lower.append(suffix)
    upper: list[Fraction] = []
    prefix = Fraction(1)
    for value in bounded:
        prefix = min(prefix, value.upper)
        upper.append(prefix)
    return tuple(Interval(a, b) for a, b in zip(reversed(lower), upper, strict=True))


def shared_q_linear(
    q_bounds: tuple[Interval, ...], coefficients: tuple[Fraction, ...]
) -> Interval:
    """Evaluate one sign-aware linear form with each cumulative Q used once."""
    if (
        type(q_bounds) is not tuple
        or type(coefficients) is not tuple
        or len(q_bounds) != len(coefficients)
        or not q_bounds
        or any(type(value) is not Interval for value in q_bounds)
        or any(type(value) is not Fraction for value in coefficients)
    ):
        raise TypeError(
            "Equal nonempty tuples of intervals and exact coefficients required"
        )
    return sum(
        (
            value * coefficient
            for value, coefficient in zip(q_bounds, coefficients, strict=True)
            if coefficient
        ),
        Interval.point(0),
    )


def _weighted_mass(
    q_bounds: tuple[Interval, ...], weights: tuple[Fraction, ...]
) -> Interval:
    if len(weights) + 1 != len(q_bounds):
        raise ValueError("One exact weight per true radial mass required")
    coefficients = (
        (weights[0],)
        + tuple(weights[i] - weights[i - 1] for i in range(1, len(weights)))
        + (-weights[-1],)
    )
    return shared_q_linear(q_bounds, coefficients)


@dataclass(frozen=True)
class RingBounds:
    geometry: Geometry
    edges: tuple[Fraction, ...]
    raw_q_bounds: tuple[Interval, ...]
    constrained_q_bounds: tuple[Interval, ...]
    h_intervals: tuple[Interval, ...]
    homogeneous: Interval
    first: Interval
    second: Interval

    @property
    def coefficient_epsilon_pass(self) -> tuple[bool, bool, bool]:
        return (
            self.homogeneous.width <= EPSILON,
            self.first.width <= EPSILON,
            self.second.width <= EPSILON,
        )

    @property
    def positive_bounds(self) -> tuple[bool, bool, bool]:
        return (self.homogeneous.lower > 0, self.first.lower > 0, self.second.lower > 0)


def _h_weights(
    h_intervals: tuple[Interval, ...],
) -> tuple[tuple[Fraction, ...], tuple[Fraction, ...]]:
    # The circle-mean derivative has fixed sign -delta. Its extrema on a ring
    # therefore occur at its endpoints, irrespective of that sign.
    h = tuple(_intersect(value, Fraction(0), Fraction(1)) for value in h_intervals)
    return (
        tuple(min(a.lower, b.lower) for a, b in zip(h[:-1], h[1:], strict=True)),
        tuple(max(a.upper, b.upper) for a, b in zip(h[:-1], h[1:], strict=True)),
    )


def coefficient_bounds(
    geometry: Geometry, edges: tuple[Fraction, ...], q_bounds: tuple[Interval, ...]
) -> RingBounds:
    """Bound the true measure with monotone h; no saved finite ring mass enters."""
    _edges(geometry, edges)
    if (
        type(q_bounds) is not tuple
        or len(q_bounds) != len(edges)
        or any(type(value) is not Interval for value in q_bounds)
    ):
        raise TypeError("Every original endpoint requires its raw Q enclosure")
    constrained = _constrained_q(q_bounds)
    h = tuple(geometry.angular(Jet.constant(radius, 0)).value for radius in edges)
    lower, upper = _h_weights(h)
    k = _intersect(
        _weighted_mass(constrained, (Fraction(1),) * (len(edges) - 1)),
        Fraction(0),
        Fraction(1),
    )
    first = Interval(
        _weighted_mass(constrained, lower).lower,
        _weighted_mass(constrained, upper).upper,
    )
    # Complementarity is applied to each symbolic weight, before interval
    # evaluation; independently subtracting evaluated K and B1 loses shared Q.
    second = Interval(
        _weighted_mass(constrained, tuple(1 - value for value in upper)).lower,
        _weighted_mass(constrained, tuple(1 - value for value in lower)).upper,
    )
    return RingBounds(
        geometry,
        edges,
        q_bounds,
        constrained,
        h,
        k,
        _intersect(first, Fraction(0), k.upper),
        _intersect(second, Fraction(0), k.upper),
    )


def deposition_bounds(
    bounds: RingBounds, first_cover: Fraction, second_cover: Fraction
) -> Interval:
    """Keep the affine field and shared cumulative mass in one signed form."""
    if type(first_cover) is not Fraction or type(second_cover) is not Fraction:
        raise TypeError("Exact finite cover coordinates required")
    lower, upper = _h_weights(bounds.h_intervals)
    difference = first_cover - second_cover
    lo, hi = (lower, upper) if difference >= 0 else (upper, lower)
    lower_weights = tuple(second_cover + difference * value for value in lo)
    upper_weights = tuple(second_cover + difference * value for value in hi)
    result = Interval(
        _weighted_mass(bounds.constrained_q_bounds, lower_weights).lower,
        _weighted_mass(bounds.constrained_q_bounds, upper_weights).upper,
    )
    # An affine mixture lies between its two exact inputs, even when signed.
    physical = (
        Interval(min(first_cover, second_cover), max(first_cover, second_cover))
        * bounds.homogeneous
    )
    return _intersect(result, physical.lower, physical.upper)


@dataclass(frozen=True)
class RingCaseResult:
    endpoints: tuple[IntegralResult | None, ...]
    refusals: tuple[str | None, ...]
    bounds: RingBounds | None
    refusal: str | None


@dataclass(frozen=True)
class RingPopulationResult:
    results: tuple[RingCaseResult, ...]
    budgets: tuple[WorkBudget, ...]
    elapsed_seconds: float


@dataclass
class _Endpoint:
    function: Integrand
    queue: list[tuple[Fraction, int, Panel]]
    lower: Fraction
    upper: Fraction
    sequence: int = 0

    @property
    def width(self) -> Fraction:
        return self.upper - self.lower

    def result(self, refusal: str | None) -> IntegralResult:
        closed = self.width <= Q_TARGET
        return IntegralResult(
            Interval(self.lower, self.upper),
            tuple(row[2] for row in sorted(self.queue, key=lambda row: row[1])),
            "certified_width" if closed else "refuse_unresolved",
            None if closed else refusal,
            SEVEN_NODE_RULE,
        )


def _refine(endpoint: _Endpoint, budget: WorkBudget, queue_size: int) -> None:
    budget.check()
    if queue_size + 1 > budget.max_queue:
        raise ResourceRefusal("queue_ceiling")
    parent = endpoint.queue[0][2]
    left, right = parent.box[0]
    midpoint = (left + right) / 2
    budget.add_leaf()
    children = [
        positive_panel(endpoint.function, ((a, b),), budget, rule=SEVEN_NODE_RULE)
        for a, b in ((left, midpoint), (midpoint, right))
    ]
    heapq.heappop(endpoint.queue)
    endpoint.lower -= parent.enclosure.lower
    endpoint.upper -= parent.enclosure.upper
    for child in children:
        endpoint.sequence += 1
        heapq.heappush(
            endpoint.queue, (-child.enclosure.width, endpoint.sequence, child)
        )
        endpoint.lower += child.enclosure.lower
        endpoint.upper += child.enclosure.upper


def enclose_ring_population(
    geometries: tuple[Geometry, ...],
    edges: tuple[tuple[Fraction, ...], ...],
    *,
    wall_seconds: float = 160,
    max_leaves: int = 4096,
    max_attempts: int = 8191,
    max_nodes: int = 73719,
    max_queue: int = 4096,
) -> RingPopulationResult:
    """Initialize all endpoint populations round-robin, then refine raw widths."""
    if (
        type(geometries) is not tuple
        or not 1 <= len(geometries) <= 6
        or type(edges) is not tuple
        or len(edges) != len(geometries)
    ):
        raise TypeError("One to six exact geometry/edge populations required")
    for geometry, radii in zip(geometries, edges, strict=True):
        _edges(geometry, radii)
    if (
        type(wall_seconds) not in (int, float)
        or not math.isfinite(wall_seconds)
        or not 0 < wall_seconds <= 160
    ):
        raise ValueError("Endpoint work may only lower its 160-second ceiling")
    started = time.monotonic()
    budgets = tuple(
        WorkBudget(
            max_leaves=max_leaves,
            max_attempts=max_attempts,
            max_nodes=max_nodes,
            max_queue=max_queue,
            wall_seconds=wall_seconds,
            started=started,
        )
        for _ in geometries
    )
    states: list[list[_Endpoint | None]] = [[None] * len(radii) for radii in edges]
    reasons: list[list[str | None]] = [[None] * len(radii) for radii in edges]
    frozen: list[str | None] = [None] * len(geometries)
    for j in range(max(map(len, edges))):
        for i, (geometry, radii, budget) in enumerate(
            zip(geometries, edges, budgets, strict=True)
        ):
            if j >= len(radii):
                continue
            if frozen[i] is not None:
                reasons[i][j] = f"not_executed:{frozen[i]}"
                continue
            attempted_before = budget.attempts
            try:
                budget.check()
                if j >= budget.max_queue:
                    raise ResourceRefusal("queue_ceiling")
                budget.add_leaf()
                operator = _q_operator(geometry, radii[j])
                function = _integrand(operator)
                box: Box = ((Fraction(0), Fraction(1)),)
                panel = positive_panel(function, box, budget, rule=SEVEN_NODE_RULE)
                enclosure = panel.enclosure
                states[i][j] = _Endpoint(
                    function,
                    [(-enclosure.width, 0, panel)],
                    enclosure.lower,
                    enclosure.upper,
                )
            except ResourceRefusal as error:
                frozen[i] = str(error)
                prefix = (
                    "initial_panel_unclosed"
                    if budget.attempts > attempted_before
                    else "not_executed"
                )
                reasons[i][j] = f"{prefix}:{error}"
    while True:
        active = [
            (i, j, value)
            for i, rows in enumerate(states)
            if frozen[i] is None
            for j, value in enumerate(rows)
            if value is not None and value.width > Q_TARGET
        ]
        if not active:
            break
        i, j, value = min(active, key=lambda row: (-row[2].width, row[0], row[1]))
        try:
            queue_size = sum(len(item.queue) for item in states[i] if item is not None)
            _refine(value, budgets[i], queue_size)
        except ResourceRefusal as error:
            frozen[i] = str(error)
    results = []
    for i, (geometry, radii) in enumerate(zip(geometries, edges, strict=True)):
        endpoints = tuple(
            value.result(frozen[i]) if value is not None else None
            for value in states[i]
        )
        dispositions = tuple(
            reasons[i][j] if value is None else value.refusal
            for j, value in enumerate(endpoints)
        )
        complete = all(value is not None for value in endpoints)
        bounds = (
            coefficient_bounds(
                geometry,
                radii,
                tuple(value.enclosure for value in endpoints if value is not None),
            )
            if complete
            else None
        )
        refusal = (
            frozen[i] if complete else f"incomplete_endpoint_population:{frozen[i]}"
        )
        results.append(RingCaseResult(endpoints, dispositions, bounds, refusal))
    return RingPopulationResult(tuple(results), budgets, time.monotonic() - started)
