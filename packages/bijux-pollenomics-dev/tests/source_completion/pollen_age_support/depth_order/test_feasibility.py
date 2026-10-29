"""Exhaustive finite-age oracles independent of the earliest-prefix solver."""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from itertools import product

import pytest

from bijux_pollenomics_dev.source_completion.pollen_age_support.depth_order import (
    AgeComponent,
    DepthAgeDomain,
    DepthCountSample,
    assess_age_order,
    assess_depth_ordered_extrema,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support.joint_membership import (
    AgeBin,
    MarginalAgeCountSample,
)


def domain(name: str, depth: str, *parts: tuple[str, str, bool]) -> DepthAgeDomain:
    return DepthAgeDomain(
        name,
        Decimal(depth),
        tuple(AgeComponent(Decimal(a), Decimal(b), closed) for a, b, closed in parts),
    )


def witnesses(rows: list[DepthAgeDomain]) -> list[tuple[Decimal, ...]]:
    """Enumerate all endpoint/midpoint partitions, without greedy selection."""
    cuts = sorted(
        {
            value
            for row in rows
            for part in row.components
            for value in (part.younger, part.older)
        }
    )
    choices = set(cuts) | {(a + b) / 2 for a, b in zip(cuts, cuts[1:], strict=False)}
    return [
        ages
        for ages in product(
            *[
                [
                    age
                    for age in sorted(choices)
                    if any(part.contains(age) for part in row.components)
                ]
                for row in rows
            ]
        )
        if all(
            (a == b if left.depth == right.depth else a <= b)
            for left, a in zip(rows, ages, strict=True)
            for right, b in zip(rows, ages, strict=True)
            if left.depth <= right.depth
        )
    ]


PARTS = [
    (("-2", "-1", True),),
    (("-1", "1", True),),
    (("0", "0", True),),
    (("0", "1", False),),
    (("1", "2", False),),
    (("2", "2", True),),
    (("-2", "-1", True), ("1", "2", False)),
    (("0", "1", False), ("2", "2", True)),
]


@pytest.mark.parametrize("first,second", product(PARTS, repeat=2))
@pytest.mark.parametrize("middle_depth", ["0", "1"])
def test_complete_existence_matches_exhaustive_age_partitions(
    first: tuple[tuple[str, str, bool], ...],
    second: tuple[tuple[str, str, bool], ...],
    middle_depth: str,
) -> None:
    rows = [
        domain("a", "0", *first),
        domain("b", middle_depth, *second),
        domain("c", "2", ("-1", "2", True)),
    ]
    oracle = witnesses(rows)
    result = assess_age_order(list(reversed(rows)), core_id="declared-core")
    assert result.attainable == bool(oracle)
    if not oracle:
        assert result.refusal is not None and not result.assignments
        assert result.refusal.sample_id in {row.sample_id for row in rows}
        return
    assigned = {row.sample_id: row.native_age for row in result.assignments}
    vector = tuple(assigned[row.sample_id] for row in rows)
    assert vector in oracle
    assert vector == min(oracle)
    assert result.refusal is None


def test_equal_depth_intersection_is_not_artificial_id_ordering() -> None:
    rows = [domain("z", "1", ("0", "1", False)), domain("a", "1", ("1", "2", True))]
    result = assess_age_order(rows, core_id="core")
    assert not result.attainable
    assert result.refusal is not None
    assert result.refusal.equal_depth_sample_ids == ("a", "z")
    valid = [domain("z", "1", ("0", "1", True)), rows[1]]
    assert {
        row.native_age for row in assess_age_order(valid, core_id="core").assignments
    } == {Decimal(1)}


def test_gap_stays_missing_and_isolated_endpoint_can_supply_age_tie() -> None:
    rows = [
        domain("first", "0", ("1", "1", True)),
        domain("next", "1", ("-2", "0", False), ("2", "2", True)),
    ]
    result = assess_age_order(rows, core_id="core")
    assert [row.native_age for row in result.assignments] == [Decimal(1), Decimal(2)]
    rows[1] = domain("next", "1", ("-2", "0", True), ("1", "1", True))
    assert [
        row.native_age for row in assess_age_order(rows, core_id="core").assignments
    ] == [Decimal(1), Decimal(1)]


@pytest.mark.parametrize("counts", [(0, 2), (1, 2), (2, 2)])
@pytest.mark.parametrize(
    "depths", [("0", "1", "2", "3"), ("0", "0", "1", "2"), ("0", "3", "1", "2")]
)
def test_joint_corner_decisions_match_independent_ordered_allocation_oracle(
    counts: tuple[int, int],
    depths: tuple[str, ...],
) -> None:
    bins = [
        AgeBin("left", Decimal(0), Decimal(2)),
        AgeBin("right", Decimal(2), Decimal(4)),
    ]
    specifications: list[tuple[str, str, str, int, int]] = [
        ("left", "0", "0", 1, 2),
        ("right", "3", "3", 1, 2),
        ("cross", "1", "3", *counts),
        ("outside", "-1", "4", 1, 3),
    ]
    samples = [
        DepthCountSample(
            MarginalAgeCountSample(name, Decimal(a), Decimal(b), n, d), Decimal(depth)
        )
        for (name, a, b, n, d), depth in zip(specifications, depths, strict=True)
    ]
    # Bin boundaries split otherwise continuous source domains; exhaustive ages
    # must represent each such partition in addition to native endpoints.
    cuts = {Decimal(v) for v in ("-1", "0", "1", "2", "3", "4")}
    ages = sorted(
        cuts
        | {(a + b) / 2 for a, b in zip(sorted(cuts), sorted(cuts)[1:], strict=False)}
    )
    fractions = set()
    for vector in product(
        *[
            [
                age
                for age in ages
                if row.sample.younger_cal_bp <= age <= row.sample.older_cal_bp
            ]
            for row in samples
        ]
    ):
        if not all(
            (a == b if x.depth == y.depth else a <= b)
            for x, a in zip(samples, vector, strict=True)
            for y, b in zip(samples, vector, strict=True)
            if x.depth <= y.depth
        ):
            continue
        values = []
        for bin_ in bins:
            selected = [
                row.sample
                for row, age in zip(samples, vector, strict=True)
                if bin_.contains(age)
            ]
            values.append(
                Fraction(
                    sum(row.numerator_count for row in selected),
                    sum(row.denominator_count for row in selected),
                )
            )
        fractions.add(tuple(values))
    result = assess_depth_ordered_extrema(samples, bins, core_id="core")
    for corner in result.corners:
        target = tuple(row.value for row in corner.independent_corner.targets)
        assert corner.attainable == (target in fractions)
        if corner.age_order is not None and corner.age_order.attainable:
            observed = {
                row.sample_id: row.native_age for row in corner.age_order.assignments
            }
            assert all(
                row.sample.younger_cal_bp
                <= observed[row.sample.sample_id]
                <= row.sample.older_cal_bp
                for row in samples
            )
        if not corner.independent_corner.attainable:
            assert corner.age_order is None and corner.independent_corner.refusals


@pytest.mark.parametrize(
    "parts",
    [
        (("1", "0", True),),
        (("0", "0", False),),
        (("NaN", "1", True),),
        (("0", "1", 1),),
    ],
)
def test_invalid_native_components_refuse(
    parts: tuple[tuple[str, str, bool], ...],
) -> None:
    with pytest.raises(ValueError):
        domain("sample", "0", *parts)


def test_duplicate_samples_overlapping_components_and_unknown_depth_refuse() -> None:
    row = domain("sample", "0", ("0", "1", True))
    with pytest.raises(ValueError, match="unique"):
        assess_age_order([row, row], core_id="core")
    with pytest.raises(ValueError, match="disjoint"):
        domain("sample", "0", ("0", "1", True), ("1", "2", True))
    with pytest.raises(ValueError, match="finite"):
        domain("sample", "NaN", ("0", "1", True))
    with pytest.raises(ValueError, match="identity"):
        assess_age_order([row], core_id="")
