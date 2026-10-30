"""Independent dyadic coverage and fixed-leaf positive quadrature replay."""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
import math
from typing import Any, cast

from ..arithmetic import Interval, Jet
from .contracts import (
    EPSILON,
    PEANO_DIVISOR,
    RULE,
    WEIGHTS,
    Box,
    Clock,
    Function,
    VerificationError,
    _same_json,
    bounds,
    encoded,
    overlaps,
    rational,
    require,
)
from .geometry import Geometry


def _box(value: object, dimensions: int) -> Box:
    require(
        isinstance(value, list) and len(value) == dimensions, "Leaf dimension differs"
    )
    result = []
    for pair in cast(list[Any], value):
        require(
            isinstance(pair, list) and len(pair) == 2, "Leaf coordinate pair missing"
        )
        a, b = map(rational, pair)
        width = b - a
        require(0 <= a < b <= 1, "Leaf outside original unit domain")
        require(
            width.numerator == 1
            and width.denominator & (width.denominator - 1) == 0
            and (a / width).denominator == 1,
            "Leaf is not an aligned dyadic rectangle",
        )
        result.append((a, b))
    return tuple(result)


def _coverage(boxes: list[Box], dimensions: int, clock: Clock) -> None:
    require(bool(boxes), "Empty leaf population")
    pending = [((((Fraction(0), Fraction(1)),) * dimensions), boxes)]
    while pending:
        clock.check()
        root, leaves = pending.pop()
        if len(leaves) == 1:
            require(leaves[0] == root, "Missing domain coverage")
            continue
        for axis, (a, b) in enumerate(root):
            midpoint = (a + b) / 2
            left = [leaf for leaf in leaves if leaf[axis][1] <= midpoint]
            right = [leaf for leaf in leaves if leaf[axis][0] >= midpoint]
            if left and right and len(left) + len(right) == len(leaves):
                one = list(root)
                two = list(root)
                one[axis] = (a, midpoint)
                two[axis] = (midpoint, b)
                pending.extend(((tuple(one), left), (tuple(two), right)))
                break
        else:
            raise VerificationError("Overlapping or nonpartitioning dyadic leaves")


def replay_leaf(
    function: Function, box: Box, clock: Clock
) -> tuple[Interval, Fraction, tuple[Fraction, ...]]:
    """Evaluate one saved leaf with independent node and error arithmetic."""
    clock.check()
    dimensions = len(box)
    lengths = tuple(b - a for a, b in box)
    volume = math.prod(lengths)
    radii = []
    for axis in range(dimensions):
        arguments = tuple(
            Jet.variable(Interval(a, b), 8)
            if axis == j
            else Jet.constant(Interval(a, b), 8)
            for j, (a, b) in enumerate(box)
        )
        derivative = function(arguments)
        require(derivative.order == 8, "Independent derivative order differs")
        radii.append(
            volume
            * lengths[axis] ** 8
            * math.factorial(8)
            * derivative.coefficients[8].magnitude
            / PEANO_DIVISOR
        )
        clock.check()
    total = Interval.point(0)
    for first, weight in enumerate(WEIGHTS):
        for second in range(7 if dimensions == 2 else 1):
            indices = (first, second)[:dimensions]
            arguments = tuple(
                Jet.constant(a + (b - a) * index / 6, 0)
                for (a, b), index in zip(box, indices, strict=True)
            )
            total += (
                function(arguments).value
                * weight
                * (WEIGHTS[second] if dimensions == 2 else 1)
            )
            clock.check()
    node_sum = total * (volume / Fraction(840**dimensions))
    return node_sum, sum(radii, Fraction(0)), tuple(radii)


def verify_certificate(
    value: Mapping[str, Any], geometry: Geometry, clock: Clock
) -> dict[str, Any]:
    """Check the complete saved leaf partition and coefficient enclosure."""
    require(
        value.get("schema_version") == "continuous-receiver-coefficient-certificate.v3"
        and value.get("quadrature_rule") == RULE,
        "Unknown conditioned certificate/rule",
    )
    require(
        value.get("partition_schema") == "continuous-receiver-dyadic-radial.v1"
        and value.get("geometry") == geometry.encoded(),
        "Foreign original geometry",
    )
    bands = geometry.bands()
    require(
        _same_json(
            value.get("radial_bands"),
            [
                {"index": i, "bounds_m": [str(a), str(b)]}
                for i, (a, b) in enumerate(bands)
            ],
        ),
        "Missing/overlapping/foreign bands",
    )
    radial_count = len(bands) + 1
    rows = cast(list[dict[str, Any]], value.get("integrals"))
    require(
        isinstance(rows, list) and len(rows) == radial_count + 2,
        "Incomplete domain population",
    )
    saved = []
    independent = []
    local = []
    leaves_total = 0
    nodes_total = 0
    ancestor_attempts = 0
    ancestor_nodes = 0
    ancestor_derivatives = 0
    for index, row in enumerate(rows):
        clock.current_domain = index
        clock.check()
        dimensions = 1 if index < 2 else 2
        require(row.get("quadrature_rule") == RULE, "Mixed integral rule")
        leaves = cast(list[dict[str, Any]], row.get("leaves"))
        require(
            isinstance(leaves, list) and 0 < len(leaves) <= 4096,
            "Invalid leaf population",
        )
        leaves_total += len(leaves)
        ancestor_attempts += 2 * len(leaves) - 1
        ancestor_nodes += (2 * len(leaves) - 1) * 7**dimensions
        ancestor_derivatives += dimensions * (2 * len(leaves) - 1)
        require(leaves_total <= 4096, "Case leaf cap exceeded")
        boxes = [_box(leaf.get("box"), dimensions) for leaf in leaves]
        _coverage(boxes, dimensions, clock)
        native_total = Interval.point(0)
        oracle_total = Interval.point(0)
        for leaf, box in zip(leaves, boxes, strict=True):
            require(leaf.get("quadrature_rule") == RULE, "Mixed leaf rule")
            node = bounds(leaf.get("node_sum"))
            radius = rational(leaf.get("error_radius"))
            directions = tuple(rational(x) for x in leaf.get("directional_radii", []))
            require(
                len(directions) == dimensions
                and all(x >= 0 for x in directions)
                and radius == sum(directions, Fraction(0)),
                "Negative/inconsistent Peano radius",
            )
            native_total += node.expanded(radius)
            own_node, own_radius, _ = replay_leaf(geometry.function(index), box, clock)
            overlaps(node, own_node, f"domain{index} node sum")
            leaf_own = own_node.expanded(own_radius)
            overlaps(node.expanded(radius), leaf_own, f"domain{index} leaf enclosure")
            oracle_total += leaf_own
            nodes_total += 7**dimensions
            clock.completed_leaves += 1
        require(bounds(row.get("bounds")) == native_total, "Saved domain sum differs")
        overlaps(native_total, oracle_total, f"domain{index} integral")
        target = EPSILON / 32 if index < 2 else EPSILON / (8 * radial_count)
        require(
            row.get("status")
            == (
                "certified_width"
                if native_total.width <= target
                else "refuse_unresolved"
            ),
            "Local status falsified",
        )
        saved.append(native_total)
        independent.append(oracle_total)
        local.append(native_total.width <= target)
    domains = cast(list[dict[str, Any]], value.get("radial_domains"))
    require(
        isinstance(domains, list) and len(domains) == radial_count,
        "Missing radial mappings",
    )
    for i, domain in enumerate(domains):
        band_index = 0 if i < 2 else i - 1
        a, b = bands[band_index]
        expected = {
            "kind": "contact_triangle" if i < 2 else "regular_band",
            "patch": i + 1 if i < 2 else None,
            "band_index": band_index,
            "band_bounds_m": [str(a), str(b)],
            "original_receiver_radius_m": str(geometry.receiver),
            "integral_index": i + 2,
            "quadrature_rule": RULE,
            "target_full_width": str(EPSILON / (8 * radial_count)),
            "bounds": encoded(saved[i + 2]),
        }
        require(
            _same_json(domain, expected), "Radial mapping/ownership/allocation differs"
        )
    require(
        value.get("radial_full_width_budget") == str(EPSILON / 8),
        "Global radial budget differs",
    )
    radial = sum(saved[2:], Interval.point(0))
    require(
        bounds(value.get("radial_sum_bounds")) == radial, "Global radial sum falsified"
    )
    products = tuple(bounds(x) for x in value.get("endpoint_products", []))
    require(len(products) == 2, "Endpoint products missing")
    for i, r in enumerate((geometry.receiver, geometry.outer)):
        overlaps(products[i], geometry.mean(r) * saved[i], "endpoint product")
    k = saved[0] - saved[1]
    first = products[0] - products[1] + radial
    second = k - first
    original = (k, first, second)
    math_bounds = cast(dict[str, Any], value.get("coefficient_bounds"))
    require(
        isinstance(math_bounds, dict) and set(math_bounds) == {"K", "B1", "B2"},
        "Coefficient population differs",
    )
    require(
        all(
            bounds(math_bounds[name]) == actual
            for name, actual in zip(("K", "B1", "B2"), original, strict=True)
        ),
        "Complementary assembly falsified",
    )
    own_k = independent[0] - independent[1]
    own_first = (
        geometry.mean(geometry.receiver) * independent[0]
        - geometry.mean(geometry.outer) * independent[1]
        + sum(independent[2:], Interval.point(0))
    )
    own = (own_k, own_first, own_k - own_first)
    for name, native_bound, oracle_bound in zip(
        ("K", "B1", "B2"), original, own, strict=True
    ):
        overlaps(native_bound, oracle_bound, name)
    final_pass = all(item.width <= EPSILON for item in original)
    require(
        value.get("status")
        == ("certified_width" if final_pass else "refuse_unresolved"),
        "Final width status falsified",
    )
    product_pass = all(item.width <= EPSILON / 16 for item in products)
    return {
        "saved_bounds": {
            name: encoded(item)
            for name, item in zip(("K", "B1", "B2"), original, strict=True)
        },
        "independent_bounds": {
            name: encoded(item)
            for name, item in zip(("K", "B1", "B2"), own, strict=True)
        },
        "independent_widths": {
            name: str(item.width)
            for name, item in zip(("K", "B1", "B2"), own, strict=True)
        },
        "all_final_widths_pass": final_pass,
        "independent_all_final_widths_pass": all(item.width <= EPSILON for item in own),
        "positive_bounds_usable": all(item.lower > 0 for item in original),
        "independent_positive_bounds_usable": all(item.lower > 0 for item in own),
        "local_integral_allocations_pass": all(local),
        "endpoint_product_allocations_pass": product_pass,
        "local_allocations_pass": all(local) and product_pass,
        "leaves": leaves_total,
        "fixed_node_evaluations": nodes_total,
        "minimum_attempted_panels": ancestor_attempts,
        "minimum_completed_nodes": ancestor_nodes,
        "minimum_derivative_boxes": ancestor_derivatives,
        "initial_domains": radial_count + 2,
    }
