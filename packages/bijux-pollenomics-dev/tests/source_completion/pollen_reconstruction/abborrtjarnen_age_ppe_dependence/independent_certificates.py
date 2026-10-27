"""Exact finite-matrix checks independent of the covariance candidate search."""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations
import math
from typing import Any

Matrix = tuple[tuple[Fraction, ...], ...]


def rational(value: Any) -> Fraction:
    """Preserve binary64 Q values and exact rational witness tokens separately."""
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Fraction)):
        raise ValueError("Invalid finite rational token")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Invalid finite rational token")
    return Fraction(value)


def matrix(value: Any, size: int = 4) -> Matrix:
    if len(value) != size or any(len(row) != size for row in value):
        raise ValueError("Exact matrix axes differ")
    result = tuple(tuple(rational(x) for x in row) for row in value)
    if any(result[i][j] != result[j][i] for i in range(size) for j in range(size)):
        raise ValueError("Exact matrix is not symmetric")
    return result


def determinant(value: Matrix) -> Fraction:
    if not value:
        return Fraction(1)
    return sum(
        (
            (-1) ** j
            * value[0][j]
            * determinant(
                tuple(
                    tuple(row[k] for k in range(len(value)) if k != j)
                    for row in value[1:]
                )
            )
            for j in range(len(value))
        ),
        Fraction(0),
    )


def principal_minors(value: Matrix) -> dict[tuple[int, ...], Fraction]:
    return {
        indices: determinant(
            tuple(tuple(value[i][j] for j in indices) for i in indices)
        )
        for n in range(1, len(value) + 1)
        for indices in combinations(range(len(value)), n)
    }


def require_psd(value: Matrix) -> dict[tuple[int, ...], Fraction]:
    minors = principal_minors(value)
    if any(x < 0 for x in minors.values()):
        raise ValueError("Exact nonnegative principal-minor certificate failed")
    return minors


def gram(rows: Any) -> Matrix:
    if (
        len(rows) != 4
        or not 1 <= len(rows[0]) <= 4
        or any(len(row) != len(rows[0]) for row in rows)
    ):
        raise ValueError("Rational Gram axes differ")
    vectors = [tuple(rational(x) for x in row) for row in rows]
    if any(sum((x * x for x in row), Fraction(0)) != 1 for row in vectors):
        raise ValueError("Rational Gram vector is not exactly unit length")
    result = tuple(
        tuple(
            sum((a * b for a, b in zip(u, v, strict=True)), Fraction(0))
            for v in vectors
        )
        for u in vectors
    )
    require_psd(result)
    return result


def objective(q: Matrix, r: Matrix) -> Fraction:
    return sum((q[i][j] * r[j][i] for i in range(4) for j in range(4)), Fraction(0))


def certificate(q: Matrix, rows: Any, diagonal: Any, sign: int) -> dict[str, Any]:
    """Certify max(sign*tr(QR)); the minus problem supplies the lower bound."""
    if sign not in (-1, 1) or len(diagonal) != 4:
        raise ValueError("Dual sign or axes differ")
    r = gram(rows)
    y = tuple(rational(x) for x in diagonal)
    slack = tuple(
        tuple((y[i] if i == j else Fraction(0)) - sign * q[i][j] for j in range(4))
        for i in range(4)
    )
    minors = require_psd(slack)
    primal = objective(q, r)
    dual = sum(y, Fraction(0))
    gap = dual - sign * primal
    if gap < 0:
        raise ValueError("Exact primal/dual ordering failed")
    trace = sum((q[i][i] for i in range(4)), Fraction(0))
    if trace < 0 or (trace == 0 and any(any(row) for row in q)):
        raise ValueError("Finite Q trace cannot normalize certificate gaps")
    normalized = gap / trace if trace else Fraction(0)
    return {
        "primal": primal,
        "dual": dual,
        "outer": sign * dual,
        "gap": gap,
        "normalized_gap": normalized,
        "minors": minors,
        "tight": normalized <= Fraction(1, 10**6),
    }


def check_record(q: Matrix, record: dict[str, Any], label: str) -> dict[str, Any]:
    """Validate saved exact quantities without accepting numerical PSD tolerances."""
    sign = -1 if label == "minimum" else 1
    diagonal = [rational(v) * sign for v in record["dual_diagonal_exact"]]
    checked = certificate(q, record["gram_rows_exact"], diagonal, sign)
    expected = {
        "attained_value_exact": checked["primal"],
        "outer_endpoint_exact": checked["outer"],
        "gap_exact": checked["gap"],
        "normalized_gap_exact": checked["normalized_gap"],
    }
    if record["endpoint_kind"] != label or any(
        rational(record[k]) != value for k, value in expected.items()
    ):
        raise ValueError("Saved exact endpoint/objective/gap differs")
    masks = {
        sum(1 << i for i in indices): value
        for indices, value in checked["minors"].items()
    }
    if [rational(v) for v in record["dual_principal_minors_exact"]] != [
        masks[i] for i in range(1, 16)
    ]:
        raise ValueError("Saved fifteen exact principal minors differ")
    status = (
        "tight_global_enclosure" if checked["tight"] else "certified_loose_enclosure"
    )
    if record["status"] != status:
        raise ValueError("Saved tight/loose certificate status differs")
    return checked


def check_total(qbounds: dict[str, dict[str, Any]], scalar: dict[str, Any]) -> None:
    """Signed endpoints and square-root display refusals have separate domains."""
    fixed = rational(scalar["fixed_age_variance"]) + rational(
        scalar["fixed_count_variance"]
    )
    lower = fixed + qbounds["minimum"]["outer"]
    upper = fixed + qbounds["maximum"]["outer"]
    saved = scalar["total_variance_outer_interval"]
    if (
        lower > upper
        or rational(saved["lower_exact"]) != lower
        or rational(saved["upper_exact"]) != upper
    ):
        raise ValueError("Saved exact total variance endpoints differ")
    display = scalar["standard_deviation_display"]
    expected: tuple[float, float] | None = None
    status = "refused_signed_outer_bound"
    if lower >= 0:
        try:
            lo, hi = float(lower), float(upper)
            if (
                not all(math.isfinite(v) for v in (lo, hi))
                or (lower > 0 and lo == 0)
                or (upper > 0 and hi == 0)
            ):
                raise ValueError("Outside finite display domain")
            expected = (math.sqrt(lo), math.sqrt(hi))
            status = "approximate_square_root_enclosure"
        except (OverflowError, ValueError):
            status = "refused_numeric_display_domain"
    if display["status"] != status or (display["lower"], display["upper"]) != (
        expected if expected is not None else (None, None)
    ):
        raise ValueError("Signed/domain square-root display differs")
