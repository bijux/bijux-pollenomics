"""Api for the LRA engine."""

from __future__ import annotations

from typing import Any

from bijux_pollenomics_lra.models.configuration import (
    BasinType,
    DistanceWeighting,
    ForwardConfig,
    LoveConfig,
    LoveMethod,
    LRAConfig,
    OptimizedLoveProfile,
    RegionalDrawLoveConfig,
    RevealsConfig,
)
from bijux_pollenomics_lra.models.errors import (
    ConvergenceError,
    LRAError,
    ValidationError,
)
from bijux_pollenomics_lra.models.observation import PollenObservationDraws
from bijux_pollenomics_lra.models.publication import (
    MultisiteRevealsInput,
    PublicationRevealsConfig,
)
from bijux_pollenomics_lra.models.regional_draw_source import (
    RegionalCoverDrawSource,
    publication_bin_bounds_sha256,
)
from bijux_pollenomics_lra.models.results import (
    ForwardResult,
    LoveResult,
    LRAResult,
    LRASeriesResult,
    MultisiteRevealsResult,
    PreparedForwardInputs,
    RevealsResult,
)
from bijux_pollenomics_lra.models.validation import (
    LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE,
)
from bijux_pollenomics_lra.reconstruction.forward import forward_deposition
from bijux_pollenomics_lra.workflows.forward import prepare_forward_inputs
from bijux_pollenomics_lra.workflows.local import (
    run_love,
    run_love_from_regional_draws,
)
from bijux_pollenomics_lra.workflows.multisite import run_reveals_multisite
from bijux_pollenomics_lra.workflows.observation import sample_pollen_observations
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
            "lra.reveals.multisite.publication-source",
            "lra.love.analytical",
            "lra.love.analytical.fall-speed-profile."
            + LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE,
            "lra.love.analytical.multisite-cover-draws.landclimii-2016-v1",
            "lra.love.optimized",
            "lra.love.optimized." + OptimizedLoveProfile.RING_TAXON_PRESERVING.value,
            "lra.series.exact-coordinate",
            "lra.forward.homogeneous-local",
            "lra.forward.prepare-target-geometry",
            "lra.observation.conditional-multinomial",
        ],
        "extension_group": "bijux_pollenomics.extensions",
        "extension_name": "lra",
        "extension_target": "bijux_pollenomics_lra.api:extension_descriptor",
    }


__all__ = [
    "BasinType",
    "ConvergenceError",
    "DistanceWeighting",
    "ForwardConfig",
    "ForwardResult",
    "LRAConfig",
    "LRAError",
    "LRAResult",
    "LRASeriesResult",
    "LoveConfig",
    "LoveMethod",
    "OptimizedLoveProfile",
    "LoveResult",
    "MultisiteRevealsInput",
    "MultisiteRevealsResult",
    "RegionalCoverDrawSource",
    "RegionalDrawLoveConfig",
    "PollenObservationDraws",
    "PreparedForwardInputs",
    "PublicationRevealsConfig",
    "RevealsConfig",
    "RevealsResult",
    "ValidationError",
    "extension_descriptor",
    "forward_deposition",
    "prepare_forward_inputs",
    "publication_bin_bounds_sha256",
    "run_love",
    "run_love_from_regional_draws",
    "run_lra",
    "run_lra_series",
    "run_reveals",
    "run_reveals_multisite",
    "sample_pollen_observations",
]
