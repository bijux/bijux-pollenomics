"""Exact per-bin pooled-fraction bounds under optional sample membership."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction


@dataclass(frozen=True, slots=True)
class IntervalFractionBounds:
    """Conditional outer extrema, independent of age probabilities or other bins."""

    lower: Fraction | None
    upper: Fraction | None
    empty_bin_possible: bool


def interval_bin_membership(
    younger: Decimal,
    older: Decimal,
    bin_younger: Decimal,
    bin_older: Decimal,
) -> str:
    """Classify a closed marginal age interval against a half-open time bin.

    The source interval [younger, older] is treated as its possible-age set,
    not as a uniform distribution or guaranteed joint confidence region.
    """
    values = (younger, older, bin_younger, bin_older)
    if any(not isinstance(value, Decimal) or not value.is_finite() for value in values):
        raise ValueError("Finite Decimal age endpoints are required")
    if younger > older or bin_younger >= bin_older:
        raise ValueError("Age intervals and time bins must be ordered")
    if older < bin_younger or younger >= bin_older:
        return "outside"
    if younger >= bin_younger and older < bin_older:
        return "mandatory"
    return "optional"


def _counts(numerator: int, denominator: int, *, allow_empty: bool) -> None:
    if (
        type(numerator) is not int
        or type(denominator) is not int
        or numerator < 0
        or denominator < 0
        or numerator > denominator
        or (not allow_empty and denominator == 0)
    ):
        raise ValueError("Exact integer counts require 0 <= numerator <= denominator")


def pooled_fraction_outer_bounds(
    mandatory_numerator: int,
    mandatory_denominator: int,
    optional_counts: Sequence[tuple[int, int]],
) -> IntervalFractionBounds:
    """Bound a pooled count fraction over every subset of optional samples.

    All counts are exact integers, with positive optional denominators. The
    extrema occur among prefixes ordered by each optional sample's fraction,
    ascending for the minimum and descending for the maximum. An optimum's
    included samples cannot lie on the worse side of its resulting fraction;
    sorting therefore supplies an extremizing threshold without enumeration.
    Fraction arithmetic retains exact ordering and avoids overflow/rounding.

    Empty allocations are excluded from numerical extrema but reported. With
    no possible positive mass, both extrema are None. Membership choices are
    independent within this bin; depth monotonicity and joint cross-bin ages
    are omitted. These are outer bounds, not joint confidence intervals or
    vegetation/taxon-cover estimates. The caller binds the source rows, age
    interval meaning, eligible counts and the numerator's biological definition.
    """
    _counts(mandatory_numerator, mandatory_denominator, allow_empty=True)
    optional = list(optional_counts)
    for numerator, denominator in optional:
        _counts(numerator, denominator, allow_empty=False)
    candidates: list[Fraction] = []
    if mandatory_denominator:
        candidates.append(Fraction(mandatory_numerator, mandatory_denominator))
    ordered = sorted(optional, key=lambda row: Fraction(*row))
    for rows in (ordered, list(reversed(ordered))):
        numerator, denominator = mandatory_numerator, mandatory_denominator
        for sample_numerator, sample_denominator in rows:
            numerator += sample_numerator
            denominator += sample_denominator
            candidates.append(Fraction(numerator, denominator))
    return IntervalFractionBounds(
        min(candidates) if candidates else None,
        max(candidates) if candidates else None,
        mandatory_denominator == 0,
    )
