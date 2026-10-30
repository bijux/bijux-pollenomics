"""Joint counting regions for one complete three-taxon and one nested panel."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import isfinite, nextafter
from typing import Literal

import numpy as np

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import vector
from bijux_pollenomics_lra.reconstruction.likelihood.multisite_likelihood import (
    _measured,
    _require_numeric_measurements,
    _require_unmasked,
)
from bijux_pollenomics_lra.reconstruction.uncertainty.multisite_counting import (
    SiteCountingSet,
)
from bijux_pollenomics_lra.reconstruction.uncertainty.two_taxon_counting import (
    MAX_TOTAL_COUNT,
    TwoTaxonCountingInterval,
    _cover,
    _directed_float,
    fixed_two_taxon_counting_interval,
)

PROFILE = "three-two-measured-panel-joint-counting-region-v1"
Pair = tuple[float, float]
ExactPair = tuple[str, str]
Triple = tuple[float, float, float]
ExactTriple = tuple[str, str, str]
IndexTriple = tuple[int, int, int]
Attainment = tuple[bool, bool, bool]


@dataclass(frozen=True, slots=True)
class MeasuredPanelCountingCorner:
    """One exact closure vertex; an excluded pure-middle-taxon limit is marked."""

    shared_cover_ratio: str
    complete_only_pollen_probability: str
    cover: ExactTriple
    attained: bool


@dataclass(frozen=True, slots=True)
class MeasuredPanelCountingRegion:
    """Exact joint polygon constraints, closure vertices and coordinate envelopes."""

    confidence_level: float
    marginal_confidence_level: float
    guaranteed_joint_confidence_lower_bound: str
    complete_counts: tuple[int, int, int]
    partial_counts: tuple[int, int]
    complete_responses: Triple
    partial_responses: Pair
    shared_panel_constraints: tuple[SiteCountingSet, SiteCountingSet]
    complete_only_counting: TwoTaxonCountingInterval | None
    complete_only_probability_interval: Pair
    ratio_interval_exact: ExactPair
    status: Literal["empty", "nonempty"]
    corners: tuple[MeasuredPanelCountingCorner, ...]
    excluded_complete_only_vertex: bool
    cover_lower_exact: ExactTriple | None
    cover_upper_exact: ExactTriple | None
    cover_lower: Triple | None
    cover_upper: Triple | None
    lower_attained: Attainment | None
    upper_attained: Attainment | None
    lower_corner_indices: IndexTriple | None
    upper_corner_indices: IndexTriple | None
    no_count_information: bool
    numerical_certification: str = "directed-binomial-tails-exact-rational-polygon"
    profile: str = PROFILE


def _confidence(value: object) -> tuple[float, float, Fraction]:
    _require_unmasked(value, "confidence_level")
    raw = np.asarray(value)
    if raw.shape != () or raw.dtype.kind not in "iuf":
        raise ValidationError("Confidence level must be one finite number")
    requested = float(raw)
    if not isfinite(requested) or not 0 < requested < 1:
        raise ValidationError("Confidence level must lie strictly between zero and one")
    target = (2 + Fraction.from_float(requested)) / 3
    marginal = float(target)
    if Fraction.from_float(marginal) < target:
        marginal = nextafter(marginal, 1.0)
    if marginal >= 1:
        raise ValidationError(
            "Three-constraint marginal confidence is not representable below one",
            reason_code="counting_interval_conditioning",
        )
    return requested, marginal, 3 * Fraction.from_float(marginal) - 2


def _shared_constraint(
    counts: tuple[int, int], response: Pair, marginal: float
) -> SiteCountingSet:
    total = sum(counts)
    interval = (
        fixed_two_taxon_counting_interval(
            counts,
            response,
            (1.0, 1.0),
            taxon_measured=(True, True),
            confidence_level=marginal,
        )
        if total
        else None
    )
    pollen = (
        interval.pollen_probability_interval if interval is not None else (0.0, 1.0)
    )
    factors = (
        1 / Fraction.from_float(response[0]),
        1 / Fraction.from_float(response[1]),
    )
    low, high = (_cover(Fraction.from_float(p), factors) for p in pollen)
    return SiteCountingSet(
        counts, total, bool(total), pollen, (str(low), str(high)), interval
    )


def _corner(
    r: Fraction, q: Fraction, response: tuple[Fraction, Fraction, Fraction]
) -> MeasuredPanelCountingCorner:
    first, middle, last = response
    effective = first * r + last * (1 - r)
    denominator = middle * (1 - q) + q * effective
    cover = (
        middle * (1 - q) * r / denominator,
        q * effective / denominator,
        middle * (1 - q) * (1 - r) / denominator,
    )
    return MeasuredPanelCountingCorner(
        str(r), str(q), (str(cover[0]), str(cover[1]), str(cover[2])), q < 1
    )


def measured_panel_counting_region(
    complete_counts: object,
    partial_counts: object,
    complete_responses: object,
    partial_responses: object,
    *,
    complete_taxon_measured: object,
    partial_taxon_measured: object,
    confidence_level: float = 0.95,
) -> MeasuredPanelCountingRegion:
    """Return a joint region on a declared three-taxon relative-cover simplex.

    Complete vectors have axes (0,1,2); partial vectors contain only (0,2).
    Every supplied cell is measured. An unmeasured middle cell is never
    supplied or filled with zero. Counts follow a complete-panel multinomial
    and a partial-panel binomial at fixed full-panel efforts. Responses are
    the actual supplied positive binary64 values; no reclosure or PPE/kernel
    recomputation is performed. Geometry/PPE/chronology/model uncertainty,
    ecological calibration, data-selected eligibility and postselection
    coverage are outside this conditional model.

    Let r=v0/(v0+v2), q=a1*v1/(a0*v0+a1*v1+a2*v2). Conditional on the RANDOM
    complete-site N02, its taxon0 count is binomial with probability p0(r).
    CP coverage holds for every N02, hence unconditionally by averaging.
    The complete middle count is binomial at fixed N012; the partial count
    is binomial at fixed N02. Three marginal coverages m >= (2+C)/3 yield
    joint coverage >= 3*m - 2 >= C, without independence between constraints or
    sites. A zero-effort constraint is [0,1], with no tail calculation and
    the SAME three-constraint budget. Thus a random all-middle outcome does
    not trigger selection, refusal or a spurious measured zero. An entirely
    uninformative fixed design returns the whole declared parameter domain.

    Inverse-transform the shared pollen intervals and intersect to obtain
    R=[l,u]; Q=[a,b] is the complete middle-pollen interval. The EXACT joint
    set has x,y,z>=0, x+y+z=1, x+z>0, and four linear inequalities:
      (1-l)x-lz>=0; (1-u)x-uz<=0;
      a1(1-a)y>=a(a0*x+a2*z); a1(1-b)y<=b(a0*x+a2*z).
    Its closure is the convex hull of four rational corner images of R*Q.
    At q=1 the image is (0,1,0), excluded because the partial conditional
    distribution is undefined there. Coordinate envelopes are NOT the joint
    set: closure endpoints without any attained optimizing corner are only
    infima/suprema. Exact r=0/1 degeneracies retain attained zero coordinates.
    Empty shared intersections remain empty; no MLE containment or repair
    is imposed. Directed displays enclose exact Fraction bounds.

    Every full-panel total is at most 10000, the existing certified CP domain.
    Range/conditioning/work-budget failures refuse; no tolerance is used for
    region emptiness, corner comparison, domain membership or attainment.
    """
    for value, label in (
        (complete_counts, "complete_counts"),
        (partial_counts, "partial_counts"),
        (complete_responses, "complete_responses"),
        (partial_responses, "partial_responses"),
    ):
        _require_numeric_measurements(value, label)
        try:
            raw = np.asarray(value)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValidationError(
                f"{label} must contain native numeric values"
            ) from error
        if raw.dtype.kind not in "iuf":
            raise ValidationError(f"{label} must contain real native numeric values")
    n = vector(complete_counts, "complete_counts", nonnegative=True)
    k = vector(partial_counts, "partial_counts", nonnegative=True)
    a = vector(complete_responses, "complete_responses", positive=True)
    b = vector(partial_responses, "partial_responses", positive=True)
    if n.shape != (3,) or a.shape != n.shape or k.shape != (2,) or b.shape != k.shape:
        raise ValidationError(
            "Exactly one complete three-taxon and nested two-taxon panel required"
        )
    _measured(complete_taxon_measured, n.shape)
    _measured(partial_taxon_measured, k.shape)
    if any(
        np.any(row != np.floor(row))
        or np.any(row > MAX_TOTAL_COUNT)
        or row.sum() > MAX_TOTAL_COUNT
        for row in (n, k)
    ):
        raise ValidationError(
            "Full measured-panel totals must be bounded nonnegative integers"
        )
    requested, marginal, guarantee = _confidence(confidence_level)
    nc = (int(n[0]), int(n[1]), int(n[2]))
    npart = (int(k[0]), int(k[1]))
    ac = (float(a[0]), float(a[1]), float(a[2]))
    apart = (float(b[0]), float(b[1]))
    sites = (
        _shared_constraint((nc[0], nc[2]), (ac[0], ac[2]), marginal),
        _shared_constraint(npart, apart, marginal),
    )
    middle_counting = (
        fixed_two_taxon_counting_interval(
            (nc[1], nc[0] + nc[2]),
            (1.0, 1.0),
            (1.0, 1.0),
            taxon_measured=(True, True),
            confidence_level=marginal,
        )
        if sum(nc)
        else None
    )
    q = (
        middle_counting.pollen_probability_interval
        if middle_counting is not None
        else (0.0, 1.0)
    )
    limits = [tuple(map(Fraction, site.first_cover_interval_exact)) for site in sites]
    lower, upper = max(v[0] for v in limits), min(v[1] for v in limits)
    corners: tuple[MeasuredPanelCountingCorner, ...] = ()
    low_exact: ExactTriple | None = None
    high_exact: ExactTriple | None = None
    low_display: Triple | None = None
    high_display: Triple | None = None
    low_attained: Attainment | None = None
    high_attained: Attainment | None = None
    low_indices: IndexTriple | None = None
    high_indices: IndexTriple | None = None
    if lower <= upper:
        response = (
            Fraction.from_float(ac[0]),
            Fraction.from_float(ac[1]),
            Fraction.from_float(ac[2]),
        )
        corners = tuple(
            _corner(r, Fraction.from_float(probability), response)
            for r, probability in (
                (lower, q[0]),
                (upper, q[0]),
                (upper, q[1]),
                (lower, q[1]),
            )
        )
        values = [tuple(map(Fraction, corner.cover)) for corner in corners]
        lows = tuple(min(v[i] for v in values) for i in range(3))
        highs = tuple(max(v[i] for v in values) for i in range(3))

        def witnesses(bounds: tuple[Fraction, ...]) -> IndexTriple:
            chosen = [
                min(
                    (j for j, v in enumerate(values) if v[i] == value),
                    key=lambda j: (not corners[j].attained, j),
                )
                for i, value in enumerate(bounds)
            ]
            return chosen[0], chosen[1], chosen[2]

        low_indices, high_indices = witnesses(lows), witnesses(highs)
        low_exact = (str(lows[0]), str(lows[1]), str(lows[2]))
        high_exact = (str(highs[0]), str(highs[1]), str(highs[2]))
        low_display = (
            _directed_float(lows[0], upper=False),
            _directed_float(lows[1], upper=False),
            _directed_float(lows[2], upper=False),
        )
        high_display = (
            _directed_float(highs[0], upper=True),
            _directed_float(highs[1], upper=True),
            _directed_float(highs[2], upper=True),
        )
        low_attained = (
            corners[low_indices[0]].attained,
            corners[low_indices[1]].attained,
            corners[low_indices[2]].attained,
        )
        high_attained = (
            corners[high_indices[0]].attained,
            corners[high_indices[1]].attained,
            corners[high_indices[2]].attained,
        )
    return MeasuredPanelCountingRegion(
        requested,
        marginal,
        str(guarantee),
        nc,
        npart,
        ac,
        apart,
        sites,
        middle_counting,
        q,
        (str(lower), str(upper)),
        "nonempty" if lower <= upper else "empty",
        corners,
        bool(corners) and q[1] == 1,
        low_exact,
        high_exact,
        low_display,
        high_display,
        low_attained,
        high_attained,
        low_indices,
        high_indices,
        sum(nc) + sum(npart) == 0,
    )
