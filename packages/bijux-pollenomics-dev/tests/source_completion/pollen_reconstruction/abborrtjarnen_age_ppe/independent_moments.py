"""Independent scalar derivatives and population moments for the age mixture."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def fixed_window(
    counts: tuple[int, ...], response: np.ndarray, ppe: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Differentiate inverse correction/closure without production Jacobians."""
    size = len(counts)
    if (
        not size
        or any(type(n) is not int or n < 0 for n in counts)
        or not sum(counts)
        or response.shape != (size,)
        or ppe.shape != (size,)
        or not np.all(np.isfinite(response))
        or not np.all(np.isfinite(ppe))
        or np.any(response <= 0)
        or np.any(ppe <= 0)
    ):
        raise ValueError("Invalid independent window inputs")
    corrected = np.array(
        [n / (k * p) for n, k, p in zip(counts, response, ppe, strict=True)]
    )
    total = float(sum(corrected))
    cover = corrected / total
    gradient = np.empty((size, size))
    derivatives = np.empty((size, size))
    for i in range(size):
        for j in range(size):
            gradient[i, j] = -cover[i] * (int(i == j) - cover[j]) / ppe[j]
            derivatives[i, j] = (int(i == j) - cover[i]) / (
                response[j] * ppe[j] * total
            )
    count_covariance = np.empty((size, size))
    for i in range(size):
        for j in range(size):
            diagonal = sum(
                counts[k] * derivatives[i, k] * derivatives[j, k] for k in range(size)
            )
            left = sum(counts[k] * derivatives[i, k] for k in range(size))
            right = sum(counts[k] * derivatives[j, k] for k in range(size))
            count_covariance[i, j] = diagonal - left * right / sum(counts)
    if not all(np.all(np.isfinite(x)) for x in (cover, count_covariance, gradient)):
        raise ValueError("Independent derivatives are not finite")
    return cover, count_covariance, gradient


def pooled_windows(
    counts: tuple[tuple[int, ...], ...], response: np.ndarray, ppe: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Stack disjoint conditional count blocks and one common PPE axis."""
    size = len(ppe)
    cover = np.empty(len(counts) * size)
    covariance = np.zeros((len(cover), len(cover)))
    gradients = np.empty((len(cover), size))
    for window, n in enumerate(counts):
        c, v, g = fixed_window(n, response, ppe)
        indices = slice(window * size, (window + 1) * size)
        cover[indices] = c
        covariance[indices, indices] = v
        gradients[indices] = g
    return cover, covariance, gradients


@dataclass
class PopulationMoments:
    """Weighted Welford age covariance, with separately accumulated noise terms."""

    sd: np.ndarray
    mean: np.ndarray
    age_second: np.ndarray
    count_sum: np.ndarray
    ppe_sum: np.ndarray
    gradient_sum: np.ndarray
    gradient_second: np.ndarray
    observations: int = 0

    @classmethod
    def empty(cls, axes: int, sd: np.ndarray) -> PopulationMoments:
        """Create zeroed moment accumulators for finite marginal standard deviations."""
        if (
            axes < 1
            or sd.ndim != 1
            or not len(sd)
            or not np.all(np.isfinite(sd))
            or np.any(sd < 0)
        ):
            raise ValueError("Invalid moment axes or marginal SD")
        return cls(
            sd.copy(),
            np.zeros(axes),
            np.zeros((axes, axes)),
            np.zeros((axes, axes)),
            np.zeros((axes, axes)),
            np.zeros((axes, len(sd))),
            np.zeros((axes, axes)),
        )

    def add(
        self,
        cover: np.ndarray,
        counting: np.ndarray,
        gradient: np.ndarray,
        *,
        multiplicity: int = 1,
    ) -> None:
        """Preserve every saved-row weight when identical pools are grouped."""
        if (
            type(multiplicity) is not int
            or multiplicity < 1
            or cover.shape != self.mean.shape
            or counting.shape != self.count_sum.shape
            or gradient.shape != self.gradient_sum.shape
            or not all(np.all(np.isfinite(x)) for x in (cover, counting, gradient))
        ):
            raise ValueError("Invalid mixture contribution")
        new_total = self.observations + multiplicity
        displacement = cover - self.mean
        self.age_second += np.outer(displacement, displacement) * (
            self.observations * multiplicity / new_total
        )
        self.mean += displacement * (multiplicity / new_total)
        self.count_sum += multiplicity * counting
        scaled = gradient * self.sd
        self.ppe_sum += multiplicity * (scaled @ scaled.T)
        old_gradient = (
            self.gradient_sum / self.observations if self.observations else gradient
        )
        gradient_displacement = (gradient - old_gradient) * self.sd
        self.gradient_second += (
            gradient_displacement
            @ gradient_displacement.T
            * (self.observations * multiplicity / new_total)
        )
        self.gradient_sum += multiplicity * gradient
        self.observations = new_total

    def finish(self) -> dict[str, np.ndarray]:
        """Use the population denominator of the exact saved-state distribution."""
        if not self.observations:
            raise ValueError("No complete age membership rows")
        n = self.observations
        age = self.age_second / n
        count = self.count_sum / n
        ppe = self.ppe_sum / n
        gradient = self.gradient_sum / n
        mean_gradient_ppe = (gradient * self.sd) @ (gradient * self.sd).T
        return {
            "mean": self.mean.copy(),
            "age": age,
            "count": count,
            "ppe": ppe,
            "total": age + count + ppe,
            "mean_gradient": gradient,
            "ppe_mean_gradient": mean_gradient_ppe,
            "ppe_gradient_variation": self.gradient_second / n,
        }
