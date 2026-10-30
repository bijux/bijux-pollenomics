"""Join ordered single-bin blocks into complete shared chronology allocations."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from decimal import Decimal
from itertools import groupby

from ..joint_membership import AgeBin
from .count_fraction import (
    CountFractionWitness,
    FeasibleCountBlocks,
    feasible_count_blocks,
)
from .domains import AgeComponent, AgeOrderAssessment, DepthAgeDomain, assess_age_order
from .extrema import DepthCountSample


def _domains(
    rows: Sequence[DepthCountSample], lower: Decimal | None, upper: Decimal | None
) -> list[DepthAgeDomain] | None:
    result = []
    for row in rows:
        lo, hi = row.sample.younger_cal_bp, row.sample.older_cal_bp
        inclusive = True
        if lower is not None:
            lo = max(lo, lower)
        if upper is not None and upper <= hi:
            hi, inclusive = upper, False
        if lo > hi or lo == hi and not inclusive:
            return None
        result.append(
            DepthAgeDomain(
                row.sample.sample_id, row.depth, (AgeComponent(lo, hi, inclusive),)
            )
        )
    return result


@dataclass(frozen=True, slots=True)
class JointBlock:
    """A nonempty whole-depth-group bin selection with its native witness."""

    start: int
    stop: int
    selection: CountFractionWitness


@dataclass(frozen=True, slots=True)
class JointBlockGraph:
    """Layered acyclic graph of exactly the joint nonempty-bin selections."""

    bins: tuple[AgeBin, ...]
    single_bin_assessments: tuple[FeasibleCountBlocks, ...]
    layers: tuple[tuple[JointBlock, ...], ...]
    successors: tuple[tuple[tuple[int, ...], ...], ...]
    feasible_path_count: int
    _groups: tuple[tuple[DepthCountSample, ...], ...]
    _core_id: str

    def __iter__(self) -> Iterator[tuple[int, ...]]:
        """Yield each selection once, without reconstructing full age vectors."""

        def visit(path: tuple[int, ...]) -> Iterator[tuple[int, ...]]:
            if len(path) == len(self.layers):
                yield path
                return
            for following in self.successors[len(path) - 1][path[-1]]:
                yield from visit((*path, following))

        for first in range(len(self.layers[0])):
            yield from visit((first,))

    def witness(self, path: tuple[int, ...]) -> AgeOrderAssessment:
        """Construct one complete age vector for an admitted graph path."""
        if (
            len(path) != len(self.layers)
            or any(type(index) is not int for index in path)
            or any(
                not 0 <= index < len(layer)
                for index, layer in zip(path, self.layers, strict=True)
            )
            or any(
                right not in self.successors[k][left]
                for k, (left, right) in enumerate(zip(path, path[1:], strict=False))
            )
        ):
            raise ValueError("A complete compatible bin-block path is required")
        domains = []
        cursor = 0
        lower = None
        for bin_, layer, index in zip(self.bins, self.layers, path, strict=True):
            block = layer[index]
            for start, stop, lo, hi in (
                (cursor, block.start, lower, bin_.younger_cal_bp),
                (
                    block.start,
                    block.stop,
                    bin_.younger_cal_bp,
                    bin_.older_cal_bp_exclusive,
                ),
            ):
                part = _domains(
                    [row for group in self._groups[start:stop] for row in group], lo, hi
                )
                if part is None:
                    raise AssertionError("A certified joint region became empty")
                domains.extend(part)
            cursor, lower = block.stop, bin_.older_cal_bp_exclusive
        suffix = _domains(
            [row for group in self._groups[cursor:] for row in group], lower, None
        )
        if suffix is None:
            raise AssertionError("A certified joint suffix became empty")
        order = assess_age_order([*domains, *suffix], core_id=self._core_id)
        if not order.attainable:
            raise AssertionError("A certified graph path lacks its complete witness")
        return order


def joint_block_graph(
    samples: Sequence[DepthCountSample], bins: Sequence[AgeBin], *, core_id: str
) -> JointBlockGraph:
    """Certify the exact finite join, including prefix, gap and suffix support.

    A nondecreasing chronology puts each half-open bin in one contiguous block
    of whole tied-depth groups. Existing single-bin enumeration certifies the
    full prefix/block/suffix for every node. Consecutive nodes are compatible
    precisely when they do not overlap and intervening groups admit ordered
    ages in [previous bin upper, next bin lower). Adjacent bins therefore
    permit no intervening groups. All region age ranges are separated, so
    independently feasible regions concatenate into one monotone chronology.
    Conversely every complete chronology induces exactly one such graph path.

    Counting paths by dynamic programming establishes the denominator before
    scoring. Iteration costs only the number of compatible block tuples; full
    source age vectors are constructed only for retained result witnesses.
    Empty-bin possibilities remain available in the single-bin assessments;
    they have no equal-bin metric and are outside the nonempty-bin graph.
    """
    if (
        len(bins) < 2
        or any(not isinstance(bin_, AgeBin) for bin_ in bins)
        or len({bin_.bin_id for bin_ in bins}) != len(bins)
        or any(
            left.older_cal_bp_exclusive > right.younger_cal_bp
            for left, right in zip(bins, bins[1:], strict=False)
        )
    ):
        raise ValueError("Distinct ordered nonoverlapping typed analysis bins required")
    assessments = tuple(
        feasible_count_blocks(samples, b, core_id=core_id) for b in bins
    )
    ordered = sorted(samples, key=lambda row: (row.depth, row.sample.sample_id))
    groups = tuple(tuple(g) for _, g in groupby(ordered, key=lambda row: row.depth))
    positions = {row.sample.sample_id: k for k, g in enumerate(groups) for row in g}
    layers = tuple(
        tuple(
            JointBlock(
                positions[block.selected_sample_ids[0]],
                positions[block.selected_sample_ids[-1]] + 1,
                block,
            )
            for block in assessment
        )
        for assessment in assessments
    )
    edges = []
    for k, (left_layer, right_layer) in enumerate(
        zip(layers, layers[1:], strict=False)
    ):
        cache: dict[tuple[int, int], bool] = {}

        def compatible(
            left: JointBlock,
            right: JointBlock,
            cache: dict[tuple[int, int], bool] = cache,
            lower: Decimal = bins[k].older_cal_bp_exclusive,
            upper: Decimal = bins[k + 1].younger_cal_bp,
        ) -> bool:
            if left.stop > right.start:
                return False
            key = left.stop, right.start
            if key not in cache:
                rows = [row for g in groups[left.stop : right.start] for row in g]
                part = _domains(rows, lower, upper)
                cache[key] = part is not None and (
                    not part or assess_age_order(part, core_id=core_id).attainable
                )
            return cache[key]

        edges.append(
            tuple(
                tuple(
                    j for j, right in enumerate(right_layer) if compatible(left, right)
                )
                for left in left_layer
            )
        )
    counts = [1] * len(layers[0])
    for following, layer in zip(edges, layers[1:], strict=True):
        updated = [0] * len(layer)
        for count, destinations in zip(counts, following, strict=True):
            for j in destinations:
                updated[j] += count
        counts = updated
    return JointBlockGraph(
        tuple(bins), assessments, layers, tuple(edges), sum(counts), groups, core_id
    )
