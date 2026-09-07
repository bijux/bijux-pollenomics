"""Shared map chronology admission contracts."""

from bijux_pollenomics.reporting.map_document.static_assets.indexes import (
    feature_interval as static_feature_interval,
)
from bijux_pollenomics.reporting.map_document.static_assets.indexes import (
    feature_temporal_admission as static_feature_temporal_admission,
)
from bijux_pollenomics.reporting.map_document.temporal_admission import (
    feature_interval,
    feature_temporal_admission,
)


def test_static_index_exports_share_the_canonical_temporal_admission() -> None:
    assert static_feature_interval is feature_interval
    assert static_feature_temporal_admission is feature_temporal_admission


def test_temporal_admission_preserves_zero_and_refuses_invalid_intervals() -> None:
    assert feature_temporal_admission(
        {"time_start_bp": 0, "time_end_bp": 100}
    ) == ("admitted", (0.0, 100.0))
    assert feature_temporal_admission(
        {"time_start_bp": None, "time_end_bp": None}
    ) == ("absent", None)
    for feature in (
        {"time_start_bp": 100, "time_end_bp": None},
        {"time_start_bp": -1, "time_end_bp": 100},
        {"time_start_bp": 200, "time_end_bp": 100},
        {"time_start_bp": "invalid", "time_end_bp": 100},
    ):
        assert feature_temporal_admission(feature) == ("refused", None)


def test_temporal_semantics_override_numeric_fields_consistently() -> None:
    feature = {
        "time_start_bp": 1,
        "time_end_bp": 999_999,
        "temporal_semantics": {
            "comparability_posture": "refused",
            "refusal_reason_code": "source_age_system_not_comparable",
        },
    }

    assert feature_temporal_admission(feature) == ("refused", None)
    assert feature_interval(feature) is None
