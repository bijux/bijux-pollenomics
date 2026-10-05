"""Publish compact accounting of actually qualified conditional joint covariance."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import hashlib
import json
import math
from pathlib import Path

from bijux_pollenomics_dev.ci.report_rebuild.source_paths import safe_source_file
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)

DESCRIPTOR = Path(
    "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/inputs/joint-source-snapshot.json"
)
DESCRIPTOR_SHA256 = "2edcb97b26bcd9d53b48ac35d0433861928c31cf7aecffaa743f356109da571f"
PINS = {
    "joint-covariance.json": "b9fb9856aa06db17dc01c3ae8e797d71346d6ae4ba5366e3b557b8d5d13599cb",
    "independent-review.json": "ea2dd28c67786a810d332e060d1cad753357e67a162c54e17f244480b4bfbb5f",
    "native-terminal.json": "45e29f1759b98049177821819254075b1801f1cacfc1b02e99a46014b75e5f8f",
    "launch-record-incident.json": "d13b90a4876c8d9157edbaf6a20616e2af8c86c2c0a4181c3f6f9dba9ccc6e45",
    "postexecution-review.json": "38c39b70496550ac06b2a99d23eea59c472a504cfcf9c24c32546bd1d40d4b1f",
}
PLAN_SHA256 = "9620790e626483cddb598437ea1f1441435880a50307c71f5d67ad80ca4a040a"
ORIGINAL_API_SHA256 = "faf894cf6db5f20cfbd8183b20efedd2f7a416f147aa7465d74f03032d1cc9b6"


def pairs(values: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in values:
        if key in result:
            raise ValueError("Duplicate joint capture JSON key")
        result[key] = value
    return result


def finite(value: object) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Nonfinite joint capture numeric value")
    if isinstance(value, dict):
        for child in value.values():
            finite(child)
    if isinstance(value, list):
        for child in value:
            finite(child)


def load_joint_inputs(repository: Path, source_root: Path) -> dict[str, dict[str, Any]]:
    descriptor = safe_source_file(
        repository, DESCRIPTOR.as_posix(), "Nordic joint covariance descriptor"
    )
    if hashlib.sha256(descriptor.read_bytes()).hexdigest() != DESCRIPTOR_SHA256:
        raise ValueError("Joint source descriptor identity changed")
    qualified = validated_external_report_sources(repository, source_root, DESCRIPTOR)
    result = {}
    for name, pin in PINS.items():
        raw = (qualified.directory / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != pin:
            raise ValueError("Joint retained source identity changed")
        value = json.loads(raw, object_pairs_hook=pairs)
        if not isinstance(value, dict):
            raise ValueError("Joint retained source must be an object")
        finite(value)
        result[name] = value
    return result


def compact_products(inputs: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    capture = inputs["joint-covariance.json"]
    review = inputs["independent-review.json"]
    terminal = inputs["native-terminal.json"]
    incident = inputs["launch-record-incident.json"]
    post = inputs["postexecution-review.json"]
    if (
        terminal["status"] != "PASS"
        or terminal["last_native_exit"] != 0
        or terminal["owned_survivors"]
        or terminal["resource_failure"] is not None
        or terminal["custody_errors"]
        or terminal["custody_after_unchanged"] is not True
        or terminal["custody_after_checked"] is not True
    ):
        raise ValueError("Joint native terminal did not admit actual output")
    if [stage["name"] for stage in terminal["stages"]] != [
        "guards",
        "producer",
        "oracle",
    ] or any(stage["native_exit"] != 0 for stage in terminal["stages"]):
        raise ValueError("Joint actual native stage authority differs")
    if (
        terminal["plan_sha256"] != PLAN_SHA256
        or terminal["joint_product_sha256"] != PINS["joint-covariance.json"]
        or terminal["independent_review_sha256"] != PINS["independent-review.json"]
    ):
        raise ValueError("Joint actual terminal output authority differs")
    if (
        terminal["source_context"]["source_changes"][
            "bijux_pollenomics_lra/reconstruction/joint_fixed_site_covariance.py"
        ]["sha256"]
        != ORIGINAL_API_SHA256
    ):
        raise ValueError("Original executed mathematics source differs")
    if (
        review["current_joint_product_sha256"] != PINS["joint-covariance.json"]
        or review["source_protocol_sha256"] != capture["protocol_sha256"]
    ):
        raise ValueError("Independent joint source/output binding differs")
    expected = {
        "case_window_results": 182,
        "cover_components": 518,
        "distinct_count_supports": 80,
        "geometry_contrasts": 124,
        "all_joint_covariance_cells_compared": 804972,
        "all_derivative_cells_compared": 121212,
        "decimal_precision": 50,
    }
    if any(review[key] != value for key, value in expected.items()):
        raise ValueError("Independent joint domain differs")
    if any(
        float(value) > 2e-12
        for value in review["maximum_absolute_differences"].values()
    ):
        raise ValueError("Independent joint numeric discrepancy differs")
    if (
        incident["actual_prelaunch_exit"] != 1
        or incident["actual_supervisor_exit"] != 0
        or incident["plan_sha256"] != PLAN_SHA256
        or incident["terminal_sha256"] != PINS["native-terminal.json"]
        or incident["launch_record_status"]
        != "STATE prelaunch entry absent; postexecution reconciliation explicitly recorded"
    ):
        raise ValueError("Joint registration incident scope differs")
    if (
        post["review_timing"]
        != "postexecution scoped audit; see preserved launch-record incident"
        or post["plan_sha256"] != PLAN_SHA256
        or post["actual_terminal_sha256"] != PINS["native-terminal.json"]
        or post["actual_independent_review_sha256"] != PINS["independent-review.json"]
        or post["frozen_members_verified"] != 9410
        or post["controls_verified"] != 10
    ):
        raise ValueError("Joint postexecution review differs")
    axes = capture["axes"]
    if (
        len(axes) != 182
        or sum(len(row["parameter_ids"]) for row in axes) != 518
        or len({row["result_id"] for row in axes}) != 182
        or len({row["count_support_sha256"] for row in axes}) != 80
        or len(capture["global_parameter_ids"]) != 8
        or len(set(capture["global_parameter_ids"])) != 8
        or len(capture["geometry_contrasts"]) != 124
        or capture["distinct_count_supports"] != 80
    ):
        raise ValueError("Joint retained result axes differ")
    for name in ("counting_covariance", "shared_ppe_covariance", "total_covariance"):
        if len(capture[name]) != 518 or any(len(row) != 518 for row in capture[name]):
            raise ValueError("Joint global covariance dimensions differ")
    if (
        len(capture["count_jacobian"]) != 518
        or len(capture["ppe_jacobian"]) != 518
        or len(capture["conditional_cover"]) != 518
    ):
        raise ValueError("Joint retained derivative/result dimensions differ")
    byid = {row["result_id"]: row for row in axes}
    for row in capture["geometry_contrasts"]:
        left, right = byid[row["left_result"]], byid[row["right_result"]]
        if (
            left["count_support_sha256"] != right["count_support_sha256"]
            or row["count_support_sha256"] != left["count_support_sha256"]
            or left["parameter_ids"] != right["parameter_ids"]
        ):
            raise ValueError("Joint contrast is not exact same-count panel support")
    if (
        capture["source_input_sha256"]["native_report"]
        != "50d2e11aa053f22afe8aeb2b0867c2ee3c00340ad002a6ece71c36aafdbbedfe"
        or capture["source_input_sha256"]["parameters"]
        != "32eac151566b41c186745dd077fabcddde06f64f9a3a2056699e88dbabd76d4d"
    ):
        raise ValueError("Joint source report/parameter identity differs")
    if any(
        capture[key] is not False
        for key in (
            "historical_reproduction_claim",
            "vegetation_accuracy_claim",
            "empirical_interval_coverage_claim",
        )
    ):
        raise ValueError("Joint capture scientific scope differs")
    compact = {
        "schema_version": 1,
        "profile": capture["profile"],
        "case_window_results": 182,
        "cover_components": 518,
        "distinct_count_supports": 80,
        "shared_literal_parameter_rows": 8,
        "geometry_contrasts": 124,
        "axes": axes,
        "global_parameter_ids": capture["global_parameter_ids"],
        "global_ppe": capture["global_ppe"],
        "global_ppe_covariance": capture["global_ppe_covariance"],
        "same_count_geometry_contrasts": capture["geometry_contrasts"],
        "omitted_uncertainty": capture["omitted_uncertainty"],
        "conditional_working_assumptions": {
            "count_PPE_cross_covariance": "zero; not observed",
            "disjoint_fixed_point_window_counts": "independent; not empirical temporal independence",
            "distinct_native_unit_counts": "independent; not empirical environmental independence",
            "global_PPE_covariance": "literal native SD² diagonal shared across all applicable results",
        },
        "full_global_covariance_source_sha256": PINS["joint-covariance.json"],
        "raw_sample_counts_published": False,
        "empirical_interval_coverage_claim": False,
        "historical_reproduction_claim": False,
        "vegetation_accuracy_claim": False,
    }
    authority = {
        "schema_version": 1,
        "capture_source_file_sha256": dict(PINS),
        "actual_plan_sha256": PLAN_SHA256,
        "actual_terminal_sha256": PINS["native-terminal.json"],
        "actual_executed_api_sha256": ORIGINAL_API_SHA256,
        "actual_scientific_candidate": terminal["candidate"],
        "original_reconstruction_candidate": terminal["source_context"][
            "original_scientific_candidate"
        ],
        "source_input_sha256": capture["source_input_sha256"],
        "native_stage_exits": [stage["native_exit"] for stage in terminal["stages"]],
        "native_stage_results": [
            {
                "name": stage["name"],
                "native_exit": stage["native_exit"],
                "log_sha256": stage["log_sha256"],
                "wall_seconds": stage["wall_seconds"],
            }
            for stage in terminal["stages"]
        ],
        "actual_supervisor_exit": incident["actual_supervisor_exit"],
        "actual_affected_source_guard_cases": 18,
        "previous_unchanged_API_math_cases": 18,
        "independent_Decimal50": review,
        "execution_record": {
            "prelaunch_registration_succeeded": False,
            "prelaunch_record_assertion_exit": incident["actual_prelaunch_exit"],
            "postexecution_audit": True,
            "frozen_members_verified": post["frozen_members_verified"],
            "control_files_verified": post["controls_verified"],
            "custody_after_checked": terminal["custody_after_checked"],
            "custody_after_unchanged": terminal["custody_after_unchanged"],
            "owned_survivors": terminal["owned_survivors"],
            "resource_failure": terminal["resource_failure"],
            "launch_incident_source_sha256": PINS["launch-record-incident.json"],
            "postexecution_audit_source_sha256": PINS["postexecution-review.json"],
        },
        "wall_seconds": terminal["wall_seconds"],
        "peak_rss_bytes": terminal["peak_rss_bytes"],
        "peak_processes": terminal["peak_processes"],
        "publication_consumer_scope": "Retained source/output accounting only; no new raw/R/physical or global numerical execution",
    }
    return {
        "joint-uncertainty.json": compact,
        "joint-capture-authority.json": authority,
    }
