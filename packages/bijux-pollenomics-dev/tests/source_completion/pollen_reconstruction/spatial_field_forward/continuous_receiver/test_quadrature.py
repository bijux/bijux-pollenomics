"""Actual Simpson error widths, deterministic partition and refusal controls."""

from __future__ import annotations

from fractions import Fraction

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.arithmetic import (
    Jet,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.quadrature import (
    ResourceRefusal,
    WorkBudget,
    integrate,
    simpson_panel,
)


def test_quartic_simpson_error_is_a_radius_not_a_full_width() -> None:
    panel = simpson_panel(
        lambda x: x[0] ** 4, ((Fraction(0), Fraction(1)),), WorkBudget()
    )
    assert panel.error_radius >= Fraction(1, 120)
    assert panel.enclosure.width >= Fraction(1, 60)
    assert panel.enclosure.lower <= Fraction(1, 5) <= panel.enclosure.upper
    assert panel.node_sum.lower <= Fraction(5, 24) <= panel.node_sum.upper


def test_tensor_error_has_two_directional_radii_without_a_mixed_term() -> None:
    panel = simpson_panel(
        lambda x: x[0] ** 4 + x[1] ** 4, ((Fraction(0), Fraction(1)),) * 2, WorkBudget()
    )
    assert panel.error_radius >= Fraction(1, 60)
    assert panel.enclosure.lower <= Fraction(2, 5) <= panel.enclosure.upper
    assert panel.enclosure.width >= Fraction(1, 30)


def test_exact_cubic_closes_and_quartic_partition_covers_without_gaps() -> None:
    cubic = integrate(lambda x: x[0] ** 3, 1, Fraction(1, 10**9), WorkBudget())
    assert cubic.status == "certified_width"
    assert cubic.enclosure.lower <= Fraction(1, 4) <= cubic.enclosure.upper
    budget = WorkBudget(max_leaves=16)
    result = integrate(lambda x: x[0] ** 4, 1, Fraction(1, 10**6), budget)
    assert result.status == "certified_width"
    boxes = sorted(panel.box[0] for panel in result.panels)
    assert boxes[0][0] == 0 and boxes[-1][1] == 1
    assert all(
        left[1] == right[0] for left, right in zip(boxes[:-1], boxes[1:], strict=True)
    )
    assert result.enclosure.lower <= Fraction(1, 5) <= result.enclosure.upper


def test_finite_refusal_retains_complete_parent_certificate() -> None:
    budget = WorkBudget(max_attempts=2)
    result = integrate(lambda x: x[0] ** 4, 1, Fraction(1, 10**20), budget)
    assert result.status == "refuse_unresolved"
    assert result.refusal == "attempt_or_node_ceiling"
    assert len(result.panels) == 1
    assert result.panels[0].box == ((Fraction(0), Fraction(1)),)
    assert result.enclosure.lower <= Fraction(1, 5) <= result.enclosure.upper
    assert budget.attempts == 2 and budget.nodes == 6


def test_declared_limits_cannot_be_raised() -> None:
    with pytest.raises(ValueError, match="ceilings"):
        WorkBudget(max_leaves=4097)
    budget = WorkBudget(max_nodes=1)
    with pytest.raises(ResourceRefusal, match="ceiling"):
        simpson_panel(
            lambda x: Jet.constant(1, x[0].order), ((Fraction(0), Fraction(1)),), budget
        )
