"""Read saved native facts without the production sampler or state extractor."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

ORIGINAL_PREFIXES = {
    314159: "ad6e64bb62b24e4bc412f698d5476e7eecf819c3e5171b361be494e20be5a4e9",
    271828: "87c2dcfeeda84d305e8a7d535837fc41bb9b2fa057024229a50fb519ac0592eb",
}
ORIGINAL_BYTES = 5_678_254


def exact_prefix(original: Path, extended: Path, expected_sha256: str) -> int:
    """Require the frozen original bytes plus a fresh following numeric row.

    Native files begin with a blank line and omit the final newline. Comparing
    a parsed matrix would miss formatting or state-serialization changes.
    """
    before = original.read_bytes()
    after = extended.read_bytes()
    if hashlib.sha256(before).hexdigest() != expected_sha256:
        raise ValueError("Original native prefix identity differs")
    if not after.startswith(before) or after[len(before) : len(before) + 1] != b"\n":
        raise ValueError("Extended native output does not preserve the exact prefix")
    if not after[len(before) :].strip():
        raise ValueError("Native output contains no extension beyond its prefix")
    return len(before)


def polynomial_ages(
    states: NDArray[np.float64],
    depths: NDArray[np.float64],
    *,
    top: float = 648.0,
    thickness: float = 5.0,
) -> NDArray[np.float64]:
    """Integrate the closed innovation polynomial at all requested depths.

    For section j, x_j=(1-w)*sum(k=j..K-2,w**(k-j)*alpha_k)
    +w**(K-1-j)*alpha_last. This evaluates powers and direct sums instead of
    the production backwards recurrence. It concerns saved quantized states.
    """
    if states.ndim != 2 or states.shape[1] < 3 or depths.ndim != 1:
        raise ValueError("Independent native age axes are invalid")
    sections = states.shape[1] - 2
    if (
        not np.isfinite(states).all()
        or not np.isfinite(depths).all()
        or not np.isfinite(top)
        or not np.isfinite(thickness)
        or thickness <= 0
        or np.any(states[:, 1:-1] <= 0)
        or np.any((states[:, -1] <= 0) | (states[:, -1] >= 1))
        or np.any((depths < top) | (depths > top + sections * thickness))
    ):
        raise ValueError("Independent native age support is invalid")
    width = np.minimum(
        thickness,
        np.maximum(0.0, depths[:, None] - top - thickness * np.arange(sections)),
    )
    result = np.empty((len(states), len(depths)), dtype=float)
    for start in range(0, len(states), 512):
        block = states[start : start + 512]
        alpha, memory = block[:, 1:-1], block[:, -1, None]
        rates = np.empty_like(alpha)
        for section in range(sections):
            powers = memory ** np.arange(sections - section)
            rates[:, section] = (1 - memory[:, 0]) * np.sum(
                powers[:, :-1] * alpha[:, section:-1], axis=1
            ) + powers[:, -1] * alpha[:, -1]
        result[start : start + len(block)] = block[:, :1] + rates @ width.T
    return result
