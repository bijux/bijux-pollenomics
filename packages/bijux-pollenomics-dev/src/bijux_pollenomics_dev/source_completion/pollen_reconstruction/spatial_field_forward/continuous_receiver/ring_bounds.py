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
COEFFICIENT_Q_TARGET = EPSILON / 16
CONTRIBUTION_STOP = "coefficient_q_uncertainty_met_raw_endpoint_width_unresolved"


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


def _mass_coefficients(weights: tuple[Fraction, ...]) -> tuple[Fraction, ...]:
    return (
        (weights[0],)
        + tuple(weights[i] - weights[i - 1] for i in range(1, len(weights)))
        + (-weights[-1],)
    )


def _weighted_mass(
    q_bounds: tuple[Interval, ...], weights: tuple[Fraction, ...]
) -> Interval:
    if len(weights) + 1 != len(q_bounds):
        raise ValueError("One exact weight per true radial mass required")
    return shared_q_linear(q_bounds, _mass_coefficients(weights))


@dataclass(frozen=True)
class RingBounds:
    """Store endpoint survival bounds and complementary ring coefficients."""

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
        """Report the final width test for each of the three coefficients."""
        return (
            self.homogeneous.width <= EPSILON,
            self.first.width <= EPSILON,
            self.second.width <= EPSILON,
        )

    @property
    def positive_bounds(self) -> tuple[bool, bool, bool]:
        """Report strict positivity of the three coefficient lower bounds."""
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
    return _assemble_bounds(geometry, edges, q_bounds, constrained, h)


def _assemble_bounds(
    geometry: Geometry,
    edges: tuple[Fraction, ...],
    q_bounds: tuple[Interval, ...],
    constrained: tuple[Interval, ...],
    h: tuple[Interval, ...],
) -> RingBounds:
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


def _coefficient_forms(h: tuple[Interval, ...]) -> dict[str, tuple[Fraction, ...]]:
    lower, upper = _h_weights(h)
    k = (Fraction(1),) + (Fraction(0),) * (len(h) - 2) + (Fraction(-1),)
    lo, hi = _mass_coefficients(lower), _mass_coefficients(upper)
    return {
        "K": k,
        "B1_lower": lo,
        "B1_upper": hi,
        "B2_lower": tuple(a - b for a, b in zip(k, hi, strict=True)),
        "B2_upper": tuple(a - b for a, b in zip(k, lo, strict=True)),
    }


def _q_spreads(
    q: tuple[Interval, ...], forms: dict[str, tuple[Fraction, ...]]
) -> dict[str, Fraction]:
    return {
        name: sum(
            (
                abs(coefficient) * value.width
                for coefficient, value in zip(coefficients, q, strict=True)
            ),
            Fraction(0),
        )
        for name, coefficients in forms.items()
    }


def coefficient_q_spreads(bounds: RingBounds) -> dict[str, Fraction]:
    """Exact Q-only box spreads; radial h ranges and rounding remain separate."""
    return _q_spreads(
        bounds.constrained_q_bounds, _coefficient_forms(bounds.h_intervals)
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
    """Retain all endpoint outcomes, coefficient bounds and case refusal."""

    endpoints: tuple[IntegralResult | None, ...]
    refusals: tuple[str | None, ...]
    bounds: RingBounds | None
    refusal: str | None


@dataclass(frozen=True)
class RingPopulationResult:
    """Retain every ring case with shared budgets and elapsed time."""

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


@dataclass
class _Contribution:
    h: tuple[Interval, ...]
    forms: dict[str, tuple[Fraction, ...]]
    sensitivity: tuple[Fraction, ...]
    constrained: tuple[Interval, ...] = ()
    priorities: tuple[Fraction, ...] = ()
    spreads: tuple[Fraction, ...] = ()

    @classmethod
    def build(cls, geometry: Geometry, edges: tuple[Fraction, ...]) -> _Contribution:
        h = tuple(geometry.angular(Jet.constant(radius, 0)).value for radius in edges)
        forms = _coefficient_forms(h)
        return cls(
            h,
            forms,
            tuple(
                max(abs(row[j]) for row in forms.values()) for j in range(len(edges))
            ),
        )

    def update(self, rows: list[_Endpoint | None]) -> None:
        if any(row is None for row in rows):
            raise ValueError(
                "Contribution priority requires the complete endpoint population"
            )
        self.constrained = _constrained_q(
            tuple(Interval(row.lower, row.upper) for row in rows if row is not None)
        )
        self.priorities = tuple(
            value.width * sensitivity
            for value, sensitivity in zip(
                self.constrained, self.sensitivity, strict=True
            )
        )
        self.spreads = tuple(_q_spreads(self.constrained, self.forms).values())

    @property
    def done(self) -> bool:
        return max(self.spreads) <= COEFFICIENT_Q_TARGET


def _contribution_stop(
    cache: _Contribution, rows: list[_Endpoint | None]
) -> str | None:
    if cache.done and any(row is not None and row.width > Q_TARGET for row in rows):
        return CONTRIBUTION_STOP
    return None


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
    priority: str = "raw_width",
) -> RingPopulationResult:
    """Close all roots, then use the declared raw or coefficient-Q objective.

    Contribution stopping bounds only the Q uncertainty in five affine forms.
    It does not qualify raw endpoint precision, the fixed-ring h envelope, final
    coefficient EPS, predictions, observations or field accuracy.
    """
    if type(priority) is not str or priority not in (
        "raw_width",
        "coefficient_contribution",
    ):
        raise ValueError("Unknown endpoint refinement priority")
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
    contributions: list[_Contribution | None] = [None] * len(geometries)
    if priority == "coefficient_contribution":
        for i, (geometry, radii) in enumerate(zip(geometries, edges, strict=True)):
            if all(value is not None for value in states[i]):
                new_cache = _Contribution.build(geometry, radii)
                new_cache.update(states[i])
                contributions[i] = new_cache
                if frozen[i] is None:
                    frozen[i] = _contribution_stop(new_cache, states[i])
    while True:
        active = (
            [
                (i, j, value)
                for i, rows in enumerate(states)
                if frozen[i] is None
                for j, value in enumerate(rows)
                if value is not None and value.width > Q_TARGET
            ]
            if priority == "raw_width"
            else [
                (i, j, value)
                for i, cache in enumerate(contributions)
                if frozen[i] is None and cache is not None and not cache.done
                for j, value in enumerate(states[i])
                if value is not None and cache.priorities[j] > 0
            ]
        )
        if not active:
            break

        def order(row: tuple[int, int, _Endpoint]) -> tuple[Fraction, int, int]:
            i, j, value = row
            cache = contributions[i]
            score = value.width if cache is None else cache.priorities[j]
            return -score, i, j

        i, j, value = min(active, key=order)
        try:
            queue_size = sum(len(item.queue) for item in states[i] if item is not None)
            _refine(value, budgets[i], queue_size)
            cache = contributions[i]
            if cache is not None:
                cache.update(states[i])
                frozen[i] = _contribution_stop(cache, states[i])
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
        cache = contributions[i]
        raw_q = tuple(value.enclosure for value in endpoints if value is not None)
        bounds = (
            _assemble_bounds(geometry, radii, raw_q, cache.constrained, cache.h)
            if complete and cache is not None
            else coefficient_bounds(geometry, radii, raw_q)
            if complete
            else None
        )
        refusal = (
            frozen[i] if complete else f"incomplete_endpoint_population:{frozen[i]}"
        )
        results.append(RingCaseResult(endpoints, dispositions, bounds, refusal))
    return RingPopulationResult(tuple(results), budgets, time.monotonic() - started)
