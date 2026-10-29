"""Authenticate saved native roles without relabeling failed whole executions."""

from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import math
from pathlib import Path
from typing import Any

from ....contracts import ReportRebuildError


def require(value: object, reason: str) -> None:
    if not value:
        raise ReportRebuildError("Neotoma publication custody: " + reason)


def exact(actual: Any, expected: Any) -> None:
    require(type(actual) is type(expected), "Metadata type differs")
    if isinstance(actual, dict) and isinstance(expected, dict):
        require(
            list(actual) == list(expected), "Metadata key order or membership differs"
        )
        for key in actual:
            exact(actual[key], expected[key])
    elif isinstance(actual, list) and isinstance(expected, list):
        require(len(actual) == len(expected), "Metadata sequence length differs")
        for left, right in zip(actual, expected, strict=True):
            exact(left, right)
    else:
        require(actual == expected, "Metadata value differs")


def metadata_bridge(
    generated: Any, governed: Any, field: str, old: str, current: str
) -> None:
    """Permit only one declared provenance leaf, preserving every other typed value and order."""
    require(
        type(old) is str and type(current) is str and old != current,
        "Invalid bridge hashes",
    )
    adjusted = deepcopy(governed)
    left, right = adjusted, generated
    keys = field.split(".")
    for key in keys[:-1]:
        require(
            type(left) is dict and type(right) is dict, "Bridge parent is not an object"
        )
        left, right = left[key], right[key]
    exact(left[keys[-1]], old)
    exact(right[keys[-1]], current)
    left[keys[-1]] = current
    exact(adjusted, generated)


def validate_history(
    plan: dict[str, Any],
    common: dict[str, Any],
    inner: dict[str, Any],
    outer: dict[str, Any],
    *,
    label: str,
    candidate: str,
    plan_sha256: str,
) -> None:
    """An observer-only success cannot promote the original two-producer/observer failure."""
    require(label in {"production", "observation"}, "Unknown native role")
    exits = [0, 0, 1] if label == "production" else [0]
    whole = 1 if label == "production" else 0
    for document in (plan, common, inner):
        exact(document["candidate"], candidate)
    exact(outer["source_candidate"], candidate)
    for document in (common, inner, outer):
        exact(document["plan_sha256"], plan_sha256)
        exact(document["actual_exit"], whole)
    exact(common["status"], "failed" if whole else "passed")
    exact(common["canonical_before"], plan["canonical_identity"])
    exact(common["canonical_after"], plan["canonical_identity"])
    exact(common["before_pin_mismatches"], [])
    exact(common["after_pin_mismatches"], [])
    exact(common["absent_input_paths_unchanged"], True)
    exact(inner["common_actual_exit"], whole)
    exact(inner["native_stages"], common["stages"])
    exact(outer["before_runtime_error"], None)
    exact(outer["after_runtime_error"], None)
    exact(outer["timed_out"], False)
    exact(outer["resource_bounds_met"], not bool(whole))
    exact(outer["delegate_actual_exit"], whole)
    exact(outer["output_measurement_error"], None)
    for key, limit in (
        (
            "completed_elapsed_seconds",
            plan["qualified_runtime_resource_bounds"]["overall_seconds"],
        ),
        (
            "completed_child_peak_rss_bytes_macos",
            plan["qualified_runtime_resource_bounds"]["completed_child_peak_rss_bytes"],
        ),
    ):
        require(
            type(outer[key]) in (int, float)
            and math.isfinite(outer[key])
            and 0 <= outer[key] <= limit,
            "Completed resource bound differs",
        )
    for key in ("output_logical_bytes_before_receipt", "own_receipt_reserved_bytes"):
        require(
            type(outer[key]) is int and outer[key] >= 0, "Invalid output accounting"
        )
    require(
        outer["output_logical_bytes_before_receipt"]
        + outer["own_receipt_reserved_bytes"]
        <= plan["qualified_runtime_resource_bounds"]["logical_output_bytes"],
        "Inclusive output bound differs",
    )
    exact(len(plan["stages"]), len(exits))
    exact(len(common["stages"]), len(exits))
    for actual, expected, code in zip(
        common["stages"], plan["stages"], exits, strict=True
    ):
        for key in ("id", "argv", "timeout_seconds", "must_succeed"):
            exact(actual[key], expected[key])
        exact(actual["actual_exit"], code)
        exact(actual["timed_out"], False)
    expected_ids = (
        [
            "maintained-publication-readiness",
            "maintained-distinct-doi-review",
            "independent-provider-registry-source-observer",
        ]
        if label == "production"
        else ["independent-saved-publication-source-observer"]
    )
    exact([stage["id"] for stage in common["stages"]], expected_ids)
    if label == "production":
        exact(
            [row["checker_actual_exit"] for row in inner["tracked_byte_comparisons"]],
            [2, 2],
        )


def validate_source_role(
    kind: str,
    source: bytes,
    receipt: dict[str, Any],
    original_pins: dict[str, dict[str, Any]],
) -> None:
    """The pinned standalone DOI CLI legitimately imports no first-party modules."""
    expected = {
        "publication": "e884947655566a7eb6d4f0390d10dff80d4d285a2be32f720161d68b83346d1f",
        "doi": "a74034a8c21f7298183a7d89f625f1308fd3000b18a4d9105f00e547404424ec",
    }
    require(kind in expected, "Unknown source entry role")
    exact(hashlib.sha256(source).hexdigest(), expected[kind])
    exact(receipt["kind"], kind)
    exact(receipt["source"]["sha256"], expected[kind])
    require(receipt["source"]["path"] in original_pins, "Executed entry was not pinned")
    exact(receipt["source"], original_pins[receipt["source"]["path"]])
    exact(receipt["source_exit"], 0)
    exact(receipt["metadata_exit"], 0)
    exact(receipt["metadata_error"], None)
    exact(
        receipt["counters"],
        {"LRA_implementation_function_calls": 0, "network_attempts": 0},
    )
    origins = receipt["first_party_origins"]
    require(type(origins) is list, "Origin sequence required")
    require(
        [row["module"] for row in origins]
        == sorted({row["module"] for row in origins}),
        "Duplicate or unordered origin",
    )
    for row in origins:
        require(set(row) == {"module", "path", "sha256", "bytes"}, "Malformed origin")
        require(row["path"] in original_pins, "Foreign or unpinned source origin")
        exact(
            {key: row[key] for key in ("path", "sha256", "bytes")},
            original_pins[row["path"]],
        )
    names = [row["module"] for row in origins]
    if kind == "doi":
        exact(origins, [])
        imports = [
            ast.unparse(node)
            for node in ast.walk(ast.parse(source))
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        exact(
            imports,
            [
                "from __future__ import annotations",
                "import argparse",
                "from collections import Counter",
                "from hashlib import sha256",
                "import json",
                "from pathlib import Path",
                "from typing import Any",
                "from urllib.parse import quote, urlsplit",
            ],
        )
    else:
        exact(len(origins), 1002)
        exact(len({row["path"] for row in origins}), 1001)
        require(
            "bijux_pollenomics.analysis.lra.materialization.neotoma.publication_intake"
            in names,
            "Actual publication parser origin missing",
        )
        require(
            all(
                name.startswith(("bijux_pollenomics", "pollenomics", "lra."))
                or name == "lra"
                for name in names
            ),
            "Foreign claimed package",
        )
    source_path = Path(receipt["source"]["path"])
    exact(receipt["executed_source_argv"][0], str(source_path))


def validate_review(review: dict[str, Any]) -> None:
    """Retain complete denominators and explicit citation/source-rights limits."""
    for key, value in {
        "actual_exit": 0,
        "original_producer_exits": [0, 0],
        "original_independent_exit": 1,
        "original_whole_exit": 1,
        "current_observer_only_execution": True,
        "package_import_roles": {
            "publication": "package-parser",
            "doi": "standalone-stdlib",
        },
        "historical_policy_and_current_policy_rights_or_human_equivalence_claimed": False,
        "complete_provider_response_counts": {
            "current": 169,
            "older_separate_epoch": 58,
        },
        "DataCite_response_count": 26,
        "current_older_overlapping_dataset_IDs": 58,
        "overlap_raw_bytes_equal": 58,
        "overlap_complete_publication_projection_equal": 58,
        "used_datasets": 85,
        "provider_publication_status_counts": {
            "multiple_source_primary_publications": 3,
            "no_publication_link": 2,
            "no_source_primary_flag": 1,
            "one_source_primary_publication": 79,
        },
        "dataset_doi_status_counts": {
            "ascii_case_equivalent_source_dois": 3,
            "distinct_source_dois": 13,
            "one_source_doi": 69,
        },
        "reviewed_DOI_pairs": 13,
        "doi_pair_status_counts": {
            "registry_declared_identical": 3,
            "same_dataset_target_without_declared_equivalence": 10,
        },
        "full_provider_source_field_order_and_native_values_checked": True,
        "all_DataCite_titles_landing_URLs_versions_relations_checked": True,
        "observed_first_party_source_origins": 1001,
        "original_acquisition_predecessor_06f08e_authenticated": False,
        "fresh_HTTP_or_rights_or_citation_selection_or_human_or_untouched_admission": False,
        "publication_ready": False,
        "lra_accepted_samples": 0,
    }.items():
        exact(review[key], value)
    exact(
        review["country_denominators"],
        {
            "SE": {
                "used_datasets": 3,
                "one_source_primary_publication": 3,
                "primary_link_review_required": 0,
                "distinct_source_dois": 2,
                "either_citation_review": 2,
            },
            "DK": {
                "used_datasets": 2,
                "one_source_primary_publication": 2,
                "primary_link_review_required": 0,
                "distinct_source_dois": 0,
                "either_citation_review": 0,
            },
            "NO": {
                "used_datasets": 52,
                "one_source_primary_publication": 49,
                "primary_link_review_required": 3,
                "distinct_source_dois": 9,
                "either_citation_review": 11,
            },
            "FI": {
                "used_datasets": 28,
                "one_source_primary_publication": 25,
                "primary_link_review_required": 3,
                "distinct_source_dois": 2,
                "either_citation_review": 5,
            },
        },
    )
