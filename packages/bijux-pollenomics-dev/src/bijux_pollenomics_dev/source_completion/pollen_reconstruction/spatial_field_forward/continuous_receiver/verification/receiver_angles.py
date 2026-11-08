"""Independent cosine primitives and complete receiver-angle certificate replay."""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction as F
import math
from typing import Any, cast

from ..arithmetic import Interval, Jet, pi_bounds
from .certificates import _box, _coverage, replay_leaf
from .contracts import (
    EPSILON,
    RULE,
    Clock,
    Function,
    _same_json,
    bounds,
    encoded,
    overlaps,
    rational,
    require,
)
from .geometry import Geometry


def _constrain(value: Jet, low: F, high: F) -> Jet:
    """Apply a proved true-parameter range only to the value coefficient."""
    return Jet(
        (Interval(max(low, value.value.lower), min(high, value.value.upper)),)
        + value.coefficients[1:]
    )


def _moments(theta: Jet, sine: Jet, cosine: Jet) -> tuple[Jet, ...]:
    """Integrate cos^n first, then subtract C_m-C_(m+2) to obtain sin²cos^m."""
    primitives = [theta, sine]
    for n in range(2, 13):
        primitives.append((sine * cosine ** (n - 1) + (n - 1) * primitives[n - 2]) / n)
    return tuple(primitives[n] - primitives[n + 2] for n in range(11))


def _full(order: int) -> tuple[Jet, ...]:
    """Use closed beta-integral coefficients rather than the producer recurrence."""
    return tuple(
        Jet.constant(
            0
            if n % 2
            else pi_bounds()
            * F(math.comb(n, n // 2), 2 * 4 ** (n // 2) * (n // 2 + 1)),
            order,
        )
        for n in range(11)
    )


class ReceiverAngles:
    """An observer formula with no dependency on producer angle-moment helpers."""

    def __init__(self, geometry: Geometry) -> None:
        """Derive normalized invariants and the original whole-integral error."""
        require(
            type(geometry) is Geometry
            and len(geometry.first) == len(geometry.second) == 2
            and geometry.outer > 3 * geometry.receiver,
            "Unsupported original receiver-angle geometry",
        )
        self.geometry = geometry
        aa, bb, self.dot, self.n, self.difference = geometry.anchors()
        self.delta = bb - aa
        self.floor = (aa + bb) ** 2 - 4 * self.dot**2
        self.q = F(0)
        self.radius = F(0)
        if self.delta:
            require(self.n > 0 and self.floor > 0, "Positive anchor floor required")
            root = Interval.point(self.floor).root(2).lower
            require(root > 0, "Anchor root floor is unresolved")
            displacement = 2 * geometry.receiver * (geometry.outer + geometry.receiver)
            self.q = 2 * displacement / root + 4 * displacement**2 / self.floor
            require(self.q < F(14, 15), "Unproved angular series radius")
            first_tail = math.prod(F(2 * k + 3, 2 * k + 2) for k in range(6))
            tail = first_tail * self.q**6 / (1 - F(15, 14) * self.q)
            error = (geometry.outer + geometry.receiver) ** 2 * abs(self.delta)
            self.radius = Interval.outward(F(0), error * tail / (self.n * root)).upper
        regions = [("inner_cap", F(0), 2 * geometry.receiver)]
        left, end = 2 * geometry.receiver, geometry.outer - geometry.receiver
        while left < end:
            require(len(regions) <= 11, "Uncovered displacement tail")
            right = min(2 * left, end)
            regions.append(("full_angle_band", left, right))
            left = right
        regions.append(("outer_cap", end, geometry.outer + geometry.receiver))
        self.regions = tuple(regions)

    def _contract(self, distance: Jet, moments: tuple[Jet, ...]) -> Jet:
        """Contract a Horner coefficient vector, independently of binomial powers."""
        centered = self.geometry.receiver**2 + distance**2 - self.dot
        scale = 1 + centered**2 * (4 / self.floor)
        shift = 2 * self.geometry.receiver * distance
        linear = centered * shift * (8 / self.floor) / scale
        square = shift**2 * (4 / self.floor) / scale
        coefficients = [F(1)]
        for k in range(5):
            coefficients.append(-coefficients[-1] * F(2 * k + 3, 2 * k + 2))
        polynomial = [Jet.constant(coefficients[-1], distance.order)]
        for coefficient in reversed(coefficients[:-1]):
            following = [
                Jet.constant(0, distance.order) for _ in range(len(polynomial) + 2)
            ]
            for index, term in enumerate(polynomial):
                following[index + 1] += linear * term
                following[index + 2] += square * term
            following[0] += coefficient
            polynomial = following
        angular = sum(
            (
                coefficient * moment
                for coefficient, moment in zip(polynomial, moments, strict=True)
            ),
            Jet.constant(0, distance.order),
        )
        normalization = (-2 * self.delta / self.n) / Interval.point(self.floor).root(2)
        return angular * normalization / scale.root(2) ** 3

    def function(self, index: int) -> Function:
        """Return independent endpoint or complete displacement-domain equations."""
        if index < 2:
            return self.geometry.function(index)
        kind, left, right = self.regions[index - 2]

        def evaluate(arguments: tuple[Jet, ...]) -> Jet:
            require(len(arguments) == 1, "One independent coordinate required")
            t = arguments[0]
            require(
                0 <= t.value.lower <= t.value.upper <= 1, "Unit coordinate required"
            )
            if not self.delta:
                return Jet.constant(0, t.order)
            r, outer = self.geometry.receiver, self.geometry.outer
            pi = Jet.constant(pi_bounds(), t.order)
            if kind == "inner_cap":
                eta = pi * t**8 / 2
                sinc = _constrain(eta.sinc(), (2 / pi_bounds()).lower, F(1))
                sine = _constrain(eta * sinc, F(0), F(1))
                cosine = _constrain(eta.sin_cos()[1], F(0), F(1))
                distance = 2 * r * sine
                power = t * (2 * r * (pi / 2) * sinc).root(8)
                measure = 32 * r**2 * t**7 * sine * cosine
                moments = _moments(pi / 2 + eta, cosine, -sine)
            elif kind == "full_angle_band":
                x = 1 + ((right - left) / left) * t
                distance = left * x
                power = x.root(8) * Interval.point(left).root(8)
                measure = 2 * left * (right - left) * x / pi
                moments = _full(t.order)
            else:
                theta = pi * t
                raw_sine, cosine = theta.sin_cos()
                sine = _constrain(raw_sine, F(0), F(1))
                rho = r / outer
                root = (1 - rho**2 * sine**2).root(2)
                distance = _constrain(outer * (root - rho * cosine), left, right)
                power = distance.root(8)
                measure = 2 * r * distance * sine * (1 - rho * cosine / root)
                moments = tuple(
                    full - partial
                    for full, partial in zip(
                        _full(t.order), _moments(theta, sine, cosine), strict=True
                    )
                )
            return (
                measure
                * (-self.geometry.coefficient * power).exp()
                * self._contract(distance, moments)
            )

        return evaluate


def verify_angle_certificate(
    value: Mapping[str, Any], geometry: Geometry, clock: Clock
) -> dict[str, Any]:
    """Replay every saved leaf and independently assemble all original coefficients."""
    oracle = ReceiverAngles(geometry)
    require(
        set(value)
        == {
            "schema_version",
            "method",
            "quadrature_rule",
            "geometry",
            "status",
            "coefficient_bounds",
            "endpoint_products",
            "approximation",
            "finite_radial_sum_bounds",
            "radial_sum_bounds",
            "radial_full_width_budget",
            "radial_quadrature_full_width_budget",
            "radial_domains",
            "integrals",
        },
        "Receiver-angle certificate fields differ",
    )
    require(
        value.get("schema_version") == "continuous-receiver-angle-moment-certificate.v1"
        and value.get("method") == "receiver-angle-moments.v1"
        and value.get("quadrature_rule") == RULE
        and _same_json(value.get("geometry"), geometry.encoded()),
        "Foreign receiver-angle certificate",
    )
    require(
        _same_json(
            value.get("approximation"),
            {
                "binomial_degree": 5,
                "maximum_angular_degree": 10,
                "q_bound": str(oracle.q),
                "remainder_radius": str(oracle.radius),
            },
        ),
        "Angular approximation witness differs",
    )
    radial_count = len(oracle.regions)
    radial_budget = EPSILON / 8 - 2 * oracle.radius
    require(radial_budget > 0, "Series tail exhausts original radial allowance")
    require(
        value.get("radial_full_width_budget") == str(EPSILON / 8)
        and value.get("radial_quadrature_full_width_budget") == str(radial_budget),
        "Original radial allocation differs",
    )
    rows = cast(list[dict[str, Any]], value.get("integrals"))
    require(
        isinstance(rows, list) and len(rows) == radial_count + 2, "Incomplete domains"
    )
    saved: list[Interval] = []
    independent: list[Interval] = []
    local: list[bool] = []
    leaves_total = 0
    for index, row in enumerate(rows):
        clock.current_domain = index
        clock.check()
        require(
            isinstance(row, dict)
            and set(row) == {"quadrature_rule", "status", "refusal", "bounds", "leaves"}
            and (row["refusal"] is None or isinstance(row["refusal"], str)),
            "Integral fields differ",
        )
        require(row.get("quadrature_rule") == RULE, "Mixed integral rule")
        leaves = cast(list[dict[str, Any]], row.get("leaves"))
        require(isinstance(leaves, list) and 0 < len(leaves) <= 4096, "Invalid leaves")
        leaves_total += len(leaves)
        require(leaves_total <= 4096, "Case leaf cap exceeded")
        boxes = [_box(leaf.get("box"), 1) for leaf in leaves]
        _coverage(boxes, 1, clock)
        native, oracle_integral = Interval.point(0), Interval.point(0)
        for leaf, box in zip(leaves, boxes, strict=True):
            require(
                isinstance(leaf, dict)
                and set(leaf)
                == {
                    "quadrature_rule",
                    "box",
                    "node_sum",
                    "error_radius",
                    "directional_radii",
                },
                "Leaf fields differ",
            )
            require(leaf.get("quadrature_rule") == RULE, "Mixed leaf rule")
            node = bounds(leaf.get("node_sum"))
            radius = rational(leaf.get("error_radius"))
            directional = [rational(x) for x in leaf.get("directional_radii", [])]
            require(directional == [radius] and radius >= 0, "Invalid Peano radius")
            own_node, own_radius, _ = replay_leaf(oracle.function(index), box, clock)
            overlaps(node, own_node, "receiver-angle fixed node sum")
            overlaps(node.expanded(radius), own_node.expanded(own_radius), "fixed leaf")
            native += node.expanded(radius)
            oracle_integral += own_node.expanded(own_radius)
            clock.completed_leaves += 1
        require(bounds(row.get("bounds")) == native, "Saved domain sum differs")
        target = EPSILON / 32 if index < 2 else radial_budget / radial_count
        passed = native.width <= target
        require(
            row.get("status") == ("certified_width" if passed else "refuse_unresolved"),
            "Local width status falsified",
        )
        saved.append(native)
        independent.append(oracle_integral)
        local.append(passed)
    expected_domains = [
        {
            "integral_index": index + 2,
            "kind": kind,
            "distance_bounds_m": [str(left), str(right)],
            "target_full_width": str(radial_budget / radial_count),
            "bounds": encoded(saved[index + 2]),
        }
        for index, (kind, left, right) in enumerate(oracle.regions)
    ]
    require(
        _same_json(value.get("radial_domains"), expected_domains),
        "Domain support differs",
    )
    finite = sum(saved[2:], Interval.point(0))
    radial = finite.expanded(oracle.radius)
    require(
        bounds(value.get("finite_radial_sum_bounds")) == finite
        and bounds(value.get("radial_sum_bounds")) == radial,
        "Whole-J tail is omitted, repeated or misplaced",
    )
    products = tuple(bounds(item) for item in value.get("endpoint_products", []))
    require(len(products) == 2, "Endpoint products missing")
    for index, radius in enumerate((geometry.receiver, geometry.outer)):
        overlaps(
            products[index], geometry.mean(radius) * saved[index], "endpoint product"
        )
    k = saved[0] - saved[1]
    first = products[0] - products[1] + radial
    original = (k, first, k - first)
    recorded = value.get("coefficient_bounds")
    require(
        isinstance(recorded, dict)
        and set(recorded) == {"K", "B1", "B2"}
        and all(
            bounds(recorded[name]) == actual
            for name, actual in zip(("K", "B1", "B2"), original, strict=True)
        ),
        "Complementary coefficient assembly differs",
    )
    own_k = independent[0] - independent[1]
    own_first = (
        geometry.mean(geometry.receiver) * independent[0]
        - geometry.mean(geometry.outer) * independent[1]
        + sum(independent[2:], Interval.point(0)).expanded(oracle.radius)
    )
    own = (own_k, own_first, own_k - own_first)
    for native, other in zip(original, own, strict=True):
        overlaps(native, other, "independent coefficient")
    success = all(item.width <= EPSILON for item in original)
    require(
        value.get("status") == ("certified_width" if success else "refuse_unresolved"),
        "Final width status falsified",
    )
    products_pass = all(item.width <= EPSILON / 16 for item in products)
    attempts = 2 * leaves_total - len(rows)
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
        "all_final_widths_pass": success,
        "independent_all_final_widths_pass": all(item.width <= EPSILON for item in own),
        "positive_bounds_usable": all(item.lower > 0 for item in original),
        "independent_positive_bounds_usable": all(item.lower > 0 for item in own),
        "local_integral_allocations_pass": all(local),
        "endpoint_product_allocations_pass": products_pass,
        "local_allocations_pass": all(local) and products_pass,
        "leaves": leaves_total,
        "fixed_node_evaluations": leaves_total * 7,
        "minimum_attempted_panels": attempts,
        "minimum_completed_nodes": attempts * 7,
        "minimum_derivative_boxes": attempts,
        "initial_domains": len(rows),
    }
