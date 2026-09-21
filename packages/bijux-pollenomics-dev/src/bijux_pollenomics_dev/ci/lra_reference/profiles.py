"""Keep source refusals and corrected forward geometry in a distinct case profile."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any

from .contracts import ReferenceRefusal, read_json

SOURCE_DOMAIN_PROFILE = "disqover-source-domains-and-corrected-forward-v1"
SOURCE_DOMAIN_SEMANTICS = {
    "S001": "source-wrapper-refusal",
    "S002": "source-wrapper-refusal",
    "S003": "legacy-source-refusal",
    "S004": "legacy-source-refusal",
    "S005": "source-supported-zero-local",
    "S006": "source-supported-zero-regional",
    **{f"S{index:03d}": "source-supported-supplied-regional" for index in range(7, 11)},
    **{f"F{index:03d}": "corrected-matrix-forward" for index in range(1, 11)},
    "F011": "corrected-matrix-single-local",
    "F012": "corrected-matrix-single-regional",
    "F013": "corrected-matrix-rounded-cover",
}


def validate_source_domains(root: Path, reference_hash: str) -> dict[str, Any]:
    """Validate the separate source-domain and corrected-forward R profile."""
    report = read_json((root / "report.json").read_bytes())
    manifest = read_json((root / "case_manifest.json").read_bytes())
    exact = {
        "schema_version": "1.0.0",
        "profile": SOURCE_DOMAIN_PROFILE,
        "source_version": "0.9.14",
        "source_archive_sha256": reference_hash,
        "prepared_cases": 23,
        "live_R_executed": True,
        "passed_cases": 23,
        "failed_cases": 0,
        "status": "passed",
        "r_exit_code": 0,
    }
    if not isinstance(report, dict) or any(
        type(report.get(key)) is not type(value) or report[key] != value
        for key, value in exact.items()
    ):
        raise ReferenceRefusal("Actual separate source-domain R profile did not pass")
    cases = report.get("cases")
    if (
        not isinstance(cases, list)
        or not isinstance(manifest, list)
        or len(cases) != 23
        or len(manifest) != 23
    ):
        raise ReferenceRefusal("Source-domain profile denominator differs")
    expected = SOURCE_DOMAIN_SEMANTICS
    if {row["id"]: row.get("semantics") for row in cases} != expected or {
        row["id"]: row.get("semantics") for row in manifest
    } != expected:
        raise ReferenceRefusal(
            "Source-compatible and corrected-forward semantics were mixed or omitted"
        )
    for row in cases:
        if (
            row.get("passed") is not True
            or type(row.get("values")) is not int
            or row["values"] < 1
        ):
            raise ReferenceRefusal(
                "Source-domain result did not pass or lacks a value denominator"
            )
        with (root / (row["id"] + "-R.csv")).open() as stream:
            raw = list(csv.DictReader(stream))
        if len(raw) != row["values"] or any(set(item) != {"value"} for item in raw):
            raise ReferenceRefusal(
                "Source-domain raw R value denominator/schema differs"
            )
        if not (root / (row["id"] + "-rings.csv")).is_file():
            raise ReferenceRefusal("Source-domain geometry input is missing")
    with (root / "R_case_status.csv").open() as stream:
        statuses = list(csv.DictReader(stream))
    if (
        len(statuses) != 23
        or {row.get("id") for row in statuses} != set(expected)
        or any(row.get("status") != "completed" for row in statuses)
    ):
        raise ReferenceRefusal("Source-domain raw R completion statuses differ")
    identities = report.get("retained_source_sha256")
    required = {"run_source_domains.py", "source_domains.R", "r_support.R"}
    if (
        not isinstance(identities, dict)
        or set(identities) != required
        or any(
            hashlib.sha256((root / name).read_bytes()).hexdigest() != identities[name]
            for name in required
        )
    ):
        raise ReferenceRefusal(
            "Executed source-domain reference scripts are missing or changed"
        )
    return report
