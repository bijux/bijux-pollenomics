"""Conditional two-site common-cover sets from certified binomial count tails."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Literal

import numpy as np

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import _reject_masked_values, matrix
from bijux_pollenomics_lra.reconstruction.likelihood.multisite_likelihood import (
    _measured,
)
from bijux_pollenomics_lra.reconstruction.uncertainty.regional_counting import (
    _confidence,
)
from bijux_pollenomics_lra.reconstruction.uncertainty.two_taxon_counting import (
    MAX_TOTAL_COUNT,
    TwoTaxonCountingInterval,
    _cover,
    _directed_float,
    fixed_two_taxon_counting_interval,
)

PROFILE = "two-site-fixed-response-binomial-common-cover-set-v1"
Pair = tuple[float, float]
ExactPair = tuple[str, str]


@dataclass(frozen=True, slots=True)
class SiteCountingSet:
    """One site's exact inverse interval; a zero-effort row is uninformative."""

    counts: tuple[int, int]
    total_count: int
    used: bool
    pollen_probability_interval: Pair
    first_cover_interval_exact: ExactPair
    counting_interval: TwoTaxonCountingInterval | None


@dataclass(frozen=True, slots=True)
class MultisiteCountingSet:
    """Exact intersection, outward complementary displays and marginal tail proofs."""

    confidence_level: float
    marginal_confidence_level: float
    guaranteed_joint_confidence_lower_bound: str
    responses: tuple[Pair, Pair]
    sites: tuple[SiteCountingSet, SiteCountingSet]
    excluded_zero_total_site_indices: tuple[int, ...]
    status: Literal["empty", "nonempty"]
    intersection_limits_exact: ExactPair
    lower_attaining_site_indices: tuple[int, ...]
    upper_attaining_site_indices: tuple[int, ...]
    cover_lower_exact: ExactPair | None
    cover_upper_exact: ExactPair | None
    cover_lower: Pair | None
    cover_upper: Pair | None
    numerical_certification: str = "directed-binomial-tails-exact-rational-intersection"
    profile: str = PROFILE


def multisite_two_taxon_counting_set(
    counts: object,
    responses: object,
    *,
    taxon_measured: object,
    confidence_level: float = 0.95,
) -> MultisiteCountingSet:
    """Intersect two conditional count sets without fitting or pooling responses.

    The declared model has common first-taxon cover v in [0,1] and fixed
    positive responses a_si. At site s, X_s conditional on N_s is binomial
    with p_s(v)=a_s1*v/(a_s1*v+a_s2*(1-v)). This requires binomial marginals;
    pooling dependent or heterogeneous source samples does not establish them.
    PPE, geometry, chronology, between-site heterogeneity and model uncertainty
    are omitted. These are conditional confidence sets, not posterior,
    predictive, calibrated field-accuracy or whole-study simultaneous bands.

    For requested C, each certified Clopper-Pearson interval has confidence
    m >= (1+C)/2, rounded upward on the binary64 lattice. The inverse
    g_s(p)=a_s2*p/(a_s1*(1-p)+a_s2*p) is strictly increasing, including the
    endpoints 0 and 1. Transforming the certified pollen endpoints with exact
    rational arithmetic gives site cover intervals I_s. The common set is
    I_1 intersect I_2, decided before outward display rounding. A union bound
    gives P(v in both I_s) >= 2*m-1 >= C; independence ACROSS sites is not
    needed. Empty intersections remain empty and are not optimizer failures.

    Each positive site total is at most 10000, the existing tail helper's
    bounded domain. Observed zero counts retain their nondegenerate binomial
    bounds. A zero-effort site contributes [0,1] and is recorded as excluded;
    the same two-site confidence budget is retained. Two empty sites refuse.
    Every cell must be explicitly measured. Responses are the supplied finite
    binary64 values themselves: a previously computed PPE*K product must not
    be silently replaced by an exact product of its unrounded factors.
    No point estimate, convergence claim or MLE-containment rule is supplied.
    """
    n = matrix(counts, "counts", nonnegative=True)
    a = matrix(responses, "responses")
    if n.shape != (2, 2) or a.shape != n.shape:
        raise ValidationError("Exactly two sites on one common two-taxon axis required")
    _measured(taxon_measured, n.shape)
    if np.any(a <= 0):
        raise ValidationError("Fixed responses must be strictly positive")
    if np.any(n != np.floor(n)) or np.any(n > MAX_TOTAL_COUNT):
        raise ValidationError("Counts must be bounded nonnegative integers")
    totals = n.sum(axis=1)
    if np.any(totals > MAX_TOTAL_COUNT):
        raise ValidationError("Each site total must be at most 10000")
    if not np.any(totals > 0):
        raise ValidationError(
            "No positive-count site is available", reason_code="no_positive_count_site"
        )
    _reject_masked_values(confidence_level, "confidence_level")
    requested, marginal, guarantee = _confidence(confidence_level)
    sites: list[SiteCountingSet] = []
    limits: list[tuple[Fraction, Fraction]] = []
    for row, response, total in zip(n, a, totals, strict=True):
        observed = int(row[0]), int(row[1])
        interval = None
        if total:
            interval = fixed_two_taxon_counting_interval(
                row,
                response,
                (1.0, 1.0),
                taxon_measured=(True, True),
                confidence_level=marginal,
            )
            pollen = interval.pollen_probability_interval
        else:
            pollen = 0.0, 1.0
        factors = (
            1 / Fraction.from_float(float(response[0])),
            1 / Fraction.from_float(float(response[1])),
        )
        lower, upper = (_cover(Fraction.from_float(p), factors) for p in pollen)
        limits.append((lower, upper))
        sites.append(
            SiteCountingSet(
                observed,
                int(total),
                bool(total),
                pollen,
                (str(lower), str(upper)),
                interval,
            )
        )
    left = max(lower for lower, _ in limits)
    right = min(upper for _, upper in limits)
    lower_exact = (left, 1 - right) if left <= right else None
    upper_exact = (right, 1 - left) if left <= right else None
    return MultisiteCountingSet(
        requested,
        marginal,
        str(guarantee),
        ((float(a[0, 0]), float(a[0, 1])), (float(a[1, 0]), float(a[1, 1]))),
        (sites[0], sites[1]),
        tuple(int(i) for i in np.flatnonzero(totals == 0)),
        "nonempty" if lower_exact is not None else "empty",
        (str(left), str(right)),
        tuple(i for i, (lower, _) in enumerate(limits) if lower == left),
        tuple(i for i, (_, upper) in enumerate(limits) if upper == right),
        None if lower_exact is None else (str(lower_exact[0]), str(lower_exact[1])),
        None if upper_exact is None else (str(upper_exact[0]), str(upper_exact[1])),
        None
        if lower_exact is None
        else (
            _directed_float(lower_exact[0], upper=False),
            _directed_float(lower_exact[1], upper=False),
        ),
        None
        if upper_exact is None
        else (
            _directed_float(upper_exact[0], upper=True),
            _directed_float(upper_exact[1], upper=True),
        ),
    )
