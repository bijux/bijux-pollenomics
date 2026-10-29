"""Reject checker-role inflation, lost source limits and nonzero native custody."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any
import unittest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.lake_registry.neotoma_lake.execution import (
    validate_lake_execution,
)


def refuses_native_inflation(records: list[Any]) -> None:
    """Exercise source-role/denominator failures against caller-provided controlled metadata."""
    validate_lake_execution(
        *records,
        expected_candidate=records[0]["candidate"],
        expected_plan_sha256=records[1]["plan_sha256"],
    )
    negatives: list[tuple[int, list[Any], Any]] = [
        (0, ["include_prerequisites"], 0),
        (1, ["actual_exit"], False),
        (1, ["before_pin_mismatches"], ["changed"]),
        (1, ["stages", 0, "actual_exit"], 1),
        (1, ["stages", 0, "argv"], ["substitute"]),
        (2, ["outer_timed_out"], True),
        (2, ["after_custody_error"], "changed"),
        (2, ["inclusive_storage_bound_pass"], False),
        (3, ["checker_only"], False),
        (3, ["new_maintained_report_written"], True),
        (3, ["actual_source_argv"], ["invented-producer"]),
        (4, ["complete_lake_report_typed_identical"], False),
        (4, ["source_table_rows"], 24553),
        (4, ["original_candidate_source_sites"], 5),
        (4, ["rights_or_human_authority_qualified"], True),
        (4, ["absence_interpretation"], "certified_absent"),
        (5, ["lra_admitted_samples"], True),
        (5, ["source_rows", 0, "source_value"], False),
        (5, ["source_rows", 0, "source_value"], float("nan")),
        (5, ["source_rows", 0, "source_row_locator", "row_index"], True),
        (5, ["source_rows", 0, "basin_admission_status"], "accepted"),
    ]
    for part, keys, value in negatives:
        bad = deepcopy(records)
        cursor = bad[part]
        for key in keys[:-1]:
            cursor = cursor[key]
        cursor[keys[-1]] = value
        with unittest.TestCase().assertRaises(ReportRebuildError):
            validate_lake_execution(
                *bad,
                expected_candidate=records[0]["candidate"],
                expected_plan_sha256=records[1]["plan_sha256"],
            )


ROOT = next(
    p
    for p in Path(__file__).resolve().parents
    if (p / "pyproject.toml").is_file() and (p / "configs/pytest.ini").is_file()
)


class NativeExecutionControls(unittest.TestCase):
    def test_retained_native_histories_and_existing_refusals(self) -> None:
        prefix = ROOT / "data/source-custody/neotoma/lakeparameters"
        packet = json.loads((prefix / "capture.json").read_bytes())
        for label in ("lake", "prerequisites"):
            members = packet["executions"][label]["execution_members"]
            records = [
                json.loads((prefix / members[name]).read_bytes())
                for name in (
                    "plan.json",
                    "terminal.json",
                    "lakeparameter-terminal.json",
                    "maintained-reader-checker.json",
                    "independent-source-review.json",
                    "independently-reconstructed-lakeparameter-report.json",
                )
            ]
            refuses_native_inflation(records)
