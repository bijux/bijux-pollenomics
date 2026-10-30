"""Independent owner count streams and one shared source-compatible PPE stream."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

import numpy as np
from numpy.typing import NDArray

from bijux_pollenomics_lra.reconstruction.draws import multidraw, rnorm_reveals

PPE_MEANS = (5.106, 1.27)
PPE_SDS = (0.303, 0.05)


@dataclass(frozen=True)
class CountOwner:
    """One physical core/window count vector on the literal two-taxon axis."""

    owner_id: str
    counts: tuple[int, int]


@dataclass(frozen=True)
class OwnerDraws:
    """Reusable fixed-total replicates from one metadata-addressed stream."""

    owner_id: str
    stream_index: tuple[int, ...]
    counts: tuple[int, int]
    samples: NDArray[np.int64]


@dataclass(frozen=True)
class DrawBank:
    """Draw accounting; a complete bank is never a fold's scientific ancestry."""

    replicates: int
    seed: int
    ppe_means: tuple[float, float]
    ppe_sds: tuple[float, float]
    ppe: NDArray[np.float64]
    owners: tuple[OwnerDraws, ...]

    def owner(self, owner_id: str) -> OwnerDraws:
        """Return only the explicitly requested physical owner's replicates."""
        matches = [owner for owner in self.owners if owner.owner_id == owner_id]
        if len(matches) != 1:
            raise ValueError("Exactly one declared count owner is required")
        return matches[0]


def owner_stream_index(owner_id: str) -> tuple[int, ...]:
    """Address a count stream by metadata alone, independent of bank membership."""
    if not isinstance(owner_id, str) or not owner_id or owner_id.strip() != owner_id:
        raise ValueError("A nonempty canonical owner identity is required")
    identity = hashlib.sha256(owner_id.encode("utf-8")).digest()
    return tuple(int.from_bytes(identity[i : i + 4], "big") for i in range(0, 32, 4))


def _validate_owners(owners: tuple[CountOwner, ...]) -> None:
    if not owners or len({owner.owner_id for owner in owners}) != len(owners):
        raise ValueError("Unique nonempty count owners are required")
    streams = tuple(owner_stream_index(owner.owner_id) for owner in owners)
    if len(set(streams)) != len(streams):
        raise ValueError("Owner stream identities collide")
    for owner in owners:
        if (
            len(owner.counts) != 2
            or any(type(n) is not int or n < 0 for n in owner.counts)
            or not 0 < sum(owner.counts) <= 2**53
        ):
            raise ValueError(
                "Exact nonnegative counts and positive safe total required"
            )


def nominal_draw_bank(
    owners: tuple[CountOwner, ...], *, ppe_means: tuple[float, float] = PPE_MEANS
) -> DrawBank:
    """Supply one original count/PPE row without invoking any random generator."""
    _validate_owners(owners)
    if len(ppe_means) != 2 or not np.isfinite(ppe_means).all() or min(ppe_means) <= 0:
        raise ValueError("Finite positive nominal PPE required")
    rows = []
    for owner in sorted(owners, key=lambda value: value.owner_id):
        samples = np.asarray([owner.counts], dtype=np.int64)
        samples.setflags(write=False)
        rows.append(
            OwnerDraws(
                owner.owner_id,
                owner_stream_index(owner.owner_id),
                owner.counts,
                samples,
            )
        )
    ppe = np.asarray([ppe_means], dtype=np.float64)
    ppe.setflags(write=False)
    return DrawBank(1, 20261027, ppe_means, PPE_SDS, ppe, tuple(rows))


def generate_draw_bank(
    owners: tuple[CountOwner, ...],
    *,
    replicates: int = 1024,
    seed: int = 20261027,
    ppe_means: tuple[float, float] = PPE_MEANS,
    ppe_sds: tuple[float, float] = PPE_SDS,
) -> DrawBank:
    """Use the engine's fixed-total counts and whole-vector normal rejection law.

    Count streams use ``(0, *owner_stream_index)``; PPE uses ``(1,)`` in
    PCG64 SeedSequence spawn keys. Neither source values nor owner enumeration
    select streams. Counts/PPE are independent conditional working laws.
    """
    if type(replicates) is not int or not 1 <= replicates <= 1024:
        raise ValueError("Replicates must be an integer in [1, 1024]")
    if type(seed) is not int or seed < 0:
        raise ValueError("Seed must be a nonnegative integer")
    _validate_owners(owners)
    if len(ppe_means) != 2 or len(ppe_sds) != 2:
        raise ValueError("The declared two-taxon PPE axis is required")
    if (
        not np.isfinite(ppe_means).all()
        or not np.isfinite(ppe_sds).all()
        or np.any(np.asarray(ppe_means) <= 0)
        or np.any(np.asarray(ppe_sds) < 0)
    ):
        raise ValueError("Finite positive nominal PPE and nonnegative SD required")
    count_draws: list[OwnerDraws] = []
    for owner in sorted(owners, key=lambda value: value.owner_id):
        index = owner_stream_index(owner.owner_id)
        rng = np.random.Generator(
            np.random.PCG64(np.random.SeedSequence(seed, spawn_key=(0, *index)))
        )
        samples = np.asarray(
            [multidraw(owner.counts, rng=rng) for _ in range(replicates)],
            dtype=np.int64,
        )
        samples.setflags(write=False)
        count_draws.append(OwnerDraws(owner.owner_id, index, owner.counts, samples))
    ppe_rng = np.random.Generator(
        np.random.PCG64(np.random.SeedSequence(seed, spawn_key=(1,)))
    )
    ppe = np.asarray(
        [rnorm_reveals(2, ppe_means, ppe_sds, rng=ppe_rng) for _ in range(replicates)],
        dtype=np.float64,
    )
    ppe.setflags(write=False)
    return DrawBank(replicates, seed, ppe_means, ppe_sds, ppe, tuple(count_draws))
