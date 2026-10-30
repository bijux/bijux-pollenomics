"""Source sampling law, exact totals and metadata-addressed stream independence."""

from __future__ import annotations

from dataclasses import replace
import hashlib
from unittest.mock import patch

import numpy as np
from numpy.typing import NDArray
import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty.draws import (
    CountOwner,
    generate_draw_bank,
    nominal_draw_bank,
    owner_stream_index,
)


def test_owner_stream_and_fixed_total_match_independent_multinomial() -> None:
    owner = CountOwner("core/window", (13, 7))
    bank = generate_draw_bank((owner,), replicates=32)
    digest = hashlib.sha256(b"core/window").digest()
    index = tuple(int.from_bytes(digest[i : i + 4], "big") for i in range(0, 32, 4))
    assert owner_stream_index(owner.owner_id) == index
    rng = np.random.Generator(
        np.random.PCG64(np.random.SeedSequence(20261027, spawn_key=(0, *index)))
    )
    expected = np.asarray([rng.multinomial(20, [13 / 20, 7 / 20]) for _ in range(32)])
    np.testing.assert_array_equal(bank.owner(owner.owner_id).samples, expected)
    np.testing.assert_array_equal(expected.sum(axis=1), np.full(32, 20))
    assert not bank.ppe.flags.writeable
    assert not bank.owner(owner.owner_id).samples.flags.writeable


def test_other_owner_values_membership_and_order_do_not_move_streams() -> None:
    first, second = CountOwner("A", (30, 10)), CountOwner("B", (12, 8))
    original = generate_draw_bank((first, second), replicates=24)
    changed = generate_draw_bank(
        (replace(second, counts=(1, 90)), first), replicates=24
    )
    alone = generate_draw_bank((first,), replicates=24)
    for value in (changed, alone):
        np.testing.assert_array_equal(
            value.owner("A").samples, original.owner("A").samples
        )
        np.testing.assert_array_equal(value.ppe, original.ppe)
    assert not np.array_equal(
        original.owner("A").samples[:, 0], original.owner("B").samples[:, 0]
    )


def test_ppe_rejects_the_whole_normal_vector_not_individual_coordinates() -> None:
    bank = generate_draw_bank(
        (CountOwner("A", (1, 0)),),
        replicates=24,
        seed=9,
        ppe_means=(0.1, 0.2),
        ppe_sds=(1.0, 2.0),
    )
    rng = np.random.Generator(
        np.random.PCG64(np.random.SeedSequence(9, spawn_key=(1,)))
    )
    accepted: list[NDArray[np.float64]] = []
    attempts = 0
    while len(accepted) < 24:
        values = rng.normal([0.1, 0.2], [1.0, 2.0])
        attempts += 1
        if min(values) >= 0:
            accepted.append(values)
    assert attempts > 24
    np.testing.assert_array_equal(bank.ppe, np.asarray(accepted))
    np.testing.assert_array_equal(bank.owner("A").samples, np.tile([1, 0], (24, 1)))


@pytest.mark.parametrize(
    "owner",
    [
        CountOwner("A", (True, 1)),
        CountOwner("A", (-1, 2)),
        CountOwner("A", (0, 0)),
        CountOwner("A", (2**53, 1)),
        CountOwner("", (1, 1)),
    ],
)
def test_invalid_count_law_is_refused(owner: CountOwner) -> None:
    with pytest.raises(ValueError):
        generate_draw_bank((owner,), replicates=2)


def test_duplicate_owners_and_nonpositive_replicates_are_refused() -> None:
    owner = CountOwner("A", (1, 1))
    with pytest.raises(ValueError, match="Unique"):
        generate_draw_bank((owner, owner), replicates=2)
    with pytest.raises(ValueError, match="Replicates"):
        generate_draw_bank((owner,), replicates=0)


def test_nominal_bank_preserves_source_rows_without_random_sampling() -> None:
    module = "bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty.draws"
    with (
        patch(module + ".multidraw", side_effect=AssertionError("No count draw")),
        patch(module + ".rnorm_reveals", side_effect=AssertionError("No PPE draw")),
    ):
        bank = nominal_draw_bank((CountOwner("B", (13, 7)), CountOwner("A", (0, 8))))
    assert bank.replicates == 1
    np.testing.assert_array_equal(bank.owner("A").samples, [[0, 8]])
    np.testing.assert_array_equal(bank.owner("B").samples, [[13, 7]])
    np.testing.assert_array_equal(bank.ppe, [[5.106, 1.27]])
    assert not bank.ppe.flags.writeable
    assert not bank.owner("A").samples.flags.writeable
