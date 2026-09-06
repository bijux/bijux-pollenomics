"""Canonical interval and mutually exclusive candidate status policy."""

from __future__ import annotations

import pytest
from bijux_pollenomics.analysis.propagation.candidates import (
    DEFAULT_PROPAGATION_SCENARIO,
    classify_candidate_propagation,
)
from bijux_pollenomics.analysis.propagation.candidates.scoring import _windows_overlap
from bijux_pollenomics.core.temporal_semantics import canonical_bp_interval
from hypothesis import given
from hypothesis import strategies as st

from .support import locality


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    (
        pytest.param((100, 200, 150), (150, 250, 200), True, id="overlap"),
        pytest.param((100, 300, 200), (150, 200, 175), True, id="containment"),
        pytest.param((100, 200, 150), (200, 300, 250), True, id="endpoint-touch"),
        pytest.param((100, 199, 150), (200, 300, 250), False, id="disjoint"),
        pytest.param((300, 100, 200), (150, 200, 175), False, id="reversed"),
        pytest.param((-1, 100, 50), (0, 50, 25), False, id="negative"),
        pytest.param((None, None, None), (0, 0, 0), False, id="null"),
        pytest.param((None, 100, None), (0, 0, 0), False, id="partial-null"),
        pytest.param((0, 0, 0), (0, 0, 0), True, id="zero-bp"),
    ),
)
def test_direct_chronology_overlap_uses_canonical_closed_bp_intervals(
    left: tuple[int | None, int | None, int | None],
    right: tuple[int | None, int | None, int | None],
    expected: bool,
) -> None:
    assert (
        _windows_overlap(
            locality(1, chronology=left),
            locality(1, chronology=right),
        )
        is expected
    )


@pytest.mark.parametrize(
    ("distance_km", "source", "target", "expected_status", "expected_arrow"),
    (
        pytest.param(
            16.0, (5600, 5600), (5500, 5500), "definite_candidate", True, id="PROP-001"
        ),
        pytest.param(
            100.0, (5600, 5600), (5500, 5500), "definite_candidate", True, id="PROP-002"
        ),
        pytest.param(
            100.001,
            (5600, 5600),
            (5500, 5500),
            "excluded_spatial",
            False,
            id="PROP-003",
        ),
        pytest.param(
            16.0,
            (5600, 5600),
            (5499, 5499),
            "excluded_temporal_too_large",
            False,
            id="PROP-004",
        ),
        pytest.param(
            16.0, (5590, 5610), (5490, 5510), "possible_candidate", True, id="PROP-005"
        ),
        pytest.param(
            16.0,
            (5580, 5620),
            (5500, 5600),
            "indeterminate_order",
            False,
            id="PROP-006",
        ),
        pytest.param(16.0, None, (5500, 5500), "unresolved", False, id="PROP-007"),
        pytest.param(
            16.0,
            (5500, 5500),
            (5500, 5500),
            "excluded_temporal_nonpositive",
            False,
            id="zero-lag",
        ),
    ),
)
def test_golden_candidate_propagation_statuses(
    distance_km: float,
    source: tuple[int, int] | None,
    target: tuple[int, int] | None,
    expected_status: str,
    expected_arrow: bool,
) -> None:
    decision = classify_candidate_propagation(
        distance_km_unrounded=distance_km,
        source_interval=canonical_bp_interval(*source) if source else None,
        target_interval=canonical_bp_interval(*target) if target else None,
    )

    assert decision.candidate_status == expected_status
    assert decision.directional_arrow_allowed is expected_arrow
    assert decision.reason_code


@given(
    distance=st.floats(
        min_value=0,
        max_value=500,
        allow_nan=False,
        allow_infinity=False,
    ),
    source_age=st.integers(min_value=0, max_value=100_000),
    target_age=st.integers(min_value=0, max_value=100_000),
)
def test_candidate_status_is_mutually_exclusive_and_arrow_safe(
    distance: float,
    source_age: int,
    target_age: int,
) -> None:
    decision = classify_candidate_propagation(
        distance_km_unrounded=distance,
        source_interval=canonical_bp_interval(source_age, source_age),
        target_interval=canonical_bp_interval(target_age, target_age),
        scenario=DEFAULT_PROPAGATION_SCENARIO,
    )

    assert decision.candidate_status in {
        "definite_candidate",
        "possible_candidate",
        "indeterminate_order",
        "unresolved",
        "excluded_spatial",
        "excluded_temporal_nonpositive",
        "excluded_temporal_too_large",
    }
    assert decision.directional_arrow_allowed is (
        decision.candidate_status in {"definite_candidate", "possible_candidate"}
    )
