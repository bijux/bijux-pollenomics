from __future__ import annotations

import pytest
from bijux_pollenomics.analysis.fieldwork.evidence_richness.candidates.sampling import (
    _classify_sampling_lake,
    _lake_sampling_fit,
)


@pytest.mark.parametrize(
    ("name", "area_km2", "expected_posture"),
    (
        ("Stor mosse", 1.0, "wetland_context_excluded"),
        ("Kraftverksdamm", 1.0, "engineered_waterbody_excluded"),
        ("Åsen", 0.049, "small_lake_review"),
        ("Åsen", 0.149, "compact_lake_candidate"),
        ("Åsen", 0.15, "sampling_lake_candidate"),
        ("Åsen", None, "sampling_lake_candidate"),
    ),
)
def test_sampling_posture_respects_identity_and_area_boundaries(
    name: str,
    area_km2: float | None,
    expected_posture: str,
) -> None:
    posture, notes = _classify_sampling_lake(name, lake_area_km2=area_km2)

    assert posture == expected_posture
    assert bool(notes) is (posture != "sampling_lake_candidate")


def test_excluded_waterbodies_have_no_sampling_fit() -> None:
    assert (
        _lake_sampling_fit(
            lake_area_km2=1.0,
            lake_sampling_posture="wetland_context_excluded",
        )
        == 0.0
    )
    assert (
        _lake_sampling_fit(
            lake_area_km2=1.0,
            lake_sampling_posture="engineered_waterbody_excluded",
        )
        == 0.0
    )
