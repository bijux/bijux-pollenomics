"""Exact frozen-prediction MAE sensitivity over shared ordered age allocations."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
import math

from ..joint_membership import AgeBin
from .count_fraction import CountFractionWitness, feasible_count_blocks
from .domains import AgeOrderAssessment, identity
from .extrema import DepthCountSample


@dataclass(frozen=True, slots=True)
class ScoreWitness:
    """One exact metric with the pooled observation and complete age witness."""

    value: Fraction
    selected_sample_ids: tuple[str, ...]
    pooled_taxon_counts: tuple[int, ...]
    age_order: AgeOrderAssessment


@dataclass(frozen=True, slots=True)
class MethodScoreBounds:
    """Sharp MAE bounds for a single already-frozen prediction."""

    method: str
    lower: ScoreWitness | None
    upper: ScoreWitness | None


@dataclass(frozen=True, slots=True)
class PairedScoreBounds:
    """Left minus right MAE on the same allocation, including attainable ties."""

    left_method: str
    right_method: str
    lower: ScoreWitness | None
    upper: ScoreWitness | None
    negative_attainable: bool
    zero_attainable: bool
    positive_attainable: bool

    @property
    def ranking_reversal(self) -> bool:
        """Both strict method orderings occur; an endpoint tie alone is insufficient."""
        return self.negative_attainable and self.positive_attainable


@dataclass(frozen=True, slots=True)
class WinnerSetWitness:
    """One attainable exact best-method set, including ties on the same block."""

    methods: tuple[str, ...]
    witness: ScoreWitness


@dataclass(frozen=True, slots=True)
class OrderedPredictionSensitivity:
    """Single-bin sensitivity, without probabilistic or cross-bin interpretation."""

    bin_id: str
    depth_group_count: int
    candidate_block_count: int
    tested_block_count: int
    feasible_block_count: int
    scored_block_count: int
    native_age_order: AgeOrderAssessment
    empty_selection_age_order: AgeOrderAssessment | None
    zero_closed_count_selections: tuple[tuple[str, ...], ...]
    method_bounds: tuple[MethodScoreBounds, ...]
    pairwise_bounds: tuple[PairedScoreBounds, ...]
    winner_sets: tuple[WinnerSetWitness, ...]
    refusal: str | None

    @property
    def possible_winners(self) -> tuple[str, ...]:
        """Methods attaining the minimum somewhere, including tied minima."""
        return tuple(
            row.method
            for row in self.method_bounds
            if any(row.method in winners.methods for winners in self.winner_sets)
        )

    @property
    def winner_set_changes(self) -> bool:
        """Different best-method sets occur; a changed tie alone may suffice."""
        return len(self.winner_sets) > 1

    @property
    def unique_winner_changes(self) -> bool:
        """At least two different methods each become a strict unique winner."""
        return sum(len(winners.methods) == 1 for winners in self.winner_sets) > 1


@dataclass(slots=True)
class _Extrema:
    lower: ScoreWitness | None = None
    upper: ScoreWitness | None = None
    negative: bool = False
    zero: bool = False
    positive: bool = False

    def add(
        self, value: Fraction, block: CountFractionWitness, counts: tuple[int, ...]
    ) -> None:
        witness = ScoreWitness(
            value, block.selected_sample_ids, counts, block.age_order
        )
        if self.lower is None or value < self.lower.value:
            self.lower = witness
        if self.upper is None or value > self.upper.value:
            self.upper = witness
        self.negative |= value < 0
        self.zero |= value == 0
        self.positive |= value > 0


def _inputs(
    samples: Sequence[DepthCountSample],
    sample_taxon_counts: Mapping[str, tuple[int, ...]],
    predictions: Mapping[str, tuple[float, ...]],
) -> tuple[int, dict[str, tuple[Fraction, ...]]]:
    if len(predictions) < 2:
        raise ValueError("At least two named frozen predictions are required")
    if set(sample_taxon_counts) != {row.sample.sample_id for row in samples}:
        raise ValueError("Exact source sample/taxon-count coverage required")
    size = 0
    for row in samples:
        counts = sample_taxon_counts[row.sample.sample_id]
        if (
            not isinstance(counts, tuple)
            or not counts
            or any(type(n) is not int or n < 0 for n in counts)
        ):
            raise ValueError("Nonempty exact nonnegative integer taxon counts required")
        size = size or len(counts)
        if len(counts) != size or sum(counts) != row.sample.numerator_count:
            raise ValueError("Taxon axis or declared closed-count denominator differs")
    exact = {}
    for method, vector in predictions.items():
        identity(method)
        if (
            not isinstance(vector, tuple)
            or len(vector) != size
            or any(
                type(value) is not float
                or not math.isfinite(value)
                or not 0 <= value <= 1
                for value in vector
            )
        ):
            raise ValueError(
                "Frozen predictions require the same finite binary64 fraction axis"
            )
        if not math.isclose(sum(vector), 1.0, rel_tol=0, abs_tol=1e-9):
            raise ValueError(
                "Frozen prediction fractions must satisfy the existing 1e-9 closure contract"
            )
        exact[method] = tuple(Fraction.from_float(value) for value in vector)
    return size, exact


def ordered_prediction_sensitivity(
    samples: Sequence[DepthCountSample],
    bin_: AgeBin,
    sample_taxon_counts: Mapping[str, tuple[int, ...]],
    predictions: Mapping[str, tuple[float, ...]],
    *,
    core_id: str,
) -> OrderedPredictionSensitivity:
    """Optimize MAE and paired differences over exactly the same feasible blocks.

    Pollen observations are pooled literal integer counts closed on their
    selected-taxon sum. Predictions retain their supplied finite binary64
    values exactly through Fraction.from_float. Admission requires the existing
    closed-composition absolute tolerance 1e-9, with zero relative tolerance;
    admitted vectors are never reclosed. There are no pseudocounts or fits.
    MAE is the mean over the declared taxon axis of the exact absolute errors;
    metric, paired-difference and ranking comparisons use no floating tolerance.

    Every pair uses left MAE minus right MAE on one shared allocation. The
    difference bounds are never obtained by subtracting independent extrema.
    Sign attainability is enumerated, since a range spanning zero need not
    contain any exact attainable tie. Empty and zero-closed-count selections
    remain unscored. Source applicability and prior exposure belong to the
    caller; these bounds are conditional sensitivity, not confidence limits.
    """
    blocks = feasible_count_blocks(samples, bin_, core_id=core_id)
    size, exact = _inputs(samples, sample_taxon_counts, predictions)
    methods = {method: _Extrema() for method in exact}
    pairs = {pair: _Extrema() for pair in combinations(exact, 2)}
    winners: dict[tuple[str, ...], WinnerSetWitness] = {}
    feasible = scored = 0
    zero_selections = []
    for block in blocks:
        feasible += 1
        counts = tuple(
            sum(
                sample_taxon_counts[sample_id][i]
                for sample_id in block.selected_sample_ids
            )
            for i in range(size)
        )
        denominator = sum(counts)
        if denominator == 0:
            zero_selections.append(block.selected_sample_ids)
            continue
        scored += 1
        observed = tuple(Fraction(n, denominator) for n in counts)
        scores = {
            method: sum(
                (abs(p - y) for p, y in zip(vector, observed, strict=True)), Fraction()
            )
            / size
            for method, vector in exact.items()
        }
        for method, score in scores.items():
            methods[method].add(score, block, counts)
        for (left, right), bounds in pairs.items():
            bounds.add(scores[left] - scores[right], block, counts)
        minimum = min(scores.values())
        best = tuple(method for method, score in scores.items() if score == minimum)
        if best not in winners:
            winners[best] = WinnerSetWitness(
                best,
                ScoreWitness(
                    minimum, block.selected_sample_ids, counts, block.age_order
                ),
            )
    refusal = None
    if not blocks.native_age_order.attainable:
        refusal = "native_age_order_infeasible"
    elif feasible == 0:
        refusal = "no_feasible_nonempty_selection"
    elif scored == 0:
        refusal = "zero_closed_count_for_all_feasible_blocks"
    return OrderedPredictionSensitivity(
        bin_.bin_id,
        blocks.depth_group_count,
        blocks.candidate_block_count,
        blocks.tested_block_count,
        feasible,
        scored,
        blocks.native_age_order,
        blocks.empty_selection_age_order,
        tuple(zero_selections),
        tuple(MethodScoreBounds(name, b.lower, b.upper) for name, b in methods.items()),
        tuple(
            PairedScoreBounds(
                left, right, b.lower, b.upper, b.negative, b.zero, b.positive
            )
            for (left, right), b in pairs.items()
        ),
        tuple(winners.values()),
        refusal,
    )
