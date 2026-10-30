"""Admission, complete-bin denominators and exact aggregate comparison contracts."""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_age_support.depth_order.joint_allocations import (
    joint_block_graph,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support.depth_order.joint_prediction_sensitivity import (
    joint_prediction_sensitivity,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support.joint_membership import (
    AgeBin,
)

from .test_prediction_sensitivity import sample

BINS = (
    AgeBin("first", Decimal(0), Decimal(1)),
    AgeBin("second", Decimal(1), Decimal(2)),
)
PREDICTIONS = {b.bin_id: {"a": (0.1, 0.9), "b": (0.75, 0.25)} for b in BINS}
COUNTS = {"a": (2, 0), "b": (0, 3)}


@pytest.mark.parametrize(
    "bins",
    [
        BINS[:1],
        (BINS[0], BINS[0]),
        tuple(reversed(BINS)),
        (BINS[0], AgeBin("overlap", Decimal("0.5"), Decimal(2))),
        ("untyped", BINS[1]),
    ],
)
def test_rejects_missing_duplicate_overlapping_unordered_or_untyped_bins(
    bins: Any,
) -> None:
    rows = [
        sample("a", "0", "0", "0", COUNTS["a"]),
        sample("b", "1", "1", "1", COUNTS["b"]),
    ]
    with pytest.raises(ValueError, match="bins"):
        joint_prediction_sensitivity(rows, bins, COUNTS, PREDICTIONS, core_id="core")


@pytest.mark.parametrize(
    "mode",
    [
        "missing_bin",
        "extra_bin",
        "method_order",
        "missing_counts",
        "bool_count",
        "nonclosed",
        "nan",
        "int_prediction",
    ],
)
def test_preserves_original_count_and_frozen_prediction_admission(mode: str) -> None:
    rows = [
        sample("a", "0", "0", "0", COUNTS["a"]),
        sample("b", "1", "1", "1", COUNTS["b"]),
    ]
    counts: Any = dict(COUNTS)
    predictions: Any = {b: dict(v) for b, v in PREDICTIONS.items()}
    if mode == "missing_bin":
        del predictions["first"]
    elif mode == "extra_bin":
        predictions["extra"] = predictions["first"]
    elif mode == "method_order":
        predictions["second"] = dict(reversed(tuple(predictions["second"].items())))
    elif mode == "missing_counts":
        del counts["a"]
    elif mode == "bool_count":
        counts["a"] = (True, 1)
    else:
        predictions["first"]["a"] = {
            "nonclosed": (0.0, 0.0),
            "nan": (float("nan"), 1.0),
            "int_prediction": (0, 1),
        }[mode]
    with pytest.raises(ValueError):
        joint_prediction_sensitivity(rows, BINS, counts, predictions, core_id="core")


def test_all_bin_denominator_never_drops_empty_or_zero_count_bin() -> None:
    rows = [sample("a", "0", "0", "0", (0, 0)), sample("b", "1", "1", "1", (0, 3))]
    result = joint_prediction_sensitivity(
        rows, BINS, {"a": (0, 0), "b": (0, 3)}, PREDICTIONS, core_id="core"
    )
    assert result.joint_feasible_count == result.zero_closed_count_allocation_count == 1
    assert result.scored_allocation_count == 0
    assert result.refusal == "zero_closed_count_in_every_joint_allocation"
    assert not result.possible_winners
    assert all(b.lower is b.upper is None for b in result.method_bounds)
    empty = joint_prediction_sensitivity(
        rows,
        (BINS[0], AgeBin("later", Decimal(3), Decimal(4))),
        {"a": (0, 0), "b": (0, 3)},
        {"first": PREDICTIONS["first"], "later": PREDICTIONS["second"]},
        core_id="core",
    )
    assert empty.joint_feasible_count == empty.scored_allocation_count == 0
    assert empty.refusal == "no_joint_nonempty_bin_selection"
    assert empty.graph.single_bin_assessments[1].empty_selection_age_order is not None


def test_slightly_unclosed_binary64_values_are_never_reclosed() -> None:
    rows = [
        sample("a", "0", "0", "0", COUNTS["a"]),
        sample("b", "1", "1", "1", COUNTS["b"]),
    ]
    predictions = {
        b.bin_id: {"original": (0.2, 0.8000000000000001), "closed": (0.2, 0.8)}
        for b in BINS
    }
    result = joint_prediction_sensitivity(
        rows, BINS, COUNTS, predictions, core_id="core"
    )
    for method, vector in predictions["first"].items():
        expected = (
            sum(
                (
                    sum(
                        (
                            abs(Fraction.from_float(p) - Fraction(n, sum(c)))
                            for p, n in zip(vector, c, strict=True)
                        ),
                        Fraction(),
                    )
                    / 2
                    for c in COUNTS.values()
                ),
                Fraction(),
            )
            / 2
        )
        bounds = next(b for b in result.method_bounds if b.method == method)
        assert bounds.lower is not None and bounds.lower.value == expected
    pair = result.pairwise_bounds[0]
    assert (
        pair.zero_attainable
    )  # Opposite pure observations cancel the same offset exactly.


@pytest.mark.parametrize("path", [(), (0,), (0, 0, 0), (-1, 0), (99, 0), (True, 0)])
def test_witness_rejects_unadmitted_partial_or_invalid_graph_path(
    path: tuple[int, ...],
) -> None:
    rows = [
        sample("a", "0", "0", "0", COUNTS["a"]),
        sample("b", "1", "1", "1", COUNTS["b"]),
    ]
    graph = joint_block_graph(rows, BINS, core_id="core")
    with pytest.raises(ValueError):
        graph.witness(path)
