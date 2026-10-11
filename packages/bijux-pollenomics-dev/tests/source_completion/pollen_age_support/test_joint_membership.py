"""Independent exhaustive age-allocation oracle for exact marginal corners."""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from itertools import product

import pytest

from bijux_pollenomics_dev.source_completion.pollen_age_support.joint_membership import (
    AgeBin,
    MarginalAgeCountSample,
    assess_joint_extrema,
)


def sample(
    name: str, younger: str, older: str, numerator: int, denominator: int
) -> MarginalAgeCountSample:
    """Construct explicitly source-native exact test counts and age support."""
    return MarginalAgeCountSample(
        name, Decimal(younger), Decimal(older), numerator, denominator
    )


def allocations(
    samples: list[MarginalAgeCountSample], bins: list[AgeBin]
) -> set[tuple[Fraction, ...]]:
    """Enumerate age partition representatives, independent of threshold logic."""
    domains: list[set[int | None]] = []
    for row in samples:
        cuts = {row.younger_cal_bp, row.older_cal_bp}
        cuts.update(
            endpoint
            for bin_ in bins
            for endpoint in (bin_.younger_cal_bp, bin_.older_cal_bp_exclusive)
            if row.younger_cal_bp <= endpoint <= row.older_cal_bp
        )
        ordered = sorted(cuts)
        witnesses = cuts | {
            (left + right) / 2
            for left, right in zip(ordered, ordered[1:], strict=False)
        }
        domains.append(
            {
                next(
                    (
                        index
                        for index, bin_ in enumerate(bins)
                        if bin_.younger_cal_bp <= age < bin_.older_cal_bp_exclusive
                    ),
                    None,
                )
                for age in witnesses
            }
        )
    fractions: set[tuple[Fraction, ...]] = set()
    for choice in product(*domains):
        numerators = [
            sum(
                row.numerator_count
                for row, where in zip(samples, choice, strict=True)
                if where == index
            )
            for index in range(len(bins))
        ]
        denominators = [
            sum(
                row.denominator_count
                for row, where in zip(samples, choice, strict=True)
                if where == index
            )
            for index in range(len(bins))
        ]
        assert all(denominators)
        fractions.add(
            tuple(
                Fraction(numerator, denominator)
                for numerator, denominator in zip(numerators, denominators, strict=True)
            )
        )
    return fractions


@pytest.mark.parametrize(
    "interval",
    [("0", "4"), ("1", "3"), ("2", "4"), ("1", "2"), ("-1", "1"), ("4", "4")],
)
@pytest.mark.parametrize("counts", [(0, 2), (1, 2), (2, 2), (2, 3)])
@pytest.mark.parametrize("second_counts", [(0, 3), (1, 2), (3, 3)])
def test_all_corners_match_independent_exhaustive_oracle(
    interval: tuple[str, str], counts: tuple[int, int], second_counts: tuple[int, int]
) -> None:
    bins = [
        AgeBin("left", Decimal(0), Decimal(2)),
        AgeBin("right", Decimal(2), Decimal(4)),
    ]
    samples = [
        sample("anchor-left", "0", "0", 1, 2),
        sample("anchor-right", "3", "3", 1, 2),
        sample("crossing", *interval, *counts),
        sample("boundary", "1", "3", *second_counts),
    ]
    oracle = allocations(samples, bins)
    result = assess_joint_extrema(samples, bins)
    for index, bound in enumerate(result.marginal_bounds):
        assert bound.lower == min(values[index] for values in oracle)
        assert bound.upper == max(values[index] for values in oracle)
    identities = {row.sample_id: row for row in samples}
    for corner in result.corners:
        target = tuple(row.value for row in corner.targets)
        assert corner.attainable == (target in oracle)
        if not corner.attainable:
            assert corner.refusals
            assert not corner.assignments
            continue
        assigned: dict[str, str | None] = {}
        for witness in corner.assignments:
            original = identities[witness.sample_id]
            assert (
                original.younger_cal_bp
                <= witness.source_native_age
                <= original.older_cal_bp
            )
            locations = [
                bin_.bin_id
                for bin_ in bins
                if bin_.younger_cal_bp
                <= witness.source_native_age
                < bin_.older_cal_bp_exclusive
            ]
            assert locations == ([] if witness.bin_id is None else [witness.bin_id])
            assigned[witness.sample_id] = witness.bin_id
        assert set(assigned) == set(identities)
        actual = tuple(
            Fraction(
                sum(
                    row.numerator_count
                    for row in samples
                    if assigned[row.sample_id] == bin_.bin_id
                ),
                sum(
                    row.denominator_count
                    for row in samples
                    if assigned[row.sample_id] == bin_.bin_id
                ),
            )
            for bin_ in bins
        )
        assert actual == target


def test_internal_gap_and_closed_right_endpoint_remain_outside_choices() -> None:
    bins = [
        AgeBin("left", Decimal(0), Decimal(1)),
        AgeBin("right", Decimal(2), Decimal(3)),
    ]
    samples = [
        sample("left", "0", "0", 1, 2),
        sample("right", "2", "2", 1, 2),
        sample("gap", "0.5", "2.5", 2, 3),
        sample("closed-right", "2.5", "3", 0, 3),
    ]
    oracle = allocations(samples, bins)
    result = assess_joint_extrema(samples, bins)
    assert all(
        corner.attainable
        == (tuple(target.value for target in corner.targets) in oracle)
        for corner in result.corners
    )


def test_native_negative_evidence_and_unbounded_integer_counts_are_exact() -> None:
    enormous = 10**1000
    bins = [AgeBin("positive", Decimal(1), Decimal(2))]
    samples = [
        sample("anchor", "1", "1", enormous, 3 * enormous),
        sample("native-negative", "-3", "-1", 1, 2),
    ]
    result = assess_joint_extrema(samples, bins)
    assert (
        result.marginal_bounds[0].lower
        == result.marginal_bounds[0].upper
        == Fraction(1, 3)
    )
    assert all(corner.attainable for corner in result.corners)
    assert all(
        next(
            row for row in corner.assignments if row.sample_id == "native-negative"
        ).bin_id
        is None
        for corner in result.corners
    )


@pytest.mark.parametrize("younger,older", [("NaN", "1"), ("0", "Infinity"), ("2", "1")])
def test_nonfinite_or_reversed_source_intervals_refuse(
    younger: str, older: str
) -> None:
    with pytest.raises(ValueError):
        sample("sample", younger, older, 1, 2)


@pytest.mark.parametrize("name", ["", " spaced", "spaced "])
def test_noncanonical_identities_refuse(name: str) -> None:
    with pytest.raises(ValueError):
        sample(name, "0", "1", 1, 2)


@pytest.mark.parametrize(
    "numerator,denominator", [(True, 2), (1, False), (-1, 2), (3, 2), (0, 0)]
)
def test_invalid_exact_count_contract_refuses(numerator: int, denominator: int) -> None:
    with pytest.raises(ValueError):
        sample("sample", "0", "1", numerator, denominator)


@pytest.mark.parametrize(
    "younger,older", [("-1", "1"), ("1", "1"), ("2", "1"), ("0", "NaN")]
)
def test_nonpositive_width_or_negative_analysis_bins_refuse(
    younger: str, older: str
) -> None:
    with pytest.raises(ValueError):
        AgeBin("bin", Decimal(younger), Decimal(older))


def test_missing_mandatory_mass_is_an_explicit_scope_refusal() -> None:
    with pytest.raises(ValueError, match="mandatory mass"):
        assess_joint_extrema(
            [sample("optional", "0", "2", 1, 2)],
            [AgeBin("bin", Decimal(0), Decimal(1))],
        )


def test_duplicate_sample_bin_and_overlapping_domains_refuse() -> None:
    row = sample("anchor", "0", "0", 1, 2)
    bin_ = AgeBin("bin", Decimal(0), Decimal(1))
    with pytest.raises(ValueError, match="sample identities"):
        assess_joint_extrema([row, row], [bin_])
    with pytest.raises(ValueError, match="bin identities"):
        assess_joint_extrema([row], [bin_, bin_])
    with pytest.raises(ValueError, match="disjoint"):
        assess_joint_extrema(
            [row], [bin_, AgeBin("overlap", Decimal("0.5"), Decimal(2))]
        )


def test_empty_input_refuses() -> None:
    with pytest.raises(ValueError, match="nonempty"):
        assess_joint_extrema([], [])
