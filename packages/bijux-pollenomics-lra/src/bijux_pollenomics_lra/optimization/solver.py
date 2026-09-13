"""Optimization solver for the LRA engine."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import warnings

import numpy as np
from scipy.optimize import Bounds, differential_evolution

from bijux_pollenomics_lra.models.errors import NativeOptimizerWarning, ValidationError
from bijux_pollenomics_lra.models.validation import integer, rng_from, vector

Objective = Callable[[np.ndarray], float]


@dataclass(slots=True)
class OptimizationResult:
    """Normalised optimization diagnostics."""

    x: np.ndarray
    fun: float
    nit: int
    nfev: int
    success: bool
    message: str
    algorithm: str

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-compatible diagnostic record."""
        return {
            "x": self.x.tolist(),
            "fun": self.fun,
            "nit": self.nit,
            "nfev": self.nfev,
            "success": self.success,
            "message": self.message,
            "algorithm": self.algorithm,
        }


@dataclass(frozen=True, slots=True)
class ReplayOptimizer:
    """Select the best result from an explicit candidate matrix.

    This backend is the preferred mechanism for R parity checks involving
    LOVEoptim.  The same candidate matrix is injected into both runtimes.
    """

    candidates: np.ndarray

    def __post_init__(self) -> None:
        candidates = np.array(self.candidates, dtype=float, copy=True)
        if candidates.ndim != 2 or 0 in candidates.shape:
            raise ValidationError("Replay candidates must be a non-empty matrix")
        if not np.isfinite(candidates).all():
            raise ValidationError("Replay candidates must be finite")
        candidates.setflags(write=False)
        object.__setattr__(self, "candidates", candidates)

    def solve(
        self,
        objective: Objective,
        lower: np.ndarray | None = None,
        upper: np.ndarray | None = None,
        **_: object,
    ) -> OptimizationResult:
        """Evaluate all candidates and return the finite minimum."""
        candidates = self.candidates
        if lower is not None and upper is not None:
            if candidates.shape[1] != len(lower):
                raise ValidationError("Replay candidate dimensionality is invalid")
            if np.any(candidates < lower) or np.any(candidates > upper):
                raise ValidationError("Replay candidates violate optimizer bounds")

        values = np.asarray(
            [float(objective(candidate.copy())) for candidate in candidates],
            dtype=float,
        )
        values = np.where(np.isfinite(values), values, np.inf)
        if np.isinf(values).all():
            raise ValidationError("Every replay candidate has an undefined objective")
        index = int(np.argmin(values))
        return OptimizationResult(
            x=candidates[index].copy(),
            fun=float(values[index]),
            nit=1,
            nfev=len(candidates),
            success=True,
            message="Fixed-candidate replay; optimizer convergence was not tested",
            algorithm="candidate-replay",
        )


def optimize_box(
    objective: Objective,
    lower: np.ndarray,
    upper: np.ndarray,
    *,
    maxiter: int = 200,
    popsize: int = 10,
    tolerance: float = 0.01,
    max_evaluations: int | None = None,
    rng: None | int | np.random.Generator = None,
    optimizer: ReplayOptimizer | object | None = None,
    trace: bool = False,
) -> OptimizationResult:
    """Minimise a bounded objective with SciPy differential evolution.

    ``popsize=10`` gives a SciPy population of ``10 * n_parameters``, matching
    the population-size convention explicitly requested by the upstream
    LOVEoptim wrapper.  Mutation, selection, stopping and random streams remain
    backend-specific and therefore are not claimed as optimizer parity.
    """
    lower_array = vector(lower, "lower")
    upper_array = vector(upper, "upper")
    if lower_array.shape != upper_array.shape or np.any(lower_array > upper_array):
        raise ValidationError("Invalid optimization bounds")
    maxiter = integer(maxiter, "maxiter")
    popsize = integer(popsize, "popsize")
    if max_evaluations is not None:
        max_evaluations = integer(max_evaluations, "max_evaluations")
    tolerance = float(tolerance)
    if not np.isfinite(tolerance) or tolerance < 0:
        raise ValidationError("tolerance must be finite and nonnegative")

    generator = rng_from(rng)
    if optimizer is not None:
        if not hasattr(optimizer, "solve"):
            raise ValidationError(
                "optimizer must expose solve(objective, lower, upper, ...)"
            )
        custom_result = optimizer.solve(
            objective,
            lower_array,
            upper_array,
            rng=generator,
            maxiter=maxiter,
            popsize=popsize,
        )
        if not isinstance(custom_result, OptimizationResult):
            raise ValidationError("optimizer.solve must return OptimizationResult")
        return custom_result

    if np.all(lower_array == upper_array):
        value = float(objective(lower_array.copy()))
        if not np.isfinite(value):
            raise ValidationError("Fixed parameter vector has an undefined objective")
        return OptimizationResult(
            lower_array.copy(), value, 0, 1, True, "All parameters fixed", "fixed"
        )

    best_x: np.ndarray | None = None
    best_value = np.inf
    evaluations = 0
    completed_generations = 0

    def record_generation(_candidate: np.ndarray, _convergence: object) -> None:
        nonlocal completed_generations
        completed_generations += 1

    class EvaluationBudgetReached(Exception):
        pass

    def safe_objective(candidate: np.ndarray) -> float:
        nonlocal best_x, best_value, evaluations
        if max_evaluations is not None and evaluations >= max_evaluations:
            raise EvaluationBudgetReached
        evaluations += 1
        value = float(objective(candidate))
        if not np.isfinite(value):
            value = np.inf
        if value < best_value:
            best_value = value
            best_x = np.asarray(candidate, dtype=float).copy()
        return value

    try:
        result = differential_evolution(
            safe_objective,
            Bounds(lower_array, upper_array),
            seed=generator,
            maxiter=maxiter,
            popsize=popsize,
            tol=tolerance,
            atol=0,
            polish=False,
            updating="immediate",
            workers=1,
            disp=trace,
            callback=record_generation,
        )
    except EvaluationBudgetReached:
        if best_x is None:
            raise ValidationError(
                "Evaluation budget ended before any finite candidate"
            ) from None
        return OptimizationResult(
            x=best_x,
            fun=float(best_value),
            nit=completed_generations,
            nfev=evaluations,
            success=False,
            message="Evaluation budget reached",
            algorithm="scipy.differential_evolution",
        )

    if best_x is None:
        raise ValidationError("Optimizer found no finite objective")
    if result.fun < best_value:
        best_x = np.asarray(result.x, dtype=float)
        best_value = float(result.fun)

    return OptimizationResult(
        x=best_x,
        fun=float(best_value),
        nit=int(getattr(result, "nit", 0)),
        nfev=evaluations,
        success=bool(result.success),
        message=str(result.message),
        algorithm="scipy.differential_evolution",
    )


def warn_optimizer_nonparity() -> None:
    """Emit the package's explicit optimizer-path warning."""
    warnings.warn(
        "The native SciPy optimizer does not reproduce RcppDE/DEoptim search "
        "trajectories. Use ReplayOptimizer for objective/wrapper parity.",
        NativeOptimizerWarning,
        stacklevel=2,
    )
