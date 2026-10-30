"""Exact feasibility of a declared nondecreasing age function of core depth."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from itertools import groupby


def identity(value: str) -> None:
    """Preserve a supplied identity without normalization or inference."""
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError("An exact nonempty identity is required")


def finite(value: Decimal) -> None:
    """Allow signed native values while rejecting nonfinite measurements."""
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError("A finite Decimal is required")


@dataclass(frozen=True, slots=True)
class AgeComponent:
    """One possible-age set with closed lower and declared upper endpoint."""

    younger: Decimal
    older: Decimal
    older_inclusive: bool = True

    def __post_init__(self) -> None:
        """Require finite ordered endpoints and a nonempty upper-bound policy."""
        finite(self.younger)
        finite(self.older)
        if type(self.older_inclusive) is not bool or self.younger > self.older:
            raise ValueError("Ordered endpoints and an explicit upper policy required")
        if self.younger == self.older and not self.older_inclusive:
            raise ValueError("An open zero-width component is empty")

    def contains(self, age: Decimal) -> bool:
        """Test exact set membership, including isolated native endpoints."""
        return self.younger <= age and (
            age < self.older or self.older_inclusive and age == self.older
        )


@dataclass(frozen=True, slots=True)
class DepthAgeDomain:
    """A source sample's declared possible ages at its unchanged native depth."""

    sample_id: str
    depth: Decimal
    components: tuple[AgeComponent, ...]

    def __post_init__(self) -> None:
        """Require a finite depth and ordered disjoint native age components."""
        identity(self.sample_id)
        finite(self.depth)
        if not isinstance(self.components, tuple) or not self.components:
            raise ValueError("A nonempty explicit tuple of age components is required")
        if any(
            not isinstance(component, AgeComponent) for component in self.components
        ):
            raise ValueError("Typed possible-age components are required")
        for left, right in zip(self.components, self.components[1:], strict=False):
            if left.older > right.younger or (
                left.older == right.younger and left.older_inclusive
            ):
                raise ValueError(
                    "Components must be ordered and disjoint; no hull is inferred"
                )


@dataclass(frozen=True, slots=True)
class OrderedAge:
    """A constructive conditional age assignment, never a reestimated chronology."""

    sample_id: str
    depth: Decimal
    native_age: Decimal


@dataclass(frozen=True, slots=True)
class AgeOrderRefusal:
    """The first source domain that cannot extend the earliest feasible prefix."""

    sample_id: str
    depth: Decimal
    minimum_required_age: Decimal
    previous_depth_sample_ids: tuple[str, ...]
    equal_depth_sample_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AgeOrderAssessment:
    """Complete witness or a refusal under the explicitly declared order model."""

    core_id: str
    assignments: tuple[OrderedAge, ...]
    refusal: AgeOrderRefusal | None

    @property
    def attainable(self) -> bool:
        """Return whether every sample has a jointly ordered supported age."""
        return self.refusal is None


def assess_age_order(
    domains: Sequence[DepthAgeDomain], *, core_id: str
) -> AgeOrderAssessment:
    """Find the earliest supported nondecreasing ages, or prove infeasibility.

    This is a single-core conditional model: equal native depths must share
    one age, and age is nondecreasing with increasing depth. Intersect the
    disjoint domains within each equal-depth group, then choose the earliest
    common age at least the preceding group's age. Every domain has a closed
    lower endpoint. A later prefix cannot rescue a failed earliest prefix;
    induction therefore makes this greedy witness/refusal complete. Component
    cursors only advance; distinct-depth work is linear after sorting, while
    a tied group uses at most its size times its total component count.

    No domain is clipped, filled, repaired or replaced by its convex hull.
    Negative ages and age/depth ties remain literal. The caller must qualify
    core identity, units, age scale and whether this order assumption is apt.
    This function supplies neither probabilities nor chronology confirmation.
    """
    identity(core_id)
    if not domains or len({row.sample_id for row in domains}) != len(domains):
        raise ValueError("Nonempty unique source sample identities are required")
    ordered = sorted(domains, key=lambda row: (row.depth, row.sample_id))
    previous: Decimal | None = None
    previous_ids: tuple[str, ...] = ()
    assignments: list[OrderedAge] = []
    for depth, members in groupby(ordered, key=lambda row: row.depth):
        rows = tuple(members)
        ids = tuple(row.sample_id for row in rows)
        candidate = max(row.components[0].younger for row in rows)
        if previous is not None:
            candidate = max(candidate, previous)
        cursors = [0] * len(rows)
        while True:
            start = candidate
            for index, row in enumerate(rows):
                while cursors[index] < len(row.components):
                    part = row.components[cursors[index]]
                    if (
                        part.older > candidate
                        or part.older_inclusive
                        and part.older == candidate
                    ):
                        break
                    cursors[index] += 1
                if cursors[index] == len(row.components):
                    refusal = AgeOrderRefusal(
                        row.sample_id, depth, candidate, previous_ids, ids
                    )
                    return AgeOrderAssessment(core_id, (), refusal)
                candidate = max(candidate, row.components[cursors[index]].younger)
            if candidate == start:
                break
        assignments.extend(OrderedAge(row.sample_id, depth, candidate) for row in rows)
        previous, previous_ids = candidate, ids
    return AgeOrderAssessment(core_id, tuple(assignments), None)
