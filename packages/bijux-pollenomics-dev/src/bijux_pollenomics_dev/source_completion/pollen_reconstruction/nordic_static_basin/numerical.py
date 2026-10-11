"""Scalar conditional inverse composition and delta covariance in Decimal50."""

from collections.abc import Sequence
from decimal import Decimal, localcontext


def oracle(
    counts: Sequence[int],
    ppe: Sequence[float],
    factors: Sequence[float],
    sd: Sequence[float],
) -> dict[str, list[Decimal] | list[list[Decimal]]]:
    """Use panel multinomial N and a diagonal shared PPE uncertainty assumption."""
    with localcontext() as context:
        context.prec = 50
        n = [Decimal(value) for value in counts]
        e = [Decimal(str(value)) for value in ppe]
        k = [Decimal(str(value)) for value in factors]
        s = [Decimal(str(value)) for value in sd]
        N = sum(n)
        if (
            N <= 0
            or any(not value.is_finite() or value <= 0 for value in e + k)
            or any(not value.is_finite() or value < 0 for value in s)
        ):
            raise ValueError("Nordic conditional numerical denominator differs")
        size = len(n)
        if len(e) != size or len(k) != size or len(s) != size:
            raise ValueError("Nordic numerical parameter axis differs")
        p = [value / N for value in n]
        a = [1 / (e[i] * k[i]) for i in range(size)]
        normalizer = sum(a[i] * p[i] for i in range(size))
        cover = [a[i] * p[i] / normalizer for i in range(size)]
        J = [
            [a[j] * (Decimal(i == j) - cover[i]) / normalizer for j in range(size)]
            for i in range(size)
        ]
        H = [
            [-cover[j] * (Decimal(i == j) - cover[i]) / e[j] for j in range(size)]
            for i in range(size)
        ]
        multinomial = [
            [
                (p[j] * Decimal(j == column) - p[j] * p[column]) / N
                for column in range(size)
            ]
            for j in range(size)
        ]
        count_covariance = [
            [
                sum(
                    (
                        J[i][j] * multinomial[j][column] * J[h][column]
                        for j in range(size)
                        for column in range(size)
                    ),
                    Decimal(0),
                )
                for h in range(size)
            ]
            for i in range(size)
        ]
        ppe_covariance = [
            [
                sum((H[i][j] * H[h][j] * s[j] ** 2 for j in range(size)), Decimal(0))
                for h in range(size)
            ]
            for i in range(size)
        ]
        total = [
            [count_covariance[i][j] + ppe_covariance[i][j] for j in range(size)]
            for i in range(size)
        ]
        se = [total[i][i].sqrt() for i in range(size)]
        return {
            "conditional_cover": cover,
            "direct_pollen_panel_fraction": p,
            "counting_covariance": count_covariance,
            "assumed_ppe_covariance": ppe_covariance,
            "total_conditional_covariance": total,
            "conditional_standard_error": se,
        }


def compare(expected: object, observed: object) -> int:
    """Refuse changed saved numerical values at the independently used tolerance."""
    if isinstance(expected, list):
        if not isinstance(observed, list) or len(expected) != len(observed):
            raise ValueError("Nordic saved numerical shape differs")
        return sum(
            compare(left, right) for left, right in zip(expected, observed, strict=True)
        )
    if not isinstance(expected, Decimal):
        raise ValueError("Nordic expected numerical cell is not Decimal")
    if type(observed) not in (int, float):
        raise ValueError("Nordic saved numerical value is not scalar")
    actual = Decimal(str(observed))
    difference = abs(expected - actual)
    if not actual.is_finite() or difference > Decimal("2e-12") + Decimal("2e-12") * abs(
        expected
    ):
        raise ValueError("Nordic saved numerical equation differs")
    return 1
