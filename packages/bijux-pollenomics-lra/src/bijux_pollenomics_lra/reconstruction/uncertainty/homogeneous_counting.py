"""Certified two-taxon counting sets with a fixed regional pollen background."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Literal

import numpy as np
import numpy.typing as npt

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.uncertainty.two_taxon_counting import (
    _directed_float,
    fixed_two_taxon_counting_interval,
)

PROFILE = "homogeneous-two-taxon-fixed-background-binomial-set-v1"


@dataclass(frozen=True, slots=True)
class HomogeneousCountingSet:
    """One scalar confidence set and its dependent complementary cover bounds."""

    counts: tuple[int, int]
    total_count: int
    confidence_level: float
    local_coefficients: tuple[float, float]
    regional_deposition: tuple[float, float]
    pollen_probability_interval: tuple[float, float]
    feasible_pollen_probability_bounds: tuple[str, str]
    point_cover: tuple[float, float]
    status: Literal["nonempty", "empty"]
    cover_lower: tuple[float, float] | None
    cover_upper: tuple[float, float] | None
    tail_target_lower_bound: str
    pollen_tail_upper_bounds: tuple[str | None, str | None]
    bound_search_evaluations: tuple[int, int]
    numerical_certification: str = "directed-decimal-binomial-and-rational-inverse"
    profile: str = PROFILE


def _pair(value: npt.ArrayLike, label: str, *, positive: bool) -> tuple[float, float]:
    try:
        original = np.asarray(value, dtype=object)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValidationError(f"{label} cannot form a finite numeric pair") from error
    if original.shape != (2,) or any(isinstance(v, (bool, np.bool_)) for v in original):
        raise ValidationError(f"{label} requires two numbers without booleans")
    try:
        raw = np.asarray(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValidationError(f"{label} cannot form a finite numeric pair") from error
    if raw.dtype.kind not in "iuf":
        raise ValidationError(f"{label} requires two native numeric values")
    try:
        numbers = np.asarray(raw, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValidationError(f"{label} cannot form a finite numeric pair") from error
    if not np.isfinite(numbers).all() or np.any(
        numbers <= 0 if positive else numbers < 0
    ):
        raise ValidationError(
            f"{label} is outside its finite nonnegative/positive domain"
        )
    return float(numbers[0]), float(numbers[1])


def _inverse(
    probability: Fraction, a: tuple[Fraction, Fraction], b: tuple[Fraction, Fraction]
) -> Fraction:
    # p(v) = (a1*v+b1)/(a1*v+a2*(1-v)+b1+b2).
    # Its derivative numerator a1*a2+a1*b2+a2*b1 is strictly positive.
    denominator = a[0] - probability * (a[0] - a[1])
    if denominator <= 0:
        raise ValidationError("Homogeneous inverse denominator is not positive")
    return (probability * (a[1] + sum(b)) - b[0]) / denominator


def homogeneous_two_taxon_counting_set(
    counts: npt.ArrayLike,
    local_coefficients: npt.ArrayLike,
    regional_deposition: npt.ArrayLike,
    *,
    taxon_measured: npt.ArrayLike,
    confidence_level: float = 0.95,
) -> HomogeneousCountingSet:
    """Invert a certified binomial set through a fixed homogeneous local model.

    For cover ``(v,1-v)``, pollen probability is
    ``p(v)=(a1*v+b1)/(a1*v+a2*(1-v)+b1+b2)``. The caller binds the two
    literal taxa and common deposition units: ``a_i`` contains PPE and the
    local terrestrial response; ``b_i`` is fixed regional deposition.
    Local coefficients must be positive; regional deposition may be zero.
    Every coefficient is interpreted as its supplied binary64 value.

    Counts are one fixed-effort Binomial(N,p(v)) observation on two measured
    taxa, with 1 <= N <= 10000. The existing directed-tail certified API owns
    the Clopper-Pearson bounds and work/refusal limits. Exact Fraction
    arithmetic intersects them with the model's exact feasible pollen range
    and inverts the strictly increasing map. Outward conversion encloses both
    complementary covers. This is one confidence set, not two independent
    taxon intervals. Empty intersections are returned as status="empty" with
    null cover bounds; they are never replaced by an endpoint interval.

    The point is the constrained binomial MLE and is reported separately even
    for an empty confidence set. The guarantee is conditional on fixed
    sampling effort/model/support and supplied coefficients; it is not
    conditional on a subsequent observed-data admission or selection event.
    PPE, regional-background, geometry, chronology, sampling-design and
    model uncertainty are omitted. No vegetation accuracy, calibrated field
    uncertainty, historical LOVE parity or uncertainty for more than two
    taxa follows. The existing point solver and zero-background API are
    unchanged. A positive interior point unrepresentable in binary64 refuses.
    """
    a_values = _pair(local_coefficients, "Local coefficients", positive=True)
    b_values = _pair(regional_deposition, "Regional deposition", positive=False)
    counting = fixed_two_taxon_counting_interval(
        counts,
        [1.0, 1.0],
        [1.0, 1.0],
        taxon_measured=taxon_measured,
        confidence_level=confidence_level,
    )
    a = (Fraction.from_float(a_values[0]), Fraction.from_float(a_values[1]))
    b = (Fraction.from_float(b_values[0]), Fraction.from_float(b_values[1]))
    background = sum(b)
    feasible_low = b[0] / (a[1] + background)
    feasible_high = (a[0] + b[0]) / (a[0] + background)
    if not 0 <= feasible_low < feasible_high <= 1:
        raise ValidationError("Homogeneous feasible pollen domain is invalid")
    observed = Fraction(counting.counts[0], counting.total_count)
    projected = min(feasible_high, max(feasible_low, observed))
    point = _inverse(projected, a, b)
    point_cover = float(point), float(1 - point)
    if 0 < point < 1 and not all(0 < v < 1 for v in point_cover):
        raise ValidationError(
            "Homogeneous counting point cannot represent interior cover",
            reason_code="counting_interval_conditioning",
        )
    low = max(
        feasible_low, Fraction.from_float(counting.pollen_probability_interval[0])
    )
    high = min(
        feasible_high, Fraction.from_float(counting.pollen_probability_interval[1])
    )
    lower: tuple[float, float] | None = None
    upper: tuple[float, float] | None = None
    status: Literal["nonempty", "empty"] = "empty"
    if low <= high:
        left, right = _inverse(low, a, b), _inverse(high, a, b)
        if not 0 <= left <= point <= right <= 1:
            raise ValidationError("Homogeneous counting set ordering failed")
        lower = (
            _directed_float(left, upper=False),
            _directed_float(1 - right, upper=False),
        )
        upper = (
            _directed_float(right, upper=True),
            _directed_float(1 - left, upper=True),
        )
        status = "nonempty"
    return HomogeneousCountingSet(
        counting.counts,
        counting.total_count,
        counting.confidence_level,
        a_values,
        b_values,
        counting.pollen_probability_interval,
        (str(feasible_low), str(feasible_high)),
        point_cover,
        status,
        lower,
        upper,
        counting.tail_target_lower_bound,
        counting.pollen_tail_upper_bounds,
        counting.bound_search_evaluations,
    )
