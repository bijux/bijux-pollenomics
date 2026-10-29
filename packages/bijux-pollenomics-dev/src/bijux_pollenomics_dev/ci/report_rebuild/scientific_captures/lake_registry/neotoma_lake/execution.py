"""Keep maintained checker roles distinct from independent source reconstruction."""

from __future__ import annotations

import math
from typing import Any

from ....contracts import ReportRebuildError


def require(value: object, reason: str) -> None:
    """Refuse a retained source or scope inconsistency."""
    if not value:
        raise ReportRebuildError("Neotoma lake-source custody: " + reason)


def exact(actual: Any, expected: Any) -> None:
    """Compare source values without Boolean, numeric or membership aliases."""
    require(type(actual) is type(expected), "Metadata type differs")
    if isinstance(actual, dict) and isinstance(expected, dict):
        require(actual.keys() == expected.keys(), "Metadata fields differ")
        for key in actual:
            exact(actual[key], expected[key])
    elif isinstance(actual, list) and isinstance(expected, list):
        require(len(actual) == len(expected), "Ordered metadata membership differs")
        for left, right in zip(actual, expected, strict=True):
            exact(left, right)
    else:
        require(actual == expected, "Metadata value differs")


def validate_lake_execution(
    plan: dict[str, Any],
    common: dict[str, Any],
    outer: dict[str, Any],
    checker: dict[str, Any],
    review: dict[str, Any],
    report: dict[str, Any],
    *,
    expected_candidate: str,
    expected_plan_sha256: str,
) -> None:
    """Validate already-observed execution records; never interpret private source pages."""
    optional = plan["include_prerequisites"]
    require(type(optional) is bool, "Prerequisite role must be explicit")
    for document in (plan, common, outer, checker, review):
        exact(document["candidate"], expected_candidate)
    for document in (common, outer):
        exact(document["plan_sha256"], expected_plan_sha256)
    exact(review["plan"]["sha256"], expected_plan_sha256)
    for value in (
        common["actual_exit"],
        outer["actual_exit"],
        checker["actual_exit"],
        review["actual_exit"],
    ):
        exact(value, 0)
    exact(common["status"], "passed")
    exact(common["canonical_before"], plan["canonical_identity"])
    exact(common["canonical_after"], plan["canonical_identity"])
    exact(common["before_pin_mismatches"], [])
    exact(common["after_pin_mismatches"], [])
    exact(common["absent_input_paths_unchanged"], True)
    exact(outer["common_native_exit"], 0)
    exact(outer["outer_timed_out"], False)
    exact(outer["after_custody_error"], None)
    for key in (
        "memory_bound_pass",
        "inclusive_storage_bound_pass",
        "completed_whole_wall_bound_pass",
    ):
        exact(outer[key], True)
    exact(outer["complete_descendant_cleanup_or_RSS_claimed"], False)
    expected_stages = plan["stages"]
    actual_stages = common["stages"]
    exact(len(expected_stages), 3 if optional else 2)
    exact(len(actual_stages), len(expected_stages))
    for actual, expected in zip(actual_stages, expected_stages, strict=True):
        for key in ("id", "argv", "timeout_seconds", "must_succeed"):
            exact(actual[key], expected[key])
        exact(actual["actual_exit"], 0)
        exact(actual["timed_out"], False)
    exact(actual_stages[0]["id"], "maintained-lakeparameter-reader-checker")
    exact(
        actual_stages[-1]["id"],
        "independent-lake-source-and-optional-projection-observer",
    )
    exact(checker["checker_only"], True)
    exact(checker["new_maintained_report_written"], False)
    exact(checker["source"], plan["maintained_reader"])
    exact(
        checker["actual_source_argv"],
        [plan["maintained_reader"]["path"], "--capture-root", plan["capture_root"]],
    )
    for key, expected in {
        "maintained_reader_checker_exit": 0,
        "complete_lake_report_typed_identical": True,
        "lake_tracked_byte_checker_exit": 0,
        "source_table_rows": 24554,
        "source_type_rows": 21,
        "original_candidate_source_sites": 54,
        "original_candidate_sites_with_observed_rows": 5,
        "original_source_locator_joins": 5,
        "source_consistency": "live_paginated_not_transactional_snapshot",
        "absence_interpretation": "not_certified_by_live_offset_pagination",
        "basin_admission_status": "not_reviewed",
        "lra_admitted_samples": 0,
        "private_source_pages_copied_or_published": False,
        "rights_or_human_authority_qualified": False,
        "HTTP_or_new_acquisition_performed": False,
    }.items():
        exact(review[key], expected)
    for key in (
        "source_table_rows",
        "source_type_rows",
        "source_consistency",
        "absence_interpretation",
        "basin_admission_status",
        "lra_admitted_samples",
    ):
        exact(report[key], review[key])
    exact(report["candidate_source_sites"], 54)
    exact(report["candidate_sites_with_observed_parameter_rows"], 5)
    exact(report["candidate_sites_without_observed_parameter_rows"], 49)
    exact(report["capture_sha256"], plan["capture_sha256"])
    exact(report["site_evidence_sha256"], plan["site_evidence_sha256"])
    exact(report["capture_site_evidence_sha256"], plan["site_evidence_sha256"])
    exact(len(report["source_rows"]), 5)
    for row in report["source_rows"]:
        exact(row["basin_admission_status"], "not_reviewed")
        require(
            type(row["source_value"]) in (int, float),
            "Native source value must remain numeric, not boolean/text",
        )
        require(math.isfinite(row["source_value"]), "Nonfinite native source value")
        locator = row["source_row_locator"]
        require(
            type(locator["row_index"]) is int and locator["row_index"] >= 0,
            "Typed native row locator required",
        )
        require(
            type(locator["page_sha256"]) is str and len(locator["page_sha256"]) == 64,
            "Native page identity required",
        )
    if not optional:
        exact(review["optional_current_projection"], None)
    else:
        require(
            type(review["optional_current_projection"]) is dict,
            "Actual prerequisite observation missing",
        )
        exact(actual_stages[1]["id"], "maintained-current-prerequisite-projection")
        exact(len(plan["optional_inputs"]), 30)
        exact(len(set(plan["optional_inputs"])), 30)
        observed = review["optional_current_projection"]
        for key, value in {
            "scientific_typed_identity": True,
            "tracked_byte_checker_exit": 0,
            "source_sites": 163,
            "necessary_source_samples": 10637,
            "lakeparameter_locator_joins": 14,
            "accepted_samples": 0,
            "independent_pollen_eligibility_recomputation_claimed": False,
        }.items():
            exact(observed[key], value)
