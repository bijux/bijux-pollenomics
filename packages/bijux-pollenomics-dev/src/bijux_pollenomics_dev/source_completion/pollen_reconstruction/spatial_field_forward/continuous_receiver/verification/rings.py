"""Independent survival-ring envelopes and closed prediction arithmetic.

The elementary interval library and the original-disk endpoint equations are
shared with the reviewed observer. Ring assembly uses independent exact linear
forms; it never imports the producer's quadrature, scheduler or ring assembly.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from fractions import Fraction
from typing import Any, cast

from ..arithmetic import Interval
from .certificates import _box, _coverage, replay_leaf
from .contracts import (
    EPSILON,
    RULE,
    Clock,
    bounds,
    encoded,
    integer,
    overlaps,
    rational,
    require,
)
from .geometry import Geometry


def constrain_survival(values: Sequence[Interval]) -> tuple[Interval, ...]:
    """Intersect with the proved decreasing survival law, retaining every edge."""
    require(2 <= len(values) <= 129, "Incomplete survival endpoint population")
    result = tuple(
        Interval(
            max(Fraction(0), *(v.lower for v in values[i:])),
            min(Fraction(1), *(v.upper for v in values[: i + 1])),
        )
        for i in range(len(values))
    )
    require(
        all(a.upper > b.lower for a, b in zip(result, result[1:], strict=False)),
        "No strictly decreasing survival selection",
    )
    return result


def telescope(values: Sequence[Interval], ring_weights: Sequence[Fraction]) -> Interval:
    """Evaluate one shared-Q linear form, with one outward rounding at closure."""
    require(
        len(values) == len(ring_weights) + 1 and bool(ring_weights),
        "Ring weight/endpoint populations differ",
    )
    require(all(type(a) is Fraction for a in ring_weights), "Exact weights required")
    coefficients = (
        ring_weights[0],
        *(b - a for a, b in zip(ring_weights, ring_weights[1:], strict=False)),
        -ring_weights[-1],
    )
    lower = sum(
        (
            c * (v.lower if c >= 0 else v.upper)
            for c, v in zip(coefficients, values, strict=True)
        ),
        Fraction(0),
    )
    upper = sum(
        (
            c * (v.upper if c >= 0 else v.lower)
            for c, v in zip(coefficients, values, strict=True)
        ),
        Fraction(0),
    )
    return Interval.outward(lower, upper)


def _means(geometry: Geometry, edges: Sequence[Fraction]) -> tuple[Interval, ...]:
    require(
        2 <= len(edges) <= 129
        and all(type(r) is Fraction for r in edges)
        and edges[0] == geometry.receiver
        and edges[-1] == geometry.outer
        and all(a < b for a, b in zip(edges, edges[1:], strict=False)),
        "Foreign, missing or unordered radial edges",
    )
    return tuple(
        Interval(max(Fraction(0), h.lower), min(Fraction(1), h.upper))
        for h in (geometry.mean(radius) for radius in edges)
    )


def ring_linear_bounds(
    geometry: Geometry,
    edges: Sequence[Fraction],
    survival: Sequence[Interval],
    first: Fraction,
    second: Fraction,
) -> Interval:
    """Enclose integral (first*h + second*(1-h)) d(-Q), before evaluation."""
    require(
        type(first) is Fraction and type(second) is Fraction,
        "Exact cover coefficients required",
    )
    require(len(edges) == len(survival), "Missing survival endpoint")
    q = constrain_survival(survival)
    means = _means(geometry, edges)
    aa, bb, _, _, _ = geometry.anchors()
    increasing = aa > bb
    lower_weights = []
    upper_weights = []
    for left, right in zip(means, means[1:], strict=False):
        lo = left.lower if increasing else right.lower
        hi = right.upper if increasing else left.upper
        difference = first - second
        lower_weights.append(second + difference * (lo if difference >= 0 else hi))
        upper_weights.append(second + difference * (hi if difference >= 0 else lo))
    lower = telescope(q, lower_weights).lower
    upper = telescope(q, upper_weights).upper
    mass = telescope(q, (Fraction(1),) * (len(q) - 1))
    physical = Interval(min(first, second), max(first, second)) * Interval(
        max(Fraction(0), mass.lower), min(Fraction(1), mass.upper)
    )
    lower, upper = max(lower, physical.lower), min(upper, physical.upper)
    require(lower <= upper, "Inconsistent ring envelope")
    return Interval(lower, upper)


def ring_coefficients(
    geometry: Geometry, edges: Sequence[Fraction], survival: Sequence[Interval]
) -> dict[str, Interval]:
    """Complement weights symbolically; never subtract independent K/B extremes."""
    q = constrain_survival(survival)
    _means(geometry, edges)
    require(len(edges) == len(q), "Missing survival endpoint")
    mass = telescope(q, (Fraction(1),) * (len(q) - 1))
    return {
        "K": Interval(max(Fraction(0), mass.lower), min(Fraction(1), mass.upper)),
        "B1": ring_linear_bounds(geometry, edges, q, Fraction(1), Fraction(0)),
        "B2": ring_linear_bounds(geometry, edges, q, Fraction(0), Fraction(1)),
    }


def verify_ring_case(
    value: Mapping[str, Any],
    geometry: Geometry,
    expected_edges: tuple[Fraction, ...],
    clock: Clock,
) -> dict[str, Any]:
    """Replay every closed endpoint; incomplete populations remain incomplete."""
    require(
        value.get("geometry") == geometry.encoded()
        and value.get("edges_exact") == [str(r) for r in expected_edges],
        "Ring case geometry/edge binding differs",
    )
    _means(geometry, expected_edges)
    rows = value.get("endpoints")
    refusals = value.get("endpoint_refusals")
    require(
        isinstance(rows, list)
        and isinstance(refusals, list)
        and len(rows) == len(refusals) == len(expected_edges),
        "Incomplete endpoint disposition inventory",
    )
    rows = cast(list[Any], rows)
    refusals = cast(list[Any], refusals)
    own: list[Interval | None] = []
    native: list[Interval] = []
    minimum_panels = 0
    leaves_total = 0
    target = Fraction(1, 10**10)
    for index, (radius, row, refusal) in enumerate(
        zip(expected_edges, rows, refusals, strict=True)
    ):
        clock.current_domain = index
        clock.check()
        if row is None:
            require(
                isinstance(refusal, str) and bool(refusal), "Missing endpoint refusal"
            )
            own.append(None)
            continue
        require(isinstance(row, dict), "Endpoint integral object required")
        require(row.get("quadrature_rule") == RULE, "Endpoint rule differs")
        leaves = row.get("leaves")
        require(isinstance(leaves, list) and bool(leaves), "Empty endpoint partition")
        leaves_total += len(leaves)
        require(leaves_total <= 4096, "Case accepted leaf cap exceeded")
        minimum_panels += 2 * len(leaves) - 1
        boxes = [_box(leaf.get("box"), 1) for leaf in leaves]
        _coverage(boxes, 1, clock)
        function = (
            geometry.function(0)
            if radius == geometry.receiver
            else Geometry(
                geometry.coefficient,
                geometry.receiver,
                radius,
                geometry.first,
                geometry.second,
            ).function(1)
        )
        saved_sum = Interval.point(0)
        independent_sum = Interval.point(0)
        for leaf, box in zip(leaves, boxes, strict=True):
            require(leaf.get("quadrature_rule") == RULE, "Mixed endpoint leaf rule")
            node = bounds(leaf.get("node_sum"))
            error = rational(leaf.get("error_radius"))
            require(
                error >= 0 and leaf.get("directional_radii") == [str(error)],
                "Invalid signed seven-node radius",
            )
            own_node, own_radius, _ = replay_leaf(function, box, clock)
            overlaps(node, own_node, "ring endpoint node sum")
            enclosure = node.expanded(error)
            own_enclosure = own_node.expanded(own_radius)
            overlaps(enclosure, own_enclosure, "ring endpoint Peano enclosure")
            saved_sum += enclosure
            independent_sum += own_enclosure
            clock.completed_leaves += 1
        require(bounds(row.get("bounds")) == saved_sum, "Endpoint integral sum differs")
        narrow = saved_sum.width <= target
        require(
            row.get("status") == ("certified_width" if narrow else "refuse_unresolved")
            and row.get("refusal") == refusal
            and (
                refusal is None
                if narrow
                else isinstance(refusal, str) and bool(refusal)
            ),
            "Endpoint width/refusal disposition differs",
        )
        native.append(saved_sum)
        own.append(independent_sum)
    work = value.get("work")
    require(isinstance(work, dict), "Case work accounting missing")
    work = cast(dict[str, Any], work)
    attempts = integer(work.get("attempted_panels"), "attempted panels", 8191)
    reserved = integer(work.get("reserved_node_evaluations"), "reserved nodes", 73719)
    completed = integer(
        work.get("completed_node_evaluations"), "completed nodes", 73719
    )
    derivatives = integer(work.get("derivative_boxes"), "derivative boxes", 8191)
    leaves = integer(work.get("leaf_reservations"), "leaf reservations", 4096)
    unattempted_reservation = int(isinstance(value.get("backend_refusal"), str))
    require(
        attempts >= minimum_panels
        and reserved == 7 * attempts
        and 7 * minimum_panels <= completed <= reserved
        and minimum_panels <= derivatives <= attempts
        and leaves_total <= leaves <= attempts + unattempted_reservation,
        "Endpoint ancestor work was reset or underreported",
    )
    complete = all(item is not None for item in own)
    require(
        value.get("raw_endpoint_widths_pass")
        is (complete and all(q.width <= target for q in native)),
        "Raw endpoint precision flag differs",
    )
    if not complete:
        require(
            value.get("coefficient_bounds") is None
            and value.get("all_final_widths_pass") is False
            and value.get("positive_bounds_usable") is False
            and isinstance(value.get("backend_refusal"), str),
            "Incomplete case promoted to coefficient certificate",
        )
        return {"complete": False, "own_q": own, "own_coefficients": None}
    claimed = value.get("coefficient_bounds")
    require(
        isinstance(claimed, dict) and set(claimed) == {"K", "B1", "B2"},
        "Coefficient population differs",
    )
    claimed = cast(dict[str, Any], claimed)
    claimed_intervals = {key: bounds(claimed[key]) for key in ("K", "B1", "B2")}
    require(
        value.get("all_final_widths_pass")
        is all(q.width <= EPSILON for q in claimed_intervals.values())
        and value.get("positive_bounds_usable")
        is all(q.lower > 0 for q in claimed_intervals.values()),
        "Coefficient precision/positivity flag differs",
    )
    independent = ring_coefficients(
        geometry, expected_edges, tuple(q for q in own if q is not None)
    )
    for key in claimed_intervals:
        overlaps(claimed_intervals[key], independent[key], f"ring {key}")
    return {
        "complete": True,
        "own_q": own,
        "own_coefficients": independent,
        "width_account": width_account(independent),
    }


def width_account(values: Mapping[str, Interval]) -> dict[str, Any]:
    require(set(values) == {"K", "B1", "B2"}, "Coefficient axis differs")
    return {
        "coefficient_bounds": {name: encoded(value) for name, value in values.items()},
        "full_widths_exact": {name: str(value.width) for name, value in values.items()},
        "all_original_epsilon_widths_pass": all(
            value.width <= EPSILON for value in values.values()
        ),
        "positive_lower_bounds": all(value.lower > 0 for value in values.values()),
    }
