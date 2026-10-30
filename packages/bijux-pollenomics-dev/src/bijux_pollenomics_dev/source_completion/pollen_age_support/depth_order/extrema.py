"""Optional depth-order restriction of existing marginal count-fraction corners."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from ..interval_fraction import interval_bin_membership
from ..joint_membership import (
    AgeBin,
    JointExtremaAssessment,
    JointExtremaCorner,
    MarginalAgeCountSample,
    assess_joint_extrema,
)
from .domains import (
    AgeComponent,
    AgeOrderAssessment,
    DepthAgeDomain,
    assess_age_order,
    finite,
)


@dataclass(frozen=True, slots=True)
class DepthCountSample:
    """Keep the existing sample/count/age identity paired to one native depth."""

    sample: MarginalAgeCountSample
    depth: Decimal

    def __post_init__(self) -> None:
        """Require an existing marginal sample and finite native depth."""
        if not isinstance(self.sample, MarginalAgeCountSample):
            raise ValueError("An existing exact marginal sample is required")
        finite(self.depth)


@dataclass(frozen=True, slots=True)
class DepthOrderedCorner:
    """Original marginal corner, with an additional optional age-order decision."""

    independent_corner: JointExtremaCorner
    age_order: AgeOrderAssessment | None

    @property
    def attainable(self) -> bool:
        """Keep every original refusal; ordering can only restrict feasibility."""
        return (
            self.independent_corner.attainable
            and self.age_order is not None
            and self.age_order.attainable
        )


@dataclass(frozen=True, slots=True)
class DepthOrderedExtrema:
    """Unchanged marginal extrema and explicitly conditional order diagnostics."""

    independent: JointExtremaAssessment
    native_interval_order: AgeOrderAssessment
    corners: tuple[DepthOrderedCorner, ...]


def _corner_domain(
    row: DepthCountSample, bins: Sequence[AgeBin], corner: JointExtremaCorner
) -> DepthAgeDomain:
    sample = row.sample
    by_id = {bin_.bin_id: bin_ for bin_ in bins}
    required: set[str] = set()
    excluded: set[str] = set()
    for target in corner.targets:
        bin_ = by_id[target.bin_id]
        membership = interval_bin_membership(
            sample.younger_cal_bp,
            sample.older_cal_bp,
            bin_.younger_cal_bp,
            bin_.older_cal_bp_exclusive,
        )
        if membership == "outside":
            continue
        favorable = (
            sample.count_fraction < target.value
            if target.side == "lower"
            else sample.count_fraction > target.value
        )
        if membership == "mandatory" or favorable:
            required.add(bin_.bin_id)
        elif sample.count_fraction != target.value:
            excluded.add(bin_.bin_id)

    def allowed(age: Decimal) -> bool:
        where = next((bin_.bin_id for bin_ in bins if bin_.contains(age)), None)
        return where not in excluded and (not required or where in required)

    cuts = {sample.younger_cal_bp, sample.older_cal_bp}
    cuts.update(
        value
        for bin_ in bins
        for value in (bin_.younger_cal_bp, bin_.older_cal_bp_exclusive)
        if sample.younger_cal_bp <= value <= sample.older_cal_bp
    )
    ordered = sorted(cuts)
    parts = [
        AgeComponent(left, right, False)
        for left, right in zip(ordered, ordered[1:], strict=False)
        if allowed(left)
    ]
    if allowed(ordered[-1]):
        parts.append(AgeComponent(ordered[-1], ordered[-1]))
    return DepthAgeDomain(sample.sample_id, row.depth, tuple(parts))


def assess_depth_ordered_extrema(
    samples: Sequence[DepthCountSample], bins: Sequence[AgeBin], *, core_id: str
) -> DepthOrderedExtrema:
    """Apply a declared depth-order model without changing the independent API.

    Original marginal bounds and independent refusals remain exact. For an
    independently attainable corner, threshold conditions require favorable
    optional samples, exclude unfavorable samples, and leave equal fractions
    free. Intersect those memberships with the native closed age interval as
    disjoint components; solve their nondecreasing feasibility. The extrema
    are not recomputed under order, and these are not probability intervals.
    """
    independent = assess_joint_extrema([row.sample for row in samples], bins)
    native = assess_age_order(
        [
            DepthAgeDomain(
                row.sample.sample_id,
                row.depth,
                (AgeComponent(row.sample.younger_cal_bp, row.sample.older_cal_bp),),
            )
            for row in samples
        ],
        core_id=core_id,
    )
    corners = tuple(
        DepthOrderedCorner(
            corner,
            assess_age_order(
                [_corner_domain(row, bins, corner) for row in samples], core_id=core_id
            )
            if corner.attainable
            else None,
        )
        for corner in independent.corners
    )
    return DepthOrderedExtrema(independent, native, corners)
