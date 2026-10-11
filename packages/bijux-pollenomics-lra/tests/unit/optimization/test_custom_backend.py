"""Budget accounting for caller supplied numerical solvers."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pytest

from bijux_pollenomics_lra.optimization.solver import OptimizationResult, optimize_box


@pytest.mark.parametrize("swallow_budget", [False, True])
def test_custom_backend_budget_caps_calls_and_retains_best_failure(
    swallow_budget: bool,
) -> None:
    evaluated: list[np.ndarray] = []

    def objective(candidate: np.ndarray) -> float:
        evaluated.append(candidate.copy())
        return float(np.dot(candidate, candidate))

    class SearchOptimizer:
        def solve(
            self,
            objective: Callable[[np.ndarray], float],
            *args: object,
            **kwargs: object,
        ) -> OptimizationResult:
            assert kwargs["tolerance"] == 0.125
            assert kwargs["max_evaluations"] == 2
            for candidate in ([0.8, 0.8], [0.5, 0.5], [0.1, 0.1]):
                try:
                    objective(np.asarray(candidate))
                except Exception:
                    if not swallow_budget:
                        raise
            return OptimizationResult(
                np.array([0.1, 0.1]), 0.02, 9, 9, True, "", "custom"
            )

    result = optimize_box(
        objective,
        np.zeros(2),
        np.ones(2),
        optimizer=SearchOptimizer(),
        max_evaluations=2,
        tolerance=0.125,
    )
    assert result.nfev == 2
    assert result.certification_nfev == 1
    assert len(evaluated) == result.nfev + result.certification_nfev
    assert not result.success
    assert result.nit == 0
    assert "completed iterations unavailable" in result.message
    np.testing.assert_array_equal(result.x, [0.5, 0.5])
    assert result.fun == 0.5


def test_legacy_custom_solver_signature_and_search_counts_remain_supported() -> None:
    class LegacyOptimizer:
        def solve(
            self,
            objective: Callable[[np.ndarray], float],
            lower: np.ndarray,
            upper: np.ndarray,
            *,
            rng: np.random.Generator,
            maxiter: int,
            popsize: int,
        ) -> OptimizationResult:
            assert maxiter == 200 and popsize == 10
            candidate = (lower + upper) / 2
            return OptimizationResult(
                candidate, objective(candidate), 1, 1, True, "", "legacy"
            )

    result = optimize_box(
        lambda x: float(x.sum()),
        np.zeros(2),
        np.ones(2),
        optimizer=LegacyOptimizer(),
        max_evaluations=1,
    )
    assert result.success
    assert result.nfev == 1
    assert result.as_dict()["certification_nfev"] == 1
