"""Independent exhaustive age allocations establish sharp ordered bounds."""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from itertools import product

import pytest

from bijux_pollenomics_dev.source_completion.pollen_age_support.depth_order.count_fraction import (
    ordered_count_fraction_bounds,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support.depth_order.extrema import (
    DepthCountSample,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support.joint_membership import (
    AgeBin,
    MarginalAgeCountSample,
)


def sample(
    name: str, depth: str, low: str, high: str, n: int, d: int
) -> DepthCountSample:
    return DepthCountSample(
        MarginalAgeCountSample(name, Decimal(low), Decimal(high), n, d), Decimal(depth)
    )


def oracle(
    rows: list[DepthCountSample], bin_: AgeBin
) -> tuple[dict[tuple[str, ...], Fraction], bool, bool]:
    """Enumerate endpoint/midpoint ages, without contiguous-block reasoning."""
    cuts = sorted(
        {bin_.younger_cal_bp, bin_.older_cal_bp_exclusive}
        | {v for r in rows for v in (r.sample.younger_cal_bp, r.sample.older_cal_bp)}
    )
    choices = sorted(
        set(cuts) | {(a + b) / 2 for a, b in zip(cuts, cuts[1:], strict=False)}
    )
    values: dict[tuple[str, ...], Fraction] = {}
    empty = native = False
    for ages in product(
        *[
            [
                a
                for a in choices
                if r.sample.younger_cal_bp <= a <= r.sample.older_cal_bp
            ]
            for r in rows
        ]
    ):
        if not all(
            (a == b if x.depth == y.depth else a <= b)
            for x, a in zip(rows, ages, strict=True)
            for y, b in zip(rows, ages, strict=True)
            if x.depth <= y.depth
        ):
            continue
        native = True
        selected = [
            r.sample for r, age in zip(rows, ages, strict=True) if bin_.contains(age)
        ]
        if not selected:
            empty = True
            continue
        ids = tuple(sorted(r.sample_id for r in selected))
        values[ids] = Fraction(
            sum(r.numerator_count for r in selected),
            sum(r.denominator_count for r in selected),
        )
    return values, empty, native


INTERVALS = [("-1", "3"), ("0", "0"), ("0", "1"), ("1", "2"), ("2", "3")]


@pytest.mark.parametrize("intervals", product(INTERVALS, repeat=3))
@pytest.mark.parametrize("depths", [("0", "1", "2"), ("0", "0", "1")])
def test_sharpness_matches_independent_exhaustive_age_assignments(
    intervals: tuple[tuple[str, str], ...], depths: tuple[str, ...]
) -> None:
    rows = [
        sample(str(i), depth, a, b, n, d)
        for i, ((a, b), depth, (n, d)) in enumerate(
            zip(intervals, depths, [(1, 2), (0, 3), (4, 5)], strict=True)
        )
    ]
    bin_ = AgeBin("inside", Decimal(0), Decimal(2))
    values, empty, native = oracle(rows, bin_)
    result = ordered_count_fraction_bounds(list(reversed(rows)), bin_, core_id="core")
    assert result.native_age_order.attainable == native
    assert (result.empty_selection_age_order is not None) == empty
    assert result.feasible_block_count == len(values)
    assert (
        result.candidate_block_count == len(set(depths)) * (len(set(depths)) + 1) // 2
    )
    if not values:
        assert result.lower is result.upper is None
        assert result.refusal == (
            "no_feasible_nonempty_selection"
            if native
            else "native_age_order_infeasible"
        )
    else:
        assert result.lower is not None and result.upper is not None
        assert result.refusal is None
        assert result.lower.value == min(values.values())
        assert result.upper.value == max(values.values())
        for witness in (result.lower, result.upper):
            assert values[tuple(sorted(witness.selected_sample_ids))] == witness.value
            assignments = {
                a.sample_id: a.native_age for a in witness.age_order.assignments
            }
            assert set(assignments) == {r.sample.sample_id for r in rows}
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
                    if bin_.contains(assignments[r.sample.sample_id])
                )
            ) == tuple(sorted(witness.selected_sample_ids))
            assert all(
                (
                    assignments[x.sample.sample_id] == assignments[y.sample.sample_id]
                    if x.depth == y.depth
                    else assignments[x.sample.sample_id]
                    <= assignments[y.sample.sample_id]
                )
                for x in rows
                for y in rows
                if x.depth <= y.depth
            )
            assert (
                Fraction(witness.numerator_count, witness.denominator_count)
                == witness.value
            )


def test_native_edges_tied_depths_negative_prefix_and_large_integer_ratios() -> None:
    large = 2**70
    rows = [
        sample("negative", "0", "-5", "-1", 1, 2),
        sample("lower", "1", "0", "0", large - 1, large),
        sample("same-depth", "1", "-1", "1", 1, large),
        sample("upper", "2", "2", "2", 0, 1),
    ]
    result = ordered_count_fraction_bounds(
        rows, AgeBin("bin", Decimal(0), Decimal(2)), core_id="core"
    )
    assert result.lower is not None and result.upper is not None
    assert result.lower.value == result.upper.value == Fraction(1, 2)
    assert result.lower.selected_sample_ids == ("lower", "same-depth")
    assert result.lower.denominator_count == 2 * large
    assert result.empty_selection_age_order is None
    ages = {r.sample_id: r.native_age for r in result.lower.age_order.assignments}
    assert ages == {
        "negative": Decimal(-5),
        "lower": Decimal(0),
        "same-depth": Decimal(0),
        "upper": Decimal(2),
    }


def test_incompatible_outside_prefix_or_suffix_cannot_supply_a_partial_witness() -> (
    None
):
    bin_ = AgeBin("bin", Decimal(1), Decimal(2))
    for rows in (
        [sample("prefix", "0", "3", "3", 0, 1), sample("inside", "1", "1", "1", 1, 2)],
        [sample("inside", "0", "1", "1", 1, 2), sample("suffix", "1", "0", "0", 0, 1)],
    ):
        result = ordered_count_fraction_bounds(rows, bin_, core_id="core")
        assert result.refusal == "native_age_order_infeasible"
        assert result.tested_block_count == 0 and result.lower is result.upper is None


def test_empty_bin_has_no_zero_fraction_and_zero_denominator_is_invalid() -> None:
    result = ordered_count_fraction_bounds(
        [sample("outside", "0", "2", "3", 0, 1)],
        AgeBin("bin", Decimal(0), Decimal(2)),
        core_id="core",
    )
    assert result.refusal == "no_feasible_nonempty_selection"
    assert result.empty_selection_age_order is not None
    assert result.lower is result.upper is None
    with pytest.raises(ValueError, match="denominator"):
        sample("invalid", "0", "0", "1", 0, 0)


def test_missing_or_duplicate_samples_refuse() -> None:
    bin_ = AgeBin("bin", Decimal(0), Decimal(1))
    with pytest.raises(ValueError, match="nonempty"):
        ordered_count_fraction_bounds([], bin_, core_id="core")
    row = sample("duplicate", "0", "0", "1", 1, 2)
    with pytest.raises(ValueError, match="unique"):
        ordered_count_fraction_bounds([row, row], bin_, core_id="core")
