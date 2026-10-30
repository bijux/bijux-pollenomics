"""Conditional LOVE sets propagating measured local and regional pollen counts."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import inf, isfinite, nextafter
from typing import Literal

import numpy as np
import numpy.typing as npt

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.uncertainty.homogeneous_counting import _pair
from bijux_pollenomics_lra.reconstruction.uncertainty.two_taxon_counting import (
    TwoTaxonCountingInterval,
    _cover,
    _directed_float,
    fixed_two_taxon_counting_interval,
)

PROFILE = "homogeneous-two-taxon-local-regional-counting-set-v1"


@dataclass(frozen=True, slots=True)
class RegionalCountingCorner:
    """One exact endpoint pair and its signed complementary LOVE solution."""

    local_pollen_probability: str
    regional_cover: str
    signed_cover: tuple[str, str]


@dataclass(frozen=True, slots=True)
class CountingImage:
    """Signed interval and its exact intersection with physical complementary cover."""

    signed_cover_lower_exact: tuple[str, str]
    signed_cover_upper_exact: tuple[str, str]
    signed_cover_lower: tuple[float, float]
    signed_cover_upper: tuple[float, float]
    status: Literal["empty", "nonempty"]
    cover_lower_exact: tuple[str, str] | None
    cover_upper_exact: tuple[str, str] | None
    cover_lower: tuple[float, float] | None
    cover_upper: tuple[float, float] | None


@dataclass(frozen=True, slots=True)
class FixedRegionalCountingControl:
    """Matched local-marginal control conditioning on regional plug-in cover."""

    regional_cover_exact: tuple[str, str]
    local_confidence_level: float
    pollen_endpoint_signed_cover: tuple[tuple[str, str], tuple[str, str]]
    image: CountingImage


@dataclass(frozen=True, slots=True)
class RegionalCountingSet:
    """An exact rectangle image, marginal tail proofs and matched fixed-c control."""

    confidence_level: float
    marginal_confidence_level: float
    guaranteed_joint_confidence_lower_bound: str
    local_kernel: tuple[float, float]
    regional_kernel: tuple[float, float]
    regional_deposition: tuple[float, float]
    ppe: tuple[float, float]
    local_counting: TwoTaxonCountingInterval
    regional_counting: TwoTaxonCountingInterval
    regional_cover_interval: tuple[str, str]
    regional_point_cover_exact: tuple[str, str]
    signed_point_cover_exact: tuple[str, str]
    signed_point_cover: tuple[float, float]
    corners: tuple[RegionalCountingCorner, ...]
    signed_lower_corner: int
    signed_upper_corner: int
    image: CountingImage
    fixed_regional_control: FixedRegionalCountingControl
    numerical_certification: str = (
        "directed-binomial-tails-exact-rational-rectangle-image"
    )
    profile: str = PROFILE


def _confidence(value: float) -> tuple[float, float, Fraction]:
    raw = np.asarray(value)
    if raw.shape != () or raw.dtype.kind not in "iuf":
        raise ValidationError("Confidence level must be one finite number")
    requested = float(raw)
    if not isfinite(requested) or not 0 < requested < 1:
        raise ValidationError("Confidence level must lie strictly between zero and one")
    target = (1 + Fraction.from_float(requested)) / 2
    marginal = float(target)
    if Fraction.from_float(marginal) < target:
        marginal = nextafter(marginal, 1.0)
    if marginal >= 1:
        raise ValidationError(
            "Equal Bonferroni marginal confidence is not representable below one",
            reason_code="counting_interval_conditioning",
        )
    return requested, marginal, 2 * Fraction.from_float(marginal) - 1


def _signed_display(value: Fraction, *, upper: bool) -> float:
    try:
        nearest = float(value)
    except OverflowError as error:
        raise ValidationError(
            "Signed LOVE cover exceeds finite binary64 display",
            reason_code="counting_interval_conditioning",
        ) from error
    if not isfinite(nearest):
        raise ValidationError("Signed LOVE cover exceeds finite binary64 display")
    rounded = Fraction.from_float(nearest)
    if upper and rounded < value or not upper and rounded > value:
        nearest = nextafter(nearest, inf if upper else -inf)
    if not isfinite(nearest):
        raise ValidationError(
            "Signed LOVE outward bound exceeds finite binary64 display",
            reason_code="counting_interval_conditioning",
        )
    return nearest


def _image(left: Fraction, right: Fraction) -> CountingImage:
    signed_low, signed_high = (left, 1 - right), (right, 1 - left)
    low, high = max(Fraction(0), left), min(Fraction(1), right)
    lower = (low, 1 - high) if low <= high else None
    upper = (high, 1 - low) if low <= high else None
    return CountingImage(
        (str(signed_low[0]), str(signed_low[1])),
        (str(signed_high[0]), str(signed_high[1])),
        (
            _signed_display(signed_low[0], upper=False),
            _signed_display(signed_low[1], upper=False),
        ),
        (
            _signed_display(signed_high[0], upper=True),
            _signed_display(signed_high[1], upper=True),
        ),
        "nonempty" if lower is not None else "empty",
        None if lower is None else (str(lower[0]), str(lower[1])),
        None if upper is None else (str(upper[0]), str(upper[1])),
        None
        if lower is None
        else (
            _directed_float(lower[0], upper=False),
            _directed_float(lower[1], upper=False),
        ),
        None
        if upper is None
        else (
            _directed_float(upper[0], upper=True),
            _directed_float(upper[1], upper=True),
        ),
    )


def _inverse(
    p: Fraction,
    c: Fraction,
    local: tuple[Fraction, Fraction],
    regional: tuple[Fraction, Fraction],
    ppe: tuple[Fraction, Fraction],
) -> Fraction:
    d = c * local[0] + (1 - c) * local[1]
    b1 = ppe[0] * c * regional[0]
    b2 = ppe[1] * (1 - c) * regional[1]
    denominator = d * (ppe[0] - p * (ppe[0] - ppe[1]))
    if denominator <= 0:
        raise ValidationError("Local/regional LOVE inverse denominator is not positive")
    return (p * (ppe[1] * d + b1 + b2) - b1) / denominator


def regional_two_taxon_counting_set(
    local_counts: npt.ArrayLike,
    regional_counts: npt.ArrayLike,
    local_kernel: npt.ArrayLike,
    regional_kernel: npt.ArrayLike,
    regional_deposition: npt.ArrayLike,
    ppe: npt.ArrayLike,
    *,
    local_taxon_measured: npt.ArrayLike,
    regional_taxon_measured: npt.ArrayLike,
    confidence_level: float = 0.95,
) -> RegionalCountingSet:
    """Invert two certified marginal count sets with an equal Bonferroni budget.

    Local and regional panels each follow their declared fixed-effort binomial
    law on the same two measured taxa. The certified marginal confidence is
    rounded upward to at least exact (1+C)/2. The union bound gives joint
    rectangle coverage at least 2*marginal-1 >= C, without assuming independence
    between the two panels. All masks, count/work limits and tail-certificate
    refusals remain owned by the existing certified binomial implementation.

    Regional pollen probability r maps to cover c using positive fixed REVEALS
    deposition and PPE. Both regional endpoints are transformed as exact
    rationals from the original certified pollen endpoints and supplied
    binary64 parameters, never from outward-rounded cover displays. For local
    pollen probability p, D(c)=c*Kloc1+(1-c)*Kloc2 and the signed inverse is
    [p*(PPE2*D+PPE1*c*Kreg1+PPE2*(1-c)*Kreg2)-PPE1*c*Kreg1]
    / [D*(PPE1-p*(PPE1-PPE2))]. Positive Kloc/PPE and nonnegative Kreg
    make every denominator positive. For fixed c this is strictly increasing
    in p; for fixed p it is affine fractional in c, with derivative of fixed
    sign. Its extrema on the closed rectangle therefore occur at corners.
    Continuity and connectedness make the entire image the interval between
    those extrema. Intersect that signed image with [0,1] for physical cover;
    an empty intersection has null bounds, never a clipped apparent success.

    The point is the signed inverse at both observed count proportions with
    regional REVEALS correction. It is a plug-in point, not a joint MLE, and
    is not clipped. A matched fixed-regional control inverts these same local
    marginal endpoints at that exact regional plug-in c. It omits regional
    uncertainty and does not carry the joint coverage guarantee. Exact rational strings and outward displays retain both
    complementary signed covers. Inputs/rectangle/model must be prespecified;
    the guarantee does not hold conditional on later outcome selection.
    PPE, kernels, chronology, geometry, pooling/sampling-law applicability,
    ecological accuracy and more than two taxa remain outside this model.
    """
    requested, marginal, guarantee = _confidence(confidence_level)
    local_values = _pair(local_kernel, "Local kernel", positive=True)
    regional_values = _pair(regional_kernel, "Regional kernel", positive=False)
    deposition_values = _pair(regional_deposition, "Regional deposition", positive=True)
    ppe_values = _pair(ppe, "PPE", positive=True)
    local_counting = fixed_two_taxon_counting_interval(
        local_counts,
        [1.0, 1.0],
        [1.0, 1.0],
        taxon_measured=local_taxon_measured,
        confidence_level=marginal,
    )
    regional_counting = fixed_two_taxon_counting_interval(
        regional_counts,
        deposition_values,
        ppe_values,
        taxon_measured=regional_taxon_measured,
        confidence_level=marginal,
    )
    local = tuple(map(Fraction.from_float, local_values))
    regional = tuple(map(Fraction.from_float, regional_values))
    productivity = tuple(map(Fraction.from_float, ppe_values))
    factors = tuple(
        1 / (Fraction.from_float(d) * Fraction.from_float(q))
        for d, q in zip(deposition_values, ppe_values, strict=True)
    )
    # Explicit pairs retain strict static shape as well as the runtime contract.
    local_pair = local[0], local[1]
    regional_pair = regional[0], regional[1]
    ppe_pair = productivity[0], productivity[1]
    response_pair = factors[0], factors[1]
    p_bounds = tuple(
        map(Fraction.from_float, local_counting.pollen_probability_interval)
    )
    c_bounds = tuple(
        _cover(Fraction.from_float(r), response_pair)
        for r in regional_counting.pollen_probability_interval
    )
    corners = []
    values = []
    for p in p_bounds:
        for c in c_bounds:
            value = _inverse(p, c, local_pair, regional_pair, ppe_pair)
            values.append(value)
            corners.append(
                RegionalCountingCorner(str(p), str(c), (str(value), str(1 - value)))
            )
    left, right = min(values), max(values)
    c_point = _cover(
        Fraction(regional_counting.counts[0], regional_counting.total_count),
        response_pair,
    )
    point = _inverse(
        Fraction(local_counting.counts[0], local_counting.total_count),
        c_point,
        local_pair,
        regional_pair,
        ppe_pair,
    )
    if not left <= point <= right:
        raise ValidationError("Signed plug-in LOVE point lies outside rectangle image")
    try:
        point_values = float(point), float(1 - point)
    except OverflowError as error:
        raise ValidationError(
            "Signed plug-in point exceeds finite binary64",
            reason_code="counting_interval_conditioning",
        ) from error
    if (
        not all(isfinite(v) for v in point_values)
        or any(
            exact != 0 and value == 0
            for exact, value in zip((point, 1 - point), point_values, strict=True)
        )
        or 0 < point < 1
        and not all(0 < v < 1 for v in point_values)
    ):
        raise ValidationError(
            "Signed plug-in point cannot be represented",
            reason_code="counting_interval_conditioning",
        )
    fixed = tuple(
        _inverse(p, c_point, local_pair, regional_pair, ppe_pair) for p in p_bounds
    )
    control = FixedRegionalCountingControl(
        (str(c_point), str(1 - c_point)),
        marginal,
        ((str(fixed[0]), str(1 - fixed[0])), (str(fixed[1]), str(1 - fixed[1]))),
        _image(fixed[0], fixed[1]),
    )
    return RegionalCountingSet(
        requested,
        marginal,
        str(guarantee),
        local_values,
        regional_values,
        deposition_values,
        ppe_values,
        local_counting,
        regional_counting,
        (str(c_bounds[0]), str(c_bounds[1])),
        (str(c_point), str(1 - c_point)),
        (str(point), str(1 - point)),
        point_values,
        tuple(corners),
        values.index(left),
        values.index(right),
        _image(left, right),
        control,
    )
