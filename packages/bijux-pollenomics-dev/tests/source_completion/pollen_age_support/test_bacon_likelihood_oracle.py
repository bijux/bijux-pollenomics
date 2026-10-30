"""Exact closed-form checks of the source-native no-hiatus likelihood oracle."""

from __future__ import annotations

from collections import Counter
import csv
from fractions import Fraction
import json
import math
from pathlib import Path

import pytest

CASES = {
    "two-section",
    "three-section",
    "constant-innovations",
    "memory-near-zero",
    "memory-near-one",
    "nondivisible-requested-range",
}


def closed_form_age(
    alpha: tuple[Fraction, ...],
    memory: Fraction,
    *,
    top: Fraction,
    depth: Fraction,
    origin: Fraction,
    width: Fraction,
) -> Fraction:
    """Use the finite geometric expansion, not the production backward loop."""
    if not alpha or not 0 < memory < 1 or any(value <= 0 for value in alpha):
        raise ValueError("Invalid positive innovation or memory axis")
    if width <= 0 or not origin <= depth <= origin + len(alpha) * width:
        raise ValueError("Depth outside the declared finite section population")
    age = top
    for index in range(len(alpha)):
        rate = memory ** (len(alpha) - 1 - index) * alpha[-1]
        rate += (1 - memory) * sum(
            (
                memory ** (position - index) * alpha[position]
                for position in range(index, len(alpha) - 1)
            ),
            Fraction(),
        )
        overlap = min(max(depth - origin - index * width, Fraction()), width)
        age += rate * overlap
    return age


def _binary(token: str) -> Fraction:
    value = float(token)
    if not math.isfinite(value):
        raise ValueError("Oracle cells must be finite binary64 values")
    return Fraction.from_float(value)


def verify_native_output(directory: Path) -> dict[str, object]:
    """Check every saved comparison and refusal without importing the producer."""
    with (directory / "comparisons.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    counts = Counter(row["case"] for row in rows)
    assert set(counts) == CASES
    assert counts == Counter(
        {case: 14 if case == "nondivisible-requested-range" else 10 for case in CASES}
    )
    keys = [(row["case"], row["fixture_row"], row["depth_cm"]) for row in rows]
    assert len(keys) == len(set(keys)) == 64
    native_gaps, helper_gaps, raw_gaps = [], [], []
    for row in rows:
        alpha = tuple(_binary(token) for token in row["innovations"].split(";"))
        assert len(alpha) == int(row["sections"])
        origin, width = (
            _binary(row["origin_cm"]),
            _binary(row["native_section_width_cm"]),
        )
        assert width == _binary(row["thick_cm"])
        assert _binary(row["native_model_end_cm"]) == origin + len(alpha) * width
        if row["case"] == "nondivisible-requested-range":
            assert len(alpha) == 51 and origin == 648 and width == 5
            assert row["requested_max_cm"] == "896"
            assert row["native_model_end_cm"] == "903"
        expected = closed_form_age(
            alpha,
            _binary(row["memory"]),
            top=_binary(row["top_age_cal_bp"]),
            depth=_binary(row["depth_cm"]),
            origin=origin,
            width=width,
        )
        native_gaps.append(abs(float(_binary(row["native_likelihood_age"]) - expected)))
        helper_gaps.append(abs(float(_binary(row["corrected_helper_age"]) - expected)))
        raw_gaps.append(abs(float(_binary(row["raw_helper_age"]) - expected)))
    assert max(native_gaps) <= 1e-8
    assert max(helper_gaps) <= 1e-8
    assert max(raw_gaps) > 1
    with (directory / "refusals.csv").open(newline="") as handle:
        refusals = list(csv.DictReader(handle))
    assert {row["case"] for row in refusals} == {
        "zero-memory",
        "unit-memory",
        "zero-terminal-rate",
        "top-outside-bound",
    }
    assert len(refusals) == 4
    assert all(row["source_support"] == "FALSE" for row in refusals)
    summary = json.loads((directory / "summary.json").read_text())
    assert summary["source_version"] == "4.0.2"
    assert summary["model_fits"] == 0
    assert summary["fixture_cases"] == 6 and summary["comparison_rows"] == 64
    assert summary["source_support_refusals"] == 4
    assert summary["absolute_tolerance"] == 1e-8 and summary["relative_tolerance"] == 0
    assert summary["passed"] is True
    return {
        "comparison_rows": len(rows),
        "source_support_refusals": len(refusals),
        "maximum_native_exact_age_gap": max(native_gaps),
        "maximum_corrected_helper_exact_age_gap": max(helper_gaps),
        "maximum_raw_helper_exact_age_gap": max(raw_gaps),
        "model_fits": 0,
    }


@pytest.mark.parametrize(
    ("depth", "expected"),
    [(0, 0), (Fraction(5, 2), 15), (5, 30), (Fraction(15, 2), 55), (10, 80)],
)
def test_two_section_exact_likelihood_age_witness(
    depth: Fraction, expected: Fraction
) -> None:
    assert (
        closed_form_age(
            (Fraction(2), Fraction(10)),
            Fraction(1, 2),
            top=Fraction(),
            depth=Fraction(depth),
            origin=Fraction(),
            width=Fraction(5),
        )
        == expected
    )


@pytest.mark.parametrize(
    "memory", [Fraction(1, 1_000_000), Fraction(1, 2), Fraction(999999, 1_000_000)]
)
def test_constant_innovations_reduce_to_one_exact_linear_age(memory: Fraction) -> None:
    for depth in [Fraction(648), Fraction(1301, 2), Fraction(663)]:
        assert closed_form_age(
            (Fraction(4),) * 3,
            memory,
            top=Fraction(-52),
            depth=depth,
            origin=Fraction(648),
            width=Fraction(5),
        ) == -52 + 4 * (depth - 648)


@pytest.mark.parametrize("memory", [Fraction(0), Fraction(1), Fraction(-1)])
def test_undefined_memory_support_is_not_a_posterior_state(memory: Fraction) -> None:
    with pytest.raises(ValueError, match="memory"):
        closed_form_age(
            (Fraction(2), Fraction(10)),
            memory,
            top=Fraction(),
            depth=Fraction(5),
            origin=Fraction(),
            width=Fraction(5),
        )


def test_nondivisible_requested_range_uses_expanded_model_geometry() -> None:
    # Source elbows 648:893 plus 898 give K=51 and native model end903.
    alpha = (Fraction(4),) * 51
    expected = closed_form_age(
        alpha,
        Fraction(1, 2),
        top=Fraction(-52),
        depth=Fraction(896),
        origin=Fraction(648),
        width=Fraction(5),
    )
    assert expected == 940
    assert Fraction(896 - 648, 50) != 5
