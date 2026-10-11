"""Parity checks against R-fitted LSM responses embedded with the package."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import numpy as np

from bijux_pollenomics_lra.dispersal.kernels import _lsm_data
from bijux_pollenomics_lra.dispersal.loess import Loess1D
from bijux_pollenomics_lra.version import (
    REFERENCE_ARCHIVE_SHA256,
    REFERENCE_VERSION,
    __version__,
)


@dataclass(frozen=True, slots=True)
class StoredParityReport:
    """Measured parity status for all saved R LSM fits."""

    status: str
    reference_package: str
    reference_version: str
    source_archive_sha256: str
    package_version: str
    models: int
    evaluation_points: int
    evaluation_max_abs_error: float
    evaluation_mean_abs_error: float
    refit_points: int
    refit_max_abs_error: float
    refit_mean_abs_error: float
    tolerance: float
    generated_at_utc: str
    scope: tuple[str, ...]
    excluded_claims: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(self.as_dict(), indent=2) + "\n", encoding="utf-8"
        )
        return destination


def run_stored_parity(tolerance: float = 3e-13) -> StoredParityReport:
    """Evaluate and independently refit every stored R LSM model."""
    data = _lsm_data()
    model_names = sorted(
        key[: -len("_r_fitted")] for key in data if key.endswith("_r_fitted")
    )
    evaluation_errors: list[np.ndarray] = []
    refit_errors: list[np.ndarray] = []
    for name in model_names:
        x_values = data[f"{name}_x"]
        r_fitted = data[f"{name}_r_fitted"]
        model = Loess1D(
            data[f"{name}_vertices"],
            data[f"{name}_values"],
            data[f"{name}_derivatives"],
            tuple(data[f"{name}_domain"]),
        )
        evaluation_errors.append(np.abs(model(x_values) - r_fitted))

        refitted = Loess1D.fit(
            x_values,
            data[f"{name}_raw_y"],
            span=float(data[f"{name}_span"].item()),
            cell=float(data[f"{name}_cell"].item()),
        )
        refit_errors.append(np.abs(refitted(x_values) - r_fitted))

    evaluation = np.concatenate(evaluation_errors)
    refit = np.concatenate(refit_errors)
    maximum = max(float(evaluation.max()), float(refit.max()))
    return StoredParityReport(
        status="passed" if maximum <= tolerance else "failed",
        reference_package="disqover",
        reference_version=REFERENCE_VERSION,
        source_archive_sha256=REFERENCE_ARCHIVE_SHA256,
        package_version=__version__,
        models=len(model_names),
        evaluation_points=len(evaluation),
        evaluation_max_abs_error=float(evaluation.max()),
        evaluation_mean_abs_error=float(evaluation.mean()),
        refit_points=len(refit),
        refit_max_abs_error=float(refit.max()),
        refit_mean_abs_error=float(refit.mean()),
        tolerance=float(tolerance),
        generated_at_utc=datetime.now(UTC).isoformat(),
        scope=(
            "evaluation of 45 serialized R-fitted LSM curves",
            "independent native LOESS refit from saved raw x/y and fit settings",
        ),
        excluded_claims=(
            "live execution of the R package",
            "identity of NumPy and R random-number streams",
            "identity of SciPy and RcppDE/DEoptim optimizer trajectories",
            "ecological validation against held-out observations",
        ),
    )
