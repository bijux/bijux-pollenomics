"""Independent rational-age enumeration checks shared-chronology MAE bounds."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from itertools import combinations, product
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_age_support.depth_order.extrema import (
    DepthCountSample,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support.depth_order.joint_prediction_sensitivity import (
    JointScoreWitness,
    joint_prediction_sensitivity,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support.joint_membership import (
    AgeBin,
    MarginalAgeCountSample,
)

Membership = tuple[tuple[str, ...], ...]
Predictions = Mapping[str, Mapping[str, tuple[float, ...]]]


@dataclass(frozen=True)
class ExhaustiveResult:
    """Distinct complete memberships and exact scores from rational age vectors."""

    native_attainable: bool
    memberships: frozenset[Membership]
    scores: Mapping[Membership, Mapping[str, Fraction]]


def _sample(
    name: str, depth: str, interval: tuple[str, str], counts: tuple[int, ...]
) -> DepthCountSample:
    return DepthCountSample(
        MarginalAgeCountSample(
            name,
            Decimal(interval[0]),
            Decimal(interval[1]),
            sum(counts),
            sum(counts) + 1,
        ),
        Decimal(depth),
    )


def _bin(name: str, low: str, high: str) -> AgeBin:
    return AgeBin(name, Decimal(low), Decimal(high))


def _membership(
    samples: Sequence[DepthCountSample],
    bins: Sequence[AgeBin],
    ages: Sequence[Fraction],
) -> Membership:
    return tuple(
        tuple(
            sorted(
                row.sample.sample_id
                for row, age in zip(samples, ages, strict=True)
                if Fraction(bin_.younger_cal_bp)
                <= age
                < Fraction(bin_.older_cal_bp_exclusive)
            )
        )
        for bin_ in bins
    )


def _scores(
    membership: Membership,
    bins: Sequence[AgeBin],
    counts: Mapping[str, tuple[int, ...]],
    predictions: Predictions,
) -> dict[str, Fraction] | None:
    methods = tuple(predictions[bins[0].bin_id])
    size = len(predictions[bins[0].bin_id][methods[0]])
    scores = dict.fromkeys(methods, Fraction())
    for bin_, selected in zip(bins, membership, strict=True):
        pooled = tuple(sum(counts[s][i] for s in selected) for i in range(size))
        total = sum(pooled)
        if not selected or not total:
            return None
        for method in methods:
            scores[method] += sum(
                (
                    abs(Fraction.from_float(p) - Fraction(n, total))
                    for p, n in zip(
                        predictions[bin_.bin_id][method], pooled, strict=True
                    )
                ),
                Fraction(),
            ) / (size * len(bins))
    return scores


def _exhaustive(
    samples: Sequence[DepthCountSample],
    bins: Sequence[AgeBin],
    counts: Mapping[str, tuple[int, ...]],
    predictions: Predictions,
) -> ExhaustiveResult:
    # Endpoints partition every source support and half-open bin predicate.
    # Within one open cell all memberships are constant. Replacing every age
    # there by its common rational midpoint preserves order and tied depths.
    cuts = sorted(
        {
            Fraction(value)
            for row in samples
            for value in (row.sample.younger_cal_bp, row.sample.older_cal_bp)
        }
        | {
            Fraction(value)
            for bin_ in bins
            for value in (bin_.younger_cal_bp, bin_.older_cal_bp_exclusive)
        }
    )
    grid = sorted(
        set(cuts) | {(a + b) / 2 for a, b in zip(cuts, cuts[1:], strict=False)}
    )
    choices = [
        [
            age
            for age in grid
            if Fraction(row.sample.younger_cal_bp)
            <= age
            <= Fraction(row.sample.older_cal_bp)
        ]
        for row in samples
    ]
    memberships: set[Membership] = set()
    native = False
    for ages in product(*choices):
        if any(
            (a != b if x.depth == y.depth else a > b)
            for x, a in zip(samples, ages, strict=True)
            for y, b in zip(samples, ages, strict=True)
            if x.depth <= y.depth
        ):
            continue
        native = True
        selected = _membership(samples, bins, ages)
        if all(selected):
            memberships.add(selected)
    scores = {}
    for selected in memberships:
        values = _scores(selected, bins, counts, predictions)
        if values is not None:
            scores[selected] = values
    return ExhaustiveResult(native, frozenset(memberships), scores)


def _witness(
    witness: Any,
    samples: Sequence[DepthCountSample],
    bins: Sequence[AgeBin],
    counts: Mapping[str, tuple[int, ...]],
) -> Membership:
    assignments = {
        a.sample_id: Fraction(a.native_age) for a in witness.age_order.assignments
    }
    assert set(assignments) == set(counts)
    for row in samples:
        age = assignments[row.sample.sample_id]
        assert (
            Fraction(row.sample.younger_cal_bp)
            <= age
            <= Fraction(row.sample.older_cal_bp)
        )
    assert all(
        (
            assignments[x.sample.sample_id] == assignments[y.sample.sample_id]
            if x.depth == y.depth
            else assignments[x.sample.sample_id] <= assignments[y.sample.sample_id]
        )
        for x in samples
        for y in samples
        if x.depth <= y.depth
    )
    membership = _membership(
        samples, bins, [assignments[r.sample.sample_id] for r in samples]
    )
    assert membership == tuple(tuple(sorted(s)) for s in witness.selected_sample_ids)
    assert (
        tuple(
            tuple(
                sum(counts[s][i] for s in selected)
                for i in range(len(next(iter(counts.values()))))
            )
            for selected in membership
        )
        == witness.pooled_taxon_counts
    )
    return membership


def _compare(
    samples: Sequence[DepthCountSample],
    bins: Sequence[AgeBin],
    counts: Mapping[str, tuple[int, ...]],
    predictions: Predictions,
) -> Any:
    oracle = _exhaustive(samples, bins, counts, predictions)
    result = joint_prediction_sensitivity(
        list(reversed(samples)), bins, counts, predictions, core_id="controlled-core"
    )
    assert all(
        row.native_age_order.attainable == oracle.native_attainable
        for row in result.graph.single_bin_assessments
    )
    assert result.joint_feasible_count == len(oracle.memberships)
    assert result.scored_allocation_count == len(oracle.scores)
    assert result.zero_closed_count_allocation_count == len(oracle.memberships) - len(
        oracle.scores
    )
    actual_memberships: set[Membership] = set()
    for path in product(*(range(len(layer)) for layer in result.graph.layers)):
        if any(
            path[i + 1] not in result.graph.successors[i][path[i]]
            for i in range(len(path) - 1)
        ):
            continue
        selected = tuple(
            layer[index].selection.selected_sample_ids
            for layer, index in zip(result.graph.layers, path, strict=True)
        )
        pooled = tuple(
            tuple(
                sum(counts[s][i] for s in members)
                for i in range(len(next(iter(counts.values()))))
            )
            for members in selected
        )
        complete = JointScoreWitness(
            Fraction(), selected, pooled, result.graph.witness(path)
        )
        actual_memberships.add(_witness(complete, samples, bins, counts))
    assert actual_memberships == set(oracle.memberships)
    expected_refusal: str | None = None
    if not oracle.native_attainable:
        expected_refusal = "native_age_order_infeasible"
    elif not oracle.memberships:
        expected_refusal = "no_joint_nonempty_bin_selection"
    elif not oracle.scores:
        expected_refusal = "zero_closed_count_in_every_joint_allocation"
    assert result.refusal == expected_refusal
    for row in result.method_bounds:
        expected = [s[row.method] for s in oracle.scores.values()]
        if not expected:
            assert row.lower is row.upper is None
            continue
        assert row.lower is not None and row.upper is not None
        assert (row.lower.value, row.upper.value) == (min(expected), max(expected))
        for witness in (row.lower, row.upper):
            selected = _witness(witness, samples, bins, counts)
            assert witness.value == oracle.scores[selected][row.method]
    for pair in result.pairwise_bounds:
        expected = [
            s[pair.left_method] - s[pair.right_method] for s in oracle.scores.values()
        ]
        assert pair.negative_attainable == any(x < 0 for x in expected)
        assert pair.zero_attainable == any(x == 0 for x in expected)
        assert pair.positive_attainable == any(x > 0 for x in expected)
        assert pair.ranking_reversal == (
            any(x < 0 for x in expected) and any(x > 0 for x in expected)
        )
        if not expected:
            assert pair.lower is pair.upper is None
            continue
        assert pair.lower is not None and pair.upper is not None
        assert (pair.lower.value, pair.upper.value) == (min(expected), max(expected))
        for witness in (pair.lower, pair.upper):
            selected = _witness(witness, samples, bins, counts)
            scores = oracle.scores[selected]
            assert witness.value == scores[pair.left_method] - scores[pair.right_method]
    winners = {
        tuple(m for m, value in scores.items() if value == min(scores.values()))
        for scores in oracle.scores.values()
    }
    assert {w.methods for w in result.winner_sets} == winners
    assert result.winner_set_changes == (len(winners) > 1)
    assert result.unique_winner_changes == (sum(len(w) == 1 for w in winners) > 1)
    assert set(result.possible_winners) == {
        method for methods in winners for method in methods
    }
    for winner in result.winner_sets:
        selected = _witness(winner.witness, samples, bins, counts)
        scores = oracle.scores[selected]
        assert winner.witness.value == min(scores.values())
        assert winner.methods == tuple(
            m for m, value in scores.items() if value == min(scores.values())
        )
    assert len(result.pairwise_bounds) == len(
        tuple(combinations(next(iter(predictions.values())), 2))
    )
    return result


INTERVALS = (("-1", "3"), ("0", "0"), ("1", "1"), ("2", "3"))


@pytest.mark.parametrize("intervals", product(INTERVALS, repeat=3))
@pytest.mark.parametrize("depths", [("0", "1", "2"), ("0", "0", "1")])
@pytest.mark.parametrize("second", [("1", "2"), ("2", "3")])
def test_joint_scores_and_complete_witnesses_match_rational_grid(
    intervals: tuple[tuple[str, str], ...],
    depths: tuple[str, ...],
    second: tuple[str, str],
) -> None:
    counts = {"a": (2, 0), "b": (0, 3), "c": (1, 1)}
    rows = [
        _sample(n, d, interval, counts[n])
        for n, d, interval in zip(counts, depths, intervals, strict=True)
    ]
    bins = (_bin("first", "0", "1"), _bin("second", *second))
    predictions = {
        "first": {
            "a": (0.1, 0.9),
            "b": (0.75, 0.25),
            "tie": (0.1, 0.9),
            "near": (0.2, 0.8000000000000001),
        },
        "second": {
            "a": (0.9, 0.1),
            "b": (0.25, 0.75),
            "tie": (0.9, 0.1),
            "near": (0.8000000000000001, 0.2),
        },
    }
    _compare(rows, bins, counts, predictions)


def test_individual_bin_minima_cannot_be_combined_without_one_age_vector() -> None:
    counts = {"a": (1, 0), "b": (1, 1), "c": (0, 1)}
    rows = [
        _sample(n, str(i), interval, counts[n])
        for i, (n, interval) in enumerate(
            zip(counts, (("0", "0"), ("0.5", "1.5"), ("1.5", "1.5")), strict=True)
        )
    ]
    bins = (_bin("first", "0", "1"), _bin("second", "1", "2"))
    predictions = {
        "first": {"against": (0.0, 1.0), "with": (1.0, 0.0)},
        "second": {"against": (1.0, 0.0), "with": (0.0, 1.0)},
    }
    result = _compare(rows, bins, counts, predictions)
    against = next(row for row in result.method_bounds if row.method == "against")
    assert against.lower.value == against.upper.value == Fraction(5, 6)
    assert against.lower.value > Fraction(2, 3)


def test_joint_difference_can_span_zero_without_an_attainable_tie() -> None:
    counts = {"a": (1, 0), "b": (1, 1), "c": (0, 1)}
    rows = [
        _sample(name, str(i), interval, counts[name])
        for i, (name, interval) in enumerate(
            zip(counts, (("0", "0"), ("0.5", "1.5"), ("1.5", "1.5")), strict=True)
        )
    ]
    bins = (_bin("first", "0", "1"), _bin("second", "1", "2"))
    predictions = {
        bin_.bin_id: {"left": (1.0, 0.0), "right": (0.0, 1.0)} for bin_ in bins
    }
    result = _compare(rows, bins, counts, predictions)
    pair = result.pairwise_bounds[0]
    assert (pair.lower.value, pair.upper.value) == (-Fraction(1, 3), Fraction(1, 3))
    assert pair.ranking_reversal and not pair.zero_attainable
    assert result.unique_winner_changes


@pytest.mark.parametrize("zero", ["all", "first", "none"])
def test_four_bins_share_one_chronology_with_explicit_zero_denominators(
    zero: str,
) -> None:
    intervals = (("0", "0"), ("1", "1"), ("2", "2"), ("4", "4"), ("0", "5"))
    counts = {
        str(i): ((0, 0) if zero == "all" or zero == "first" and i == 0 else (i % 2, 1))
        for i in range(5)
    }
    rows = [
        _sample(str(i), str(i) if i < 4 else "2.5", interval, counts[str(i)])
        for i, interval in enumerate(intervals)
    ]
    bins = tuple(_bin(str(i), str(i), str(i + 1)) for i in (0, 1, 2, 4))
    predictions = {
        b.bin_id: {
            "left": (1.0, 0.0),
            "right": (0.0, 1.0),
            "left-tie": (1.0, 0.0),
            "center": (0.5, 0.5),
        }
        for b in bins
    }
    result = _compare(rows, bins, counts, predictions)
    assert result.joint_feasible_count > 0
    assert (result.scored_allocation_count == 0) == (zero != "none")


@pytest.mark.parametrize("adjacent", [True, False])
def test_shared_boundary_belongs_only_to_right_bin_or_to_neither_in_gap(
    adjacent: bool,
) -> None:
    counts = {"negative": (1, 0), "first": (1, 1), "boundary": (0, 1), "second": (1, 0)}
    rows = [
        _sample(name, str(i), (age, age), counts[name])
        for i, (name, age) in enumerate(
            zip(counts, ("-1", "0", "1", "2.5"), strict=True)
        )
    ]
    bins = (_bin("first", "0", "1"), _bin("second", "1" if adjacent else "2", "3"))
    predictions = {b.bin_id: {"a": (1.0, 0.0), "b": (0.0, 1.0)} for b in bins}
    result = _compare(rows, bins, counts, predictions)
    assert result.joint_feasible_count == result.scored_allocation_count == 1
    witness = result.method_bounds[0].lower
    assert witness.selected_sample_ids == (
        ("first",),
        ("boundary", "second") if adjacent else ("second",),
    )
