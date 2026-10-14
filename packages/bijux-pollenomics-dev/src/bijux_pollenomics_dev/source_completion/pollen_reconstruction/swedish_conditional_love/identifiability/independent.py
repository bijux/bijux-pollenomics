"""Exact rational source-constant certificate independent of the affine helper."""

from __future__ import annotations

from fractions import Fraction
from typing import Any


def require(condition: object, reason: str) -> None:
    if not condition:
        raise ValueError("Independent identifiability oracle: " + reason)


def rational(value: Any) -> Fraction:
    return Fraction(str(value))


def review(inputs: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    """Use exact serialized constants, rather than a fitted response or optimizer."""
    native = inputs["three-conditional-love-cases.json"]
    p = list(map(rational, native["ppe"]))
    n = list(map(rational, native["raw_local_panel_counts"]))
    q = [v / sum(n) for v in n]
    U = [
        sum(
            (
                rational(count[i]) / (rational(k[i]) * p[i])
                for count, k in zip(
                    native["regional_training_counts"],
                    native["training_whole_factors"],
                    strict=True,
                )
            ),
            Fraction(),
        )
        for i in range(2)
    ]
    r = [v / sum(U) for v in U]
    a = [rational(native["local_factors"][i]) * p[i] for i in range(2)]
    c = [rational(native["regional_factors"][i]) * p[i] * r[i] for i in range(2)]
    A = sum(q[i] / a[i] for i in range(2))
    B = sum(c[i] / a[i] for i in range(2))
    u = [q[i] / (a[i] * A) for i in range(2)]
    d = [(q[i] * B / A - c[i]) / a[i] for i in range(2)]
    require(sum(u) == 1 and sum(d) == 0, "exact affine closure")
    bounds = []
    for i in range(2):
        if d[i] < 0:
            bounds.append(-u[i] / d[i])
        elif d[i] > 0:
            bounds.append((1 - u[i]) / d[i])
    upper = min(bounds) if bounds else None
    if upper is None:
        raise ValueError("Native source unexpectedly has an unbounded ratio domain")
    require(
        upper > Fraction(1, 2) and upper < 1,
        "native feasibility orientation",
    )
    errors: dict[str, dict[str, Any]] = {}

    def check(name: str, value: Any, expected: Fraction) -> None:
        error = abs(rational(value) - expected)
        scale = max(abs(expected), abs(rational(value)))
        bound = Fraction(2, 10**13)
        if scale > Fraction(1, 10**12):
            bound = min(bound, Fraction(1, 10**18) + Fraction(5, 10**10) * scale)
        require(error <= bound, name + " scalar differs")
        m = errors.setdefault(
            name,
            {
                "scalars": 0,
                "maximum_absolute_error": 0.0,
                "maximum_error_to_bound": 0.0,
            },
        )
        m["scalars"] += 1
        m["maximum_absolute_error"] = max(m["maximum_absolute_error"], float(error))
        m["maximum_error_to_bound"] = max(
            m["maximum_error_to_bound"], float(error / bound)
        )

    for key, values in [
        ("pollen", q),
        ("regional_cover", r),
        ("local_response", a),
        ("unit_background", c),
        ("intercept", u),
        ("slope", d),
    ]:
        for v, e in zip(actual[key], values, strict=True):
            check(key, v, e)
    check("upper_ratio", actual["nonnegative_ratio_domain"]["upper"], upper)
    exact_points = []
    for row in actual["points"]:
        ratio = rational(row["ratio"])
        T = (1 + ratio * B) / A
        # Solve the original closure substitution directly rather than evaluate
        # the production intercept/slope expansion.
        cover = [(T * q[i] - ratio * c[i]) / a[i] for i in range(2)]
        for v, e in zip(row["signed_cover"], cover, strict=True):
            check("point_cover", v, e)
        weights = [a[i] * cover[i] + ratio * c[i] for i in range(2)]
        total = sum(weights)
        predicted = [v / total for v in weights]
        require(predicted == q, "exact closed forward identity")
        for v, e in zip(row["closed_forward_pollen"], predicted, strict=True):
            check("forward_pollen", v, e)
        # Independent quotient derivatives on v_B and lambda, with v_P=1-v_B.
        jv = (a[0] * total - weights[0] * (a[0] - a[1])) / (total**2)
        jl = (c[0] * total - weights[0] * sum(c)) / (total**2)
        J = [[jv, jl], [-jv, -jl]]
        require(
            jv != 0
            and jv * d[0] + jl == 0
            and J[0][0] * J[1][1] - J[0][1] * J[1][0] == 0,
            "exact rank-one/null certificate",
        )
        for i in range(2):
            for j in range(2):
                check("jacobian", row["response_jacobian"][i][j], J[i][j])
        check("null_residual", row["null_direction_residual"], Fraction())
        exact_points.append(
            {
                "id": row["id"],
                "ratio_serialized": str(ratio),
                "feasible_at_serialized_binary64_ratio": all(
                    0 <= x <= 1 for x in cover
                ),
                "minimum_exact_cover": float(min(cover)),
            }
        )
    for original, row in zip(
        native["cases"], actual["original_case_comparisons"], strict=True
    ):
        ratio = rational(original["scenario"]["lambda"])
        T = (1 + ratio * B) / A
        cover = [(T * q[i] - ratio * c[i]) / a[i] for i in range(2)]
        require(
            row["ratio"] == float(ratio)
            and row["original_simplex_feasible"] == original["simplex_feasible"]
            and row["original_maintained_forward_status"]
            == original["maintained_forward"]["status"],
            "original signed/refusal population",
        )
        for v, e in zip(original["cover"], cover, strict=True):
            check("original_signed_cover", v, e)
        require(
            all(0 <= x <= 1 for x in cover) == original["simplex_feasible"],
            "ratio orientation changed",
        )
    eps = Fraction(1, 2**20)
    bracket = []
    for label, ratio in [
        ("inside", upper * (1 - eps)),
        ("endpoint", upper),
        ("outside", upper * (1 + eps)),
    ]:
        v = [u[i] + ratio * d[i] for i in range(2)]
        feasible = all(0 <= x <= 1 for x in v)
        require(feasible == (label != "outside"), "exact endpoint inequality")
        bracket.append(
            {
                "position": label,
                "feasible": feasible,
                "ratio_approximation": float(ratio),
                "minimum_cover_approximation": float(min(v)),
            }
        )
    return {
        "status": "passed",
        "arithmetic": "Exact rational algebra on serialized native source constants, not exact physical parameters",
        "comparisons": errors,
        "scalar_checks": sum(x["scalars"] for x in errors.values()),
        "exact_rank": 1,
        "exact_null_residual": "0",
        "exact_determinant": "0",
        "exact_nonnegative_ratio_domain": {
            "lower": "0",
            "lower_closed": True,
            "upper_numerator": str(upper.numerator),
            "upper_denominator": str(upper.denominator),
            "upper_approximation": float(upper),
            "upper_closed": True,
        },
        "positive_ratio_domain": {
            "lower": 0,
            "lower_closed": False,
            "upper": float(upper),
            "upper_closed": True,
            "empty": False,
        },
        "endpoint_inequalities": bracket,
        "point_classification": exact_points,
        "limitations": "A conditional deterministic feasible domain and structural certificate, not a likelihood fit, ratio posterior, confidence interval, physical accuracy or uncertainty coverage.",
    }
