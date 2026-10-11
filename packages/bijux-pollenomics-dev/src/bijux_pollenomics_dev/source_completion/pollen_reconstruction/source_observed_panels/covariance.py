"""Independently verify retained two-taxon conditional covariance cells."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal, localcontext
import math
from typing import TypedDict


class ConditionalCovariance(TypedDict):
    """Describe the saved two-taxon numerical result checked by this boundary."""

    deposition: list[list[float]]
    conditional_panel_cover: list[float]
    conditional_standard_error: list[float]
    counting_covariance: list[list[float]]
    shared_ppe_covariance: list[list[float]]
    total_conditional_covariance: list[list[float]]
    direct_observed_panel_pollen_fraction: list[float]


def finite(value: object) -> float:
    """Require a finite native numerical cell before comparing retained results."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("scientific numerical cells must be finite numeric values")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("scientific numerical cells must be finite")
    return value


def scalar_covariance(
    counts: Sequence[Sequence[float]],
    deposition: list[list[float]],
    ppe: list[float],
    sd: list[float],
) -> tuple[float, float, float]:
    """Use scalar derivatives with shared PPE and fixed multinomial site counts."""
    if not counts or len(counts) != len(deposition):
        raise ValueError("two-taxon site/parameter population differs")
    if len(ppe) != 2 or len(sd) != 2:
        raise ValueError("two-taxon parameter population differs")
    for count_row in counts:
        if (
            len(count_row) != 2
            or any(type(n) is not int or n < 0 for n in count_row)
            or sum(count_row) == 0
        ):
            raise ValueError(
                "observed panel counts must be finite nonnegative integers with positive total"
            )
    if any(len(row) != 2 for row in deposition):
        raise ValueError("two-taxon deposition population differs")
    if (
        any(finite(v) <= 0 for row in deposition for v in row)
        or any(finite(v) <= 0 for v in ppe)
        or any(finite(v) < 0 for v in sd)
    ):
        raise ValueError("deposition/PPE/SD domain differs")
    with localcontext() as context:
        context.prec = 50

        def dec(value: float) -> Decimal:
            return Decimal(str(value))

        p = list(map(dec, ppe))
        k = [[dec(v) for v in row] for row in deposition]
        n = [[Decimal(v) for v in row] for row in counts]
        a = sum(
            (row[0] / (factor[0] * p[0]) for row, factor in zip(n, k, strict=True)),
            Decimal(0),
        )
        b = sum(
            (row[1] / (factor[1] * p[1]) for row, factor in zip(n, k, strict=True)),
            Decimal(0),
        )
        total = a + b
        q = a / total
        counting = Decimal(0)
        for row, factor in zip(n, k, strict=True):
            da = b / (total**2 * factor[0] * p[0])
            db = -a / (total**2 * factor[1] * p[1])
            counting += row[0] * row[1] / sum(row) * (da - db) ** 2
        productivity = (
            q**2
            * (1 - q) ** 2
            * sum(
                ((dec(s) / mean) ** 2 for s, mean in zip(sd, p, strict=True)),
                Decimal(0),
            )
        )
        return float(q), float(counting), float(productivity)


def verify_result(
    result: ConditionalCovariance,
    counts: Sequence[Sequence[float]],
    ppe: list[float],
    sd: list[float],
) -> dict[str, float]:
    """Check every retained cover, SE and within-result covariance cell."""
    q, counting, productivity = scalar_covariance(counts, result["deposition"], ppe, sd)
    errors = {}
    expected_cover = [q, 1 - q]
    if (
        len(result["conditional_panel_cover"]) != 2
        or len(result["conditional_standard_error"]) != 2
    ):
        raise ValueError("retained cover/SE population differs")
    errors["cover"] = max(
        abs(finite(actual) - expected)
        for actual, expected in zip(
            result["conditional_panel_cover"], expected_cover, strict=True
        )
    )
    matrices = {
        "counting_covariance": result["counting_covariance"],
        "shared_ppe_covariance": result["shared_ppe_covariance"],
        "total_conditional_covariance": result["total_conditional_covariance"],
    }
    for name, variance in [
        ("counting_covariance", counting),
        ("shared_ppe_covariance", productivity),
        ("total_conditional_covariance", counting + productivity),
    ]:
        matrix = matrices[name]
        if len(matrix) != 2 or any(len(row) != 2 for row in matrix):
            raise ValueError("retained two-taxon covariance population differs")
        errors[name] = max(
            abs(finite(matrix[i][j]) - variance * (1 if i == j else -1))
            for i in range(2)
            for j in range(2)
        )
    errors["standard_error"] = max(
        abs(finite(v) - math.sqrt(counting + productivity))
        for v in result["conditional_standard_error"]
    )
    total_counts = sum(sum(row) for row in counts)
    expected_pollen = [sum(row[i] for row in counts) / total_counts for i in range(2)]
    if len(result["direct_observed_panel_pollen_fraction"]) != 2:
        raise ValueError("retained observed pollen fraction population differs")
    errors["direct_panel_pollen_fraction"] = max(
        abs(finite(v) - e)
        for v, e in zip(
            result["direct_observed_panel_pollen_fraction"],
            expected_pollen,
            strict=True,
        )
    )
    if any(v > 1e-12 for v in errors.values()):
        raise ValueError(
            "retained conditional covariance/cover differs from scalar equation"
        )
    return errors
