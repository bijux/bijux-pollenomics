"""Signed synthetic calendar admission retains exact support and legacy refusal."""

from __future__ import annotations

import copy
import json
from typing import Any

import pytest

from bijux_pollenomics.core.calendar_support import (
    SIGNED_CALENDAR_PROFILE,
    SignedCalendarSupport,
)
from bijux_pollenomics.reporting.map_document.native_lra import (
    native_view_bytes,
    select_native_rows,
    validate_native_layers,
)
from bijux_pollenomics.reporting.map_document.state import build_map_document_state
from bijux_pollenomics.reporting.map_document.temporal_admission import (
    feature_interval,
    feature_temporal_admission,
)
from bijux_pollenomics.reporting.scope_policy import MAP_SCOPE_POLICIES

from .signed_support import signed_fixture
from .support import selection_fixture


@pytest.mark.parametrize("bounds", [(-50.75, -49.25), (-0.5, 0.25), (0, 0), (10, 20)])
def test_exact_signed_state_and_native_selection(
    bounds: tuple[int | float, int | float],
) -> None:
    view, layers = signed_fixture(*bounds)
    assert json.loads(native_view_bytes(view)) == view
    validate_native_layers(view, layers)
    feature = layers[0]["features"][0]
    assert feature_temporal_admission(feature) == ("refused", None)
    assert feature_interval(feature, temporal_profile=SIGNED_CALENDAR_PROFILE) == bounds
    state = build_map_document_state(
        policy=MAP_SCOPE_POLICIES["custom"],
        point_layers=layers,
        polygon_layers=[],
        temporal_profile=SIGNED_CALENDAR_PROFILE,
    )
    assert state.source_time_bounds_bp == bounds
    assert (state.initial_time_start_bp, state.initial_time_end_bp) == bounds
    assert state.initial_time_interval_years == bounds[1] - bounds[0]
    context = {
        "time_window_bp": list(bounds),
        "active_layer_keys": [layer["key"] for layer in layers],
        "temporal_profile": SIGNED_CALENDAR_PROFILE,
        "temporal_axis": "BP1950",
    }
    selected = select_native_rows(view, selection_fixture(view), context)
    assert selected["selected_row_ids"] == ["r0", "r1"]
    assert selected["counts"] == {
        "selected_rows": 2,
        "mapped_anchors": 2,
        "refused_sites": 0,
        "missing_values": 1,
    }
    assert selected["global_context"] == {
        **context,
        "active_layer_keys": sorted(context["active_layer_keys"]),
    }
    context["time_window_bp"] = [bounds[1], bounds[1]]
    assert (
        len(
            select_native_rows(view, selection_fixture(view), context)[
                "mapped_anchor_ids"
            ]
        )
        == 2
    )
    context["time_window_bp"] = [bounds[1] + 1, bounds[1] + 1]
    with pytest.raises(ValueError, match="outside its declared extent"):
        select_native_rows(view, selection_fixture(view), context)


@pytest.mark.parametrize(
    "value",
    [None, True, "-0.5", float("nan"), float("inf"), 2**53, float(2**53), -1e308],
)
def test_raw_signed_feature_endpoints_cannot_override_support(value: object) -> None:
    view, layers = signed_fixture()
    layers[0]["features"][0]["time_start_bp"] = value
    assert feature_temporal_admission(
        layers[0]["features"][0], temporal_profile=SIGNED_CALENDAR_PROFILE
    ) == ("refused", None)
    with pytest.raises(ValueError):
        validate_native_layers(view, layers)


@pytest.mark.parametrize(
    "field,value",
    [
        ("data_kind", "source_observations"),
        ("age_type", "radiocarbon_bp"),
        ("evidence_role", "source_chronology"),
    ],
)
def test_signed_generic_source_labels_remain_unadmitted(field: str, value: str) -> None:
    _, layers = signed_fixture()
    feature = layers[0]["features"][0]
    feature[field] = value
    assert feature_interval(feature, temporal_profile=SIGNED_CALENDAR_PROFILE) is None


@pytest.mark.parametrize(
    "mutation",
    [
        "profile",
        "axis",
        "missing",
        "calibration",
        "half_open",
        "raw_age",
        "geometry_refused_age",
        "bin",
    ],
)
def test_complete_view_support_domain_refuses_partial_or_relabelled_claims(
    mutation: str,
) -> None:
    view, _ = signed_fixture()
    row = view["rows"][0]
    if mutation == "profile":
        view["temporal_profile"] = "unknown"
    elif mutation == "axis":
        view["temporal_axis"] = "CE"
    elif mutation == "missing":
        row["source_calendar_support"] = None
    elif mutation == "calibration":
        row["source_calendar_support"]["calibration_status"] = "calibrated"
    elif mutation == "half_open":
        row["source_calendar_support"] = SignedCalendarSupport(
            -50.75,
            -49.25,
            support_kind="calendar_time_support",
            younger_inclusive=False,
        ).as_dict()
    elif mutation == "raw_age":
        row["age_support_bp"] = [[-50.5, -49.25]]
    elif mutation == "geometry_refused_age":
        view["rows"][-1]["age_type"] = "calibrated_bp"
    else:
        row["declared_bin"]["younger_bp"] = -50
    with pytest.raises(ValueError):
        native_view_bytes(view)


def test_signed_global_context_requires_exact_profile_and_retains_subyear_window() -> (
    None
):
    view, _ = signed_fixture()
    context: dict[str, Any] = {
        "time_window_bp": [-50.5, -50.25],
        "active_layer_keys": ["layer-r", "layer-l"],
        "temporal_profile": SIGNED_CALENDAR_PROFILE,
        "temporal_axis": "BP1950",
    }
    assert select_native_rows(view, selection_fixture(view), context)["global_context"][
        "time_window_bp"
    ] == [-50.5, -50.25]
    for key in ("temporal_profile", "temporal_axis"):
        changed = copy.deepcopy(context)
        del changed[key]
        with pytest.raises(ValueError):
            select_native_rows(view, selection_fixture(view), changed)


def test_derived_display_span_outside_browser_domain_refuses() -> None:
    _, layers = signed_fixture(-(2**53 - 1), 2**53 - 1)
    with pytest.raises(ValueError, match="span"):
        build_map_document_state(
            policy=MAP_SCOPE_POLICIES["custom"],
            point_layers=layers,
            polygon_layers=[],
            temporal_profile=SIGNED_CALENDAR_PROFILE,
        )


def test_distinct_regional_local_ages_remain_valid_inside_shared_bin() -> None:
    view, layers = signed_fixture()
    for row, layer, bounds in zip(
        view["rows"], layers, [(-50.5, -50.25), (-50.0, -49.5)], strict=True
    ):
        source = SignedCalendarSupport(
            *bounds, support_kind="closed_age_support"
        ).as_dict()
        row["source_calendar_support"] = source
        row["age_support_bp"] = [list(bounds)]
        layer["features"][0]["source_calendar_support"] = source.copy()
        layer["features"][0]["source_age_support_bp"] = [list(bounds)]
    native_view_bytes(view)
    validate_native_layers(view, layers)


@pytest.mark.parametrize(
    "case", ["changed_envelope", "second_site", "second_sample", "same_sample_ages"]
)
def test_role_sample_and_full_bin_closure_refuses_coherent_partial_changes(
    case: str,
) -> None:
    view, layers = signed_fixture()
    if case == "changed_envelope":
        row, feature = view["rows"][1], layers[1]["features"][0]
        row["declared_bin"]["older_bp"] = -49.0
        row["declared_calendar_support"]["older_bp"] = -49.0
        feature["time_end_bp"] = -49.0
        feature["declared_calendar_support"]["older_bp"] = -49.0
    else:
        added = copy.deepcopy(view["rows"][1])
        added["row_id"] = "r2"
        view["rows"].append(added)
        if case == "second_site":
            added["site_id"] = "another-site"
            added["sample_id"] = "another-sample"
            site = copy.deepcopy(view["sites"][1])
            site.update(
                site_id="another-site",
                model_row_ids=["r2"],
                anchor_id="another-anchor",
                layer_key="another-layer",
            )
            view["sites"].append(site)
        else:
            view["sites"][1]["model_row_ids"].append("r2")
            if case == "second_sample":
                added["sample_id"] = "another-sample"
            else:
                added["age_support_bp"][0][0] = -50.5
                added["source_calendar_support"]["younger_bp"] = -50.5
    with pytest.raises(ValueError):
        native_view_bytes(view)


def test_one_geometry_refused_role_keeps_valid_age_and_selected_rows() -> None:
    view, layers = signed_fixture()
    view["sites"][1].update(
        map_status="refused",
        reason_codes=["synthetic_geometry_not_supplied"],
        anchor_id=None,
        layer_key=None,
    )
    validate_native_layers(view, layers[:1])
    context = {
        "time_window_bp": [-50.5, -50.25],
        "active_layer_keys": [],
        "temporal_profile": SIGNED_CALENDAR_PROFILE,
        "temporal_axis": "BP1950",
    }
    selected = select_native_rows(view, selection_fixture(view), context)
    assert selected["selected_row_ids"] == ["r1"]
    assert selected["counts"] == {
        "selected_rows": 1,
        "mapped_anchors": 0,
        "refused_sites": 1,
        "missing_values": 1,
    }


@pytest.mark.parametrize("legacy", [None, {}, {"comparability_posture": "refused"}])
def test_signed_features_cannot_bypass_legacy_temporal_semantics(
    legacy: object,
) -> None:
    view, layers = signed_fixture()
    layers[0]["features"][0]["temporal_semantics"] = legacy
    with pytest.raises(ValueError):
        validate_native_layers(view, layers)


def test_numeric_value_join_matches_browser_without_erasing_raw_bytes() -> None:
    view, layers = signed_fixture(0, 0)
    for row, layer in zip(view["rows"], layers, strict=True):
        for key in ("source_calendar_support", "declared_calendar_support"):
            row[key]["younger_bp"] = 0.0
            row[key]["older_bp"] = 0.0
            layer["features"][0][key] = row[key].copy()
    encoded = native_view_bytes(view)
    validate_native_layers(view, layers)
    assert b'"age_support_bp":[[0,0]]' in encoded
    assert b'"younger_bp":0.0' in encoded
    layers[0]["features"][0]["time_start_bp"] = False
    with pytest.raises(ValueError):
        validate_native_layers(view, layers)


@pytest.mark.parametrize("window", [[-50.8, -50.5], [-50.5, -49.2], [-100, 100]])
def test_signed_selection_refuses_partial_or_complete_extent_overrun(
    window: list[float],
) -> None:
    view, layers = signed_fixture()
    context = {
        "time_window_bp": window,
        "active_layer_keys": [layer["key"] for layer in layers],
        "temporal_profile": SIGNED_CALENDAR_PROFILE,
        "temporal_axis": "BP1950",
    }
    with pytest.raises(ValueError, match="outside its declared extent"):
        select_native_rows(view, selection_fixture(view), context)


def test_all_geometry_refused_rows_keep_their_actual_signed_envelope() -> None:
    view, _layers = signed_fixture()
    for site in view["sites"]:
        site.update(
            map_status="refused",
            reason_codes=["synthetic_geometry_not_supplied"],
            anchor_id=None,
            layer_key=None,
        )
    validate_native_layers(view, [])
    context = {
        "time_window_bp": [-50.5, -50.25],
        "active_layer_keys": [],
        "temporal_profile": SIGNED_CALENDAR_PROFILE,
        "temporal_axis": "BP1950",
    }
    result = select_native_rows(view, selection_fixture(view), context)
    assert result["selected_row_ids"] == ["r0", "r1"]
    assert result["counts"]["refused_sites"] == 2
    assert result["mapped_anchor_ids"] == []
    assert result["global_context"]["time_window_bp"] == [-50.5, -50.25]
    empty = selection_fixture(view)
    empty["roles"] = []
    assert select_native_rows(view, empty, context)["selected_row_ids"] == []
