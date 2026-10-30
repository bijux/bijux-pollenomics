"""Certify finite four-parameter covariance bounds independently of search status."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import permutations, product
import math
from typing import Any

import numpy as np
from scipy.optimize import minimize

from ..abborrtjarnen_ppe_dependence.sources import require

Matrix = tuple[tuple[Fraction, ...], ...]


def rational(value: Fraction) -> str:
    """Encode a fraction using its exact numerator and denominator."""
    return f"{value.numerator}/{value.denominator}"


def principal_minors(matrix: Matrix) -> tuple[Fraction, ...]:
    """Check all fifteen principal minors, including nonleading submatrices."""
    require(
        len(matrix) == 4 and all(len(row) == 4 for row in matrix),
        "Four-by-four exact matrix required",
    )
    require(
        all(matrix[i][j] == matrix[j][i] for i in range(4) for j in range(4)),
        "Exact matrix is nonsymmetric",
    )
    minors = []
    for mask in range(1, 16):
        indices = [i for i in range(4) if mask & (1 << i)]
        determinant = Fraction()
        for order in permutations(range(len(indices))):
            inversions = sum(
                order[i] > order[j]
                for i in range(len(order))
                for j in range(i + 1, len(order))
            )
            term = Fraction(-1 if inversions % 2 else 1)
            for i, j in enumerate(order):
                term *= matrix[indices[i]][indices[j]]
            determinant += term
        minors.append(determinant)
    return tuple(minors)


def gram(rows: Matrix) -> Matrix:
    """Build a rational Gram matrix from four exact unit rows."""
    require(
        len(rows) == 4
        and bool(rows[0])
        and all(len(row) == len(rows[0]) for row in rows),
        "Four unit Gram rows required",
    )
    require(
        all(sum((v * v for v in row), Fraction()) == 1 for row in rows),
        "Gram row is not exactly unit length",
    )
    return tuple(
        tuple(sum((a * b for a, b in zip(x, y, strict=True)), Fraction()) for y in rows)
        for x in rows
    )


def circle_rows(angles: np.ndarray, bits: int) -> Matrix:
    """A bounded stereographic chart makes every serialized row exactly unit."""
    require(
        angles.shape == (3,) and bool(np.isfinite(angles).all()),
        "Finite three-angle candidate required",
    )
    rows = [(Fraction(1), Fraction())]
    denominator = 1 << bits
    for angle in angles:
        x, y = math.cos(float(angle)), math.sin(float(angle))
        sign = -1 if x < 0 else 1
        t = Fraction(round((sign * y / (1 + sign * x)) * denominator), denominator)
        rows.append((sign * (1 - t * t) / (1 + t * t), sign * 2 * t / (1 + t * t)))
    return tuple(rows)


def trace_product(left: Matrix, right: Matrix) -> Fraction:
    """Compute the exact trace of the product of two four-axis matrices."""
    return sum(
        (left[i][j] * right[j][i] for i in range(4) for j in range(4)), Fraction()
    )


@dataclass(frozen=True)
class Candidate:
    """Store a candidate identifier, rational Gram rows and objective value."""

    identifier: str
    rows: Matrix
    objective: Fraction


def candidates(
    q: Matrix, sign: int, trace: Fraction, configuration: dict[str, Any]
) -> tuple[list[Candidate], list[dict[str, Any]]]:
    """Numerical angle optimization proposes witnesses; it does not prove bounds."""
    signed = tuple(tuple(sign * v for v in row) for row in q)
    identity = tuple(tuple(Fraction(int(i == j)) for j in range(4)) for i in range(4))
    result = [Candidate("identity", identity, trace_product(signed, gram(identity)))]
    for index, signs in enumerate(product((1, -1), repeat=3)):
        rows: Matrix = tuple((Fraction(v),) for v in (1, *signs))
        result.append(
            Candidate(f"sign_{index}", rows, trace_product(signed, gram(rows)))
        )
    if not any(v for row in q for v in row):
        return result[:1], []
    normalized = None
    try:
        normalized = np.array([[float(v / trace) for v in row] for row in signed])
        if not np.isfinite(normalized).all():
            normalized = None
    except (OverflowError, ValueError):
        pass
    attempts = []
    for k in range(1, configuration["starts"] + 1):
        angles = np.array(
            [
                2
                * math.pi
                * ((k * m) % configuration["angle_modulus"])
                / configuration["angle_modulus"]
                for m in configuration["angle_multipliers"]
            ]
        )
        record: dict[str, Any] = {
            "start_id": k,
            "initial_angles": angles.tolist(),
            "candidate_admitted": False,
        }
        if normalized is None:
            attempts.append(
                {
                    **record,
                    "status": "refused_normalization_domain",
                    "message": "Finite normalized search matrix unavailable",
                }
            )
            continue

        def objective(theta: np.ndarray) -> tuple[float, np.ndarray]:
            vectors = np.vstack(
                ([1.0, 0.0], np.column_stack((np.cos(theta), np.sin(theta))))
            )
            transformed = normalized @ vectors
            derivative = np.column_stack((-np.sin(theta), np.cos(theta)))
            return -float(np.sum(vectors * transformed)), -2 * np.sum(
                derivative * transformed[1:], axis=1
            )

        try:
            fitted = minimize(
                objective,
                angles,
                method="SLSQP",
                jac=True,
                options={
                    "maxiter": configuration["maxiter"],
                    "ftol": configuration["ftol"],
                    "disp": False,
                },
            )
            record.update(
                status=int(fitted.status),
                success=bool(fitted.success),
                message=str(fitted.message),
                iterations=int(fitted.nit),
                function_evaluations=int(fitted.nfev),
            )
            if np.isfinite(fitted.x).all():
                rows = circle_rows(fitted.x, configuration["circle_dyadic_bits"])
                candidate = Candidate(
                    f"angle_{k}", rows, trace_product(signed, gram(rows))
                )
                result.append(candidate)
                record.update(
                    candidate_admitted=True,
                    candidate_id=candidate.identifier,
                    candidate_objective_exact=rational(candidate.objective),
                    final_angles=fitted.x.tolist(),
                )
            else:
                record["candidate_refusal"] = "nonfinite_final_angles"
        except (ValueError, RuntimeError, FloatingPointError) as error:
            record.update(
                status="refused_search_exception",
                message=f"{type(error).__name__}: {error}",
            )
        attempts.append(record)
    return result, attempts


def dual_certificate(
    q: Matrix, sign: int, witness: Matrix, trace: Fraction, exponents: list[int]
) -> dict[str, Any]:
    """Exact raw-Q PSD slacks establish weak-duality endpoints, not local optimality."""
    signed = tuple(tuple(sign * value for value in row) for row in q)
    base = tuple(
        sum((signed[i][j] * witness[i][j] for j in range(4)), Fraction())
        for i in range(4)
    )

    def check(diagonal: tuple[Fraction, ...]) -> tuple[Fraction, ...]:
        return principal_minors(
            tuple(
                tuple(
                    (diagonal[i] if i == j else Fraction()) - signed[i][j]
                    for j in range(4)
                )
                for i in range(4)
            )
        )

    gershgorin = tuple(
        signed[i][i] + sum((abs(signed[i][j]) for j in range(4) if i != j), Fraction())
        for i in range(4)
    )
    fallback = check(gershgorin)
    require(
        all(v >= 0 for v in fallback), "Exact Gershgorin dual failed PSD certification"
    )
    diagonal, minors, source, exponent = gershgorin, fallback, "gershgorin", None
    checks = 0
    for power in [None, *exponents]:
        padding = Fraction() if power is None else trace * Fraction(2) ** power
        proposed = tuple(v + padding for v in base)
        proposed_minors = check(proposed)
        checks += 1
        if all(v >= 0 for v in proposed_minors):
            if sum(proposed) <= sum(diagonal):
                diagonal, minors, source, exponent = (
                    proposed,
                    proposed_minors,
                    "candidate_stationarity_padding",
                    power,
                )
            break
    return {
        "diagonal": diagonal,
        "minors": minors,
        "source": source,
        "padding_exponent": exponent,
        "padding_checks": checks,
    }


def bounds(matrix: np.ndarray, configuration: dict[str, Any]) -> dict[str, Any]:
    """Separate attained values from certified outer endpoints and exact gaps."""
    require(
        matrix.shape == (4, 4) and bool(np.isfinite(matrix).all()),
        "Finite four-by-four Q required",
    )
    require(
        np.array_equal(matrix, matrix.T),
        "Frozen Q is nonsymmetric; projection is forbidden",
    )
    q = tuple(tuple(Fraction.from_float(float(v)) for v in row) for row in matrix)
    trace = sum((q[i][i] for i in range(4)), Fraction())
    require(
        trace > 0 or not any(v for row in q for v in row),
        "Nonzero Q has nonpositive trace",
    )
    endpoints = {}
    for label, sign in (("minimum", -1), ("maximum", 1)):
        options, attempts = candidates(q, sign, trace, configuration)
        best = max(options, key=lambda candidate: candidate.objective)
        witness = gram(best.rows)
        certified = dual_certificate(
            q, sign, witness, trace, configuration["padding_exponents"]
        )
        attained = trace_product(q, witness)
        outer = sign * sum(certified["diagonal"], Fraction())
        gap = sign * (outer - attained)
        require(gap >= 0, "Exact primal/dual gap is negative")
        normalized_gap = gap / trace if trace else Fraction()
        endpoints[label] = {
            "endpoint_kind": label,
            "candidate_id": best.identifier,
            "gram_rows_exact": [[rational(v) for v in row] for row in best.rows],
            "attained_value_exact": rational(attained),
            "dual_diagonal_exact": [rational(sign * v) for v in certified["diagonal"]],
            "dual_principal_minors_exact": [rational(v) for v in certified["minors"]],
            "outer_endpoint_exact": rational(outer),
            "gap_exact": rational(gap),
            "normalized_gap_exact": rational(normalized_gap),
            "status": "tight_global_enclosure"
            if normalized_gap <= Fraction(configuration["normalized_gap_threshold"])
            else "certified_loose_enclosure",
            "dual_source": certified["source"],
            "padding_exponent": certified["padding_exponent"],
            "padding_checks": certified["padding_checks"],
            "search_attempts": attempts,
            "candidate_count": len(options),
        }
    require(
        Fraction(endpoints["minimum"]["outer_endpoint_exact"])
        <= Fraction(endpoints["maximum"]["outer_endpoint_exact"]),
        "Exact covariance endpoints are unordered",
    )
    q_minors = principal_minors(q)
    return {
        "normalization_trace_exact": rational(trace),
        "Q_principal_minors_exact": [rational(v) for v in q_minors],
        "finite_Q_exact_psd": all(v >= 0 for v in q_minors),
        **endpoints,
        "status": "tight_global_enclosure"
        if all(e["status"] == "tight_global_enclosure" for e in endpoints.values())
        else "certified_loose_enclosure",
    }


def total_variance(bound: dict[str, Any], age: float, count: float) -> dict[str, Any]:
    """Keep signed outer bounds; unsupported square roots remain explicit refusals."""
    require(
        math.isfinite(age) and math.isfinite(count),
        "Fixed age/count variance is nonfinite",
    )
    fixed = Fraction.from_float(float(age)) + Fraction.from_float(float(count))
    lower = fixed + Fraction(bound["minimum"]["outer_endpoint_exact"])
    upper = fixed + Fraction(bound["maximum"]["outer_endpoint_exact"])
    require(lower <= upper, "Exact total variance endpoints are unordered")
    display: dict[str, Any] = {
        "status": "refused_signed_outer_bound",
        "lower": None,
        "upper": None,
        "precision_posture": "Exact nonnegative ordered endpoints permit approximate binary64 square-root displays only; no directed-rounding or field-coverage claim.",
    }
    if lower >= 0:
        try:
            lo, hi = float(lower), float(upper)
            if (
                not all(math.isfinite(v) for v in (lo, hi))
                or (lower > 0 and lo == 0)
                or (upper > 0 and hi == 0)
            ):
                raise ValueError("Positive endpoint underflow or nonfinite display")
            display.update(
                status="approximate_square_root_enclosure",
                lower=math.sqrt(lo),
                upper=math.sqrt(hi),
            )
        except (OverflowError, ValueError):
            display["status"] = "refused_numeric_display_domain"
    return {
        "total_variance_outer_interval": {
            "lower_exact": rational(lower),
            "upper_exact": rational(upper),
        },
        "standard_deviation_display": display,
    }
