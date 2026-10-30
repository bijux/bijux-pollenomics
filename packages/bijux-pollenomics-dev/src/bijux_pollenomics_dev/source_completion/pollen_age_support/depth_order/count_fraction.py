"""Sharp pooled-count fractions under a declared nondecreasing age function."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from fractions import Fraction
from itertools import groupby

from ..joint_membership import AgeBin
from .domains import AgeComponent, AgeOrderAssessment, DepthAgeDomain, assess_age_order
from .extrema import DepthCountSample


@dataclass(frozen=True, slots=True)
class CountFractionWitness:
    """An exact pooled fraction and a complete supported age assignment."""

    value: Fraction
    numerator_count: int
    denominator_count: int
    selected_sample_ids: tuple[str, ...]
    age_order: AgeOrderAssessment


@dataclass(frozen=True, slots=True)
class OrderedCountFractionBounds:
    """Sharp single-bin bounds; different bins need not share their witnesses."""

    bin_id: str
    depth_group_count: int
    candidate_block_count: int
    tested_block_count: int
    feasible_block_count: int
    native_age_order: AgeOrderAssessment
    empty_selection_age_order: AgeOrderAssessment | None
    lower: CountFractionWitness | None
    upper: CountFractionWitness | None
    refusal: str | None


@dataclass(frozen=True, slots=True)
class FeasibleCountBlocks:
    """One reusable enumeration of supported nonempty bin selections."""

    bin_id: str
    depth_group_count: int
    candidate_block_count: int
    native_age_order: AgeOrderAssessment
    empty_selection_age_order: AgeOrderAssessment | None
    _groups: tuple[tuple[DepthCountSample, ...], ...]
    _bin: AgeBin
    _core_id: str

    @property
    def tested_block_count(self) -> int:
        """A contradictory native core needs no constrained block search."""
        return self.candidate_block_count if self.native_age_order.attainable else 0

    def __iter__(self) -> Iterator[CountFractionWitness]:
        """Yield exact fractions and full witnesses in stable depth-block order."""
        if not self.native_age_order.attainable:
            return
        for start in range(self.depth_group_count):
            numerator = denominator = 0
            selected: list[str] = []
            for stop in range(start + 1, self.depth_group_count + 1):
                for row in self._groups[stop - 1]:
                    numerator += row.sample.numerator_count
                    denominator += row.sample.denominator_count
                    selected.append(row.sample.sample_id)
                order = _allocation(self._groups, self._bin, start, stop, self._core_id)
                if order is not None and order.attainable:
                    yield CountFractionWitness(
                        Fraction(numerator, denominator),
                        numerator,
                        denominator,
                        tuple(selected),
                        order,
                    )


def _allocation(
    groups: tuple[tuple[DepthCountSample, ...], ...],
    bin_: AgeBin,
    start: int,
    stop: int,
    core_id: str,
) -> AgeOrderAssessment | None:
    domains = []
    for index, group in enumerate(groups):
        for row in group:
            sample = row.sample
            lower, upper = sample.younger_cal_bp, sample.older_cal_bp
            inclusive = True
            if index >= start:
                lower = max(
                    lower,
                    bin_.younger_cal_bp
                    if index < stop
                    else bin_.older_cal_bp_exclusive,
                )
            if index < stop:
                boundary = (
                    bin_.younger_cal_bp
                    if index < start
                    else bin_.older_cal_bp_exclusive
                )
                if boundary <= upper:
                    upper, inclusive = boundary, False
            if lower > upper or lower == upper and not inclusive:
                return None
            domains.append(
                DepthAgeDomain(
                    sample.sample_id,
                    row.depth,
                    (AgeComponent(lower, upper, inclusive),),
                )
            )
    return assess_age_order(domains, core_id=core_id)


def feasible_count_blocks(
    samples: Sequence[DepthCountSample], bin_: AgeBin, *, core_id: str
) -> FeasibleCountBlocks:
    """Enumerate every possible nonempty bin block and certify its full core.

    Nondecreasing ages imply that membership in [younger, older) is one
    contiguous block of depth groups. Equal depths share one age and cannot
    be split. Conversely, intersecting the native closed intervals with the
    before/inside/after regions and checking the complete age order proves
    whether each block is attainable. Exhaustive block enumeration therefore
    yields sharp exact integer-ratio bounds, not probabilistic intervals.

    Empty selection is checked separately over every possible prefix/suffix
    cut. It has no fraction. Positive individual denominators are enforced by
    DepthCountSample's existing typed count contract. Native negative ages
    remain possible, and no assignments to other analysis bins are inferred.
    """
    if (
        not isinstance(bin_, AgeBin)
        or not samples
        or any(not isinstance(row, DepthCountSample) for row in samples)
    ):
        raise ValueError(
            "A typed analysis bin and nonempty depth/count samples required"
        )
    ordered = sorted(samples, key=lambda row: (row.depth, row.sample.sample_id))
    native = assess_age_order(
        [
            DepthAgeDomain(
                row.sample.sample_id,
                row.depth,
                (AgeComponent(row.sample.younger_cal_bp, row.sample.older_cal_bp),),
            )
            for row in ordered
        ],
        core_id=core_id,
    )
    groups = tuple(
        tuple(rows) for _, rows in groupby(ordered, key=lambda row: row.depth)
    )
    count = len(groups)
    candidates = count * (count + 1) // 2
    empty = None
    if native.attainable:
        for cut in range(count + 1):
            order = _allocation(groups, bin_, cut, cut, core_id)
            if order is not None and order.attainable:
                empty = order
                break
    return FeasibleCountBlocks(
        bin_.bin_id, count, candidates, native, empty, groups, bin_, core_id
    )


def ordered_count_fraction_bounds(
    samples: Sequence[DepthCountSample], bin_: AgeBin, *, core_id: str
) -> OrderedCountFractionBounds:
    """Find sharp single-bin fractions using the shared feasible-block iterator."""
    blocks = feasible_count_blocks(samples, bin_, core_id=core_id)
    lower: CountFractionWitness | None = None
    upper: CountFractionWitness | None = None
    feasible = 0
    for witness in blocks:
        feasible += 1
        if lower is None or witness.value < lower.value:
            lower = witness
        if upper is None or witness.value > upper.value:
            upper = witness
    return OrderedCountFractionBounds(
        blocks.bin_id,
        blocks.depth_group_count,
        blocks.candidate_block_count,
        blocks.tested_block_count,
        feasible,
        blocks.native_age_order,
        blocks.empty_selection_age_order,
        lower,
        upper,
        "native_age_order_infeasible"
        if not blocks.native_age_order.attainable
        else (None if lower is not None else "no_feasible_nonempty_selection"),
    )
