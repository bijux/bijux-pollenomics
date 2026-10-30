"""Independent exhaustive allocations verify score and paired ranking sensitivity."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from fractions import Fraction
from itertools import product
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_age_support.depth_order.extrema import (
    DepthCountSample,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support.depth_order.prediction_sensitivity import (
    ordered_prediction_sensitivity,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support.joint_membership import (
    AgeBin,
    MarginalAgeCountSample,
)


def sample(
    name: str, depth: str, low: str, high: str, counts: tuple[int, ...]
) -> DepthCountSample:
    return DepthCountSample(
        MarginalAgeCountSample(
            name, Decimal(low), Decimal(high), sum(counts), sum(counts) + 1
        ),
        Decimal(depth),
    )


PREDICTIONS = {
    "left": (0.1, 0.9),
    "right": (0.75, 0.25),
    "center": (0.5, 0.5),
    "unrounded": (0.2, 0.8000000000000001),
}
BIN = AgeBin("target", Decimal(0), Decimal(2))
INTERVALS = [("-1", "3"), ("0", "0"), ("0", "1"), ("1", "2"), ("2", "3")]


def exhaustive_scores(
    rows: list[DepthCountSample],
    counts: Mapping[str, tuple[int, ...]],
    predictions: Mapping[str, tuple[float, ...]],
) -> tuple[
    dict[tuple[str, ...], dict[str, Fraction]], bool, bool, set[tuple[str, ...]]
]:
    cuts = sorted(
        {Decimal(0), Decimal(2)}
        | {v for r in rows for v in (r.sample.younger_cal_bp, r.sample.older_cal_bp)}
    )
    ages = sorted(
        set(cuts) | {(a + b) / 2 for a, b in zip(cuts, cuts[1:], strict=False)}
    )
    scored = {}
    native = empty = False
    zeros = set()
    for vector in product(
        *[
            [a for a in ages if r.sample.younger_cal_bp <= a <= r.sample.older_cal_bp]
            for r in rows
        ]
    ):
        if not all(
            (a == b if x.depth == y.depth else a <= b)
            for x, a in zip(rows, vector, strict=True)
            for y, b in zip(rows, vector, strict=True)
            if x.depth <= y.depth
        ):
            continue
        native = True
        selected = tuple(
            sorted(
                r.sample.sample_id
                for r, age in zip(rows, vector, strict=True)
                if 0 <= age < 2
            )
        )
        if not selected:
            empty = True
            continue
        total = tuple(
            sum(counts[s][i] for s in selected)
            for i in range(len(next(iter(predictions.values()))))
        )
        if not sum(total):
            zeros.add(selected)
            continue
        scored[selected] = {
            method: sum(
                (
                    abs(Fraction.from_float(p) - Fraction(n, sum(total)))
                    for p, n in zip(prediction, total, strict=True)
                ),
                Fraction(),
            )
            / len(total)
            for method, prediction in predictions.items()
        }
    return scored, empty, native, zeros


@pytest.mark.parametrize("intervals", product(INTERVALS, repeat=3))
@pytest.mark.parametrize("depths", [("0", "1", "2"), ("0", "0", "1")])
def test_exact_scores_pairs_and_winners_match_independent_age_enumeration(
    intervals: tuple[tuple[str, str], ...], depths: tuple[str, ...]
) -> None:
    counts = {"a": (2, 0), "b": (0, 3), "c": (1, 1)}
    rows = [
        sample(name, depth, low, high, counts[name])
        for name, depth, (low, high) in zip(counts, depths, intervals, strict=True)
    ]
    oracle, empty, native, zeros = exhaustive_scores(rows, counts, PREDICTIONS)
    result = ordered_prediction_sensitivity(
        list(reversed(rows)), BIN, counts, PREDICTIONS, core_id="core"
    )
    assert result.native_age_order.attainable == native
    assert (result.empty_selection_age_order is not None) == empty
    assert result.scored_block_count == len(oracle)
    assert result.feasible_block_count == len(oracle) + len(zeros)
    assert set(result.zero_closed_count_selections) == zeros
    winners = {
        tuple(
            method for method, score in scores.items() if score == min(scores.values())
        )
        for scores in oracle.values()
    }
    assert {w.methods for w in result.winner_sets} == winners
    assert result.winner_set_changes == (len(winners) > 1)
    assert result.unique_winner_changes == (sum(len(w) == 1 for w in winners) > 1)
    assert set(result.possible_winners) == {
        method for methods in winners for method in methods
    }
    for row in result.method_bounds:
        if not oracle:
            assert row.lower is row.upper is None
            continue
        assert row.lower is not None and row.upper is not None
        expected = [scores[row.method] for scores in oracle.values()]
        assert (row.lower.value, row.upper.value) == (min(expected), max(expected))
        for w in (row.lower, row.upper):
            assert oracle[tuple(sorted(w.selected_sample_ids))][row.method] == w.value
            assignments = {a.sample_id: a.native_age for a in w.age_order.assignments}
            assert set(assignments) == set(counts)
            assert all(
                r.sample.younger_cal_bp
                <= assignments[r.sample.sample_id]
                <= r.sample.older_cal_bp
                for r in rows
            )
            assert tuple(
                sorted(
                    r.sample.sample_id
                    for r in rows
                    if BIN.contains(assignments[r.sample.sample_id])
                )
            ) == tuple(sorted(w.selected_sample_ids))
    assert len(result.pairwise_bounds) == 6
    for pair in result.pairwise_bounds:
        expected = [
            scores[pair.left_method] - scores[pair.right_method]
            for scores in oracle.values()
        ]
        assert pair.negative_attainable == any(x < 0 for x in expected)
        assert pair.zero_attainable == any(x == 0 for x in expected)
        assert pair.positive_attainable == any(x > 0 for x in expected)
        assert pair.ranking_reversal == (
            any(x < 0 for x in expected) and any(x > 0 for x in expected)
        )
        if expected:
            assert pair.lower is not None and pair.upper is not None
            assert (pair.lower.value, pair.upper.value) == (
                min(expected),
                max(expected),
            )
            for w in (pair.lower, pair.upper):
                scores = oracle[tuple(sorted(w.selected_sample_ids))]
                assert w.value == scores[pair.left_method] - scores[pair.right_method]
        else:
            assert pair.lower is pair.upper is None
    for winner in result.winner_sets:
        scores = oracle[tuple(sorted(winner.witness.selected_sample_ids))]
        assert winner.witness.value == min(scores.values())
        assert winner.methods == tuple(
            m for m, value in scores.items() if value == min(scores.values())
        )


def test_same_allocation_difference_cannot_subtract_independent_ranges() -> None:
    counts = {"a": (1, 0), "b": (0, 1)}
    rows = [
        sample(name, str(i), "-1", "3", vector)
        for i, (name, vector) in enumerate(counts.items())
    ]
    predictions = {"same-a": (1.0, 0.0), "same-b": (1.0, 0.0)}
    result = ordered_prediction_sensitivity(
        rows, BIN, counts, predictions, core_id="core"
    )
    a, b = result.method_bounds
    assert (
        a.lower is not None
        and a.upper is not None
        and b.lower is not None
        and b.upper is not None
    )
    assert a.lower.value - b.upper.value == -1 and a.upper.value - b.lower.value == 1
    pair = result.pairwise_bounds[0]
    assert pair.lower is not None and pair.upper is not None
    assert pair.lower.value == pair.upper.value == 0
    assert pair.zero_attainable and not pair.ranking_reversal


def test_pairwise_flip_does_not_imply_best_predictor_changes() -> None:
    counts = {"a": (49, 51), "b": (51, 49)}
    rows = [
        sample(name, str(i), "-1", "3", vector)
        for i, (name, vector) in enumerate(counts.items())
    ]
    predictions = {
        "left": (0.0, 1.0),
        "right": (1.0, 0.0),
        "center-a": (0.5, 0.5),
        "center-b": (0.5, 0.5),
    }
    result = ordered_prediction_sensitivity(
        rows, BIN, counts, predictions, core_id="core"
    )
    assert result.pairwise_bounds[0].ranking_reversal
    assert result.possible_winners == ("center-a", "center-b")
    assert len(result.winner_sets) == 1
    assert result.winner_sets[0].methods == ("center-a", "center-b")
    assert not result.winner_set_changes and not result.unique_winner_changes


def test_exact_pair_range_spanning_zero_need_not_have_an_attainable_tie() -> None:
    counts = {"a": (1, 2), "b": (4, 1)}
    rows = [
        sample(name, str(i), "-1", "3", vector)
        for i, (name, vector) in enumerate(counts.items())
    ]
    predictions = {"left": (0.0, 1.0), "right": (1.0, 0.0)}
    result = ordered_prediction_sensitivity(
        rows, BIN, counts, predictions, core_id="core"
    )
    pair = result.pairwise_bounds[0]
    assert pair.ranking_reversal and not pair.zero_attainable
    assert result.unique_winner_changes


def test_stored_predictions_are_never_reclosed_or_rounded_to_decimal() -> None:
    counts = {"a": (1, 0)}
    rows = [sample("a", "0", "0", "0", counts["a"])]
    predictions = {"not-reclosed": (0.5, 0.5000000005), "binary": (0.1, 0.9)}
    result = ordered_prediction_sensitivity(
        rows, BIN, counts, predictions, core_id="core"
    )
    a, b = result.method_bounds
    assert a.lower is not None and b.lower is not None
    q0, q1 = map(Fraction.from_float, predictions["not-reclosed"])
    assert q0 + q1 != 1
    assert a.lower.value == (1 - q0 + q1) / 2
    assert a.lower.value != 1 - q0 / (q0 + q1)
    assert (
        b.lower.value == (1 - Fraction.from_float(0.1) + Fraction.from_float(0.9)) / 2
    )
    assert b.lower.value != Fraction(9, 10)


@pytest.mark.parametrize(
    "vector,admitted",
    [
        ((0.5, 0.5000000005), True),
        ((0.5, 0.4999999995), True),
        ((0.5, 0.500000002), False),
        ((0.5, 0.499999998), False),
    ],
)
def test_prediction_admission_matches_existing_composition_contract(
    vector: tuple[float, ...], admitted: bool
) -> None:
    from bijux_pollenomics.analysis.lra_validation.metrics import closed_composition

    counts = {"a": (1, 0)}
    rows = [sample("a", "0", "0", "0", counts["a"])]
    values = {str(i): value for i, value in enumerate(vector)}
    predictions = {"tested": vector, "reference": (0.5, 0.5)}
    if admitted:
        assert closed_composition(values) == values
        result = ordered_prediction_sensitivity(
            rows, BIN, counts, predictions, core_id="core"
        )
        assert result.refusal is None
    else:
        with pytest.raises(ValueError):
            closed_composition(values)
        with pytest.raises(ValueError, match="closure contract"):
            ordered_prediction_sensitivity(
                rows, BIN, counts, predictions, core_id="core"
            )


def test_zero_closed_counts_empty_selection_and_inconsistent_core_stay_unscored() -> (
    None
):
    zeros = {"zero": (0, 0)}
    result = ordered_prediction_sensitivity(
        [sample("zero", "0", "0", "0", (0, 0))], BIN, zeros, PREDICTIONS, core_id="core"
    )
    assert result.refusal == "zero_closed_count_for_all_feasible_blocks"
    assert result.zero_closed_count_selections == (("zero",),)
    assert result.scored_block_count == 0 and not result.possible_winners
    outside = ordered_prediction_sensitivity(
        [sample("zero", "0", "2", "3", (0, 0))], BIN, zeros, PREDICTIONS, core_id="core"
    )
    assert (
        outside.refusal == "no_feasible_nonempty_selection"
        and outside.empty_selection_age_order is not None
    )
    counts = {"a": (1, 0), "b": (0, 1)}
    inconsistent = ordered_prediction_sensitivity(
        [
            sample("a", "0", "3", "3", counts["a"]),
            sample("b", "1", "0", "0", counts["b"]),
        ],
        BIN,
        counts,
        PREDICTIONS,
        core_id="core",
    )
    assert inconsistent.refusal == "native_age_order_infeasible"
    assert inconsistent.tested_block_count == 0 and not inconsistent.winner_sets


@pytest.mark.parametrize(
    "corruption",
    [
        "missing",
        "extra",
        "negative",
        "sum",
        "float_count",
        "axis",
        "nan",
        "integer_prediction",
        "outside",
        "all_zero",
        "unclosed",
        "beyond_closure",
        "one_method",
    ],
)
def test_invalid_count_identity_and_frozen_prediction_contract_refuses(
    corruption: str,
) -> None:
    rows = [sample("a", "0", "0", "1", (1, 1))]
    counts: Any = {"a": (1, 1)}
    predictions: Any = dict(PREDICTIONS)
    if corruption == "missing":
        counts = {}
    elif corruption == "extra":
        counts["extra"] = (1, 1)
    elif corruption == "negative":
        counts["a"] = (-1, 3)
    elif corruption == "sum":
        counts["a"] = (1, 2)
    elif corruption == "float_count":
        counts["a"] = (1.0, 1)
    elif corruption == "axis":
        predictions["left"] = (0.1,)
    elif corruption == "nan":
        predictions["left"] = (float("nan"), 0.9)
    elif corruption == "integer_prediction":
        predictions["left"] = (0, 1)
    elif corruption == "outside":
        predictions["left"] = (-0.1, 1.1)
    elif corruption == "all_zero":
        predictions["left"] = (0.0, 0.0)
    elif corruption == "unclosed":
        predictions["left"] = (0.25, 0.5)
    elif corruption == "beyond_closure":
        predictions["left"] = (0.5, 0.500000002)
    else:
        predictions = {"only": (0.5, 0.5)}
    with pytest.raises(ValueError):
        ordered_prediction_sensitivity(rows, BIN, counts, predictions, core_id="core")
