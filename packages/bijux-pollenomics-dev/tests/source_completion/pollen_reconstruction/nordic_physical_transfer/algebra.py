"""Independent decimal point-transfer and compositional loss equations."""

from __future__ import annotations

from decimal import Decimal, localcontext
from typing import Any

PRECISION = 80
TOLERANCE = Decimal("1e-12")


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError("Independent physical transfer: " + message)


def number(value: object) -> Decimal:
    require(type(value) in (int, float, Decimal), "finite numeric scalar")
    result = Decimal(str(value))
    require(result.is_finite(), "finite numeric scalar")
    return result


def vector(values: Any, *, positive: bool = False) -> list[Decimal]:
    require(type(values) is list and len(values) == 2, "two-axis vector")
    result = [number(value) for value in values]
    require(all(v > 0 if positive else v >= 0 for v in result), "vector domain")
    return result


def count_vector(values: Any) -> list[int]:
    require(
        type(values) is list
        and len(values) == 2
        and all(type(v) is int and v >= 0 for v in values)
        and 0 < sum(values) < 2**53,
        "positive native integer-token panel with total below2**53",
    )
    return list(values)


def close(values: list[Decimal]) -> list[Decimal]:
    require(
        all(v.is_finite() and v >= 0 for v in values) and sum(values, Decimal(0)) > 0,
        "nonnegative finite positive-total closure",
    )
    with localcontext() as context:
        context.prec = PRECISION
        return [v / sum(values, Decimal(0)) for v in values]


def inverse(counts: Any, coefficients: Any, ppe: Any) -> dict[str, Any]:
    n, k, a = (
        count_vector(counts),
        vector(coefficients, positive=True),
        vector(ppe, positive=True),
    )
    with localcontext() as context:
        context.prec = PRECISION
        unclosed = [Decimal(n[i]) / (k[i] * a[i]) for i in range(2)]
        return {"preclosure": unclosed, "cover": close(unclosed)}


def predict(
    sources: list[dict[str, Any]], target_coefficients: Any, ppe: Any
) -> dict[str, Any]:
    """Every structural source is required; weights are not adapted to its counts."""
    require(bool(sources), "nonempty structural source population")
    weights = [number(row["weight"]) for row in sources]
    require(
        all(w > 0 for w in weights) and abs(sum(weights, Decimal(0)) - 1) <= TOLERANCE,
        "positive closed structural weights",
    )
    k, a = vector(target_coefficients, positive=True), vector(ppe, positive=True)
    with localcontext() as context:
        context.prec = PRECISION
        individual = [
            inverse(row["counts"], row["coefficients"], ppe) for row in sources
        ]
        weighted = [
            sum(w * row["cover"][i] for w, row in zip(weights, individual, strict=True))
            for i in range(2)
        ]
        forward = [k[i] * a[i] * weighted[i] for i in range(2)]
        return {
            "individual": individual,
            "weighted_cover": weighted,
            "forward_preclosure": forward,
            "physical": close(forward),
            "direct": direct_prediction(sources),
        }


def direct_prediction(sources: list[dict[str, Any]]) -> list[Decimal]:
    """The matched direct channel has no numerical response/PPE dependency."""
    require(bool(sources), "nonempty direct training cohort")
    weights = [number(row["weight"]) for row in sources]
    require(
        all(w > 0 for w in weights) and abs(sum(weights, Decimal(0)) - 1) <= TOLERANCE,
        "closed direct structural weights",
    )
    with localcontext() as context:
        context.prec = PRECISION
        return [
            sum(
                (
                    w * close([Decimal(x) for x in count_vector(row["counts"])])[i]
                    for w, row in zip(weights, sources, strict=True)
                ),
                Decimal(0),
            )
            for i in range(2)
        ]


def metrics(prediction: Any, counts: Any) -> dict[str, Any]:
    p, n = vector(prediction), count_vector(counts)
    require(abs(sum(p, Decimal(0)) - 1) <= TOLERANCE, "closed pollen prediction")
    with localcontext() as context:
        context.prec = PRECISION
        observation = close([Decimal(x) for x in n])
        errors = [p[i] - observation[i] for i in range(2)]
        absolute = sum((abs(v) for v in errors), Decimal(0)) / 2
        return {
            "mae_fraction": absolute,
            "hellinger_stable": (
                sum(
                    ((p[i].sqrt() - observation[i].sqrt()) ** 2 for i in range(2)),
                    Decimal(0),
                )
                / 2
            ).sqrt(),
            "total_variation": absolute,
            "signed_error_by_taxon": errors,
        }


def compare(actual: Any, expected: Any, label: str = "result") -> None:
    """Exact structural/types checks; only declared numerical outputs get tolerance."""
    if isinstance(expected, dict):
        require(type(actual) is dict and set(actual) == set(expected), label + " keys")
        for key, value in expected.items():
            compare(actual[key], value, label + "/" + key)
    elif isinstance(expected, list):
        require(
            type(actual) is list and len(actual) == len(expected), label + " population"
        )
        for i, (left, right) in enumerate(zip(actual, expected, strict=True)):
            compare(left, right, label + "/" + str(i))
    elif type(expected) is Decimal:
        require(
            abs(number(actual) - expected) <= TOLERANCE, label + " decimal equation"
        )
    else:
        require(
            type(actual) is type(expected) and actual == expected,
            label + " exact value",
        )
