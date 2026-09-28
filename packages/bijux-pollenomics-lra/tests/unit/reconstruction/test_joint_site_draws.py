"""Explicit multi-source draws retain site geometry and shared PPE identity."""

from __future__ import annotations

import numpy as np
import pytest

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.joint_site_draws import (
    PROFILE,
    joint_site_cover_draws,
)


def _inputs() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    counts = np.array([[9, 1], [1, 9]])
    deposition = np.array([[1.0, 2.0], [4.0, 1.0]])
    indices = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
    count_draws = np.broadcast_to(counts, (4, 2, 2)).copy()
    ppe_draws = np.broadcast_to([1.0, 3.0], (4, 2)).copy()
    return counts, deposition, indices, count_draws, ppe_draws


def test_duplicate_sites_reuse_their_count_draw_and_geometry() -> None:
    counts, deposition, indices, count_draws, ppe_draws = _inputs()
    result = joint_site_cover_draws(
        counts,
        deposition,
        indices,
        count_draws,
        ppe_draws,
        taxon_measured=np.ones_like(counts, dtype=bool),
    )
    first = np.array([18.0, 2.0]) / np.array([1.0, 2.0]) / ppe_draws[0]
    last = np.array([2.0, 18.0]) / np.array([4.0, 1.0]) / ppe_draws[-1]
    np.testing.assert_allclose(result.cover_draws[0], first / first.sum())
    np.testing.assert_allclose(result.cover_draws[-1], last / last.sum())
    np.testing.assert_allclose(result.cover_draws[1], result.cover_draws[2])
    np.testing.assert_allclose(result.cover_draws.sum(axis=1), 1)
    np.testing.assert_allclose(result.mean_cover, result.cover_draws.mean(axis=0))
    assert result.profile == PROFILE
    assert not result.cover_draws.flags.writeable


def test_shared_parameter_and_count_draws_change_paired_cover() -> None:
    counts, deposition, indices, count_draws, ppe_draws = _inputs()
    baseline = joint_site_cover_draws(
        counts,
        deposition,
        indices,
        count_draws,
        ppe_draws,
        taxon_measured=np.ones_like(counts, dtype=bool),
    )
    count_draws[0, 0] = [8, 2]
    ppe_draws[1] = [2.0, 3.0]
    changed = joint_site_cover_draws(
        counts,
        deposition,
        indices,
        count_draws,
        ppe_draws,
        taxon_measured=np.ones_like(counts, dtype=bool),
    )
    assert changed.cover_draws[0, 0] < baseline.cover_draws[0, 0]
    assert changed.cover_draws[1, 0] < baseline.cover_draws[1, 0]
    np.testing.assert_array_equal(changed.cover_draws[2:], baseline.cover_draws[2:])


def test_changed_site_total_and_bad_site_index_are_refused() -> None:
    counts, deposition, indices, count_draws, ppe_draws = _inputs()
    count_draws[0, 0, 0] += 1
    with pytest.raises(ValidationError, match="totals"):
        joint_site_cover_draws(
            counts,
            deposition,
            indices,
            count_draws,
            ppe_draws,
            taxon_measured=np.ones_like(counts, dtype=bool),
        )
    count_draws[0, 0, 0] -= 1
    indices[0, 0] = 2
    with pytest.raises(ValidationError, match="identities"):
        joint_site_cover_draws(
            counts,
            deposition,
            indices,
            count_draws,
            ppe_draws,
            taxon_measured=np.ones_like(counts, dtype=bool),
        )


def test_unmeasured_taxon_is_refused_before_joint_resampling() -> None:
    counts, deposition, indices, count_draws, ppe_draws = _inputs()
    measured = np.ones_like(counts, dtype=bool)
    measured[0, 1] = False
    with pytest.raises(ValidationError) as error:
        joint_site_cover_draws(
            counts, deposition, indices, count_draws, ppe_draws, taxon_measured=measured
        )
    assert error.value.reason_code == "taxon_measurement_unresolved"
