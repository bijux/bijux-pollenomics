from __future__ import annotations

import pytest
from bijux_pollenomics.core.temporal_semantics import (
    InvalidBpIntervalError,
    admit_bp_interval,
    build_temporal_semantics,
    canonical_bp_interval,
    closed_bp_intervals_overlap,
    directional_lag_bounds,
    normalize_temporal_semantics_payload,
)
from hypothesis import given
from hypothesis import strategies as st


@pytest.mark.parametrize(
    ("younger", "older", "reason"),
    (
        (None, 10, "partial_interval"),
        (-1, 10, "negative_bp"),
        (20, 10, "reversed_interval"),
        (float("inf"), 10, "non_finite"),
    ),
)
def test_bp_interval_admission_retains_normative_refusal_reason(
    younger: object,
    older: object,
    reason: str,
) -> None:
    admission = admit_bp_interval(younger, older)

    assert admission.interval is None
    assert not admission.admitted
    assert admission.refusal_reason_code == reason


def test_temporal_semantics_refuses_negative_bounds_without_losing_source_label() -> (
    None
):
    payload = build_temporal_semantics(
        source_family="test",
        evidence_class="direct",
        precision_posture="source_interval",
        comparability_posture="numeric_interval",
        time_start_bp=-10,
        time_end_bp=20,
        time_mean_bp=5,
        summary_label="source interval -10 to 20 BP",
    ).as_dict()

    assert payload["comparability_posture"] == "refused"
    assert payload["refusal_reason_code"] == "negative_bp"
    assert payload["time_start_bp"] is None
    assert payload["time_end_bp"] is None
    assert payload["time_mean_bp"] is None
    assert payload["summary_label"] == "source interval -10 to 20 BP"


def test_serialized_temporal_semantics_cannot_reintroduce_negative_bp() -> None:
    payload = normalize_temporal_semantics_payload(
        {
            "comparability_posture": "numeric_interval",
            "time_start_bp": -0.4,
            "time_end_bp": 20,
            "time_mean_bp": 10,
            "temporal_window_key": "recent_historical",
            "temporal_window_label": "Recent and historical (0-1000 BP)",
        }
    )

    assert payload["comparability_posture"] == "refused"
    assert payload["refusal_reason_code"] == "negative_bp"
    assert payload["time_start_bp"] is None
    assert payload["time_end_bp"] is None
    assert payload["time_mean_bp"] is None
    assert payload["temporal_window_key"] == "unresolved"


@pytest.mark.parametrize(
    ("fixture_id", "source", "target", "expected"),
    (
        ("TIME-001", (5600, 5600), (5500, 5500), (100, 100)),
        ("TIME-002", (5600, 5600), (5499, 5499), (101, 101)),
        ("TIME-003", (5600, 5600), (5501, 5501), (99, 99)),
        ("TIME-004", (5500, 5500), (5500, 5500), (0, 0)),
        ("TIME-005", (5590, 5610), (5490, 5510), (80, 120)),
        ("TIME-006", (5580, 5620), (5500, 5600), (-20, 120)),
        ("TIME-007", (5610, 5630), (5480, 5500), (110, 150)),
        ("TIME-008", (5500, 5520), (5530, 5550), (-50, -10)),
    ),
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_golden_directional_lag_bounds(
    fixture_id: str,
    source: tuple[int, int],
    target: tuple[int, int],
    expected: tuple[int, int],
) -> None:
    del fixture_id
    bounds = directional_lag_bounds(
        canonical_bp_interval(*source),
        canonical_bp_interval(*target),
    )

    assert bounds is not None
    assert (bounds.minimum_lag_years, bounds.maximum_lag_years) == expected


@pytest.mark.parametrize("_fixture_id", [pytest.param("TIME-009", id="TIME-009")])
def test_missing_interval_remains_unresolved(_fixture_id: str) -> None:
    assert directional_lag_bounds(canonical_bp_interval(5500, 5500), None) is None


@pytest.mark.parametrize("_fixture_id", [pytest.param("TIME-010", id="TIME-010")])
def test_zero_bp_is_not_missing(_fixture_id: str) -> None:
    assert canonical_bp_interval(0, 0) is not None
    assert canonical_bp_interval(None, None) is None


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    (
        ((100, 200), (150, 250), True),
        ((100, 300), (150, 200), True),
        ((100, 200), (200, 300), True),
        ((100, 199.999), (200, 300), False),
    ),
)
def test_closed_bp_interval_overlap(
    left: tuple[float, float],
    right: tuple[float, float],
    expected: bool,
) -> None:
    left_interval = canonical_bp_interval(*left)
    right_interval = canonical_bp_interval(*right)

    assert left_interval is not None
    assert right_interval is not None
    assert closed_bp_intervals_overlap(left_interval, right_interval) is expected


@pytest.mark.parametrize(
    ("fixture_id", "younger", "older"),
    (
        ("TIME-011", 5600, 5500),
        ("TIME-012", 5500, None),
        ("non-finite", float("nan"), 5500),
        ("negative", -1, 0),
    ),
)
def test_invalid_canonical_intervals_are_refused(
    fixture_id: str,
    younger: float | None,
    older: float | None,
) -> None:
    del fixture_id
    with pytest.raises(InvalidBpIntervalError):
        canonical_bp_interval(younger, older)


@given(
    source_younger=st.integers(min_value=0, max_value=100_000),
    source_width=st.integers(min_value=0, max_value=10_000),
    target_younger=st.integers(min_value=0, max_value=100_000),
    target_width=st.integers(min_value=0, max_value=10_000),
)
def test_directional_lag_bounds_are_ordered_for_every_canonical_pair(
    source_younger: int,
    source_width: int,
    target_younger: int,
    target_width: int,
) -> None:
    bounds = directional_lag_bounds(
        canonical_bp_interval(source_younger, source_younger + source_width),
        canonical_bp_interval(target_younger, target_younger + target_width),
    )

    assert bounds is not None
    assert bounds.minimum_lag_years <= bounds.maximum_lag_years
