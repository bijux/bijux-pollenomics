"""Controlled BP playback declares eligibility without changing raw-source admission."""

from copy import deepcopy

import pytest

from bijux_pollenomics.reporting.map_document.temporal_admission import (
    feature_temporal_admission,
)
from bijux_pollenomics_dev.ci.atlas_browser.playback_keyboard_candidate import (
    fixture_points,
)


@pytest.mark.parametrize("index,bp", [(0, 0), (1, 150), (2, 300)])
def test_controlled_point_preserves_numeric_bp(index: int, bp: int) -> None:
    point = fixture_points()[index]
    assert type(point["time_start_bp"]) is int
    assert point["time_start_bp"] == point["time_end_bp"] == bp
    assert point["fixture_status"] == "controlled_bp_chronology_only"
    assert feature_temporal_admission(point) == ("admitted", (float(bp), float(bp)))


@pytest.mark.parametrize("index", [0, 1, 2])
def test_undeclared_raw_numeric_point_stays_contextual(index: int) -> None:
    point = fixture_points()[index]
    del point["temporal_semantics"]
    assert feature_temporal_admission(point) == ("contextual", None)


@pytest.mark.parametrize(
    "posture,status", [("context_only", "contextual"), ("refused", "refused")]
)
def test_source_posture_overrides_controlled_numeric_fields(
    posture: str, status: str
) -> None:
    point = fixture_points()[0]
    point["temporal_semantics"]["comparability_posture"] = posture
    assert feature_temporal_admission(point) == (status, None)


def test_controlled_semantics_are_owned_by_each_point_and_call() -> None:
    points = fixture_points()
    original = deepcopy(points)
    points[0]["temporal_semantics"]["comparability_posture"] = "refused"
    assert points[1:] == original[1:]
    assert fixture_points() == original
