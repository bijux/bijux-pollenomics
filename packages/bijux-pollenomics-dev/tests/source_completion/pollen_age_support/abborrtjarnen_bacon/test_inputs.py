"""Check actual source controls against the immutable native sample consumer."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from bijux_pollenomics_dev.source_completion.pollen_age_support.abborrtjarnen_bacon.inputs import (
    read_inputs,
)


def test_retained_core_inputs_bind_all_dates_counts_and_frozen_predictions() -> None:
    repository = Path(__file__).resolve().parents[6]
    source_root = repository.parent / "-bijux-pollenomics-data"
    if not (source_root / "legacyage/zenodo-5815192").is_dir():
        pytest.skip("Original LegacyAge source archive is not installed")
    case = read_inputs(repository, source_root)
    assert len(case.controls) == 7
    assert len(case.sample_ids) == 107 and len(set(case.sample_ids)) == 107
    assert case.counts.shape == (107, 16)
    assert case.predictions.shape == (4, 4, 16)
    np.testing.assert_allclose(case.predictions.sum(axis=2), 1, atol=1e-9, rtol=0)
    assert case.depths[[0, -1]].tolist() == [648, 896]
    assert case.controls[0]["age"] == -52
    assert case.controls[0]["cc"] == 0
    original = {row["sample_id"]: row for row in case.controls[1:]}
    assert original["Poz-4446"]["age"] == 2235
    assert original["Poz-4445"]["error"] == 35
    assert original["Poz-4514"]["depth"] == 880.5
