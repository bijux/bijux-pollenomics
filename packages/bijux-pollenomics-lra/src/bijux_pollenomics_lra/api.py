"""Api for the LRA engine."""

from __future__ import annotations

from typing import Any

from bijux_pollenomics_lra.models.configuration import (
    BasinType,
    DistanceWeighting,
    LoveConfig,
    LoveMethod,
    LRAConfig,
    RevealsConfig,
)
from bijux_pollenomics_lra.models.errors import (
    ConvergenceError,
    LRAError,
    ValidationError,
)
from bijux_pollenomics_lra.models.results import (
    ForwardResult,
    LoveResult,
    LRAResult,
    LRASeriesResult,
    RevealsResult,
)
from bijux_pollenomics_lra.reconstruction.forward import forward_deposition
from bijux_pollenomics_lra.workflows.local import run_love
from bijux_pollenomics_lra.workflows.paired import run_lra
from bijux_pollenomics_lra.workflows.regional import run_reveals
from bijux_pollenomics_lra.workflows.series import run_lra_series


def extension_descriptor() -> dict[str, Any]:
    """Return the optional-extension descriptor for host registration."""
    from bijux_pollenomics_lra.version import NUMERICAL_BACKEND, __version__

    return {
        "schema_version": "1.0.0",
        "distribution": "bijux-pollenomics-lra",
        "import_package": "bijux_pollenomics_lra",
        "version": __version__,
        "python": ">=3.11,<4",
        "numerical_backend": NUMERICAL_BACKEND,
        "python_api": "bijux_pollenomics_lra.api",
        "license": "GPL-2.0-or-later",
        "integration_mode": "optional-separate-distribution",
        "capabilities": [
            "lra.reveals.regional",
            "lra.love.analytical",
            "lra.love.optimized",
            "lra.series.exact-coordinate",
            "lra.forward.homogeneous-local",
        ],
        "extension_group": "bijux_pollenomics.extensions",
        "extension_name": "lra",
        "extension_target": "bijux_pollenomics_lra.api:extension_descriptor",
    }


__all__ = [
    "BasinType",
    "DistanceWeighting",
    "LRAConfig",
    "LRAError",
    "ForwardResult",
    "forward_deposition",
    "ConvergenceError",
    "LRAResult",
    "LRASeriesResult",
    "LoveConfig",
    "LoveMethod",
    "LoveResult",
    "RevealsConfig",
    "RevealsResult",
    "ValidationError",
    "run_love",
    "run_lra",
    "run_lra_series",
    "run_reveals",
    "extension_descriptor",
]
