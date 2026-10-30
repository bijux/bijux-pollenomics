"""Sharp equal-bin frozen-predictor comparisons on one ordered chronology."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from math import lcm

from ..joint_membership import AgeBin
from .domains import AgeOrderAssessment
from .extrema import DepthCountSample
from .joint_allocations import JointBlockGraph, joint_block_graph
from .prediction_sensitivity import _inputs


@dataclass(frozen=True, slots=True)
class JointScoreWitness:
    """One exact aggregate value and the same complete chronology in every bin."""

    value: Fraction
    selected_sample_ids: tuple[tuple[str, ...], ...]
    pooled_taxon_counts: tuple[tuple[int, ...], ...]
    age_order: AgeOrderAssessment


@dataclass(frozen=True, slots=True)
class JointMethodScoreBounds:
    """Sharp conditional equal-bin MAE range for one frozen method."""

    method: str
    lower: JointScoreWitness | None
    upper: JointScoreWitness | None


@dataclass(frozen=True, slots=True)
class JointPairedScoreBounds:
    """Exact left-minus-right aggregate differences on the same chronology."""

    left_method: str
    right_method: str
    lower: JointScoreWitness | None
    upper: JointScoreWitness | None
    negative_attainable: bool
    zero_attainable: bool
    positive_attainable: bool

    @property
    def ranking_reversal(self) -> bool:
        """Require two attainable strict orderings rather than a tie alone."""
        return self.negative_attainable and self.positive_attainable


@dataclass(frozen=True, slots=True)
class JointWinnerSetWitness:
    """One attainable best-method set from all scores on the same chronology."""

    methods: tuple[str, ...]
    witness: JointScoreWitness


@dataclass(frozen=True, slots=True)
class JointPredictionSensitivity:
    """Finite joint membership sensitivity, without a probability interpretation."""

    graph: JointBlockGraph
    pooled_counts: tuple[tuple[tuple[int, ...], ...], ...]
    joint_feasible_count: int
    scored_allocation_count: int
    zero_closed_count_allocation_count: int
    method_bounds: tuple[JointMethodScoreBounds, ...]
    pairwise_bounds: tuple[JointPairedScoreBounds, ...]
    winner_sets: tuple[JointWinnerSetWitness, ...]
    refusal: str | None

    @property
    def possible_winners(self) -> tuple[str, ...]:
        """Include methods attaining a tied or unique minimum somewhere."""
        return tuple(
            row.method
            for row in self.method_bounds
            if any(row.method in w.methods for w in self.winner_sets)
        )

    @property
    def winner_set_changes(self) -> bool:
        """Different exact argmin sets occur on feasible scored chronologies."""
        return len(self.winner_sets) > 1

    @property
    def unique_winner_changes(self) -> bool:
        """At least two different methods each attain a strict minimum."""
        return sum(len(w.methods) == 1 for w in self.winner_sets) > 1


@dataclass(slots=True)
class _IntegerExtrema:
    lower: tuple[int, tuple[int, ...]] | None = None
    upper: tuple[int, tuple[int, ...]] | None = None
    negative: bool = False
    zero: bool = False
    positive: bool = False

    def add(self, value: int, path: tuple[int, ...]) -> None:
        if self.lower is None or value < self.lower[0]:
            self.lower = value, path
        if self.upper is None or value > self.upper[0]:
            self.upper = value, path
        self.negative |= value < 0
        self.zero |= value == 0
        self.positive |= value > 0


def joint_prediction_sensitivity(
    samples: Sequence[DepthCountSample],
    bins: Sequence[AgeBin],
    sample_taxon_counts: Mapping[str, tuple[int, ...]],
    predictions: Mapping[str, Mapping[str, tuple[float, ...]]],
    *,
    core_id: str,
) -> JointPredictionSensitivity:
    """Bound the equal-bin mean of exact taxon MAEs on shared age allocations.

    Every declared bin must contain a nonempty selected block with positive
    closed-taxon count. Missing bins are not dropped or scored as zero; the
    result is conditional on that complete fixed-bin denominator. Marginal
    empty-bin witnesses and zero-count exclusions remain explicit. Each method
    has the same bin/taxon axis and the identical allocation in each comparison.

    Binary64 predictions are admitted under the existing absolute 1e-9 closure
    contract without reclosure, then treated exactly. Observations use literal
    integer counts, without pseudocounts. Per-block rational MAEs are calculated
    once and embedded losslessly in one integer scale using their denominator
    LCM. Compatible graph paths are enumerated using integer score sums only;
    division by the number of bins happens after exact extrema/sign/tie/winner
    decisions. No independent extrema are subtracted and a range spanning zero
    is not mistaken for an attainable exact tie. There are no probability
    weights, chronology posterior draws, refits or new independent observations.
    """
    graph = joint_block_graph(samples, bins, core_id=core_id)
    if set(predictions) != {b.bin_id for b in bins}:
        raise ValueError(
            "Exact frozen prediction coverage of every analysis bin required"
        )
    methods = tuple(predictions[bins[0].bin_id])
    if any(tuple(predictions[b.bin_id]) != methods for b in bins):
        raise ValueError(
            "The same ordered frozen method identities required in every bin"
        )
    pooled = []
    fractions = []
    scale = 1
    for bin_, layer in zip(bins, graph.layers, strict=True):
        size, exact = _inputs(samples, sample_taxon_counts, predictions[bin_.bin_id])
        totals, scores = [], []
        for block in layer:
            counts = tuple(
                sum(
                    sample_taxon_counts[s][i]
                    for s in block.selection.selected_sample_ids
                )
                for i in range(size)
            )
            totals.append(counts)
            denominator = sum(counts)
            values = (
                None
                if denominator == 0
                else tuple(
                    sum(
                        (
                            abs(p - Fraction(n, denominator))
                            for p, n in zip(vector, counts, strict=True)
                        ),
                        Fraction(),
                    )
                    / size
                    for vector in exact.values()
                )
            )
            if values is not None:
                scale = lcm(scale, *(v.denominator for v in values))
            scores.append(values)
        pooled.append(tuple(totals))
        fractions.append(scores)
    integer_scores = tuple(
        tuple(
            None
            if scores is None
            else tuple(v.numerator * (scale // v.denominator) for v in scores)
            for scores in layer
        )
        for layer in fractions
    )
    method_extrema = [_IntegerExtrema() for _ in methods]
    pairs = tuple(combinations(range(len(methods)), 2))
    pair_extrema = [_IntegerExtrema() for _ in pairs]
    winners: dict[tuple[str, ...], tuple[int, tuple[int, ...]]] = {}
    scored = 0

    def visit(path: tuple[int, ...], totals: tuple[int, ...]) -> None:
        nonlocal scored
        if len(path) < len(bins):
            for index in graph.successors[len(path) - 1][path[-1]]:
                values = integer_scores[len(path)][index]
                if values is not None:
                    visit(
                        (*path, index),
                        tuple(a + b for a, b in zip(totals, values, strict=True)),
                    )
            return
        scored += 1
        for bounds, value in zip(method_extrema, totals, strict=True):
            bounds.add(value, path)
        for bounds, (left, right) in zip(pair_extrema, pairs, strict=True):
            bounds.add(totals[left] - totals[right], path)
        minimum = min(totals)
        best = tuple(
            method
            for method, value in zip(methods, totals, strict=True)
            if value == minimum
        )
        if best not in winners:
            winners[best] = minimum, path

    for index, integer_values in enumerate(integer_scores[0]):
        if integer_values is not None:
            visit((index,), integer_values)
    orders: dict[tuple[int, ...], AgeOrderAssessment] = {}

    def witness(
        endpoint: tuple[int, tuple[int, ...]] | None,
    ) -> JointScoreWitness | None:
        if endpoint is None:
            return None
        value, path = endpoint
        if path not in orders:
            orders[path] = graph.witness(path)
        return JointScoreWitness(
            Fraction(value, scale * len(bins)),
            tuple(
                layer[i].selection.selected_sample_ids
                for layer, i in zip(graph.layers, path, strict=True)
            ),
            tuple(layer[i] for layer, i in zip(pooled, path, strict=True)),
            orders[path],
        )

    refusal = None
    if not graph.single_bin_assessments[0].native_age_order.attainable:
        refusal = "native_age_order_infeasible"
    elif graph.feasible_path_count == 0:
        refusal = "no_joint_nonempty_bin_selection"
    elif scored == 0:
        refusal = "zero_closed_count_in_every_joint_allocation"
    winner_rows = []
    for best, endpoint in winners.items():
        w = witness(endpoint)
        assert w is not None
        winner_rows.append(JointWinnerSetWitness(best, w))
    return JointPredictionSensitivity(
        graph,
        tuple(pooled),
        graph.feasible_path_count,
        scored,
        graph.feasible_path_count - scored,
        tuple(
            JointMethodScoreBounds(name, witness(b.lower), witness(b.upper))
            for name, b in zip(methods, method_extrema, strict=True)
        ),
        tuple(
            JointPairedScoreBounds(
                methods[left],
                methods[right],
                witness(b.lower),
                witness(b.upper),
                b.negative,
                b.zero,
                b.positive,
            )
            for (left, right), b in zip(pairs, pair_extrema, strict=True)
        ),
        tuple(winner_rows),
        refusal,
    )
