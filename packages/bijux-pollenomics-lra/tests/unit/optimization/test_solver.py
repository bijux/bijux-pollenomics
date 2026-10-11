"""Independent small-domain optima and honest bounded-search diagnostics."""

from __future__ import annotations

from dataclasses import replace
import math

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_lra.api import ConvergenceError, LoveConfig, run_love
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.optimization.solver import ReplayOptimizer, optimize_box
from bijux_pollenomics_lra.reconstruction.optimized import tf


def _objective(name: str, candidate: np.ndarray) -> float:
    if name == "interior":
        regional, coefficients, observed = [0, 0], [1, 1], [0.5, 0.5]
    elif name == "boundary":
        regional, coefficients, observed = [1, 1], [2, 2], [1, 0]
    else:
        regional, coefficients, observed = [1, 1, 1], [0, 0, 2], [0.25, 0.25, 0.5]
    return tf(
        candidate,
        regional,
        np.repeat(np.array([coefficients], dtype=float) / 2, 2, axis=0),
        np.ones(2),
        observed,
        np.ones(len(regional)),
    )


def _ambiguous_optimum() -> tuple[float, float]:
    # f=2*log((1-p)/(.502))**2+log(p/.501)**2 is strictly convex
    # on [1/3,3/5]: each predicted/target ratio stays below exp(1).
    lower, upper = 1 / 3, 3 / 5
    for _ in range(80):
        p = (lower + upper) / 2
        derivative = -4 * math.log((1 - p) / 0.502) / (1 - p)
        derivative += 2 * math.log(p / 0.501) / p
        if derivative > 0:
            upper = p
        else:
            lower = p
    p = (lower + upper) / 2
    cover = (3 * p - 1) / (2 * (1 - p))
    value = math.sqrt(2 * math.log((1 - p) / 0.502) ** 2 + math.log(p / 0.501) ** 2)
    return cover, value


@pytest.mark.parametrize("seed", range(8))
@pytest.mark.parametrize("name", ["interior", "boundary", "ambiguous"])
def test_seeded_search_matches_independent_known_optimum(name: str, seed: int) -> None:
    dimensions = 3 if name == "ambiguous" else 2
    result = optimize_box(
        lambda candidate: _objective(name, candidate),
        np.zeros(dimensions),
        np.ones(dimensions),
        maxiter=400,
        tolerance=1e-7,
        max_evaluations=20000,
        rng=seed,
    )
    cover = result.x / result.x.sum()
    if name == "interior":
        # Symmetry and strict convexity give p=1/2, including source +.001.
        expected = math.sqrt(2) * abs(math.log(0.5 / 0.501))
        assert cover[0] == pytest.approx(0.5, abs=1e-3)
    elif name == "boundary":
        # On attainable p1 in[1/4,3/4], both derivative terms are negative.
        expected = math.hypot(math.log(0.75 / 1.001), math.log(0.25 / 0.001))
        assert cover[0] == pytest.approx(1.0, abs=2e-4)
    else:
        expected_cover, expected = _ambiguous_optimum()
        assert cover[2] == pytest.approx(expected_cover, abs=1e-3)
    assert result.success
    assert result.fun == pytest.approx(expected, abs=1e-6)
    assert result.fun == _objective(name, result.x)
    assert result.nfev <= 20000


def test_scale_equivalent_weights_and_distinct_ambiguous_compositions() -> None:
    assert _objective("interior", np.array([0.2, 0.2])) == _objective(
        "interior", np.array([0.8, 0.8])
    )
    cover, expected = _ambiguous_optimum()
    first = np.array([1 - cover, 0, cover])
    second = np.array([0, 1 - cover, cover])
    assert not np.array_equal(first, second)
    assert _objective("ambiguous", first) == pytest.approx(expected, abs=1e-14)
    assert _objective("ambiguous", second) == pytest.approx(expected, abs=1e-14)
    replay = optimize_box(
        lambda candidate: _objective("ambiguous", candidate),
        np.zeros(3),
        np.ones(3),
        optimizer=ReplayOptimizer(np.array([first, second])),
    )
    assert replay.algorithm == "candidate-replay"
    assert "convergence was not tested" in replay.message
    np.testing.assert_array_equal(replay.x, first)


@pytest.mark.parametrize(("budget", "generations"), [(1, 0), (20, 0), (60, 2), (80, 3)])
def test_budget_reports_completed_generations_and_exact_evaluation_count(
    budget: int, generations: int
) -> None:
    evaluations: list[np.ndarray] = []

    def objective(candidate: np.ndarray) -> float:
        evaluations.append(candidate.copy())
        return 1 + float(np.dot(candidate, candidate))

    result = optimize_box(
        objective, np.zeros(2), np.ones(2), rng=9, tolerance=0, max_evaluations=budget
    )
    assert not result.success
    assert result.message == "Evaluation budget reached"
    assert result.nfev == len(evaluations) == budget
    assert result.nit == generations
    assert result.fun == min(1 + float(np.dot(x, x)) for x in evaluations)


def test_maximum_iterations_and_undefined_objectives_are_not_success() -> None:
    result = optimize_box(
        lambda x: 1 + float(np.dot(x, x)),
        np.zeros(2),
        np.ones(2),
        rng=9,
        tolerance=0,
        maxiter=1,
    )
    assert not result.success
    assert result.nit == 1
    assert result.nfev == 40
    with pytest.raises(ValidationError, match="no finite"):
        optimize_box(lambda _x: float("nan"), np.zeros(2), np.ones(2), maxiter=1, rng=9)
    fixed = optimize_box(lambda x: float(x.sum()), np.ones(2), np.ones(2))
    assert fixed.success and fixed.nit == 0 and fixed.nfev == 1


def test_public_supported_optimized_and_analytical_symmetry_and_refusal() -> None:
    pollen = pd.DataFrame({"coordinate": [1], "Alnus": [50], "Betula": [50]})
    params = pd.DataFrame(
        {
            "Taxon": ["Alnus", "Betula"],
            "ppe": [1.0, 1.0],
            "ppe.error": [0.0, 0.0],
            "fallspeed": [0.03, 0.03],
        }
    )
    inner, outer = (
        np.array([10.0, 30.0, 100.0, 500.0]),
        np.array([30.0, 100.0, 500.0, 100000.0]),
    )
    area = np.pi * (outer**2 - inner**2)
    rings = pd.DataFrame(
        {
            "inner": inner,
            "outer": outer,
            "mean": (inner + outer) / 2,
            "ring": area,
            "terrestrial": area * [0, 1, 1, 1],
        }
    )
    common = LoveConfig(
        method="analytical",
        regional_basin_type="lake",
        regional_basin_diameter_m=300,
        local_basin_diameter_m=12,
        max_ring=2,
        repeats=1,
        stochastic=False,
        seed=3,
    )
    # Explicit construction keeps typing and source geometry contracts visible.
    analytical = run_love(pollen, pollen, params, rings, common)
    optimized = run_love(
        pollen,
        pollen,
        params,
        rings,
        replace(
            common,
            method="optimized",
            optimizer_iterations=400,
            optimizer_tolerance=1e-7,
        ),
    )
    np.testing.assert_allclose(analytical.cover["mean"].to_numpy(), 0.5, atol=1e-12)
    assert optimized.cover["mean"].iloc[0].isna().all()
    np.testing.assert_allclose(
        optimized.cover["mean"].iloc[1].to_numpy(), 0.5, atol=1e-4
    )
    with pytest.raises(ConvergenceError) as failure:
        run_love(
            pollen,
            pollen,
            params,
            rings,
            replace(
                common,
                method="optimized",
                optimizer_tolerance=0,
                optimizer_max_evaluations=60,
            ),
        )
    assert len(failure.value.diagnostics) == 1
    assert failure.value.diagnostics[0]["nit"] == 2
    assert failure.value.diagnostics[0]["nfev"] == 60
