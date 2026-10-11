"""Require manifest provenance from complete fresh native comparison results."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.lra_validation.native_reference.source_replay import (
    build_source_replay,
)

ROOT = Path(__file__).resolve().parents[5]
REVISION = "0123456789abcdef0123456789abcdef01234567"


@pytest.fixture
def native_report() -> dict[str, Any]:
    # This retained report is an input-shape fixture, not a new R execution.
    path = ROOT / "docs/report/method-certification/current-r-oracle/report.json"
    record = cast(dict[str, Any], json.loads(path.read_text()))
    if record["schema_version"] == "retained-native-r-comparison-report.v1":
        # Exercise the immutable native serializer's input shape, not a new R run.
        record["schema_version"] = "current-native-r-reference.1"
    return record


def test_manifest_derives_actual_source_case_and_csv_identities(
    native_report: dict[str, Any],
) -> None:
    before = copy.deepcopy(native_report)
    result = build_source_replay(native_report, REVISION)
    assert native_report == before
    assert result["source_revision"] == REVISION
    for field in (
        "current_inputs_sha256",
        "analysis_inputs_sha256",
        "source_lock_sha256",
        "original_certificate_sha256",
        "runner_sha256",
        "rscript_sha256",
    ):
        assert result[field] == native_report[field]
    csv = {
        key: digest
        for key, digest in native_report["raw_results_sha256"].items()
        if key.endswith(".csv")
    }
    assert result["retained_numeric_csv"] == {
        "file_count": len(csv),
        "mapping_sha256": hashlib.sha256(
            json.dumps(csv, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }
    assert result["cases"]["optimized_love_ids"] == [
        row["id"] for row in native_report["new_core_cases"]
    ]
    assert result["cases"]["optimized_love_passed"] == 18
    assert result["cases"]["original_r_vectors_passed"] == len(
        native_report["original_R_to_current_R_cases"]
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "source-locked-retained-r-python-comparison.v1"),
        ("status", "failed"),
        ("fresh_R_executed", False),
        ("fresh_R_executed", 1),
        ("release_certificate", True),
    ],
)
def test_retained_or_failed_comparison_cannot_emit_native_manifest(
    native_report: dict[str, Any], field: str, value: object
) -> None:
    native_report[field] = value
    with pytest.raises(ValueError, match="Fresh native comparison"):
        build_source_replay(native_report, REVISION)


@pytest.mark.parametrize(
    "field",
    [
        "current_core_attempted",
        "current_core_passed",
        "current_domains_attempted",
        "current_domains_passed",
        "original_R_to_current_R_compared",
    ],
)
@pytest.mark.parametrize("boolean", [False, True])
def test_case_counts_remain_complete_exact_integer_denominators(
    native_report: dict[str, Any], field: str, boolean: bool
) -> None:
    native_report[field] = True if boolean else native_report[field] - 1
    with pytest.raises(ValueError, match="denominators"):
        build_source_replay(native_report, REVISION)


@pytest.mark.parametrize("revision", ["0123456789", "g" * 40, "A" * 40])
def test_source_revision_is_full_and_unambiguous(
    native_report: dict[str, Any], revision: str
) -> None:
    with pytest.raises(ValueError, match="full source revision"):
        build_source_replay(native_report, revision)


@pytest.mark.parametrize("population", ["prospective", "paired", "csv"])
def test_missing_actual_result_members_refuse_before_manifest(
    native_report: dict[str, Any], population: str
) -> None:
    if population == "prospective":
        native_report["new_core_cases"][-1]["id"] = native_report["new_core_cases"][0][
            "id"
        ]
    elif population == "paired":
        native_report["original_R_to_current_R_cases"].pop()
    else:
        native_report["raw_results_sha256"].pop("oracle/C0000.csv")
    with pytest.raises(ValueError):
        build_source_replay(native_report, REVISION)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("rscript_sha256", True),
        ("source_lock_sha256", False),
        ("original_certificate_sha256", "bad"),
        ("runner_sha256", "g" * 64),
    ],
)
def test_malformed_scalar_source_digests_refuse(
    native_report: dict[str, Any], field: str, value: object
) -> None:
    native_report[field] = value
    with pytest.raises(ValueError, match="SHA256"):
        build_source_replay(native_report, REVISION)


@pytest.mark.parametrize("field", ["current_inputs_sha256", "analysis_inputs_sha256"])
@pytest.mark.parametrize("corruption", ["boolean", "invalid_digest", "empty"])
def test_incomplete_or_malformed_source_hash_mapping_refuses(
    native_report: dict[str, Any], field: str, corruption: str
) -> None:
    if corruption == "empty":
        native_report[field] = {}
    else:
        native_report[field][next(iter(native_report[field]))] = (
            True if corruption == "boolean" else "not-sha256"
        )
    with pytest.raises(ValueError, match="digest"):
        build_source_replay(native_report, REVISION)


@pytest.mark.parametrize(
    "corruption", ["boolean", "invalid_digest", "same_count_wrong_member"]
)
def test_csv_hash_or_membership_corruption_refuses(
    native_report: dict[str, Any], corruption: str
) -> None:
    raw = native_report["raw_results_sha256"]
    key = next(name for name in raw if name.endswith(".csv"))
    if corruption == "same_count_wrong_member":
        raw["oracle/unrelated.csv"] = raw.pop(key)
    else:
        raw[key] = True if corruption == "boolean" else "not-sha256"
    with pytest.raises(ValueError):
        build_source_replay(native_report, REVISION)


@pytest.mark.parametrize(
    "field", ["current_inputs_sha256", "analysis_inputs_sha256", "raw_results_sha256"]
)
@pytest.mark.parametrize(
    "name",
    [
        "/absolute.py",
        "../escape.py",
        "source/../escape.py",
        "source//alias.py",
        "source/./alias.py",
        "source\\alias.py",
        "source\0alias.py",
        "",
    ],
)
def test_hash_map_paths_are_confined_canonical_identities(
    native_report: dict[str, Any], field: str, name: str
) -> None:
    raw = native_report[field]
    raw[name] = raw.pop(next(iter(raw)))
    with pytest.raises(ValueError, match="confined"):
        build_source_replay(native_report, REVISION)


def test_well_shaped_changed_digest_is_declared_provenance_only(
    native_report: dict[str, Any],
) -> None:
    # Physical equality is authenticated by summarize and execution custody.
    key = next(iter(native_report["current_inputs_sha256"]))
    native_report["current_inputs_sha256"][key] = "0" * 64
    result = build_source_replay(native_report, REVISION)
    assert result["current_inputs_sha256"][key] == "0" * 64
    assert result["current_inputs_sha256"] is not native_report["current_inputs_sha256"]
