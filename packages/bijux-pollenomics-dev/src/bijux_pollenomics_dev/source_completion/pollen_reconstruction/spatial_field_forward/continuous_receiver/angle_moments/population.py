"""Explicit angle-moment entry to the unchanged shared finite-work frontier."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import cast

from ..kernel import Geometry
from ..population import _enclose_population
from ..quadrature import WorkBudget
from .results import MomentCoefficient


@dataclass(frozen=True)
class MomentPopulation:
    """Retain every supplied owner, including incomplete and unexecuted cases."""

    results: tuple[MomentCoefficient | None, ...]
    refusals: tuple[str | None, ...]
    budgets: tuple[WorkBudget, ...]
    elapsed_seconds: float

    def __post_init__(self) -> None:
        """Keep the original ordered bounded population and every refusal slot."""
        if (
            type(self.results) is not tuple
            or type(self.refusals) is not tuple
            or type(self.budgets) is not tuple
            or not 1 <= len(self.results) <= 6
            or len(self.results) != len(self.refusals)
            or len(self.results) != len(self.budgets)
            or not math.isfinite(self.elapsed_seconds)
            or self.elapsed_seconds < 0
        ):
            raise ValueError("Complete bounded angle population disposition required")


def enclose_population(
    geometries: tuple[Geometry, ...],
    *,
    wall_seconds: float = 160,
    max_leaves: int = 4096,
    max_attempts: int = 8191,
    max_nodes: int = 73719,
    max_queue: int = 4096,
) -> MomentPopulation:
    """Use the same epsilon stopping, shared clock and per-case ceilings as before."""
    results, refusals, budgets, elapsed = _enclose_population(
        geometries,
        wall_seconds=wall_seconds,
        max_leaves=max_leaves,
        max_attempts=max_attempts,
        max_nodes=max_nodes,
        max_queue=max_queue,
        angle_moments=True,
    )
    if any(
        value is not None and type(value) is not MomentCoefficient for value in results
    ):
        raise ValueError("Foreign coefficient method in angle population")
    return MomentPopulation(
        cast(tuple[MomentCoefficient | None, ...], results), refusals, budgets, elapsed
    )
