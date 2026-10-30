"""Freeze matched Nordic source windows before conditional wind sensitivity."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

REPORT = "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/report.json"
REPORT_SHA256 = "50d2e11aa053f22afe8aeb2b0867c2ee3c00340ad002a6ece71c36aafdbbedfe"
SOURCE_EPOCH = "33d45ecfd6be7d275b69a7a7350bb72ae7c5269e"
PROFILE = "nordic-conditional-wind-sensitivity.v1"
VECTOR_FIELDS = (
    "conditional_cover",
    "direct_pollen_panel_fraction",
    "conditional_standard_error",
)
MATRIX_FIELDS = (
    "counting_covariance",
    "assumed_ppe_covariance",
    "total_conditional_covariance",
)
CASE_WINDOWS = {
    "52082.metadata_static_radius": 24,
    "52082.reported_25_5_ha_static_circle": 24,
    "20034.metadata_static_radius": 22,
    "20034.reported_7_2_ha_static_circle": 22,
    "20034.reported_8_0_ha_static_circle": 22,
    "4445.metadata_static_radius": 23,
    "4445.reported_2_5_ha_static_circle": 23,
    "4446.metadata_static_radius": 11,
    "4446.reported_2_5_ha_static_circle": 11,
}


def fingerprint(value: object) -> str:
    """Digest canonical finite protocol metadata."""
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def number(value: object, *, positive: bool = False) -> float:
    """Require a finite native number within its declared domain."""
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise ValueError("Finite native numerical value required")
    result = float(value)
    if positive and result <= 0:
        raise ValueError("Positive source parameter required")
    return result


def _vector(value: Any, size: int, *, positive: bool = False) -> None:
    if not isinstance(value, list) or len(value) != size:
        raise ValueError("Complete source taxon axis required")
    for cell in value:
        number(cell, positive=positive)


def prepare(report: dict[str, Any], protocol: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate the finite saved population; construct no factors or compositions."""
    if protocol != {
        "schema_version": PROFILE,
        "source_report_sha256": REPORT_SHA256,
        "baseline_wind_speed_m_s": 3,
        "alternative_wind_speed_m_s": [2, 4],
        "regional_extent_m": 100000,
        "diffusion_coefficient": 0.12,
        "turbulence_parameter": 0.25,
        "alternative_status": "declared_conditional_assumptions_not_measured_winds",
        "justification": "Reuse the Swedish static-basin wind2/4 one-axis sensitivity around the same3m/s baseline; test numerical sensitivity, not physical likelihood or Nordic wind observations.",
        "geometry_policy": "retain_all_nine_original_static_geometries_without_new_radius_or_shape",
        "claims": {
            "measured_wind": False,
            "source_qualified_alternative_extent": False,
            "historical_reproduction": False,
            "vegetation_accuracy": False,
            "whole_lci_030": False,
        },
    }:
        raise ValueError("Frozen conditional wind protocol differs")
    if (
        report["candidate"] != SOURCE_EPOCH
        or report["source_samples"] != 314
        or report["accepted_source_samples"] != 313
        or report["unique_physical_tuples"] != 23
        or report["physical_tuple_case_uses"] != 29
    ):
        raise ValueError("Original Nordic source population differs")
    if any(value is not False for value in protocol["claims"].values()):
        raise ValueError("Conditional protocol cannot promote scientific claims")
    source_protocol = report["protocol"]
    for key, value in (
        ("wind_speed_m_s", 3),
        ("regional_extent_m", 100000),
        ("diffusion_coefficient", 0.12),
        ("turbulence_parameter", 0.25),
    ):
        if (
            type(source_protocol[key]) not in (int, float)
            or source_protocol[key] != value
        ):
            raise ValueError("Original fixed transport setting differs")
    cases = report["cases"]
    if len(cases) != 9 or {case["case_id"] for case in cases} != set(CASE_WINDOWS):
        raise ValueError("Missing, duplicate or foreign source geometry case")
    core_axes: dict[int, object] = {}
    source_population = report["source_population"]
    if (
        len(source_population) != 4
        or len({row["native_dataset_id"] for row in source_population}) != 4
    ):
        raise ValueError("Original per-core source dispositions differ")
    if (
        sum(row["source_samples"] for row in source_population) != 314
        or sum(row["accepted_samples"] for row in source_population) != 313
    ):
        raise ValueError("Original exclusion denominator differs")
    output = []
    physical_tuples: set[tuple[float, float]] = set()
    for case in cases:
        size = len(case["parameter_taxa"])
        if not size or len(set(case["parameter_taxa"])) != size or size > 6:
            raise ValueError("Original literal source panel differs")
        if (
            case["panel_N_not_full_NISP"] is not True
            or case["source_present_not_hypothesized_zero"] is not True
            or case["occupied_windows"] != CASE_WINDOWS[case["case_id"]]
        ):
            raise ValueError("Source panel eligibility or window denominator differs")
        for name in ("PPE", "fall_speed_m_s"):
            _vector(case[name], size, positive=True)
        _vector(case["PPE_SD"], size)
        if any(value < 0 for value in case["PPE_SD"]):
            raise ValueError("Negative source PPE standard deviation")
        radius = number(case["static_geometry"]["radius_m"], positive=True)
        if radius >= 100000:
            raise ValueError("Source annulus support differs")
        physical_tuples.update(
            (radius, float(speed)) for speed in case["fall_speed_m_s"]
        )
        _vector(case["physical_response"]["factors"][0], size, positive=True)
        if len(case["physical_response"]["factors"]) != 1:
            raise ValueError("Source deposition site axis differs")
        windows = case["results"]
        if len(windows) != CASE_WINDOWS[case["case_id"]]:
            raise ValueError("Missing source window")
        keys = set()
        last = -math.inf
        for window in windows:
            younger = number(window["younger_cal_bp"])
            older = number(window["older_cal_bp_exclusive"])
            if not last <= younger < older or (younger, older) in keys:
                raise ValueError("Duplicate, reordered or overlapping source windows")
            keys.add((younger, older))
            last = older
            if len(window["counts"]) != 1 or len(window["counts"][0]) != size:
                raise ValueError("Source count axes differ")
            counts = window["counts"][0]
            if any(type(value) is not int or value < 0 for value in counts):
                raise ValueError("Native nonnegative integer counts required")
            total = sum(counts)
            if (
                type(window["panel_count_denominator"]) is not int
                or not 0 < total < 2**53
                or total != window["panel_count_denominator"]
            ):
                raise ValueError("Exact panel denominator differs")
            if (
                type(window["reported_all_pollen_NISP_sum"]) is not int
                or window["reported_all_pollen_NISP_sum"] < total
                or window["unparameterized_reported_NISP_sum"]
                != window["reported_all_pollen_NISP_sum"] - total
                or window["actual_source_panel_presence"] is not True
                or window["assumed_zero_cells"] != 0
            ):
                raise ValueError("Source residual or actual-presence contract differs")
            for name in VECTOR_FIELDS:
                _vector(window[name], size)
            for name in MATRIX_FIELDS:
                if not isinstance(window[name], list) or len(window[name]) != size:
                    raise ValueError("Source covariance row axis differs")
                for row in window[name]:
                    _vector(row, size)
            support = window["local_actual_source_support_sha256"]
            if (
                not isinstance(support, str)
                or len(support) != 64
                or any(c not in "0123456789abcdef" for c in support)
            ):
                raise ValueError("Exact source support identity required")
        core = case["native_dataset_id"]
        if str(core) != case["case_id"].split(".", 1)[0]:
            raise ValueError("Foreign native core identity")
        axis = (
            case["parameter_taxa"],
            case["PPE"],
            case["PPE_SD"],
            case["fall_speed_m_s"],
            [
                (
                    w["younger_cal_bp"],
                    w["older_cal_bp_exclusive"],
                    w["counts"],
                    w["local_actual_source_support_sha256"],
                )
                for w in windows
            ],
        )
        if core in core_axes and core_axes[core] != axis:
            raise ValueError(
                "Geometry variants must share exact native window/count/parameter axes"
            )
        core_axes[core] = axis
        output.append(case)
    if len(physical_tuples) != 23:
        raise ValueError("Original unique physical tuple population differs")
    if sum(len(case["results"]) for case in output) != 182:
        raise ValueError("Complete matched window population required")
    return output
