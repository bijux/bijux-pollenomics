"""True-mass affine algebra and bounded endpoint-population controls."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver import (
    quadrature,
    ring_bounds,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.arithmetic import (
    Interval,
    Jet,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.kernel import (
    Geometry,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.quadrature import (
    Box,
    Integrand,
    Panel,
    WorkBudget,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.ring_bounds import (
    Q_TARGET,
    coefficient_bounds,
    deposition_bounds,
    enclose_ring_population,
    evaluate_q,
    shared_q_linear,
)

UNIT = ((Fraction(0), Fraction(1)),)
EDGES = (Fraction(1), Fraction(2), Fraction(3))


def model(index: int = 0) -> Geometry:
    return Geometry(
        Fraction(index),
        Fraction(1),
        Fraction(3),
        (Fraction(-1), Fraction(0)),
        (Fraction(1), Fraction(0)),
    )


def points(*values: Fraction | int) -> tuple[Interval, ...]:
    return tuple(Interval.point(value) for value in values)


def controlled(
    monkeypatch: pytest.MonkeyPatch,
    *,
    radius: Fraction = Fraction(1),
    clock: list[float] | None = None,
    no_contraction: bool = False,
) -> list[tuple[int, Fraction, Box]]:
    monkeypatch.setattr(
        ring_bounds,
        "_q_operator",
        lambda geometry, r: (
            lambda t: Jet.constant((100 * geometry.coefficient + r) / 1000, t.order)
        ),
    )
    events: list[tuple[int, Fraction, Box]] = []

    def panel(function: Integrand, box: Box, budget: WorkBudget, *, rule: str) -> Panel:
        budget.panel(1, nodes_per_axis=7)
        budget.derivative_boxes += 1
        value = function((Jet.constant(0, 0),)).value.lower
        owner = int(value * 1000) // 100
        edge = value * 1000 - 100 * owner
        events.append((owner, edge, box))
        length = box[0][1] - box[0][0]
        error = radius * length ** (1 if no_contraction else 2)
        budget.completed_nodes += 7
        if clock is not None:
            clock[0] += 0.4
            budget.check()
        return Panel(box, Interval.point(value * length), error, (error,), rule)

    monkeypatch.setattr(ring_bounds, "positive_panel", panel)
    return events


def test_q_dispatch_changes_only_evaluation_radius(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[tuple[str, Geometry]] = []

    def contact(geometry: Geometry, t: Jet) -> Jet:
        events.append(("contact", geometry))
        return Jet.constant(1, t.order)

    def outer(geometry: Geometry, t: Jet) -> Jet:
        events.append(("outer", geometry))
        return Jet.constant(0, t.order)

    monkeypatch.setattr(Geometry, "contact_survival", contact)
    monkeypatch.setattr(Geometry, "outer_survival", outer)
    geometry = model(1)
    evaluate_q(geometry, Fraction(1), Jet.constant(0))
    evaluate_q(geometry, Fraction(2), Jet.constant(0))
    assert events[0] == ("contact", geometry)
    assert events[1] == ("outer", replace(geometry, outer=Fraction(2)))
    with pytest.raises(ValueError, match="original geometry"):
        evaluate_q(geometry, Fraction(4), Jet.constant(0))


def test_signed_linear_form_uses_each_cumulative_coordinate_once() -> None:
    bounds = (
        Interval(Fraction(3, 4), Fraction(4, 5)),
        Interval(Fraction(1, 4), Fraction(3, 10)),
    )
    value = shared_q_linear(bounds, (Fraction(2), Fraction(-3)))
    assert value.lower <= Fraction(3, 5) and value.upper >= Fraction(17, 20)
    with pytest.raises(TypeError):
        shared_q_linear(bounds, (Fraction(1),))


def test_monotone_constraints_preserve_raw_bounds_and_reject_contradiction() -> None:
    raw = (
        Interval(Fraction(1, 10), Fraction(6, 5)),
        Interval(Fraction(2, 5), Fraction(9, 10)),
        Interval(Fraction(-1, 5), Fraction(4, 5)),
    )
    result = coefficient_bounds(model(), EDGES, raw)
    assert result.raw_q_bounds == raw
    assert result.constrained_q_bounds == (
        Interval(Fraction(2, 5), Fraction(1)),
        raw[1],
        Interval(Fraction(0), Fraction(4, 5)),
    )
    with pytest.raises(ValueError, match="Reversed"):
        coefficient_bounds(model(), EDGES, points(Fraction(1, 5), Fraction(4, 5), 0))


def test_complement_and_constant_cover_telescope_before_interval_evaluation() -> None:
    raw = (
        Interval(Fraction(7, 8), Fraction(1)),
        Interval(Fraction(1, 2), Fraction(3, 4)),
        Interval(Fraction(1, 8), Fraction(1, 4)),
    )
    bounds = coefficient_bounds(model(), EDGES, raw)
    assert bounds.first == bounds.second == bounds.homogeneous * Fraction(1, 2)
    assert bounds.second.width < (bounds.homogeneous - bounds.first).width
    assert deposition_bounds(
        bounds, Fraction(3, 4), Fraction(3, 4)
    ) == bounds.homogeneous * Fraction(3, 4)
    assert deposition_bounds(bounds, Fraction(-1), Fraction(-2)).upper < 0
    assert bounds.positive_bounds == (True, True, True)
    assert bounds.coefficient_epsilon_pass == (False, False, False)


@pytest.mark.parametrize(
    "covers",
    [
        (Fraction(3, 4), Fraction(1, 4)),
        (Fraction(1, 4), Fraction(3, 4)),
        (Fraction(-1), Fraction(-2)),
    ],
)
def test_ring_endpoint_extrema_contain_positive_mass_interior_witnesses(
    covers: tuple[Fraction, Fraction],
) -> None:
    geometry = replace(
        model(1), first=(Fraction(1), Fraction(0)), second=(Fraction(2), Fraction(0))
    )
    bounds = coefficient_bounds(
        geometry, EDGES, points(1, Fraction(3, 4), Fraction(1, 4))
    )
    witness = Interval.point(0)
    for a, b, mass in zip(
        EDGES[:-1], EDGES[1:], (Fraction(1, 4), Fraction(1, 2)), strict=True
    ):
        h = geometry.angular(Jet.constant((a + b) / 2, 0)).value
        witness += (covers[1] + (covers[0] - covers[1]) * h) * mass
    result = deposition_bounds(bounds, *covers)
    assert result.lower <= witness.lower <= witness.upper <= result.upper


def test_all_six_129_endpoint_populations_use_actual_degree_seven_rule(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ring_bounds, "_q_operator", lambda geometry, r: lambda t: (4 - r) * t**7 / 4
    )
    edges = tuple(Fraction(1) + Fraction(i, 64) for i in range(129))
    result = enclose_ring_population(tuple(model(i) for i in range(6)), (edges,) * 6)
    assert len(result.results) == 6
    for case, budget in zip(result.results, result.budgets, strict=True):
        assert len(case.endpoints) == len(case.refusals) == 129
        assert case.refusal is None and all(reason is None for reason in case.refusals)
        assert case.bounds is not None and all(case.bounds.coefficient_epsilon_pass)
        assert budget.attempts == 129 and budget.nodes == budget.completed_nodes == 903
        assert case.endpoints[0] is not None
        assert (
            case.endpoints[0].enclosure.lower
            <= Fraction(3, 32)
            <= case.endpoints[0].enclosure.upper
        )
    assert sum(value.nodes for value in result.budgets) == 5418


def test_round_robin_initialization_precedes_all_raw_width_refinement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events = controlled(monkeypatch)
    result = enclose_ring_population(
        (model(), model(1)), (EDGES, EDGES), max_attempts=5
    )
    assert [(owner, r) for owner, r, _ in events[:6]] == [
        (owner, r) for r in EDGES for owner in (0, 1)
    ]
    assert all(box == UNIT for _, _, box in events[:6])
    assert events[6][:2] == (0, Fraction(1))
    assert all(case.bounds is not None for case in result.results)
    assert all(case.refusal == "attempt_or_node_ceiling" for case in result.results)
    assert all(value.attempts == 5 for value in result.budgets)


def test_interrupted_child_retains_parent_and_next_case_advances(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events = controlled(monkeypatch)
    result = enclose_ring_population(
        (model(), model(1)), (EDGES, EDGES), max_attempts=4
    )
    assert len(events) == 8
    for case, budget in zip(result.results, result.budgets, strict=True):
        assert case.endpoints[0] is not None
        assert case.endpoints[0].panels[0].box == UNIT
        assert len(case.endpoints[0].panels) == 1
        assert budget.attempts == 4 and budget.nodes == 28


def test_constraints_do_not_turn_broad_endpoint_roots_into_precision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broad(function: Integrand, box: Box, budget: WorkBudget, *, rule: str) -> Panel:
        budget.panel(1, nodes_per_axis=7)
        length = box[0][1] - box[0][0]
        budget.completed_nodes += 7
        return Panel(
            box,
            Interval.point(Fraction(3, 2) * length),
            length / 2,
            (length / 2,),
            rule,
        )

    monkeypatch.setattr(ring_bounds, "positive_panel", broad)
    # A=0 has exact Q=1. Raw [1,2] intersects the proved probability domain
    # at that point, but this cannot certify the raw quadrature-width target.
    result = enclose_ring_population((model(),), (EDGES,), max_attempts=3)
    case = result.results[0]
    assert case.bounds is not None
    assert case.bounds.constrained_q_bounds == points(1, 1, 1)
    assert all(
        value is not None
        and value.enclosure.width > Q_TARGET
        and value.status == "refuse_unresolved"
        for value in case.endpoints
    )
    assert case.refusal == "attempt_or_node_ceiling"


def test_global_clock_retains_every_unclosed_and_unexecuted_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = [100.0]
    timer = SimpleNamespace(monotonic=lambda: clock[0])
    monkeypatch.setattr(ring_bounds, "time", timer)
    monkeypatch.setattr(quadrature, "time", timer)
    controlled(monkeypatch, clock=clock)
    result = enclose_ring_population(
        (model(), model(1)), (EDGES, EDGES), wall_seconds=1
    )
    assert all(
        case.bounds is None and len(case.endpoints) == len(case.refusals) == 3
        for case in result.results
    )
    assert result.results[0].refusals[1] == "initial_panel_unclosed:wall_seconds"
    assert result.results[1].refusals[1] == "not_executed:wall_seconds"
    assert all(
        case.refusals[2] == "not_executed:wall_seconds" for case in result.results
    )
    assert [value.started for value in result.budgets] == [100.0, 100.0]
    assert [value.attempts for value in result.budgets] == [2, 1]
    assert result.elapsed_seconds == pytest.approx(1.2)


@pytest.mark.parametrize(
    "limits",
    [{"max_attempts": 2}, {"max_nodes": 20}, {"max_leaves": 2}, {"max_queue": 2}],
)
def test_incomplete_endpoint_populations_keep_all_dispositions(
    monkeypatch: pytest.MonkeyPatch, limits: dict[str, int]
) -> None:
    controlled(monkeypatch)
    result = enclose_ring_population((model(), model(1)), (EDGES, EDGES), **limits)
    assert all(
        case.bounds is None and len(case.endpoints) == 3 for case in result.results
    )
    assert all(
        case.refusal is not None
        and case.refusal.startswith("incomplete_endpoint_population:")
        for case in result.results
    )
    assert all(
        value.attempts <= value.max_attempts
        and value.nodes <= value.max_nodes
        and value.leaves <= value.max_leaves
        for value in result.budgets
    )


@pytest.mark.parametrize(
    "limits",
    [
        {"wall_seconds": 161},
        {"wall_seconds": float("nan")},
        {"max_nodes": 73720},
        {"max_attempts": 8192},
        {"max_leaves": 4097},
        {"max_queue": 4097},
    ],
)
def test_endpoint_limits_only_lower_declared_ceilings(limits: dict[str, Any]) -> None:
    with pytest.raises((ValueError, TypeError)):
        enclose_ring_population((model(),), (EDGES,), **limits)


def test_foreign_reordered_or_incomplete_radial_edges_refuse_before_evaluation() -> (
    None
):
    for edges in (
        (Fraction(0), Fraction(3)),
        (Fraction(1), Fraction(3), Fraction(2)),
        (Fraction(1), Fraction(2)),
    ):
        with pytest.raises(ValueError):
            enclose_ring_population((model(),), (edges,))
