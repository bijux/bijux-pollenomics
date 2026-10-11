"""Forward pollen deposition with homogeneous local vegetation across rings."""

from __future__ import annotations

import numpy as np

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.results import ForwardResult
from bijux_pollenomics_lra.models.validation import matrix, vector


def _deposition_components(
    cover: np.ndarray,
    regional: np.ndarray,
    kernels: np.ndarray,
    fractions: np.ndarray,
    productivity: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Shared equation after the profile-specific caller validates its inputs."""
    local = np.sum(
        kernels * (cover * productivity)[None, :] * fractions[:, None], axis=0
    )
    return local, local + regional


def forward_deposition(
    local_cover: object,
    regional_deposition: object,
    local_k: object,
    terrestrial_fraction: object,
    ppe: object,
) -> ForwardResult:
    """Predict pollen fractions using the explicit DISQOVER homogeneous profile.

    Cover is a closed taxon fraction vector, never percentages. Regional input
    is already PPE-weighted pollen deposition, in the same arbitrary deposition
    units as the local kernel. Every ring uses the same local cover vector.
    Inputs are not mutated; result arrays own their data. The host retains the
    taxon order, time support and parameter/geometry source identities.
    """
    cover = vector(local_cover, "local_cover", nonnegative=True)
    regional = vector(regional_deposition, "regional_deposition", nonnegative=True)
    productivity = vector(ppe, "ppe", positive=True)
    kernels = matrix(local_k, "local_k", nonnegative=True)
    fractions = vector(terrestrial_fraction, "terrestrial_fraction", nonnegative=True)
    if regional.shape != cover.shape or productivity.shape != cover.shape:
        raise ValidationError(
            "Forward cover, regional deposition and PPE taxon dimensions must match"
        )
    if kernels.shape != (fractions.size, cover.size):
        raise ValidationError("Forward local_k must have exactly (rings, taxa) shape")
    if np.any(fractions > 1):
        raise ValidationError("terrestrial_fraction must lie in [0, 1]")
    if not np.isclose(cover.sum(), 1.0, rtol=0, atol=1e-12):
        raise ValidationError("local_cover must sum to one as fractions")
    local, total = _deposition_components(
        cover, regional, kernels, fractions, productivity
    )
    mass = total.sum()
    if not np.isfinite(total).all() or not np.isfinite(mass) or mass <= 0:
        raise ValidationError("Forward deposition has nonfinite or zero total mass")
    return ForwardResult(
        pollen_fraction=np.array(total / mass, copy=True),
        local_deposition=np.array(local, copy=True),
        regional_deposition=np.array(regional, copy=True),
        total_deposition=np.array(total, copy=True),
    )
