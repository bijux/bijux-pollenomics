"""Whole-cell conservative aggregation and explicitly matched modeled comparisons."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import fsum, isfinite

from ..quarantine import IntakeRefusal
from .grid import Bounds
from .models import DeclaredGridLayer
from .time import TimeSupport


@dataclass(frozen=True)
class LandUseAggregate:
    """Both full land support and retained-data denominator accompany each value."""

    source_sha256: str
    target: Bounds
    time_support: TimeSupport
    category_key: str
    scenario: str
    quantity: str
    value_units: str
    total_units: str
    full_land_area_km2: float
    observed_land_area_km2: float
    missing_land_area_km2: float
    source_cell_count: int
    observed_cell_count: int
    total: float | None
    value: float | None
    evidence_role: str = field(default="modeled_comparison_only", init=False)
    public_release_allowed: bool = field(default=False, init=False)


@dataclass(frozen=True)
class ModeledComparison:
    """Difference on the common mask, alongside each input's full available support."""

    left_common: LandUseAggregate
    right_common: LandUseAggregate
    left_available: LandUseAggregate
    right_available: LandUseAggregate
    class_match_reference: str
    category_key: str
    scenarios: tuple[str, str]
    value_difference: float
    total_difference: float
    independent_observation_truth: bool = field(default=False, init=False)
    public_release_allowed: bool = field(default=False, init=False)


def _selected_cells(
    layer: DeclaredGridLayer, target: Bounds
) -> tuple[tuple[int, float], ...]:
    if not layer.grid.bounds.contains(target):
        raise IntakeRefusal("hyde_target_outside_grid", repr(target))
    selected = []
    for index in range(len(layer.values)):
        row, column = divmod(index, layer.grid.columns)
        cell = layer.grid.cell_bounds(row, column)
        if not cell.overlaps(target):
            continue
        if not target.contains(cell):
            raise IntakeRefusal(
                "hyde_partial_cell_transfer_requires_land_overlay", str(index)
            )
        selected.append((index, cell.area_km2 * layer.land_fractions[index]))
    return tuple(selected)


def aggregate_layer(layer: DeclaredGridLayer, target: Bounds) -> LandUseAggregate:
    """Sum extensive quantities; land-area-weight fractions over observed support."""
    return _aggregate(layer, target, None)


def _aggregate(
    layer: DeclaredGridLayer, target: Bounds, common_mask: frozenset[int] | None
) -> LandUseAggregate:
    selected = _selected_cells(layer, target)
    observed = [
        (index, area)
        for index, area in selected
        if layer.values[index] is not None
        and (common_mask is None or index in common_mask)
    ]
    full_area = fsum(area for _, area in selected)
    observed_area = fsum(area for _, area in observed)
    contributions = []
    for index, area in observed:
        value = layer.values[index]
        assert value is not None
        contributions.append(
            value * area if layer.variable.quantity == "land_fraction" else value
        )
    try:
        total = fsum(contributions) if observed_area > 0 else None
    except OverflowError as exc:
        raise IntakeRefusal(
            "hyde_aggregate_non_finite", layer.variable.quantity
        ) from exc
    if total is not None and not isfinite(total):
        raise IntakeRefusal("hyde_aggregate_non_finite", layer.variable.quantity)
    raw_contributions = [layer.source_values[index] for index, _ in observed]
    if layer.variable.quantity == "population" and all(
        type(value) is int for value in raw_contributions
    ):
        exact_total = sum(
            value for value in raw_contributions if isinstance(value, int)
        )
        if total is not None and total != exact_total:
            raise IntakeRefusal(
                "hyde_population_precision_loss",
                "Aggregate integer total cannot be represented exactly",
            )
    value = total
    if layer.variable.quantity == "land_fraction" and total is not None:
        value = total / observed_area
    return LandUseAggregate(
        source_sha256=layer.interchange_sha256,
        target=target,
        time_support=layer.time,
        category_key=layer.variable.category_key,
        scenario=layer.variable.scenario,
        quantity=layer.variable.quantity,
        value_units=layer.variable.units,
        total_units="km2"
        if layer.variable.quantity == "land_fraction"
        else layer.variable.units,
        full_land_area_km2=full_area,
        observed_land_area_km2=observed_area,
        missing_land_area_km2=fsum(
            area
            for index, area in selected
            if layer.values[index] is None
            or (common_mask is not None and index not in common_mask)
        ),
        source_cell_count=len(selected),
        observed_cell_count=len(observed),
        total=total,
        value=value,
    )


def compare_layers(
    left: DeclaredGridLayer,
    right: DeclaredGridLayer,
    target: Bounds,
    *,
    class_match_reference: str,
) -> ModeledComparison:
    """Compare exact time/category support without inventing a vegetation-truth label.

    The caller must supply a governed class-match reference. This reference is
    recorded, not treated as proof of a scientist's approval or source admission.
    """
    if not isinstance(class_match_reference, str) or not class_match_reference.strip():
        raise IntakeRefusal(
            "hyde_class_match_reference_required", "No implicit vegetation mapping"
        )
    if left.grid != right.grid or left.land_fractions != right.land_fractions:
        raise IntakeRefusal(
            "hyde_comparison_grid_or_land_mask_mismatch",
            "Conservative alignment is required",
        )
    if left.time != right.time:
        raise IntakeRefusal(
            "hyde_comparison_time_support_mismatch",
            "No implicit temporal interpolation",
        )
    if (left.variable.category_key, left.variable.quantity, left.variable.units) != (
        right.variable.category_key,
        right.variable.quantity,
        right.variable.units,
    ):
        raise IntakeRefusal(
            "hyde_comparison_class_or_quantity_mismatch",
            "No automatic category conversion",
        )
    mask = frozenset(
        index
        for index, (a, b) in enumerate(zip(left.values, right.values, strict=True))
        if a is not None and b is not None
    )
    left_common, right_common = (
        _aggregate(left, target, mask),
        _aggregate(right, target, mask),
    )
    if (
        left_common.value is None
        or right_common.value is None
        or left_common.total is None
        or right_common.total is None
    ):
        raise IntakeRefusal("hyde_no_common_observed_land_support", repr(target))
    return ModeledComparison(
        left_common=left_common,
        right_common=right_common,
        left_available=aggregate_layer(left, target),
        right_available=aggregate_layer(right, target),
        class_match_reference=class_match_reference,
        category_key=left.variable.category_key,
        scenarios=(left.variable.scenario, right.variable.scenario),
        value_difference=left_common.value - right_common.value,
        total_difference=left_common.total - right_common.total,
    )
