"""Ratio delta-method precision from fixed ordered nonoverlapping batches."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any

import numpy as np
from numpy.typing import NDArray

Array = NDArray[np.float64]


def require(condition: bool, message: str) -> None:
    """Raise ValueError when a declared batch-means condition fails."""
    if not condition:
        raise ValueError(message)


@dataclass(frozen=True)
class Chain:
    """Native chain population and ordered batch-deviation summaries."""

    rows: int
    complete: int
    batch_size: int
    joint_mean: Array
    batch_deviations: Array

    @property
    def mean(self) -> Array:
        """Return the conditional cover mean from the joint indicator-cover mean."""
        result: Array = self.joint_mean[1:] / self.joint_mean[0]
        return result


def prepare(covers: Array, defined: NDArray[np.bool_], batch_size: int) -> Chain:
    """An undefined state has a zero ratio numerator, never an observed cover."""
    require(
        covers.ndim == 2
        and covers.shape[1] > 0
        and defined.shape == (len(covers),)
        and defined.dtype == np.bool_,
        "Cover/support array axes differ",
    )
    rows = len(covers)
    require(
        type(batch_size) is int
        and batch_size > 0
        and rows >= 2 * batch_size
        and rows % batch_size == 0,
        "Fixed equal batches must partition every chain row without a tail",
    )
    require(
        bool(np.isfinite(covers[defined]).all())
        and bool(np.isnan(covers[~defined]).all()),
        "Supported covers must be finite; undefined states must remain missing",
    )
    complete = int(defined.sum())
    require(complete > 0, "Empty conditioning event has no ratio mean")
    joint = np.zeros((rows, covers.shape[1] + 1), dtype=float)
    joint[:, 0] = defined
    joint[defined, 1:] = covers[defined]
    with np.errstate(over="ignore", invalid="ignore"):
        joint_mean = joint.mean(axis=0)
        batches = joint.reshape(rows // batch_size, batch_size, -1).mean(axis=1)
        deviations = batches - joint_mean
    require(
        bool(np.isfinite(joint_mean).all()) and bool(np.isfinite(deviations).all()),
        "Nonfinite joint batch arithmetic",
    )
    return Chain(rows, complete, batch_size, joint_mean, deviations)


def scalar_map() -> Array:
    """All twenty components and thirty older-minus-younger contrasts."""
    matrix = np.zeros((50, 20), dtype=float)
    matrix[:20] = np.eye(20)
    row = 20
    for younger, older in combinations(range(4), 2):
        for taxon in range(5):
            matrix[row, 5 * older + taxon] = 1
            matrix[row, 5 * younger + taxon] = -1
            row += 1
    return matrix


def contribution(
    chain: Chain, joint_mean: Array, mean_weight_squared: float, mapping: Array
) -> tuple[Array, Array, float]:
    """Apply the ratio Jacobian to centered joint batch means before products."""
    dimension = len(chain.joint_mean) - 1
    require(
        joint_mean.shape == (dimension + 1,)
        and mapping.ndim == 2
        and mapping.shape[1] == dimension
        and bool(np.isfinite(joint_mean).all())
        and joint_mean[0] > 0
        and bool(np.isfinite(mapping).all())
        and np.isfinite(mean_weight_squared)
        and mean_weight_squared > 0,
        "Ratio Jacobian/mapping domain differs",
    )
    probability = joint_mean[0]
    conditional_mean = joint_mean[1:] / probability
    jacobian = np.column_stack((-conditional_mean, np.eye(dimension))) / probability
    scale = (
        mean_weight_squared
        * chain.batch_size
        / (len(chain.batch_deviations) - 1)
        / chain.rows
    )
    with np.errstate(over="ignore", invalid="ignore", under="ignore"):
        transformed = chain.batch_deviations @ jacobian.T
        scalar_batches = transformed @ mapping.T
        covariance = scale * (transformed.T @ transformed)
        variances = scale * np.square(scalar_batches).sum(axis=0)
        probability_variance = float(
            scale * np.square(chain.batch_deviations[:, 0]).sum()
        )
    require(
        bool(np.isfinite(covariance).all())
        and bool(np.isfinite(variances).all())
        and np.isfinite(probability_variance)
        and bool((variances >= 0).all())
        and probability_variance >= 0,
        "Nonfinite or negative batch variance; no projection is permitted",
    )
    require(
        not bool(((scalar_batches != 0).any(axis=0) & (variances == 0)).any())
        and not (
            bool((chain.batch_deviations[:, 0] != 0).any())
            and probability_variance == 0
        ),
        "Positive batch variation lost through numerical underflow",
    )
    return covariance, variances, probability_variance


def estimate(chains: list[Chain], mapping: Array) -> dict[str, Any]:
    """Pool chain means on their original row weights, retaining serial effects."""
    require(len(chains) == 2, "Exactly two independently seeded chains required")
    require(
        chains[0].joint_mean.shape == chains[1].joint_mean.shape,
        "Chain dimensions differ",
    )
    rows = sum(chain.rows for chain in chains)
    joint_mean = (
        sum(
            (chain.rows * chain.joint_mean for chain in chains),
            np.zeros_like(chains[0].joint_mean),
        )
        / rows
    )
    own = [contribution(chain, chain.joint_mean, 1.0, mapping) for chain in chains]
    pooled = [
        contribution(chain, joint_mean, (chain.rows / rows) ** 2, mapping)
        for chain in chains
    ]
    return {
        "chain_covariances": [entry[0] for entry in own],
        "chain_variances": [entry[1] for entry in own],
        "chain_probability_variances": [entry[2] for entry in own],
        "pooled_joint_mean": joint_mean,
        "pooled_covariance": pooled[0][0] + pooled[1][0],
        "pooled_variances": pooled[0][1] + pooled[1][1],
        "pooled_probability_variance": pooled[0][2] + pooled[1][2],
        "difference_mean": chains[1].mean - chains[0].mean,
        "difference_covariance": own[0][0] + own[1][0],
        "difference_variances": own[0][1] + own[1][1],
    }
