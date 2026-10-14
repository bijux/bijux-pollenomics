"""Conditional two-component affine inverse and its feasible abundance-ratio family."""

from __future__ import annotations

from dataclasses import dataclass
import math

Axis = tuple[float, float]


def require(condition: object, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _axis(value: Axis) -> None:
    require(
        isinstance(value, (tuple, list))
        and len(value) == 2
        and all(type(x) in (int, float) and math.isfinite(x) for x in value),
        "A finite two-taxon numeric axis is required",
    )


@dataclass(frozen=True)
class AffineCoverFamily:
    """A deterministic conditional domain, without a ratio probability model."""

    pollen: Axis
    local_response: Axis
    unit_background: Axis
    intercept: Axis
    slope: Axis
    inverse_denominator: float
    background_sum: float
    upper_ratio: float | None

    def evaluate(self, ratio: float) -> Axis:
        """Retain signed cover outside the feasible domain, without clipping."""
        require(
            type(ratio) in (int, float) and math.isfinite(ratio) and ratio >= 0,
            "Ratio must be finite and nonnegative",
        )
        values = tuple(
            u + ratio * d for u, d in zip(self.intercept, self.slope, strict=True)
        )
        require(
            all(math.isfinite(x) for x in values),
            "Cover family exceeds its finite domain",
        )
        return values[0], values[1]


def affine_family(
    pollen: Axis, local_response: Axis, unit_background: Axis
) -> AffineCoverFamily:
    """Solve closure for every declared nonnegative abundance ratio at fixed response."""
    for axis in (pollen, local_response, unit_background):
        _axis(axis)
    pollen = (pollen[0], pollen[1])
    local_response = (local_response[0], local_response[1])
    unit_background = (unit_background[0], unit_background[1])
    require(
        all(x >= 0 for x in pollen) and abs(sum(pollen) - 1) <= 1e-14,
        "Observed pollen must be a closed nonnegative panel",
    )
    require(
        all(x > 0 for x in local_response) and all(x >= 0 for x in unit_background),
        "Local responses must be positive and backgrounds nonnegative",
    )
    try:
        qa = [pollen[i] / local_response[i] for i in range(2)]
        ca = [unit_background[i] / local_response[i] for i in range(2)]
        require(
            all(math.isfinite(x) for x in [*qa, *ca])
            and all(pollen[i] == 0 or qa[i] > 0 for i in range(2))
            and all(unit_background[i] == 0 or ca[i] > 0 for i in range(2)),
            "Response ratios exceed the finite positive domain",
        )
        A, B = sum(qa), sum(ca)
        require(
            math.isfinite(A) and A > 0 and math.isfinite(B) and B >= 0,
            "Affine normalization is not finite positive",
        )
        intercept = (qa[0] / A, qa[1] / A)
        slope = (
            (pollen[0] * (B / A) - unit_background[0]) / local_response[0],
            (pollen[1] * (B / A) - unit_background[1]) / local_response[1],
        )
        require(
            all(math.isfinite(x) for x in [*intercept, *slope]),
            "Affine coefficients exceed the finite domain",
        )
        require(
            abs(sum(intercept) - 1) <= 2e-13 and abs(sum(slope)) <= 2e-13,
            "Affine closure differs",
        )
        upper = math.inf
        for u, d in zip(intercept, slope, strict=True):
            if d != 0:
                bound = -u / d if d < 0 else (1 - u) / d
                require(
                    math.isfinite(bound), "Ratio endpoint exceeds the finite domain"
                )
                upper = min(upper, bound)
        require(
            upper >= 0 and not math.isnan(upper),
            "Feasible nonnegative ratio domain is empty",
        )
    except (OverflowError, ZeroDivisionError) as error:
        raise ValueError("Affine arithmetic exceeds its finite domain") from error
    return AffineCoverFamily(
        pollen,
        local_response,
        unit_background,
        intercept,
        slope,
        A,
        B,
        None if math.isinf(upper) else upper,
    )


def forward_and_jacobian(
    family: AffineCoverFamily, ratio: float
) -> tuple[Axis, tuple[Axis, Axis]]:
    """Differentiate the same closed mixture on coordinates (v_Betula, ratio)."""
    v = family.evaluate(ratio)
    a, c = family.local_response, family.unit_background
    try:
        w = (a[0] * v[0] + ratio * c[0], a[1] * (1 - v[0]) + ratio * c[1])
        total = sum(w)
        require(
            all(math.isfinite(x) for x in w) and math.isfinite(total) and total > 0,
            "Forward mixture denominator is not finite positive",
        )
        q = (w[0] / total, w[1] / total)
        # Quotient derivatives on the one free local composition coordinate.
        jv = (a[0] * total - w[0] * (a[0] - a[1])) / (total * total)
        jr = (c[0] * total - w[0] * sum(c)) / (total * total)
        require(
            all(math.isfinite(x) for x in [*q, jv, jr]),
            "Forward Jacobian exceeds its finite domain",
        )
    except (OverflowError, ZeroDivisionError) as error:
        raise ValueError("Forward arithmetic exceeds its finite domain") from error
    return q, ((jv, jr), (-jv, -jr))
