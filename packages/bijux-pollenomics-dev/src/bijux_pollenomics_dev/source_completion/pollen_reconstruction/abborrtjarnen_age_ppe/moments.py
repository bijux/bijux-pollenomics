"""Conditional physical delta moments and population total-covariance mixture."""

from __future__ import annotations

from itertools import combinations
import math
from typing import Any

import numpy as np

from bijux_pollenomics_lra.api import fixed_site_cover_covariance

from ..abborrtjarnen_ppe_dependence.calculation import ppe_jacobian
from ..abborrtjarnen_ppe_dependence.sources import TAXA, WINDOWS, require

COMPONENTS = (
    "age",
    "count",
    "shared_ppe",
    "total",
    "mean_gradient_ppe",
    "age_ppe_interaction",
)


def window_moments(
    counts: tuple[int, ...],
    deposition: np.ndarray,
    ppe: np.ndarray,
    covariance: np.ndarray,
) -> dict[str, np.ndarray]:
    """Reuse the five-taxon inverse and its conditional pooled multinomial law."""
    result = fixed_site_cover_covariance(
        np.array([counts]),
        deposition[None, :],
        ppe,
        covariance,
        taxon_measured=np.ones((1, 5), dtype=bool),
    )
    gradient = ppe_jacobian(result.cover, ppe)
    require(
        bool(
            np.allclose(
                result.ppe_covariance,
                gradient @ covariance @ gradient.T,
                atol=1e-12,
                rtol=0,
            )
        ),
        "Existing physical/PPE Jacobian mismatch",
    )
    return {
        "cover": result.cover,
        "count": result.counting_covariance,
        "gradient": gradient,
    }


def joint_window_moments(
    windows: list[dict[str, np.ndarray]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Stack four source-disjoint windows; share one PPE vector across them."""
    require(len(windows) == 4, "Four complete window moments required")
    cover = np.concatenate([w["cover"] for w in windows])
    gradient = np.vstack([w["gradient"] for w in windows])
    count = np.zeros((20, 20))
    for i, w in enumerate(windows):
        count[i * 5 : (i + 1) * 5, i * 5 : (i + 1) * 5] = w["count"]
    return cover, count, gradient


class PopulationMoments:
    """Welford age covariance and averaged conditional count/PPE components."""

    def __init__(self, covariance: np.ndarray) -> None:
        """Initialize streaming age, count and PPE moments for diagonal covariance."""
        require(
            bool(
                covariance.shape == (5, 5)
                and np.isfinite(covariance).all()
                and np.all(np.diag(covariance) >= 0)
                and np.array_equal(covariance, np.diag(np.diag(covariance)))
            ),
            "This profile requires a finite shared diagonal PPE covariance",
        )
        self.covariance = covariance
        self.n = 0
        self.mean = np.zeros(20)
        self.age_m2 = np.zeros((20, 20))
        self.mean_count = np.zeros((20, 20))
        self.mean_ppe = np.zeros((20, 20))
        self.mean_gradient = np.zeros((20, 5))

    def add(self, cover: np.ndarray, count: np.ndarray, gradient: np.ndarray) -> None:
        """Add one eligible saved state once, retaining its empirical multiplicity."""
        require(
            cover.shape == (20,)
            and count.shape == (20, 20)
            and gradient.shape == (20, 5)
            and all(np.isfinite(v).all() for v in (cover, count, gradient)),
            "Finite moment axes differ",
        )
        self.n += 1
        delta = cover - self.mean
        self.mean += delta / self.n
        self.age_m2 += np.outer(delta, cover - self.mean)
        self.mean_count += (count - self.mean_count) / self.n
        self.mean_ppe += (
            gradient @ self.covariance @ gradient.T - self.mean_ppe
        ) / self.n
        self.mean_gradient += (gradient - self.mean_gradient) / self.n

    def result(self) -> dict[str, Any]:
        """Use finite-mixture population denominator M_C, not sample M_C−1."""
        if not self.n:
            return {
                "status": "refused_no_complete_draws",
                "draws": 0,
                "mean": None,
                "mean_ppe_gradient": None,
                "covariance_components": None,
                "conditional_standard_deviation": None,
                "contrasts": [
                    {
                        "younger_window_id": WINDOWS[a],
                        "older_window_id": WINDOWS[b],
                        "taxon": taxon,
                        "status": "refused_no_complete_draws",
                    }
                    for a, b in combinations(range(4), 2)
                    for taxon in TAXA
                ],
            }
        age = self.age_m2 / self.n
        mean_ppe = self.mean_gradient @ self.covariance @ self.mean_gradient.T
        matrices = {
            "age": age,
            "count": self.mean_count,
            "shared_ppe": self.mean_ppe,
            "total": age + self.mean_count + self.mean_ppe,
            "mean_gradient_ppe": mean_ppe,
            "age_ppe_interaction": self.mean_ppe - mean_ppe,
        }
        checks = {}
        closure = np.kron(np.eye(4), np.ones((1, 5)))
        require(
            bool(np.max(np.abs(closure @ self.mean_gradient)) <= 1e-12),
            "PPE gradient window closure failed",
        )
        require(
            bool(np.allclose(closure @ self.mean, 1, atol=1e-12, rtol=0)),
            "Conditional cover closure failed",
        )
        for name, matrix in matrices.items():
            symmetry = float(np.max(np.abs(matrix - matrix.T)))
            eigen = float(np.linalg.eigvalsh(matrix).min())
            residual = float(np.max(np.abs(closure @ matrix)))
            require(
                bool(
                    np.isfinite(matrix).all()
                    and symmetry <= 1e-12
                    and eigen >= -1e-12
                    and residual <= 1e-12
                ),
                f"Conditional {name} covariance failed numeric checks",
            )
            checks[name] = {
                "maximum_symmetry_residual": symmetry,
                "minimum_eigenvalue": eigen,
                "maximum_window_closure_residual": residual,
            }
        contrasts = []
        for a, b in combinations(range(4), 2):
            for i, taxon in enumerate(TAXA):
                left, right = a * 5 + i, b * 5 + i
                variances = {
                    name: float(
                        matrix[left, left]
                        + matrix[right, right]
                        - matrix[left, right]
                        - matrix[right, left]
                    )
                    for name, matrix in matrices.items()
                }
                require(
                    min(variances.values()) >= -1e-12,
                    "Negative contrast variance beyond roundoff tolerance",
                )
                contrasts.append(
                    {
                        "younger_window_id": WINDOWS[a],
                        "older_window_id": WINDOWS[b],
                        "taxon": taxon,
                        "status": "conditional_on_complete",
                        "mean_difference": float(self.mean[right] - self.mean[left]),
                        "variance_components": variances,
                        "standard_deviation": math.sqrt(max(0.0, variances["total"])),
                    }
                )
        return {
            "status": "conditional_on_complete",
            "draws": self.n,
            "mean": self.mean.tolist(),
            "mean_ppe_gradient": self.mean_gradient.tolist(),
            "covariance_components": {
                name: matrix.tolist() for name, matrix in matrices.items()
            },
            "conditional_standard_deviation": np.sqrt(
                np.maximum(0, np.diag(matrices["total"]))
            ).tolist(),
            "contrasts": contrasts,
            "numeric_checks": checks,
        }
