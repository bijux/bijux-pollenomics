"""Exact covariance existence for a declared laminar uncertainty hierarchy."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True, slots=True)
class LengthInterval:
    """An explicit closed interval for one nonnegative uncertainty magnitude."""

    lower: Fraction
    upper: Fraction

    def __post_init__(self) -> None:
        """Require exact rational bounds; no floating tolerance is inferred."""
        if (
            not isinstance(self.lower, Fraction)
            or not isinstance(self.upper, Fraction)
            or not 0 <= self.lower <= self.upper
        ):
            raise ValueError("Ordered nonnegative exact Fraction bounds required")


@dataclass(frozen=True, slots=True)
class NodeLengthAssessment:
    """Subtree feasibility before ancestor constraints, with exact sum margins."""

    variable: str
    supplied: LengthInterval
    children: tuple[str, ...] | None
    sum_range: LengthInterval | None
    attainable: LengthInterval | None
    lower_overlap_margin: Fraction | None
    upper_overlap_margin: Fraction | None
    refusal: str | None


@dataclass(frozen=True, slots=True)
class LaminarUncertaintyAssessment:
    """A conditional covariance existence result for exactly the supplied sums."""

    nodes: tuple[NodeLengthAssessment, ...]
    roots: tuple[str, ...]
    ungrouped_variables: tuple[str, ...]

    @property
    def feasible(self) -> bool:
        """Every component of the declared forest admits a covariance."""
        return all(node.attainable is not None for node in self.nodes)


def _identity(value: str) -> None:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError("Exact nonempty variable identities required")


def _structure(
    lengths: Mapping[str, LengthInterval], groups: Mapping[str, tuple[str, ...]]
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    if not lengths:
        raise ValueError("A nonempty uncertainty variable population required")
    for name, interval in lengths.items():
        _identity(name)
        if not isinstance(interval, LengthInterval):
            raise ValueError("Typed uncertainty length intervals required")
    parents: dict[str, str] = {}
    for name, children in groups.items():
        _identity(name)
        if name not in lengths or not isinstance(children, tuple):
            raise ValueError(
                "Every group needs a supplied interval and tuple of children"
            )
        for child in children:
            _identity(child)
            if child not in lengths:
                raise ValueError(
                    "Every child needs its own supplied uncertainty interval"
                )
            if child in parents:
                raise ValueError(
                    "Duplicate children or overlapping multiple-parent groups refused"
                )
            parents[child] = name
    # Single-parent components are trees or contain a directed cycle. Peeling
    # their leaves gives a child-before-parent order without recursion limits.
    remaining = {name: len(groups.get(name, ())) for name in lengths}
    ready = [name for name, count in remaining.items() if count == 0]
    order = []
    while ready:
        name = ready.pop()
        order.append(name)
        if name in parents:
            parent = parents[name]
            remaining[parent] -= 1
            if remaining[parent] == 0:
                ready.append(parent)
    if len(order) != len(lengths):
        raise ValueError("Cycles or self-referential uncertainty sums refused")
    roots = tuple(name for name in lengths if name not in parents)
    ungrouped = tuple(name for name in roots if name not in groups)
    return tuple(order), roots, ungrouped


def sum_length_range(children: tuple[LengthInterval, ...]) -> LengthInterval:
    """Return every attainable norm of a sum of freely oriented vectors.

    Child vector lengths may range over their supplied closed intervals. Their
    directions are unrestricted, not statistically independent. The largest
    norm is the sum of upper bounds. The smallest is the largest child lower
    bound minus all other upper bounds, floored at zero. A zero-child sum is
    identically zero, and a one-child sum preserves that child's interval.
    """
    if not isinstance(children, tuple) or any(
        not isinstance(c, LengthInterval) for c in children
    ):
        raise ValueError("An explicit tuple of typed child length intervals required")
    upper = sum((child.upper for child in children), Fraction())
    lower = max(
        [Fraction(), *(child.lower - (upper - child.upper) for child in children)]
    )
    return LengthInterval(lower, upper)


def assess_laminar_uncertainty(
    lengths: Mapping[str, LengthInterval], groups: Mapping[str, tuple[str, ...]]
) -> LaminarUncertaintyAssessment:
    """Decide existence of one real PSD covariance for the declared tree sums.

    Represent centered errors by Gram vectors: uncertainty is vector norm and
    a sum identity is vector addition. Each node's attainable norm interval is
    its supplied interval intersected with sum_length_range of its children.
    The polygon inequalities are necessary and sufficient locally. Conversely,
    choose an attainable root vector and realize its child sum; each child's
    entire subtree can be rotated or reflected to that vector without changing
    any internal norm or sum. Recursion proves simultaneous feasibility, even
    in one shared plane. A zero resultant has no orientation obstruction.

    The structural admission requires disjoint children, at most one parent
    per variable, and no cycles. Shared/overlapping leaf constraints are not
    approximated by independent tests. An empty child tuple declares a constant
    centered error, requiring zero uncertainty; a missing group declares a leaf.

    All magnitudes must use the same units and uncertainty meaning. A zero
    root interval imposes a caller-declared constant total; neither biological
    exhaustiveness nor observed mean closure is inferred here. Ungrouped
    variables are reported and impose no sum constraints. For a partial PFT
    hierarchy, this establishes only its declared identities, not all omitted
    taxon-to-PFT relationships or the original producer's covariance.

    Recorded decimals can be supplied as exact point intervals. Wider intervals
    require an explicit external rounding/admission model; no decimal rounding
    envelope, confidence level or numerical tolerance is manufactured. A PSD
    covariance does not establish a bounded random composition with specified
    means, identify shared draws, or reproduce a historical delta method.
    """
    order, roots, ungrouped = _structure(lengths, groups)
    assessments: dict[str, NodeLengthAssessment] = {}
    for name in order:
        supplied = lengths[name]
        children = groups.get(name)
        if children is None:
            assessments[name] = NodeLengthAssessment(
                name, supplied, None, None, supplied, None, None, None
            )
            continue
        attainable_children = tuple(assessments[child].attainable for child in children)
        if any(child is None for child in attainable_children):
            assessments[name] = NodeLengthAssessment(
                name, supplied, children, None, None, None, None, "child_sum_infeasible"
            )
            continue
        admitted = tuple(child for child in attainable_children if child is not None)
        possible = sum_length_range(admitted)
        lower, upper = (
            max(supplied.lower, possible.lower),
            min(supplied.upper, possible.upper),
        )
        feasible = lower <= upper
        assessments[name] = NodeLengthAssessment(
            name,
            supplied,
            children,
            possible,
            LengthInterval(lower, upper) if feasible else None,
            supplied.upper - possible.lower,
            possible.upper - supplied.lower,
            None if feasible else "sum_length_outside_supplied_interval",
        )
    return LaminarUncertaintyAssessment(
        tuple(assessments[name] for name in lengths), roots, ungrouped
    )
