"""Analytic boundary-simplex examples for the independent Decimal reference."""

from __future__ import annotations

import math

import pytest

from bijux_pollenomics_dev.lra_validation.spatial_reference.hellinger import (
    predict,
)


def test_single_and_identical_training_rows_keep_the_literal_simplex() -> None:
    row = [0.0, 0.25, 0.75]
    assert predict([row], [99.0], 20.0) == {"fractions": row, "weights": [1.0]}
    result = predict([row, row, row], [0.0, 3.0, 10.0], 20.0)
    assert result["fractions"] == row
    assert sum(result["weights"]) == pytest.approx(1.0)


def test_disjoint_supports_give_squared_gaussian_weights_not_arithmetic_mean() -> None:
    # A distance sqrt(2 log 3) at unit scale yields weights 3/4 and 1/4.
    result = predict([[1.0, 0.0], [0.0, 1.0]], [0.0, math.sqrt(2 * math.log(3))], 1.0)
    assert result["weights"] == pytest.approx([0.75, 0.25], abs=1e-15)
    assert result["fractions"] == pytest.approx([0.9, 0.1], abs=1e-15)


def test_shared_taxon_can_exceed_all_training_values_without_leaving_simplex() -> None:
    result = predict([[0.5, 0.5, 0.0], [0.5, 0.0, 0.5]], [10.0, 10.0], 100.0)
    assert result["fractions"] == pytest.approx([2 / 3, 1 / 6, 1 / 6], abs=1e-15)
    assert result["weights"] == [0.5, 0.5]


def test_objective_gap_equals_positive_root_sphere_distance() -> None:
    rows = [[0.81, 0.09, 0.1], [0.0, 0.5, 0.5], [0.2, 0.3, 0.5]]
    result = predict(rows, [1.0, 7.0, 12.0], 20.0)
    a = [
        math.fsum(
            w * math.sqrt(row[t])
            for w, row in zip(result["weights"], rows, strict=True)
        )
        for t in range(3)
    ]
    norm = math.sqrt(math.fsum(value * value for value in a))

    def objective(q: list[float]) -> float:
        return math.fsum(
            w
            * math.fsum(
                (math.sqrt(p) - math.sqrt(v)) ** 2 for p, v in zip(row, q, strict=True)
            )
            / 2
            for w, row in zip(result["weights"], rows, strict=True)
        )

    for competitor in ([1.0, 0.0, 0.0], [0.25, 0.25, 0.5], [0.2, 0.3, 0.5]):
        gap = objective(competitor) - objective(result["fractions"])
        square = (
            norm
            * math.fsum((math.sqrt(competitor[t]) - a[t] / norm) ** 2 for t in range(3))
            / 2
        )
        assert gap == pytest.approx(square, abs=1e-15)
        assert gap >= 0


def test_taxon_training_and_group_label_permutations_preserve_associated_weights() -> (
    None
):
    rows, distances = (
        [[0.0, 0.25, 0.75], [0.5, 0.5, 0.0], [0.1, 0.6, 0.3]],
        [2.0, 8.0, 10.0],
    )
    original = predict(rows, distances, 20.0)
    training_order, taxon_order = [2, 0, 1], [1, 2, 0]
    permuted = predict(
        [[rows[i][j] for j in taxon_order] for i in training_order],
        [distances[i] for i in training_order],
        20.0,
    )
    assert permuted["fractions"] == pytest.approx(
        [original["fractions"][j] for j in taxon_order], abs=1e-15
    )
    assert permuted["weights"] == pytest.approx(
        [original["weights"][i] for i in training_order], abs=1e-15
    )


def test_entirely_absent_taxon_is_exactly_zero_without_a_pseudocount() -> None:
    result = predict([[0.2, 0.8, 0.0], [0.6, 0.4, 0.0]], [1.0, 2.0], 20.0)
    assert result["fractions"][2] == 0.0
    assert min(result["fractions"][:2]) > 0


def test_remote_equal_distance_weights_do_not_vanish_together() -> None:
    result = predict([[1.0, 0.0], [0.0, 1.0]], [1e150, 1e150], 1.0)
    assert result == {"fractions": [0.5, 0.5], "weights": [0.5, 0.5]}


def test_admitted_near_closed_rows_are_not_implicitly_renormalized() -> None:
    excess = 5e-10
    rows = [[0.5, 0.5 + excess], [0.5, 0.5]]
    result = predict(rows, [0.0, 0.0], 20.0)
    first_root = math.sqrt(0.5)
    second_root = (math.sqrt(0.5 + excess) + math.sqrt(0.5)) / 2
    assert result["fractions"] == pytest.approx(
        [
            first_root**2 / (first_root**2 + second_root**2),
            second_root**2 / (first_root**2 + second_root**2),
        ],
        abs=1e-15,
    )


@pytest.mark.parametrize(
    "rows,distances,scale",
    [
        ([], [], 20.0),
        ([[0.5, 0.5]], [], 20.0),
        ([[], []], [0.0, 1.0], 20.0),
        ([[0.5, 0.5], [1.0]], [0.0, 1.0], 20.0),
        ([[0.0, 0.0]], [0.0], 20.0),
        ([[-1e-16, 1.0]], [0.0], 20.0),
        ([[0.5, 0.5 + 2e-9]], [0.0], 20.0),
        ([[float("nan"), 1.0]], [0.0], 20.0),
        ([[True, 0.0]], [0.0], 20.0),
        ([[1.0, 0.0]], [-1.0], 20.0),
        ([[1.0, 0.0]], [float("inf")], 20.0),
        ([[1.0, 0.0]], [0.0], 0.0),
        ([[1.0, 0.0]], [0.0], -1.0),
        ([[1.0, 0.0]], [0.0], float("nan")),
    ],
)
def test_invalid_numeric_domain_and_support_are_refused(
    rows: list[list[float]], distances: list[float], scale: float
) -> None:
    with pytest.raises(ValueError):
        predict(rows, distances, scale)


def test_positive_relative_weight_underflow_is_a_refusal_not_a_nearest_fallback() -> (
    None
):
    with pytest.raises(ValueError, match="relative weight underflow"):
        predict([[1.0, 0.0], [0.0, 1.0]], [0.0, 1000.0], 1.0)


def test_normalization_cannot_erase_a_positive_relative_weight() -> None:
    with pytest.raises(ValueError, match="normalized weight underflow"):
        predict([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]], [0.0, 0.0, math.sqrt(1490)], 1.0)


def test_supported_output_underflow_is_distinct_from_exact_absence() -> None:
    # exp(-400) remains representable; its squared contribution does not.
    with pytest.raises(ValueError, match="output support underflow"):
        predict([[1.0, 0.0], [0.0, 1.0]], [0.0, math.sqrt(800)], 1.0)
