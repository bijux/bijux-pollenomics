"""Observe conditional mean precision through masked residual batch influences."""

from __future__ import annotations

from collections.abc import Sequence
from itertools import combinations
import math
from typing import Any

Vector = tuple[float, ...]
Matrix = tuple[Vector, ...]
Rows = tuple[Vector | None, ...]
BINS = (3, 4, 5, 9)
TAXA = ("Betula", "Cyperaceae", "Juniperus communis", "Pinus sylvestris", "Poaceae")
TAXON_IDS = (29, 74, 4416, 1287, 417)


def scalar_axes() -> list[dict[str, Any]]:
    return [
        {"kind": "component", "window_id": b, "taxon": name, "native_taxon_id": taxon}
        for b in BINS
        for name, taxon in zip(TAXA, TAXON_IDS, strict=True)
    ] + [
        {
            "kind": "contrast",
            "younger_window_id": younger,
            "older_window_id": older,
            "taxon": name,
            "native_taxon_id": taxon,
        }
        for younger, older in combinations(BINS, 2)
        for name, taxon in zip(TAXA, TAXON_IDS, strict=True)
    ]


def conditional_mean(rows: Rows) -> tuple[float, Vector]:
    complete = [row for row in rows if row is not None]
    if not rows or not complete:
        raise ValueError("No complete conditional mean is available")
    dimension = len(complete[0])
    if dimension < 1 or any(
        len(row) != dimension or not all(math.isfinite(v) for v in row)
        for row in complete
    ):
        raise ValueError("Complete influence row dimension or finite domain differs")
    return len(complete) / len(rows), tuple(
        math.fsum(row[j] for row in complete) / len(complete) for j in range(dimension)
    )


def sample_crossproducts(vectors: Sequence[Vector], factor: float) -> Matrix:
    if len(vectors) < 2 or not math.isfinite(factor) or factor <= 0:
        raise ValueError("Batch covariance needs positive scale and multiple batches")
    d = len(vectors[0])
    if any(len(v) != d or not all(math.isfinite(x) for x in v) for v in vectors):
        raise ValueError("Batch influence axes differ")
    center = tuple(math.fsum(v[j] for v in vectors) / len(vectors) for j in range(d))
    result = tuple(
        tuple(
            factor * math.fsum((v[i] - center[i]) * (v[j] - center[j]) for v in vectors)
            for j in range(d)
        )
        for i in range(d)
    )
    if any(not math.isfinite(x) for row in result for x in row):
        raise ValueError("Nonfinite residual batch crossproducts")
    if any(
        result[j][j] == 0 and any(v[j] != center[j] for v in vectors) for j in range(d)
    ):
        raise ValueError(
            "Positive residual batch variation lost to numerical underflow"
        )
    return result


def residual_batches(
    rows: Rows, mean: Vector, probability: float, size: int
) -> list[Vector]:
    """Retain missing states at their native positions, with zero numerator only."""
    if (
        type(size) is not int
        or size < 1
        or len(rows) % size
        or len(rows) // size < 2
        or not 0 < probability <= 1
    ):
        raise ValueError("Fixed complete native batch partition or probability differs")
    conditional_mean(rows)
    if not all(math.isfinite(v) for v in mean) or any(
        row is not None and len(row) != len(mean) for row in rows
    ):
        raise ValueError("Conditional center and native influence axes differ")
    return [
        tuple(
            math.fsum(
                (row[j] - mean[j]) / probability
                for row in rows[start : start + size]
                if row is not None
            )
            / size
            for j in range(len(mean))
        )
        for start in range(0, len(rows), size)
    ]


def mean_covariance(rows: Rows, mean: Vector, probability: float, size: int) -> Matrix:
    batches = residual_batches(rows, mean, probability, size)
    return sample_crossproducts(batches, size / ((len(batches) - 1) * len(rows)))


def indicator_variance(rows: Rows, size: int) -> tuple[float, str]:
    conditional_mean(rows)
    if type(size) is not int or size < 1 or len(rows) % size or len(rows) // size < 2:
        raise ValueError("Indicator native batch partition differs")
    batches = [
        (sum(row is not None for row in rows[start : start + size]) / size,)
        for start in range(0, len(rows), size)
    ]
    variance = sample_crossproducts(batches, size / ((len(batches) - 1) * len(rows)))[
        0
    ][0]
    constant = all(row is not None for row in rows)
    return variance, (
        "empirically_constant_indicator_insufficient_transitions"
        if constant
        else "observed_indicator_variation_no_mixing_guarantee"
    )


def pooled_covariance(
    chains: Sequence[Rows], size: int
) -> tuple[float, Vector, Matrix]:
    """Center the common-target influence batches within each independent chain."""
    if len(chains) < 2:
        raise ValueError("Independent pooled mean needs multiple chains")
    all_rows = tuple(row for chain in chains for row in chain)
    probability, mean = conditional_mean(all_rows)
    n = len(all_rows)
    covariances = [mean_covariance(chain, mean, probability, size) for chain in chains]
    matrix = tuple(
        tuple(
            math.fsum(
                len(chain) ** 2 * covariance[i][j] / n**2
                for chain, covariance in zip(chains, covariances, strict=True)
            )
            for j in range(len(mean))
        )
        for i in range(len(mean))
    )
    return probability, mean, matrix


def scalar_projection(mean: Vector, covariance: Matrix) -> list[tuple[float, float]]:
    if (
        len(mean) != 20
        or len(covariance) != 20
        or any(len(row) != 20 for row in covariance)
    ):
        raise ValueError("Twenty output components required for temporal contrasts")
    result = [(v, covariance[j][j]) for j, v in enumerate(mean)]
    for younger, older in combinations(range(4), 2):
        for t in range(5):
            i, j = 5 * younger + t, 5 * older + t
            result.append(
                (
                    mean[j] - mean[i],
                    math.fsum(
                        (covariance[i][i], covariance[j][j], -2 * covariance[i][j])
                    ),
                )
            )
    return result


def variance_display(value: float) -> tuple[str, float | None]:
    if not math.isfinite(value) or value < 0:
        return "refused_signed_or_nonfinite_variance", None
    if value == 0:
        return "empirically_zero_batch_variation_not_zero_target_error", 0.0
    return "batch_means_estimate_under_declared_assumptions", math.sqrt(value)


def compare_numbers(
    actual: Any, expected: Any, *, absolute: float = 1e-18, relative: float = 1e-10
) -> float:
    """Require finite numeric output and preserve negative values without repair."""
    if type(actual) not in (float, int) or type(expected) not in (float, int):
        raise ValueError("Finite numeric observation required")
    if not math.isfinite(actual) or not math.isfinite(expected):
        raise ValueError("Nonfinite mean precision observation")
    gap = abs(actual - expected)
    if gap > absolute + relative * abs(expected):
        raise ValueError("Independent masked residual correspondence differs")
    return float(gap)
