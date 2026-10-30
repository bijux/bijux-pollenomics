"""Independent high-precision likelihood and scoring checks for native Namibia rows.

The count objective uses a last-taxon zero-log-response gauge and independent
Gaussian elimination/Newton backtracking. Working precision is 160 decimal digits
so an O(1e-110) Armijo decrement remains resolvable near the fixed 1e-55 score
criterion. Agreement bounds compare implementations; they certify neither
statistical uncertainty nor ecological parameter accuracy.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal, localcontext

D = Decimal
ZERO, ONE = D(0), D(1)
Vector = tuple[Decimal, ...]
Matrix = list[list[Decimal]]
Fit = tuple[Vector, Decimal, Vector, Decimal, int]

PROBABILITY_BOUND = D("1e-8")
SCORE_BOUND = D("1e-10")
ORACLE_SCORE = D("1e-55")
ORACLE_RELATIVE = D("1e-50")


def require(condition: object, message: str) -> None:
    """Raise an assertion when an independent verification condition fails."""
    if not condition:
        raise AssertionError(message)


def close(values: Sequence[Decimal]) -> Vector:
    """Normalize positive-total Decimal values to a closed composition."""
    total = sum(values, ZERO)
    require(total > 0, "nonpositive composition denominator")
    return tuple(x / total for x in values)


def linear_solve(matrix: Sequence[Sequence[Decimal]], rhs: Sequence[Decimal]) -> Vector:
    """Independent partial-pivoted Gaussian elimination in Decimal arithmetic."""
    n = len(rhs)
    a = [list(row) + [value] for row, value in zip(matrix, rhs, strict=True)]
    for j in range(n):
        pivot = max(range(j, n), key=lambda i: abs(a[i][j]))
        require(a[pivot][j] != 0, "singular oracle Hessian")
        a[j], a[pivot] = a[pivot], a[j]
        for i in range(j + 1, n):
            factor = a[i][j] / a[j][j]
            for k in range(j + 1, n + 1):
                a[i][k] -= factor * a[j][k]
            a[i][j] = ZERO
    answer = [ZERO] * n
    for i in reversed(range(n)):
        answer[i] = (
            a[i][n] - sum((a[i][j] * answer[j] for j in range(i + 1, n)), ZERO)
        ) / a[i][i]
    return tuple(answer)


def probabilities(
    theta: Sequence[Decimal], log_area: Sequence[Decimal]
) -> tuple[Vector, Decimal]:
    """Return Decimal probabilities and the log normalizer for one area row."""
    logits = [a + t for a, t in zip(log_area, (*theta, ZERO), strict=True)]
    maximum = max(logits)
    weights = [(x - maximum).exp() for x in logits]
    normalizer = sum(weights, ZERO)
    return tuple(x / normalizer for x in weights), maximum + normalizer.ln()


def evaluate(
    theta: Sequence[Decimal],
    counts: Sequence[Sequence[int]],
    log_areas: Sequence[Sequence[Decimal]],
) -> tuple[Decimal, Vector, Matrix, Decimal]:
    """Return the count-weighted objective, score, Hessian and count residual."""
    dimension = len(theta)
    grand = D(sum(sum(row) for row in counts))
    expected = [ZERO] * (dimension + 1)
    observed = [sum((D(row[i]) for row in counts), ZERO) for i in range(dimension + 1)]
    hessian = [[ZERO] * dimension for _ in range(dimension)]
    nll = ZERO
    for count, log_area in zip(counts, log_areas, strict=True):
        p, log_z = probabilities(theta, log_area)
        effort = D(sum(count))
        nll -= sum(
            (
                D(n) * (a + t - log_z)
                for n, a, t in zip(count, log_area, (*theta, ZERO), strict=True)
            ),
            ZERO,
        )
        for i in range(dimension + 1):
            expected[i] += effort * p[i]
        for i in range(dimension):
            for j in range(dimension):
                hessian[i][j] += (
                    effort * p[i] * ((ONE if i == j else ZERO) - p[j]) / grand
                )
    score = tuple((expected[i] - observed[i]) / grand for i in range(dimension + 1))
    relative = max(
        abs(expected[i] - observed[i]) / observed[i] for i in range(dimension + 1)
    )
    return nll / grand, score, hessian, relative


def solve(counts: Sequence[Sequence[int]], areas: Sequence[Sequence[Decimal]]) -> Fit:
    """Fit a positive common response in a last-taxon zero-log-response gauge."""
    require(counts and len(counts) == len(areas), "oracle source shape")
    axis = len(counts[0])
    require(
        axis >= 2 and all(len(r) == axis for r in (*counts, *areas)),
        "oracle taxon axis",
    )
    require(
        all(type(n) is int and n > 0 for r in counts for n in r),
        "oracle native positive counts",
    )
    require(
        all(a.is_finite() and a > 0 for r in areas for a in r), "oracle positive area"
    )
    log_areas = [tuple(a.ln() for a in row) for row in areas]
    theta = (ZERO,) * (axis - 1)
    for iteration in range(100):
        value, score, hessian, relative = evaluate(theta, counts, log_areas)
        if max(map(abs, score)) <= ORACLE_SCORE and relative <= ORACLE_RELATIVE:
            return theta, value, score, relative, iteration
        direction = linear_solve(hessian, score[:-1])
        decrement = sum(
            (g * d for g, d in zip(score[:-1], direction, strict=True)), ZERO
        )
        require(decrement > 0, "oracle Newton direction is not descending")
        alpha = ONE
        for _ in range(200):
            candidate = tuple(
                t - alpha * d for t, d in zip(theta, direction, strict=True)
            )
            objective = evaluate(candidate, counts, log_areas)[0]
            if objective <= value - D("0.0001") * alpha * decrement:
                theta = candidate
                break
            alpha /= 2
        else:
            raise AssertionError("oracle line search refused")
    raise AssertionError("oracle Newton iterations exhausted")


def analytic_controls() -> None:
    """Controlled analytical cases; these never read the scientific source files."""
    with localcontext() as context:
        context.prec = 160
        counts = [(9, 4, 3, 2, 7), (3, 8, 1, 6, 2)]
        row = tuple(map(D, (2, 3, 5, 7, 11)))
        theta, _, score, _, _ = solve(counts, [row, row])
        expected = [D(sum(r[i] for r in counts)) / row[i] for i in range(5)]
        expected_theta = tuple((v / expected[-1]).ln() for v in expected[:-1])
        require(
            max(abs(a - b) for a, b in zip(theta, expected_theta, strict=True))
            < D("1e-50"),
            "equal-area analytical reduction",
        )
        require(max(map(abs, score)) <= ORACLE_SCORE, "analytical balance")
        # For these heterogeneous binomial sites the exact response ratio is one.
        theta, _, score, _, _ = solve([(9, 1), (5, 5)], [(D(9), ONE), (ONE, ONE)])
        require(
            abs(theta[0]) < D("1e-50") and max(map(abs, score)) <= ORACLE_SCORE,
            "heterogeneous two-taxon analytical root",
        )
        theta, _, score, _, _ = solve([(9, 1), (1, 9)], [(D(9), ONE), (ONE, ONE)])
        require(
            abs(theta[0] - (ONE / 3).ln()) < D("1e-50")
            and max(map(abs, score)) <= ORACLE_SCORE,
            "nontrivial heterogeneous scalar root t=1/3",
        )
        print(
            "PASS controlled equal-response five-taxon and heterogeneous two-taxon analytical controls"
        )


def losses(
    predicted: Sequence[Decimal], count: Sequence[int]
) -> tuple[Decimal, Decimal, Decimal]:
    """Return cross entropy, mean absolute error and squared Hellinger loss."""
    observed = close(tuple(map(D, count)))
    nll = -sum((x * q.ln() for x, q in zip(observed, predicted, strict=True)), ZERO)
    h2 = (
        sum(
            (
                (x.sqrt() - q.sqrt()) ** 2
                for x, q in zip(observed, predicted, strict=True)
            ),
            ZERO,
        )
        / 2
    )
    mae = sum(
        (abs(x - q) for x, q in zip(observed, predicted, strict=True)), ZERO
    ) / len(count)
    return nll, mae, h2
