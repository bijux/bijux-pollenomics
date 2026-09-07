"""Shared validation for semantics-bearing atlas capture-frame evidence."""

from __future__ import annotations

from collections.abc import Mapping

_SOURCE_LAYER_KEYS = {
    "source_sample_presence": "neotoma-source-sample-pollen-context",
    "source_ecological_code": "neotoma-source-ecological-code",
    "source_taxon": "neotoma-source-exact-taxon",
}
_MODELED_LAYER_KEY = "landclim-reveals-temporal-grid"


def expected_capture_layer_key(*, story_kind: object, source_level: object) -> str:
    """Resolve the governed evidence layer without trusting browser declarations."""
    if story_kind == "modeled_context":
        return _MODELED_LAYER_KEY
    return (
        _SOURCE_LAYER_KEYS.get(source_level, "")
        if isinstance(source_level, str)
        else ""
    )


def capture_frame_evidence_valid(
    value: Mapping[str, object],
    *,
    evidence_role: str,
    source_level: object,
    expected_evidence_layer_key: str,
    expected_title: str,
    expected_source_count: object,
    expected_source_site_count: object,
    expected_source_observation_count: object,
    source_site_denominator: object,
    source_node_denominator: object,
    source_observation_denominator: object,
    expected_modeled_count: object,
    expected_modeled_no_pollen_data_count: object,
    source_window_label: object,
    time_start_bp: object,
    time_end_bp: object,
) -> bool:
    """Validate dimensions, isolation, presentation, and unobstructed layout."""
    point_count = value.get("visible_point_count")
    polygon_layer_count = value.get("visible_polygon_layer_count")
    polygon_feature_count = value.get("visible_polygon_feature_count")
    source_count = value.get("visible_source_chronology_point_count")
    modeled_count = value.get("visible_modeled_context_feature_count")
    if any(
        not _nonnegative_integer(count)
        for count in (
            point_count,
            polygon_layer_count,
            polygon_feature_count,
            source_count,
            modeled_count,
        )
    ):
        return False
    if value.get("visible_feature_count") != point_count + polygon_feature_count:  # type: ignore[operator]
        return False
    if (polygon_layer_count == 0) != (polygon_feature_count == 0):
        return False
    if not _capture_layers_valid(
        value.get("capture_layers"),
        expected_evidence_layer_key=expected_evidence_layer_key,
    ):
        return False
    if not _capture_presentation_valid(
        value.get("capture_presentation"),
        evidence_role=evidence_role,
        source_level=source_level,
        source_preset=value.get("source_preset"),
        expected_title=expected_title,
        expected_source_count=expected_source_count,
        expected_source_site_count=expected_source_site_count,
        source_site_denominator=source_site_denominator,
        source_node_denominator=source_node_denominator,
        source_observation_denominator=source_observation_denominator,
        visible_source_observations=value.get("visible_source_observation_denominator"),
        expected_modeled_count=expected_modeled_count,
        expected_modeled_no_pollen_data_count=expected_modeled_no_pollen_data_count,
        source_window_label=source_window_label,
        time_start_bp=time_start_bp,
        time_end_bp=time_end_bp,
    ):
        return False
    if not _capture_layout_valid(value.get("capture_layout")):
        return False
    if evidence_role == "observation_chronology":
        visible_observations = value.get("visible_source_observation_denominator")
        return (
            _nonnegative_integer(expected_source_count)
            and _nonnegative_integer(expected_source_site_count)
            and _nonnegative_integer(source_site_denominator)
            and _nonnegative_integer(expected_source_observation_count)
            and _nonnegative_integer(source_node_denominator)
            and _nonnegative_integer(source_observation_denominator)
            and source_count == expected_source_count
            and value.get("facet_site_count") == source_site_denominator
            and value.get("visible_site_count") == expected_source_site_count
            and visible_observations == expected_source_observation_count
            and expected_source_site_count <= expected_source_count  # type: ignore[operator]
            and point_count == source_count
            and modeled_count == 0
            and value.get("visible_source_node_count") == source_count
            and (
                (expected_source_count == 0 and visible_observations == 0)
                or (
                    expected_source_count > 0  # type: ignore[operator]
                    and _nonnegative_integer(visible_observations)
                    and expected_source_observation_count > 0  # type: ignore[operator]
                    and expected_source_observation_count <= source_observation_denominator  # type: ignore[operator]
                )
            )
            and value.get("visible_modeled_no_pollen_data_count") is None
        )
    if evidence_role != "modeled_context":
        return False
    return (
        _nonnegative_integer(expected_modeled_count)
        and source_count == 0
        and point_count == 0
        and modeled_count == expected_modeled_count
        and modeled_count <= polygon_feature_count  # type: ignore[operator]
        and value.get("visible_source_node_count") is None
        and value.get("visible_source_observation_denominator") is None
        and value.get("facet_site_count") is None
        and value.get("visible_site_count") is None
        and _nonnegative_integer(value.get("visible_modeled_no_pollen_data_count"))
        and _nonnegative_integer(expected_modeled_no_pollen_data_count)
        and expected_modeled_no_pollen_data_count <= expected_modeled_count  # type: ignore[operator]
        and value.get("visible_modeled_no_pollen_data_count")
        == expected_modeled_no_pollen_data_count
    )


def _capture_layers_valid(value: object, *, expected_evidence_layer_key: str) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "active_keys",
        "evidence_layer_key",
        "orientation_keys",
    }:
        return False
    active_keys = value.get("active_keys")
    evidence_layer_key = value.get("evidence_layer_key")
    orientation_keys = value.get("orientation_keys")
    if (
        not isinstance(active_keys, list)
        or not isinstance(orientation_keys, list)
        or not isinstance(evidence_layer_key, str)
        or not evidence_layer_key
        or any(not isinstance(key, str) or not key for key in active_keys)
        or any(not isinstance(key, str) or not key for key in orientation_keys)
    ):
        return False
    expected_orientation_keys = ["country-boundaries"]
    expected = sorted({*expected_orientation_keys, expected_evidence_layer_key})
    return (
        active_keys == sorted(active_keys)
        and orientation_keys == sorted(orientation_keys)
        and len(set(active_keys)) == len(active_keys)
        and len(set(orientation_keys)) == len(orientation_keys)
        and evidence_layer_key == expected_evidence_layer_key
        and orientation_keys == expected_orientation_keys
        and active_keys == expected
    )


def _capture_presentation_valid(
    value: object,
    *,
    evidence_role: str,
    source_level: object,
    source_preset: object,
    expected_title: str,
    expected_source_count: object,
    expected_source_site_count: object,
    source_site_denominator: object,
    source_node_denominator: object,
    source_observation_denominator: object,
    visible_source_observations: object,
    expected_modeled_count: object,
    expected_modeled_no_pollen_data_count: object,
    source_window_label: object,
    time_start_bp: object,
    time_end_bp: object,
) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "null_handling",
        "interpolation_allowed",
        "propagation_use_allowed",
        "evidence_role",
        "role_label",
        "title",
        "time_label",
        "counts_label",
        "key_labels",
        "key_items",
        "caveat",
    }:
        return False
    key_labels = value.get("key_labels")
    key_items = value.get("key_items")
    caveat = value.get("caveat")
    if evidence_role == "observation_chronology":
        expected_role_label = "Observed source chronology"
        expected_caveat = (
            "Literal exact-ID source-label union only · not an accepted "
            "classification or abundance · no interpolation, flow, propagation, "
            "migration, or causation inference."
            if isinstance(source_preset, str) and source_preset
            else "Observed source records only · site, node, and display-cluster "
            "counts are not abundance · no interpolation, flow, propagation, "
            "migration, or causation inference."
        )
        expected_key_labels = [
            "source record",
            "records grouped at current zoom",
            "country boundary",
        ]
        expected_cues = ["point", "cluster-count", "line"]
        source_colors = {
            "source_sample_presence": ("rgb(180, 83, 9)", "rgb(120, 53, 15)"),
            "source_ecological_code": ("rgb(15, 118, 110)", "rgb(19, 78, 74)"),
            "source_taxon": ("rgb(124, 58, 237)", "rgb(76, 29, 149)"),
        }
        selected_fill, selected_stroke = (
            source_colors.get(source_level, (None, None))
            if isinstance(source_level, str)
            else (None, None)
        )
        expected_styles = [
            (selected_fill, selected_stroke),
            (selected_fill, selected_stroke),
            ("rgba(0, 0, 0, 0)", "rgb(100, 116, 139)"),
        ]
        observation_label = (
            "unavailable"
            if visible_source_observations is None
            else str(visible_source_observations)
        )
        expected_counts_label = (
            f"{expected_source_site_count}/{source_site_denominator} unique source sites · "
            f"{expected_source_count}/{source_node_denominator} governed source nodes in this interval · "
            f"{observation_label}/{source_observation_denominator} contributing observations"
        )
    else:
        expected_role_label = "Modeled context · published source window"
        expected_caveat = (
            "Published modeled cells are context only, not an observed pollen "
            "trajectory · no atlas interpolation, flow, propagation, migration, "
            "or causation inference."
        )
        expected_key_labels = [
            "0–20%",
            ">20–40%",
            ">40–60%",
            ">60–80%",
            ">80–100%",
            "no pollen data · N/A, not 0",
            "country boundary",
        ]
        expected_cues = ["area", "area", "area", "area", "area", "area", "line"]
        expected_styles = [
            ("rgb(27, 67, 50)", "rgb(51, 65, 85)"),
            ("rgb(82, 121, 111)", "rgb(51, 65, 85)"),
            ("rgb(167, 201, 87)", "rgb(51, 65, 85)"),
            ("rgb(242, 204, 143)", "rgb(51, 65, 85)"),
            ("rgb(217, 119, 6)", "rgb(51, 65, 85)"),
            ("rgb(203, 213, 225)", "rgb(51, 65, 85)"),
            ("rgba(0, 0, 0, 0)", "rgb(100, 116, 139)"),
        ]
        expected_counts_label = (
            f"{expected_modeled_count}/{expected_modeled_count} published cells visible · "
            f"{expected_modeled_no_pollen_data_count} explicitly have no pollen data · {source_window_label}"
        )
    return (
        value.get("schema_version") == "atlas-capture-presentation.v1"
        and value.get("null_handling") == "null_not_zero"
        and value.get("interpolation_allowed") is False
        and value.get("propagation_use_allowed") is False
        and value.get("evidence_role") == evidence_role
        and value.get("role_label") == expected_role_label
        and value.get("title") == expected_title
        and value.get("time_label")
        == f"[{time_start_bp}, {time_end_bp}] BP · oldest → present"
        and value.get("counts_label") == expected_counts_label
        and key_labels == expected_key_labels
        and isinstance(key_items, list)
        and len(key_items) == len(expected_key_labels)
        and all(
            isinstance(item, dict)
            and set(item) == {"label", "cue", "fill", "stroke"}
            and item.get("label") == label
            and item.get("cue") == expected_cues[index]
            and (item.get("fill"), item.get("stroke")) == expected_styles[index]
            for index, (item, label) in enumerate(
                zip(key_items, expected_key_labels, strict=True)
            )
        )
        and caveat == expected_caveat
    )


def _capture_layout_valid(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "overlay_visible",
        "overlay_bounded",
        "overlay_content_bounded",
        "overlay_content_overflow",
        "overlay_overlaps_map",
        "map_bounded",
        "map_width_px",
        "map_height_px",
        "scroll_x_px",
        "scroll_y_px",
        "viewport_width_px",
        "viewport_height_px",
    }:
        return False
    map_width = value.get("map_width_px")
    map_height = value.get("map_height_px")
    scroll_x = value.get("scroll_x_px")
    scroll_y = value.get("scroll_y_px")
    return (
        value.get("overlay_visible") is True
        and value.get("overlay_bounded") is True
        and value.get("overlay_content_bounded") is True
        and value.get("overlay_content_overflow") is False
        and value.get("overlay_overlaps_map") is False
        and value.get("map_bounded") is True
        and _nonnegative_integer(scroll_x)
        and scroll_x == 0
        and _nonnegative_integer(scroll_y)
        and scroll_y == 0
        and value.get("viewport_width_px") == 1440
        and value.get("viewport_height_px") == 900
        and _nonnegative_integer(map_width)
        and 936 <= map_width <= 1440  # type: ignore[operator]
        and _nonnegative_integer(map_height)
        and 0 < map_height <= 900  # type: ignore[operator]
    )


def _nonnegative_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0
