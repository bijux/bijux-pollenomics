"""Map-bound admission for exact source-chronology ages."""

from __future__ import annotations

import pytest

from bijux_pollenomics.reporting.map_document.state import build_map_document_state
from bijux_pollenomics.reporting.map_publication import MapScopePolicy


def _policy() -> MapScopePolicy:
    return MapScopePolicy(
        key="source-time-test",
        label="Source time test",
        eyebrow_label="Source time test",
        summary="Source time test",
        bounds_summary="Source time test",
        default_basemap="none",
        initial_diameter_km=0,
        minimum_bounds=((55.0, 10.0), (70.0, 30.0)),
        filter_surfaces=(),
        legend_sections=(),
        visible_caveats=(),
        engine_summary="Source time test",
    )


def test_fractional_source_extrema_expand_global_bounds_outward() -> None:
    state = build_map_document_state(
        policy=_policy(),
        point_layers=[
            {
                "features": [
                    {
                        "latitude": 59,
                        "longitude": 18,
                        "time_start_bp": 0.75,
                        "time_end_bp": 878.26,
                        "temporal_semantics": {
                            "schema_version": "temporal-semantics.v1",
                            "comparability_posture": "numeric_interval_with_caveat",
                            "evidence_class": "direct_numeric_sample_date",
                            "precision_posture": "sample_precise_interval",
                            "comparison_note": "Source fractional endpoints; only navigation bounds round outward.",
                        },
                    }
                ]
            }
        ],
        polygon_layers=[],
    )

    assert state.has_time_data is True
    assert (state.time_min_bp, state.time_max_bp) == (0, 879)
    assert state.initial_time_start_bp == 0
    assert state.initial_time_end_bp == 879
    assert state.initial_time_interval_years == 879
    assert state.source_time_bounds_bp == (0.75, 878.26)


def test_invalid_source_ages_do_not_create_global_time_bounds() -> None:
    state = build_map_document_state(
        policy=_policy(),
        point_layers=[
            {
                "features": [
                    {"time_start_bp": None, "time_end_bp": None},
                    {"time_start_bp": -54, "time_end_bp": -51},
                    {"time_start_bp": 20, "time_end_bp": 10},
                    {"time_start_bp": False, "time_end_bp": 0},
                ]
            }
        ],
        polygon_layers=[],
    )

    assert state.has_time_data is False
    assert (state.time_min_bp, state.time_max_bp) == (0, 0)


@pytest.mark.parametrize(
    "declaration",
    [
        None,
        {},
        {"comparability_posture": "contextual_label_only"},
        {"comparability_posture": "refused", "refusal_reason_code": "source_refusal"},
    ],
)
def test_fractional_numbers_without_source_permission_do_not_create_bounds(
    declaration: dict[str, object] | None,
) -> None:
    feature: dict[str, object] = {
        "latitude": 59,
        "longitude": 18,
        "time_start_bp": 0.75,
        "time_end_bp": 878.26,
    }
    if declaration is not None:
        feature["temporal_semantics"] = declaration
    state = build_map_document_state(
        policy=_policy(), point_layers=[{"features": [feature]}], polygon_layers=[]
    )
    assert not state.has_time_data
    assert state.source_time_bounds_bp is None
    assert feature["time_start_bp"] == 0.75 and feature["time_end_bp"] == 878.26
