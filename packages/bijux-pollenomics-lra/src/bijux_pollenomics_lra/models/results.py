"""Models results for the LRA engine."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.optimization.solver import OptimizationResult
from bijux_pollenomics_lra.provenance.manifest import RunManifest


@dataclass(slots=True)
class RevealsResult:
    """Regional reconstruction table, K factors, optional draws, and provenance."""

    table: pd.DataFrame
    deposition: pd.Series
    manifest: RunManifest
    samples: np.ndarray | None = None

    def write(self, directory: str | Path) -> Path:
        """Write a complete artifact bundle."""
        from bijux_pollenomics_lra.outputs.serialization import write_reveals_result

        return write_reveals_result(self, directory)


@dataclass(slots=True)
class LoveResult:
    """Normalised local reconstruction result."""

    method: str
    cover: Mapping[str, pd.DataFrame]
    manifest: RunManifest
    pollen_percentages: Mapping[str, pd.DataFrame] = field(default_factory=dict)
    outlier: pd.Series | None = None
    outlier_quantile: pd.Series | None = None
    objective_values: pd.DataFrame | None = None
    diagnostics: list[OptimizationResult] = field(default_factory=list)
    samples: Mapping[str, np.ndarray] = field(default_factory=dict)
    auxiliary: Mapping[str, Any] = field(default_factory=dict)

    def write(self, directory: str | Path) -> Path:
        """Write a complete artifact bundle."""
        from bijux_pollenomics_lra.outputs.serialization import write_love_result

        return write_love_result(self, directory)


@dataclass(slots=True)
class LRAResult:
    """One paired regional and local LRA reconstruction."""

    regional: RevealsResult
    local: LoveResult
    manifest: RunManifest

    def write(self, directory: str | Path) -> Path:
        """Write regional, local, and parent manifests."""
        from bijux_pollenomics_lra.outputs.serialization import write_lra_result

        return write_lra_result(self, directory)


@dataclass(slots=True)
class LRASeriesResult:
    """A coordinate-keyed sequence of paired LRA reconstructions."""

    runs: Mapping[str, LRAResult]
    manifest: RunManifest

    def write(self, directory: str | Path) -> Path:
        from bijux_pollenomics_lra.outputs.serialization import (
            write_lra_series_result,
        )

        return write_lra_series_result(self, directory)


@dataclass(frozen=True, slots=True)
class ForwardResult:
    """Pollen prediction and inspectable unnormalized deposition contributions."""

    pollen_fraction: np.ndarray
    local_deposition: np.ndarray
    regional_deposition: np.ndarray
    total_deposition: np.ndarray
    method_profile: str = "disqover-0.9.14-homogeneous-local-forward"
