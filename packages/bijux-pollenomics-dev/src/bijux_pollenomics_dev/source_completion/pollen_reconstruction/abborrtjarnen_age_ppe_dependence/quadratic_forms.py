"""Accumulate one common-covariance quadratic form per output or contrast."""

from __future__ import annotations

from collections.abc import Iterable
from itertools import combinations
from typing import Any

import numpy as np

from ..abborrtjarnen_ppe_dependence.calculation import ppe_jacobian
from ..abborrtjarnen_ppe_dependence.sources import TAXA, TAXON_IDS, WINDOWS, require


def scalar_axes() -> list[dict[str, Any]]:
    return [
        {"kind": "component", "window_id": b, "taxon": name, "native_taxon_id": taxon}
        for b in WINDOWS
        for name, taxon in zip(TAXA, TAXON_IDS, strict=True)
    ] + [
        {
            "kind": "contrast",
            "younger_window_id": a,
            "older_window_id": b,
            "taxon": name,
            "native_taxon_id": taxon,
        }
        for a, b in combinations(WINDOWS, 2)
        for name, taxon in zip(TAXA, TAXON_IDS, strict=True)
    ]


def scaled_gradients(
    covers: list[float], ppe: np.ndarray, sd: np.ndarray
) -> np.ndarray:
    """Poaceae is retained as an output, while its zero-SD parameter is fixed."""
    require(
        len(covers) == 20 and ppe.shape == sd.shape == (5,),
        "Cover/parameter axes differ",
    )
    gradient = np.vstack(
        [ppe_jacobian(np.asarray(covers[i : i + 5]), ppe) for i in range(0, 20, 5)]
    )
    require(bool(np.isfinite(gradient).all()), "Saved-cover gradient is nonfinite")
    contrasts = [
        gradient[5 * b + i] - gradient[5 * a + i]
        for a, b in combinations(range(4), 2)
        for i in range(5)
    ]
    result: np.ndarray = np.vstack([gradient, contrasts])[:, :4] * sd[:4]
    require(
        result.shape == (50, 4) and bool(np.isfinite(result).all()),
        "Scaled contrast-gradient axes/domain differ",
    )
    return result


def accumulate(
    rows: Iterable[list[float] | None], ppe: np.ndarray, sd: np.ndarray
) -> tuple[np.ndarray, int, int]:
    """Use compensated outer sums after forming each whole-state contrast."""
    total = np.zeros((50, 4, 4))
    compensation = np.zeros_like(total)
    requested = complete = 0
    for covers in rows:
        requested += 1
        if covers is None:
            continue
        complete += 1
        scaled = scaled_gradients(covers, ppe, sd)
        outer = scaled[:, :, None] * scaled[:, None, :]
        adjusted = outer - compensation
        updated = total + adjusted
        compensation = (updated - total) - adjusted
        total = updated
    require(complete > 0, "No complete saved covers define a covariance form")
    result = total / complete
    require(
        bool(np.isfinite(result).all())
        and np.array_equal(result, result.transpose(0, 2, 1)),
        "Finite quadratic forms are nonfinite or nonsymmetric",
    )
    return result, requested, complete


def reference_scalars(result: dict[str, Any]) -> list[dict[str, float]]:
    """Retain the qualified means and age/count variances without recalculation."""
    source = result["conditional_on_complete"]
    components = source["covariance_components"]
    records = [
        {
            "mean": source["mean"][i],
            "fixed_age_variance": components["age"][i][i],
            "fixed_count_variance": components["count"][i][i],
            "diagonal_ppe_variance": components["shared_ppe"][i][i],
        }
        for i in range(20)
    ]
    axes = scalar_axes()[20:]
    require(
        len(source["contrasts"]) == 30, "Qualified temporal-contrast population differs"
    )
    for identity, contrast in zip(axes, source["contrasts"], strict=True):
        require(
            all(
                contrast[k] == identity[k]
                for k in ("younger_window_id", "older_window_id", "taxon")
            ),
            "Qualified temporal-contrast identity differs",
        )
        records.append(
            {
                "mean": contrast["mean_difference"],
                "fixed_age_variance": contrast["variance_components"]["age"],
                "fixed_count_variance": contrast["variance_components"]["count"],
                "diagonal_ppe_variance": contrast["variance_components"]["shared_ppe"],
            }
        )
    return records
