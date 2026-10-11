"""Build replay provenance from validated fresh native R comparison results."""

from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath
from typing import Any


def _sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _digest_map(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or not value:
        raise ValueError("Native source replay digest mapping required")
    result = {}
    for name, digest in value.items():
        if (
            not isinstance(name, str)
            or not name
            or "\\" in name
            or "\0" in name
            or PurePosixPath(name).is_absolute()
            or any(part in {"", ".", ".."} for part in name.split("/"))
            or not isinstance(digest, str)
            or not _sha256(digest)
        ):
            raise ValueError("Native source replay confined path/digest required")
        result[name] = digest
    return result


def _numeric_paths() -> set[str]:
    # These identities are emitted by the maintained core and domain runners.
    core = {f"oracle/C{index:04d}.csv" for index in range(43)}
    domains = {
        f"source-domains/{prefix}{index:03d}-{kind}.csv"
        for prefix, count in (("F", 13), ("S", 10))
        for index in range(1, count + 1)
        for kind in ("R", "rings")
    }
    corrected = {
        f"source-domains/S{index:03d}-{kind}-output.csv"
        for index in (3, 4)
        for kind in ("corrected", "legacy")
    }
    return (
        core
        | domains
        | corrected
        | {
            "oracle/R_case_status.csv",
            "source-domains/R_case_status.csv",
            "source-domains/case_manifest.csv",
            "source-domains/parameters.csv",
        }
    )


def build_source_replay(report: dict[str, Any], revision: str) -> dict[str, Any]:
    """Validate declared provenance shape after the caller authenticates native bytes."""
    if (
        report.get("schema_version") != "current-native-r-reference.1"
        or report.get("status") != "passed"
        or report.get("fresh_R_executed") is not True
        or report.get("release_certificate") is not False
        or not isinstance(revision, str)
        or len(revision) != 40
        or any(character not in "0123456789abcdef" for character in revision)
    ):
        raise ValueError("Fresh native comparison and full source revision required")
    for field in (
        "rscript_sha256",
        "source_lock_sha256",
        "original_certificate_sha256",
        "runner_sha256",
    ):
        if not _sha256(report.get(field)):
            raise ValueError("Native source replay SHA256 digest required")
    current_inputs = _digest_map(report.get("current_inputs_sha256"))
    analysis_inputs = _digest_map(report.get("analysis_inputs_sha256"))
    raw_results = _digest_map(report.get("raw_results_sha256"))
    counts = {
        "current_core_attempted": 43,
        "current_core_passed": 43,
        "current_domains_attempted": 23,
        "current_domains_passed": 23,
        "original_R_to_current_R_compared": 48,
    }
    if any(
        type(report.get(key)) is not int or report[key] != value
        for key, value in counts.items()
    ):
        raise ValueError("Native source replay case denominators differ")
    optimized_ids = [row["id"] for row in report["new_core_cases"]]
    if (
        len(report["original_R_to_current_R_cases"]) != 48
        or len(optimized_ids) != 18
        or set(optimized_ids) != {f"C{index:04d}" for index in range(25, 43)}
    ):
        raise ValueError("Native prospective case identities differ")
    numeric = {
        name: digest for name, digest in raw_results.items() if name.endswith(".csv")
    }
    if set(numeric) != _numeric_paths():
        raise ValueError("Native source replay numeric CSV population differs")
    return {
        "schema_version": "native-r-source-replay.v1",
        "scope": "current Python source against freshly executed locked native DISQOVER and original R certificate",
        "source_revision": revision,
        **{
            key: report[key]
            for key in (
                "r_version",
                "rscript_sha256",
                "source_lock_sha256",
                "original_certificate_sha256",
                "runner_sha256",
            )
        },
        "current_inputs_sha256": current_inputs,
        "analysis_inputs_sha256": analysis_inputs,
        "retained_numeric_csv": {
            "file_count": len(numeric),
            "mapping_sha256": hashlib.sha256(
                json.dumps(numeric, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
        },
        "cases": {
            "core_attempted": report["current_core_attempted"],
            "core_passed": report["current_core_passed"],
            "source_domain_attempted": report["current_domains_attempted"],
            "source_domain_passed": report["current_domains_passed"],
            "optimized_love_passed": len(optimized_ids),
            "optimized_love_ids": optimized_ids,
            "original_r_vectors_compared": report["original_R_to_current_R_compared"],
            "original_r_vectors_passed": len(report["original_R_to_current_R_cases"]),
        },
    }
