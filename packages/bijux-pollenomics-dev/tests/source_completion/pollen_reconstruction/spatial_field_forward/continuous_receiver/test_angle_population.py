"""Opt-in one-dimensional work, complete dispositions and original-law assembly."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction as F

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.angle_moments.certificates import (
    certificate,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.angle_moments.population import (
    enclose_population,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.arithmetic import (
    Interval,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.kernel import (
    Geometry,
)


def model(outer: int = 4) -> Geometry:
    return Geometry(F(1, 2), F(1), F(outer), (F(1000), F(0)), (F(2000), F(0)))


def test_actual_initial_forest_keeps_finite_series_and_one_global_tail() -> None:
    population = enclose_population((model(),), max_leaves=5)
    result = population.results[0]
    assert result is not None
    assert population.refusals == ("leaf_ceiling",)
    assert result.status == "refuse_unresolved"
    assert len(result.integrals) == 5
    assert all(len(leaf.box) == 1 for row in result.integrals for leaf in row.panels)
    budget = population.budgets[0]
    assert budget.attempts == budget.leaves == budget.derivative_boxes == 5
    assert budget.nodes == budget.completed_nodes == 35
    finite = sum((row.enclosure for row in result.integrals[2:]), Interval.point(0))
    assert result.finite_radial_sum == finite
    assert result.radial_sum == finite.expanded(
        result.partition.contraction.remainder_radius
    )
    assert result.second == result.homogeneous - result.first
    saved = certificate(result)
    assert saved["method"] == "receiver-angle-moments.v1"
    assert len(saved["radial_domains"]) == 3  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="whole J exactly once"):
        replace(result, radial_sum=finite)
    with pytest.raises(ValueError, match="epsilon"):
        replace(result, status="certified_width")


def test_incomplete_initial_owner_is_retained_with_no_false_certificate() -> None:
    population = enclose_population((model(), model()), max_leaves=4)
    assert population.results == (None, None)
    assert population.refusals == ("initial_coverage_incomplete:leaf_ceiling",) * 2
    assert all(row.leaves == 4 and row.attempts == 4 for row in population.budgets)


def test_narrow_cap_domain_refusal_belongs_only_to_opt_in_method() -> None:
    geometry = model(3)  # Original Geometry deliberately still admits L=3R.
    population = enclose_population((geometry,))
    assert population.results == (None,)
    assert population.refusals[0] is not None
    assert population.refusals[0].startswith("angle_method_domain:")
    assert population.budgets[0].attempts == 0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"wall_seconds": 161},
        {"max_leaves": 4097},
        {"max_attempts": 8192},
        {"max_nodes": 73720},
        {"max_queue": 4097},
    ],
)
def test_original_resource_ceiling_cannot_be_enlarged(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        enclose_population((model(),), **kwargs)
