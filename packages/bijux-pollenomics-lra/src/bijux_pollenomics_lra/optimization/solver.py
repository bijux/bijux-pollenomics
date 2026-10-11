"""Optimization solver for the LRA engine."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import suppress
from dataclasses import dataclass, replace
from inspect import Parameter, signature
import warnings

import numpy as np
from scipy.optimize import Bounds, differential_evolution

from bijux_pollenomics_lra.models.errors import NativeOptimizerWarning, ValidationError
from bijux_pollenomics_lra.models.validation import (
    finite_number,
    integer,
    rng_from,
    vector,
)

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
    certification_nfev: int = 0

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
            "certification_nfev": self.certification_nfev,
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
        max_evaluations: int | None = None,
        **_: object,
    ) -> OptimizationResult:
        """Evaluate all candidates and return the finite minimum."""
        candidates = self.candidates
        if lower is not None and upper is not None:
            if candidates.shape[1] != len(lower):
                raise ValidationError("Replay candidate dimensionality is invalid")
            if np.any(candidates < lower) or np.any(candidates > upper):
                raise ValidationError("Replay candidates violate optimizer bounds")

        evaluation_count = len(candidates)
        if max_evaluations is not None:
            evaluation_count = min(
                evaluation_count, integer(max_evaluations, "max_evaluations")
            )
        complete = evaluation_count == len(candidates)
        values = np.asarray(
            [
                float(objective(candidate.copy()))
                for candidate in candidates[:evaluation_count]
            ],
            dtype=float,
        )
        values = np.where(np.isfinite(values), values, np.inf)
        if np.isinf(values).all():
            if not complete:
                raise ValidationError(
                    "Evaluation budget ended before any finite candidate"
                )
            raise ValidationError("Every replay candidate has an undefined objective")
        index = int(np.argmin(values))
        return OptimizationResult(
            x=candidates[index].copy(),
            fun=float(values[index]),
            nit=1,
            nfev=evaluation_count,
            success=complete,
            message=(
                "Fixed-candidate replay; optimizer convergence was not tested"
                if complete
                else "Evaluation budget reached before complete candidate replay"
            ),
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
        search_evaluations = 0
        best_candidate: np.ndarray | None = None
        best_objective = np.inf
        budget_reached = False

        class CustomEvaluationBudgetReached(Exception):
            pass

        def custom_objective(candidate: np.ndarray) -> float:
            nonlocal search_evaluations, best_candidate, best_objective, budget_reached
            if max_evaluations is not None and search_evaluations >= max_evaluations:
                budget_reached = True
                raise CustomEvaluationBudgetReached
            search_evaluations += 1
            owned_candidate = vector(candidate, "optimizer candidate").copy()
            if owned_candidate.shape != lower_array.shape or np.any(
                (owned_candidate < lower_array) | (owned_candidate > upper_array)
            ):
                raise ValidationError(
                    "Optimizer candidate violates dimensions or bounds"
                )
            value = float(objective(owned_candidate.copy()))
            if np.isfinite(value) and value < best_objective:
                best_objective = value
                best_candidate = owned_candidate
            return value

        options: dict[str, object] = {
            "rng": generator,
            "maxiter": maxiter,
            "popsize": popsize,
        }
        parameters: Mapping[str, Parameter]
        try:
            parameters = signature(optimizer.solve).parameters
        except (TypeError, ValueError):
            parameters = {}
        accepts_keywords = any(
            parameter.kind == Parameter.VAR_KEYWORD for parameter in parameters.values()
        )
        for name, option in {
            "tolerance": tolerance,
            "max_evaluations": max_evaluations,
        }.items():
            if accepts_keywords or (
                name in parameters
                and parameters[name].kind != Parameter.POSITIONAL_ONLY
            ):
                options[name] = option

        custom_result = None
        with suppress(CustomEvaluationBudgetReached):
            custom_result = optimizer.solve(
                custom_objective,
                lower_array.copy(),
                upper_array.copy(),
                **options,
            )
        if budget_reached:
            if best_candidate is None:
                raise ValidationError(
                    "Evaluation budget ended before any finite candidate"
                )
            custom_result = OptimizationResult(
                best_candidate,
                float(best_objective),
                0,
                search_evaluations,
                False,
                "Evaluation budget reached; completed iterations unavailable",
                "custom",
            )
        if not isinstance(custom_result, OptimizationResult):
            raise ValidationError("optimizer.solve must return OptimizationResult")
        candidate = vector(custom_result.x, "optimizer result x").copy()
        if candidate.shape != lower_array.shape:
            raise ValidationError("Optimizer result dimensionality is invalid")
        if np.any(candidate < lower_array) or np.any(candidate > upper_array):
            raise ValidationError("Optimizer result violates bounds")
        reported_value = finite_number(custom_result.fun, "optimizer result fun")
        # The model objective is deterministic for a frozen repeat's inputs.
        # Certify it independently before downstream cover/pollen publication.
        verified_value = float(objective(candidate.copy()))
        if not np.isfinite(verified_value):
            raise ValidationError("Optimizer result has an undefined objective")
        if not np.isclose(reported_value, verified_value, rtol=1e-12, atol=1e-12):
            raise ValidationError(
                "Optimizer result objective disagrees with evaluation"
            )
        nit = integer(custom_result.nit, "optimizer result nit", minimum=0)
        nfev = integer(custom_result.nfev, "optimizer result nfev")
        if max_evaluations is not None and nfev != search_evaluations:
            raise ValidationError(
                "Optimizer result nfev disagrees with observed search calls"
            )
        if not isinstance(custom_result.success, (bool, np.bool_)):
            raise ValidationError("Optimizer result success must be boolean")
        return replace(
            custom_result,
            x=candidate,
            fun=verified_value,
            nit=nit,
            nfev=nfev,
            success=bool(custom_result.success),
            certification_nfev=1,
        )

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
