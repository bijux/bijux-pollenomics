"""Population coverage, final-width stopping and non-resetting work boundaries."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import FrozenInstanceError
from fractions import Fraction
import inspect
from types import SimpleNamespace
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver import (
    population,
    quadrature,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.arithmetic import (
    Interval,
    Jet,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.coefficients import (
    EPSILON,
    Q_WIDTH,
    assemble_coefficients,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.kernel import (
    Geometry,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.population import (
    enclose_population,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.quadrature import (
    SEVEN_NODE_RULE,
    Box,
    IntegralResult,
    Integrand,
    Panel,
    WorkBudget,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.radial_partition import (
    RadialDomain,
    RadialPartition,
)

UNIT = ((Fraction(0), Fraction(1)),)


def model(index: int = 0, outer: int = 2) -> Geometry:
    return Geometry(
        Fraction(index),
        Fraction(1),
        Fraction(outer),
        (Fraction(-1), Fraction(0)),
        (Fraction(1), Fraction(0)),
    )


def controlled_panels(
    monkeypatch: pytest.MonkeyPatch,
    radii: dict[tuple[int, int], Fraction] | None = None,
    clock: list[float] | None = None,
) -> list[tuple[int, int, Box]]:
    """Conservative constant-function panels expose scheduling independently of cost."""
    monkeypatch.setattr(
        Geometry,
        "contact_survival",
        lambda self, t: Jet.constant(100 * self.coefficient + 1, t.order),
    )
    monkeypatch.setattr(
        Geometry,
        "outer_survival",
        lambda self, t: Jet.constant(100 * self.coefficient + 2, t.order),
    )
    monkeypatch.setattr(
        RadialDomain,
        "evaluate",
        lambda self, args: Jet.constant(
            100 * self.band.geometry.coefficient
            + (self.patch or self.band.index + 2)
            + 2,
            args[0].order,
        ),
    )
    events: list[tuple[int, int, Box]] = []

    def panel(function: Integrand, box: Box, budget: WorkBudget, *, rule: str) -> Panel:
        assert rule == SEVEN_NODE_RULE
        budget.panel(len(box), nodes_per_axis=7)
        value = function(tuple(Jet.constant(0, 0) for _ in box)).value.lower
        case, role = divmod(int(value), 100)
        events.append((case, role, box))
        volume = Fraction(1)
        for lower, upper in box:
            volume *= upper - lower
        radius = (
            Fraction(1) if radii is None else radii.get((case, role), Fraction(0))
        ) * volume**2
        budget.completed_nodes += 7 ** len(box)
        if clock is not None:
            clock[0] += 0.4
            budget.check()
        return Panel(
            box,
            Interval.point(value * volume),
            radius,
            (radius / len(box),) * len(box),
            rule,
        )

    monkeypatch.setattr(population, "positive_panel", panel)
    return events


def test_actual_degree_seven_primitive_and_native_constant_anchor_symmetry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Geometry, "contact_survival", lambda self, t: t**7)
    monkeypatch.setattr(Geometry, "outer_survival", lambda self, t: t**7)
    monkeypatch.setattr(
        RadialDomain, "evaluate", lambda self, args: Jet.constant(0, args[0].order)
    )
    result = enclose_population((model(), model(1)))
    assert result.refusals == (None, None)
    for row, budget in zip(result.results, result.budgets, strict=True):
        assert row is not None and row.status == "certified_width"
        assert (
            row.integrals[0].enclosure.lower
            <= Fraction(1, 8)
            <= row.integrals[0].enclosure.upper
        )
        assert all(
            value.lower <= 0 <= value.upper
            for value in (row.homogeneous, row.first, row.second)
        )
        assert budget.attempts == 4 and budget.nodes == budget.completed_nodes == 112
    with pytest.raises(FrozenInstanceError):
        result.__setattr__("results", ())


def test_exact_zero_attenuation_symmetry_has_zero_coefficients() -> None:
    geometry = model()
    partition = RadialPartition.build(geometry)
    integrals = tuple(
        IntegralResult(
            Interval.point(value), (), "certified_width", None, SEVEN_NODE_RULE
        )
        for value in (1, 1, 0, 0)
    )
    result = assemble_coefficients(
        geometry,
        integrals,
        rule=SEVEN_NODE_RULE,
        conditioning=partition,
        require_local_allocations=False,
    )
    assert result.homogeneous == result.first == result.second == Interval.point(0)


def test_all_case_roots_close_before_adaptation_and_worst_case_is_first(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    radii = {
        (case, role): Fraction(case + 1) for case in (0, 1) for role in (1, 2, 3, 4)
    }
    events = controlled_panels(monkeypatch, radii)
    result = enclose_population((model(), model(1)), max_attempts=6)
    assert [(case, role) for case, role, _ in events[:8]] == [
        (case, role) for case in (0, 1) for role in (1, 2, 3, 4)
    ]
    assert all(box in (UNIT, UNIT * 2) for _, _, box in events[:8])
    assert events[8][0] == 1
    assert all(row is not None for row in result.results)
    assert result.refusals == ("attempt_or_node_ceiling",) * 2
    assert all(budget.attempts == 6 for budget in result.budgets)
    assert {case for case, _, box in events if box not in (UNIT, UNIT * 2)} == {0, 1}


def test_endpoint_weight_and_domain_ties_select_the_first_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events = controlled_panels(
        monkeypatch,
        {
            (0, 1): Fraction(1),
            (0, 2): Fraction(1),
            (0, 3): Fraction(3, 2),
            (0, 4): Fraction(3, 2),
        },
    )
    enclose_population((model(),), max_attempts=6)
    assert events[4][:2] == (0, 1)
    assert events[4][2] == ((Fraction(0), Fraction(1, 2)),)
    assert events[5][2] == ((Fraction(1, 2), Fraction(1)),)


def test_case_width_ties_use_case_order_and_case_cap_does_not_stop_others(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events = controlled_panels(monkeypatch)
    result = enclose_population((model(), model(1)), max_attempts=6)
    assert events[8][0] == 0
    assert result.budgets[0].attempts == result.budgets[1].attempts == 6
    assert sum(budget.nodes for budget in result.budgets) <= 2 * 73719
    assert all(
        row is not None and row.status == "refuse_unresolved" for row in result.results
    )


def test_interrupted_second_child_preserves_the_complete_parent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controlled_panels(monkeypatch)
    result = enclose_population((model(),), max_attempts=5)
    row = result.results[0]
    assert row is not None
    assert len(row.integrals[0].panels) == 1
    assert row.integrals[0].panels[0].box == UNIT
    assert all(len(value.panels) == 1 for value in row.integrals)
    assert result.budgets[0].attempts == 5
    assert result.budgets[0].nodes == result.budgets[0].completed_nodes == 119
    assert result.refusals == ("attempt_or_node_ceiling",)


def test_common_clock_exposes_incomplete_and_unexecuted_cases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = [100.0]
    timer = SimpleNamespace(monotonic=lambda: clock[0])
    monkeypatch.setattr(population, "time", timer)
    monkeypatch.setattr(quadrature, "time", timer)
    controlled_panels(monkeypatch, clock=clock)
    result = enclose_population((model(), model(1)), wall_seconds=1)
    assert result.results == (None, None)
    assert result.refusals == (
        "initial_coverage_incomplete:wall_seconds",
        "not_executed:wall_seconds",
    )
    assert [budget.started for budget in result.budgets] == [100.0, 100.0]
    assert result.budgets[0].attempts == 3 and result.budgets[1].attempts == 0
    assert result.elapsed_seconds == pytest.approx(1.2)


@pytest.mark.parametrize(
    "limits",
    [{"max_attempts": 3}, {"max_queue": 3}, {"max_leaves": 3}, {"max_nodes": 111}],
)
def test_initial_case_caps_never_publish_a_partial_coefficient_sum(
    monkeypatch: pytest.MonkeyPatch, limits: dict[str, int]
) -> None:
    controlled_panels(monkeypatch)
    result = enclose_population((model(), model(1)), **limits)
    assert result.results == (None, None)
    assert all(
        reason is not None and reason.startswith("initial_coverage_incomplete:")
        for reason in result.refusals
    )
    for budget in result.budgets:
        assert (
            budget.attempts <= budget.max_attempts and budget.nodes <= budget.max_nodes
        )
        assert budget.leaves <= budget.max_leaves


def test_uncovered_band_tail_keeps_its_owner_and_other_case(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controlled_panels(monkeypatch, {})
    result = enclose_population((model(outer=4097), model(1)))
    assert result.results[0] is None
    assert result.refusals[0] == "radial_band_ceiling_uncovered_tail"
    assert result.budgets[0].attempts == 0
    assert (
        result.results[1] is not None and result.results[1].status == "certified_width"
    )


def test_final_width_can_close_without_local_allocation_becoming_a_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controlled_panels(monkeypatch, {(0, 1): EPSILON / 32})
    result = enclose_population((model(),))
    row = result.results[0]
    assert row is not None and row.status == "certified_width"
    assert row.integrals[0].enclosure.width > Q_WIDTH
    assert row.integrals[0].status == "refuse_unresolved"
    assert result.refusals == (None,) and result.budgets[0].attempts == 4
    strict = assemble_coefficients(
        model(), row.integrals, rule=SEVEN_NODE_RULE, conditioning=row.conditioning
    )
    assert strict.status == "refuse_unresolved"


@pytest.mark.parametrize(
    "limits",
    [
        {"wall_seconds": 161},
        {"wall_seconds": float("nan")},
        {"wall_seconds": True},
        {"max_nodes": 73720},
        {"max_leaves": 4097},
        {"max_attempts": 8192},
        {"max_queue": 4097},
    ],
)
def test_declared_population_limits_can_only_be_lowered(limits: dict[str, Any]) -> None:
    with pytest.raises((TypeError, ValueError)):
        enclose_population((model(),), **limits)


def test_population_interface_has_no_reference_observation_or_score_input() -> None:
    assert tuple(inspect.signature(enclose_population).parameters) == (
        "geometries",
        "wall_seconds",
        "max_leaves",
        "max_attempts",
        "max_nodes",
        "max_queue",
    )
    with pytest.raises(TypeError):
        cast(Callable[..., object], enclose_population)(
            (model(),), saved_reference=object()
        )
    for values in ((), tuple(model() for _ in range(7)), [model()]):
        with pytest.raises(TypeError):
            enclose_population(cast(tuple[Geometry, ...], values))
