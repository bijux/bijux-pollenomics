"""Tail-certified binomial counting intervals for a fixed two-taxon response."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import (
    ROUND_CEILING,
    ROUND_FLOOR,
    Context,
    Decimal,
    DecimalException,
    DivisionByZero,
    Inexact,
    InvalidOperation,
    Overflow,
    Subnormal,
    Underflow,
)
from fractions import Fraction
from functools import lru_cache
from math import isfinite, nextafter
from struct import pack, unpack

import numpy as np
import numpy.typing as npt
from scipy.special import betainccinv, betaincinv

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import _reject_masked_values

PROFILE = "fixed-two-taxon-binomial-equal-tail-v1"
MAX_TOTAL_COUNT = 10_000
MAX_TAIL_EVALUATIONS = 128
_ONE_BITS = 0x3FF0000000000000
_ZERO = Decimal(0)
_ONE = Decimal(1)


@dataclass(frozen=True, slots=True)
class TwoTaxonCountingInterval:
    """Closed conditional cover bounds and accepted-request tail certificates."""

    counts: tuple[int, int]
    total_count: int
    confidence_level: float
    pollen_probability_interval: tuple[float, float]
    cover: tuple[float, float]
    cover_lower: tuple[float, float]
    cover_upper: tuple[float, float]
    tail_target_lower_bound: str
    pollen_tail_upper_bounds: tuple[str | None, str | None]
    bound_search_evaluations: tuple[int, int]
    numerical_certification: str = "directed-decimal-tail-and-rational-transform"
    profile: str = PROFILE


def _positive_pair(value: npt.ArrayLike, label: str) -> npt.NDArray[np.float64]:
    _reject_masked_values(value, label)
    original = np.asarray(value, dtype=object)
    if original.shape != (2,) or any(
        isinstance(item, (bool, np.bool_)) for item in original
    ):
        raise ValidationError(f"{label} must be two numbers without booleans")
    raw = np.asarray(value)
    if raw.shape != (2,) or raw.dtype.kind not in "iuf":
        raise ValidationError(f"{label} must be exactly two numeric values")
    result = np.asarray(raw, dtype=np.float64)
    if not np.isfinite(result).all() or np.any(result <= 0):
        raise ValidationError(f"{label} must be finite and strictly positive")
    return result


def _context(*, upper: bool) -> Context:
    # N <= 10000 and binary64 probabilities require at most 3.24 million
    # negative decimal exponents. Trap every range loss, including subnormal.
    context = Context(
        prec=80,
        rounding=ROUND_CEILING if upper else ROUND_FLOOR,
        Emin=-10_000_000,
        Emax=10_000_000,
    )
    for signal in [InvalidOperation, DivisionByZero, Overflow, Underflow, Subnormal]:
        context.traps[signal] = True
    return context


def _power(value: Decimal, exponent: int, context: Context) -> Decimal:
    """Enclose a nonnegative integer power using only directed multiplication."""
    result = _ONE
    factor = value
    while exponent:
        if exponent & 1:
            result = context.multiply(result, factor)
        exponent //= 2
        if exponent:
            factor = context.multiply(factor, factor)
    return result


def _cdf(
    total: int, count: int, p: Decimal, q: Decimal, down: Context, up: Context
) -> tuple[Decimal, Decimal]:
    """Enclose the binomial CDF; p and q are exact complementary points."""
    if count < 0:
        return _ZERO, _ZERO
    if count >= total or p == 0:
        return _ONE, _ONE
    if q == 0:
        return _ZERO, _ZERO
    if count > total // 2:
        low, high = _cdf(total, total - count - 1, q, p, down, up)
        return max(_ZERO, down.subtract(_ONE, high)), min(_ONE, up.subtract(_ONE, low))
    low = _power(q, total, down)
    high = _power(q, total, up)
    sum_low, sum_high = low, high
    ratio_low, ratio_high = down.divide(p, q), up.divide(p, q)
    for index in range(count):
        numerator, denominator = Decimal(total - index), Decimal(index + 1)
        low = down.multiply(
            down.divide(down.multiply(low, numerator), denominator), ratio_low
        )
        high = up.multiply(
            up.divide(up.multiply(high, numerator), denominator), ratio_high
        )
        sum_low = down.add(sum_low, low)
        sum_high = up.add(sum_high, high)
    return max(_ZERO, sum_low), min(_ONE, sum_high)


def _complement(value: Decimal) -> Decimal:
    # Every binary64 fraction and 1 minus that fraction has an exact decimal
    # expansion with at most 1075 significant digits. An Inexact trap protects
    # this premise rather than assuming a rounded q is an exact point.
    context = Context(prec=1200, Emin=-10_000_000, Emax=10_000_000)
    context.traps[Inexact] = True
    for signal in [InvalidOperation, DivisionByZero, Overflow, Underflow, Subnormal]:
        context.traps[signal] = True
    return context.subtract(_ONE, value)


def _certify_bound(
    total: int,
    first: int,
    seed: float,
    *,
    upper: bool,
    tail_lower: Decimal,
) -> tuple[float, str, int]:
    if not isfinite(seed) or not 0 <= seed <= 1:
        raise ValidationError("Binomial inverse returned an invalid seed")
    down, up = _context(upper=False), _context(upper=True)
    evaluations = 0

    def evaluate(bits: int) -> tuple[bool, str]:
        nonlocal evaluations
        if evaluations >= MAX_TAIL_EVALUATIONS:
            raise ValidationError(
                "Binomial tail search exceeds the bounded evaluation budget",
                reason_code="counting_interval_certification",
            )
        evaluations += 1
        probability = _float_from_bits(bits)
        p = Decimal.from_float(probability)
        q = _complement(p)
        # Lower endpoint: P_p(X >= first) = F_(1-p)(N-first).
        # Upper endpoint: P_p(X <= first) = F_p(first).
        _, certificate = (
            _cdf(total, first, p, q, down, up)
            if upper
            else _cdf(total, total - first, q, p, down, up)
        )
        return certificate <= tail_lower, str(certificate)

    seed_bits = 0 if seed == 0 else int(unpack(">Q", pack(">d", seed))[0])
    accepted, certificate = evaluate(seed_bits)
    if accepted:
        return seed, certificate, evaluations
    rejected_bits = seed_bits
    direction = 1 if upper else -1
    distance = 1
    while True:
        probe = min(_ONE_BITS, max(0, seed_bits + direction * distance))
        accepted, certificate = evaluate(probe)
        if accepted:
            accepted_bits = probe
            break
        if probe == (0 if direction < 0 else _ONE_BITS):
            raise ValidationError("Exact binomial domain endpoint failed certification")
        rejected_bits = probe
        distance *= 2
    # Nonnegative binary64 bit patterns are ordered by numerical value.
    # Bracketing spans at most 62 bits; at most 63 bracket and 62 bisection
    # probes plus the seed fit within the explicit 128-evaluation budget.
    while abs(accepted_bits - rejected_bits) > 1:
        probe = (accepted_bits + rejected_bits) // 2
        accepted, probe_certificate = evaluate(probe)
        if accepted:
            accepted_bits, certificate = probe, probe_certificate
        else:
            rejected_bits = probe
    return _float_from_bits(accepted_bits), certificate, evaluations


def _float_from_bits(bits: int) -> float:
    return float(unpack(">d", pack(">Q", bits))[0])


@lru_cache(maxsize=4096)
def _probability_bounds(
    total: int, first: int, confidence: float
) -> tuple[float, float, str, tuple[str | None, str | None], tuple[int, int]]:
    tail = (Fraction(1) - Fraction.from_float(confidence)) / 2
    down = _context(upper=False)
    tail_lower = down.divide(Decimal(tail.numerator), Decimal(tail.denominator))
    seed_tail = float(tail)
    second = total - first
    lower, lower_certificate, lower_steps = (
        (0.0, None, 0)
        if first == 0
        else _certify_bound(
            total,
            first,
            float(betaincinv(first, second + 1, seed_tail)),
            upper=False,
            tail_lower=tail_lower,
        )
    )
    upper, upper_certificate, upper_steps = (
        (1.0, None, 0)
        if second == 0
        else _certify_bound(
            total,
            first,
            float(betainccinv(first + 1, second, seed_tail)),
            upper=True,
            tail_lower=tail_lower,
        )
    )
    if not 0 <= lower < upper <= 1:
        raise ValidationError("Certified binomial bounds fail interval ordering")
    return (
        lower,
        upper,
        str(tail_lower),
        (lower_certificate, upper_certificate),
        (lower_steps, upper_steps),
    )


def _cover(probability: Fraction, factors: tuple[Fraction, Fraction]) -> Fraction:
    first = factors[0] * probability
    second = factors[1] * (1 - probability)
    return first / (first + second)


def _directed_float(value: Fraction, *, upper: bool) -> float:
    nearest = float(value)
    exact_nearest = Fraction.from_float(nearest)
    if (upper and exact_nearest < value) or (not upper and exact_nearest > value):
        return nextafter(nearest, 1.0 if upper else 0.0)
    return nearest


def fixed_two_taxon_counting_interval(
    counts: npt.ArrayLike,
    deposition: npt.ArrayLike,
    ppe: npt.ArrayLike,
    *,
    taxon_measured: npt.ArrayLike,
    confidence_level: float = 0.95,
) -> TwoTaxonCountingInterval:
    """Return a tail-certified Clopper-Pearson conditional cover interval.

    Exactly one fixed-effort count vector on two measured taxa is supported,
    with 1 <= N <= 10000. Counts follow Binomial(N,p) on the declared panel;
    fixed positive correction factors are a_i=1/(deposition_i*ppe_i).
    The strictly increasing g(p)=a_1*p/(a_1*p+a_2*(1-p)) transfers the binomial
    confidence set to complementary cover, not independent taxon tests.

    SciPy inverses supply seeds only. Directed Decimal arithmetic certifies
    each accepted endpoint's binomial tail against a lower enclosure of the
    exact binary64 confidence tail. Outward lattice bracketing and bisection use at most128 tail
    evaluations per endpoint; requests exceeding the work bound refuse. Recurrence work is
    bounded by N, with at most floor(N/2)+1 positive terms per certificate.
    Range loss traps refuse. Exact rational transforms of the supplied
    binary64 response/PPE and directed conversion enclose both covers.
    The statistical guarantee remains conditional on this binomial model;
    it does not qualify ecological accuracy or uncertain response parameters.

    PPE, response, chronology, geometry, sampling-design, repeated-sample and
    model uncertainty are omitted. Independent aliquots, heterogeneous
    pooling, estimated PPE and more than two taxa require another model.
    No multinomial/Wald covariance API is replaced. Extreme correction
    factors and unrepresentable interior point estimates refuse.
    """
    _reject_masked_values(counts, "counts")
    original = np.asarray(counts, dtype=object)
    if original.shape != (2,) or any(
        isinstance(item, (bool, np.bool_)) for item in original
    ):
        raise ValidationError("Counts must be two numbers without booleans")
    raw = np.asarray(counts)
    if raw.shape != (2,) or raw.dtype.kind not in "iuf":
        raise ValidationError("Counts must be one numeric vector of exactly two taxa")
    if raw.dtype.kind in "iu" and any(int(value) > MAX_TOTAL_COUNT for value in raw):
        raise ValidationError("Counts exceed the bounded total-count domain")
    numeric = np.asarray(raw, dtype=np.float64)
    if (
        not np.isfinite(numeric).all()
        or np.any(numeric < 0)
        or np.any(numeric != np.floor(numeric))
        or np.any(numeric > MAX_TOTAL_COUNT)
    ):
        raise ValidationError("Counts must be finite nonnegative bounded integers")
    observed = (int(numeric[0]), int(numeric[1]))
    total = sum(observed)
    if not 1 <= total <= MAX_TOTAL_COUNT:
        raise ValidationError("Counting total must lie between 1 and 10000")
    _reject_masked_values(taxon_measured, "taxon_measured")
    measured = np.asarray(taxon_measured)
    if measured.shape != (2,) or measured.dtype != bool:
        raise ValidationError(
            "Measured-taxon mask must be a two-element boolean vector"
        )
    if not measured.all():
        raise ValidationError(
            "Unmeasured taxa cannot be assigned observed zero counts",
            reason_code="taxon_measurement_unresolved",
        )
    _reject_masked_values(confidence_level, "confidence_level")
    level = np.asarray(confidence_level)
    if level.shape != () or level.dtype.kind not in "iuf":
        raise ValidationError("Confidence level must be one finite number")
    confidence = float(level)
    if not isfinite(confidence) or not 0 < confidence < 1:
        raise ValidationError("Confidence level must lie strictly between zero and one")
    response = _positive_pair(deposition, "Deposition")
    productivity = _positive_pair(ppe, "PPE")
    with np.errstate(over="ignore", under="ignore", divide="ignore", invalid="ignore"):
        numeric_factors = 1 / (response * productivity)
        normalized = numeric_factors / np.max(numeric_factors)
    if (
        not np.isfinite(numeric_factors).all()
        or np.any(numeric_factors <= 0)
        or not np.isfinite(normalized).all()
        or np.any(normalized <= 0)
    ):
        raise ValidationError(
            "Fixed correction factors are outside the finite positive domain",
            reason_code="counting_interval_conditioning",
        )
    factors = (
        1
        / (
            Fraction.from_float(float(response[0]))
            * Fraction.from_float(float(productivity[0]))
        ),
        1
        / (
            Fraction.from_float(float(response[1]))
            * Fraction.from_float(float(productivity[1]))
        ),
    )
    first = observed[0]
    try:
        lower, upper, target, certificates, adjustments = _probability_bounds(
            total, first, confidence
        )
    except DecimalException as error:
        raise ValidationError(
            "Directed binomial arithmetic refused numerical range loss",
            reason_code="counting_interval_certification",
        ) from error
    point = _cover(Fraction(first, total), factors)
    point_values = (float(point), float(1 - point))
    if 0 < first < total and not all(0 < value < 1 for value in point_values):
        raise ValidationError(
            "Two-taxon response cannot represent an interior cover",
            reason_code="counting_interval_conditioning",
        )
    low = _cover(Fraction.from_float(lower), factors)
    high = _cover(Fraction.from_float(upper), factors)
    lower_values = (
        _directed_float(low, upper=False),
        _directed_float(1 - high, upper=False),
    )
    upper_values = (
        _directed_float(high, upper=True),
        _directed_float(1 - low, upper=True),
    )
    if any(
        not lo <= value <= hi
        for lo, value, hi in zip(lower_values, point_values, upper_values, strict=True)
    ):
        raise ValidationError("Transformed counting bounds fail interval ordering")
    return TwoTaxonCountingInterval(
        observed,
        total,
        confidence,
        (lower, upper),
        point_values,
        lower_values,
        upper_values,
        target,
        certificates,
        adjustments,
    )
