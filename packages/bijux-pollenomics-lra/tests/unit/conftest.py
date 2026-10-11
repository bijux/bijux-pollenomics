"""Shared publication scientific inputs for domain tests."""

import numpy as np
import pytest

from bijux_pollenomics_lra.api import MultisiteRevealsInput


@pytest.fixture
def publication_inputs() -> MultisiteRevealsInput:
    return MultisiteRevealsInput(
        site_ids=("small", "large"),
        bin_ids=("recent",),
        taxon_ids=("A", "B", "C"),
        counts=np.array([[[100, 200, 300]], [[300, 200, 100]]]),
        availability=np.ones((2, 1), dtype=bool),
        basin_radius_m=np.array([[25.0], [100.0]]),
        basin_type=np.array([["peatland"], ["lake"]]),
        bin_bounds_bp=np.array([[0.0, 100.0]]),
        ppe=np.array([1.0, 2.0, 3.0]),
        ppe_covariance=np.diag([0.01, 0.04, 0.09]),
        fall_speed_m_s=np.array([0.02, 0.03, 0.04]),
    )
