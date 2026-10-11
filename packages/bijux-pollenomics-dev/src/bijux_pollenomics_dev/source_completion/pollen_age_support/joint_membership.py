"""Exact joint attainability of marginal pooled-count fraction extrema."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from itertools import product
from typing import Literal

from .interval_fraction import interval_bin_membership, pooled_fraction_outer_bounds

BoundSide = Literal["lower", "upper"]
RefusalReason = Literal["forced_into_distinct_bins", "no_supported_age_location"]


def _identity(value: str, label: str) -> None:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{label} must be an exact nonempty identity")


def _finite(value: Decimal, label: str) -> None:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError(f"{label} must be a finite Decimal")


@dataclass(frozen=True, slots=True)
class MarginalAgeCountSample:
    """Native marginal age support and one explicitly defined count fraction.

    Native negative bounds may remain as source evidence. They are not admitted
    canonical dates. The caller supplies the numerator's biological meaning.
    """

    sample_id: str
    younger_cal_bp: Decimal
    older_cal_bp: Decimal
    numerator_count: int
    denominator_count: int

    def __post_init__(self) -> None:
        """Validate native age support and exact positive-denominator counts."""
        _identity(self.sample_id, "sample_id")
        _finite(self.younger_cal_bp, "younger_cal_bp")
        _finite(self.older_cal_bp, "older_cal_bp")
        if self.younger_cal_bp > self.older_cal_bp:
            raise ValueError("Native marginal age bounds must be ordered")
        if (
            type(self.numerator_count) is not int
            or type(self.denominator_count) is not int
            or not 0 <= self.numerator_count <= self.denominator_count
            or self.denominator_count <= 0
        ):
            raise ValueError("Exact counts require 0 <= numerator <= denominator > 0")

    @property
    def count_fraction(self) -> Fraction:
        """Return the exact observed count fraction, without a pseudocount."""
        return Fraction(self.numerator_count, self.denominator_count)


@dataclass(frozen=True, slots=True)
class AgeBin:
    """One nonnegative half-open analysis bin; adjacent bins remain disjoint."""

    bin_id: str
    younger_cal_bp: Decimal
    older_cal_bp_exclusive: Decimal

    def __post_init__(self) -> None:
        """Validate the named nonnegative half-open analysis interval."""
        _identity(self.bin_id, "bin_id")
        _finite(self.younger_cal_bp, "bin_younger_cal_bp")
        _finite(self.older_cal_bp_exclusive, "bin_older_cal_bp_exclusive")
        if not Decimal(0) <= self.younger_cal_bp < self.older_cal_bp_exclusive:
            raise ValueError("Analysis bins require nonnegative ordered endpoints")

    def contains(self, age: Decimal) -> bool:
        """Test half-open membership without rounding the source age."""
        return self.younger_cal_bp <= age < self.older_cal_bp_exclusive


@dataclass(frozen=True, slots=True)
class MarginalFractionBounds:
    """Individually attainable extrema, conditional on marginal age support."""

    bin_id: str
    lower: Fraction
    upper: Fraction


@dataclass(frozen=True, slots=True)
class FractionBoundTarget:
    """One requested marginal extremum in a joint corner."""

    bin_id: str
    side: BoundSide
    value: Fraction


@dataclass(frozen=True, slots=True)
class SampleAllocationRefusal:
    """A source sample that cannot satisfy the necessary extremum memberships."""

    sample_id: str
    reason: RefusalReason
    required_bins: tuple[str, ...]
    excluded_bins: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SourceAgeAssignment:
    """A constructive possible source age, never a reestimated chronology."""

    sample_id: str
    bin_id: str | None
    source_native_age: Decimal


@dataclass(frozen=True, slots=True)
class JointExtremaCorner:
    """Exact joint feasibility and either source refusals or a constructive witness."""

    targets: tuple[FractionBoundTarget, ...]
    refusals: tuple[SampleAllocationRefusal, ...]
    assignments: tuple[SourceAgeAssignment, ...]

    @property
    def attainable(self) -> bool:
        """Return whether one independent source-age choice per sample suffices."""
        return not self.refusals


@dataclass(frozen=True, slots=True)
class JointExtremaAssessment:
    """Conditional count-fraction corners, excluding probabilities and depth coupling."""

    marginal_bounds: tuple[MarginalFractionBounds, ...]
    corners: tuple[JointExtremaCorner, ...]


def _membership(sample: MarginalAgeCountSample, bin_: AgeBin) -> str:
    return interval_bin_membership(
        sample.younger_cal_bp,
        sample.older_cal_bp,
        bin_.younger_cal_bp,
        bin_.older_cal_bp_exclusive,
    )


def _outside_age(
    sample: MarginalAgeCountSample, bins: Sequence[AgeBin]
) -> Decimal | None:
    candidates = {sample.younger_cal_bp, sample.older_cal_bp}
    candidates.update(bin_.older_cal_bp_exclusive for bin_ in bins)
    return next(
        (
            age
            for age in sorted(candidates)
            if sample.younger_cal_bp <= age <= sample.older_cal_bp
            and not any(bin_.contains(age) for bin_ in bins)
        ),
        None,
    )


def assess_joint_extrema(
    samples: Sequence[MarginalAgeCountSample], bins: Sequence[AgeBin]
) -> JointExtremaAssessment:
    """Assess every marginal lower/upper corner with one age per sample.

    Each bin must have positive mandatory mass. At a minimum, every optional
    sample below the resulting fraction is included and every sample above it
    is excluded; maxima reverse those inequalities. Equal fractions are free.
    These conditions are necessary by the one-sample add/remove argument and
    sufficient because neutral changes preserve the exact fraction. With no
    depth or probabilistic coupling, joint feasibility is therefore precisely
    nonempty source-age domains after those conditions. Positive mandatory
    mass prevents empty-bin ambiguities. Original marginal bounds stay valid.

    This does not calculate a joint confidence region, vegetation fraction,
    calibrated chronology, monotone age model, or ecological admission.
    """
    if not samples or not bins:
        raise ValueError("Samples and analysis bins must be nonempty")
    if len({sample.sample_id for sample in samples}) != len(samples):
        raise ValueError("Source sample identities must be unique")
    if len({bin_.bin_id for bin_ in bins}) != len(bins):
        raise ValueError("Analysis bin identities must be unique")
    ordered_bins = sorted(bins, key=lambda bin_: bin_.younger_cal_bp)
    if any(
        left.older_cal_bp_exclusive > right.younger_cal_bp
        for left, right in zip(ordered_bins, ordered_bins[1:], strict=False)
    ):
        raise ValueError("Half-open analysis bins must be disjoint")
    bounds: list[MarginalFractionBounds] = []
    for bin_ in ordered_bins:
        mandatory = [s for s in samples if _membership(s, bin_) == "mandatory"]
        optional = [s for s in samples if _membership(s, bin_) == "optional"]
        denominator = sum(s.denominator_count for s in mandatory)
        if denominator == 0:
            raise ValueError(
                "Joint extrema require positive mandatory mass in every bin"
            )
        limits = pooled_fraction_outer_bounds(
            sum(s.numerator_count for s in mandatory),
            denominator,
            [(s.numerator_count, s.denominator_count) for s in optional],
        )
        if limits.lower is None or limits.upper is None or limits.empty_bin_possible:
            raise ValueError("Mandatory count-fraction bounds must be nonempty")
        bounds.append(MarginalFractionBounds(bin_.bin_id, limits.lower, limits.upper))
    sides: tuple[BoundSide, BoundSide] = ("lower", "upper")
    corners: list[JointExtremaCorner] = []
    for choice in product(sides, repeat=len(ordered_bins)):
        targets = tuple(
            FractionBoundTarget(
                bound.bin_id, side, bound.lower if side == "lower" else bound.upper
            )
            for bound, side in zip(bounds, choice, strict=True)
        )
        refusals: list[SampleAllocationRefusal] = []
        assignments: list[SourceAgeAssignment] = []
        for sample in sorted(samples, key=lambda sample: sample.sample_id):
            required: set[str] = set()
            excluded: set[str] = set()
            possible: list[AgeBin] = []
            for bin_, target in zip(ordered_bins, targets, strict=True):
                membership = _membership(sample, bin_)
                if membership == "outside":
                    continue
                possible.append(bin_)
                extremum_requires = (
                    sample.count_fraction < target.value
                    if target.side == "lower"
                    else sample.count_fraction > target.value
                )
                if membership == "mandatory" or extremum_requires:
                    required.add(bin_.bin_id)
                elif sample.count_fraction != target.value:
                    excluded.add(bin_.bin_id)
            if len(required) > 1:
                refusals.append(
                    SampleAllocationRefusal(
                        sample.sample_id,
                        "forced_into_distinct_bins",
                        tuple(sorted(required)),
                        tuple(sorted(excluded)),
                    )
                )
                continue
            selected = next(
                (
                    bin_
                    for bin_ in possible
                    if bin_.bin_id not in excluded
                    and (not required or bin_.bin_id in required)
                ),
                None,
            )
            outside = _outside_age(sample, ordered_bins) if not required else None
            if selected is None and outside is None:
                refusals.append(
                    SampleAllocationRefusal(
                        sample.sample_id,
                        "no_supported_age_location",
                        tuple(sorted(required)),
                        tuple(sorted(excluded)),
                    )
                )
            else:
                age = (
                    max(sample.younger_cal_bp, selected.younger_cal_bp)
                    if selected is not None
                    else outside
                )
                if age is None:
                    raise ValueError("Constructive native-age witness is absent")
                assignments.append(
                    SourceAgeAssignment(
                        sample.sample_id,
                        selected.bin_id if selected is not None else None,
                        age,
                    )
                )
        corners.append(
            JointExtremaCorner(
                targets, tuple(refusals), () if refusals else tuple(assignments)
            )
        )
    return JointExtremaAssessment(tuple(bounds), tuple(corners))
