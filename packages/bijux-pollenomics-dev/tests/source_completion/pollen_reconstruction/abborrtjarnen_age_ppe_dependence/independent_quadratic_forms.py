"""Reconstruct finite age-averaged gradient forms from saved cover rows."""

from __future__ import annotations

from itertools import combinations
from typing import Any

import numpy as np
from numpy.typing import NDArray

AXIS = ("Betula", "Cyperaceae", "Juniperus communis", "Pinus sylvestris", "Poaceae")
TAXON_IDS = (29, 74, 4416, 1287, 417)
BINS = (3, 4, 5, 9)
Array = NDArray[np.float64]


def scalar_axes() -> list[dict[str, Any]]:
    return [
        {"kind": "component", "window_id": b, "taxon": name, "native_taxon_id": taxon}
        for b in BINS
        for name, taxon in zip(AXIS, TAXON_IDS, strict=True)
    ] + [
        {
            "kind": "contrast",
            "younger_window_id": a,
            "older_window_id": b,
            "taxon": name,
            "native_taxon_id": taxon,
        }
        for a, b in combinations(BINS, 2)
        for name, taxon in zip(AXIS, TAXON_IDS, strict=True)
    ]


def gradients(covers: Array, ppe: Array, sd: Array) -> Array:
    """Differentiate inverse-PPE closure; zero reference SD removes no output."""
    if (
        covers.ndim != 2
        or covers.shape[1] != 20
        or ppe.shape != (5,)
        or sd.shape != (5,)
    ):
        raise ValueError("Cover or parameter axes differ")
    if (
        not np.isfinite(covers).all()
        or not np.isfinite(ppe).all()
        or not np.isfinite(sd).all()
        or (ppe <= 0).any()
        or (sd[:4] <= 0).any()
        or sd[4] != 0
    ):
        raise ValueError("Finite positive-PPE/four-SD domain differs")
    c = covers.reshape(-1, 4, 5)
    if (
        (c < 0).any()
        or (c > 1).any()
        or not np.allclose(c.sum(axis=2), 1, rtol=0, atol=1e-12)
    ):
        raise ValueError("Saved cover simplex differs")
    result = c[:, :, :, None] * c[:, :, None, :4]
    for j in range(4):
        result[:, :, j, j] -= c[:, :, j]
    result *= (sd[:4] / ppe[:4])[None, None, None, :]
    return result.reshape(-1, 20, 4)


def quadratic_forms(covers: Array, ppe: Array, sd: Array) -> Array:
    g = gradients(covers, ppe, sd)
    if not len(g):
        raise ValueError("No complete finite-age population")
    vectors = [g[:, i] for i in range(20)]
    vectors.extend(
        g[:, 5 * b + t] - g[:, 5 * a + t]
        for a, b in combinations(range(4), 2)
        for t in range(5)
    )
    return np.asarray([v.T @ v / len(v) for v in vectors])


def compare_forms(actual: Any, expected: Array) -> float:
    value = np.asarray(actual, dtype=float)
    if value.shape != expected.shape or not np.isfinite(value).all():
        raise ValueError("Saved finite Q axes/domain differ")
    difference = np.abs(value - expected)
    if np.any(difference > 1e-18 + 1e-11 * np.abs(expected)):
        raise ValueError("Saved Q differs from independent cover derivatives")
    return float(difference.max(initial=0))
