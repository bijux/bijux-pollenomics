"""Project an executed counting trajectory to aggregate public evidence only."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_contracts.literal_pair_counting import (
    validated_pair_counting_capture,
)

CAPTURE_SHA256 = {
    "report.json": "5d7752d21f0d17b81991f35c0f52095b8f66a3510ec64bb6e7dfb0a6ab077f4b",
    "terminal.json": "50066bd9c4176e1492c6404a73aaeb48683c66062ca6c57006332017a23e5599",
    "independent-verification.json": "ece762411f867b852ab20b3182ebad2c7521dddd8a1431d0bf9541a50fbd0a84",
    "protocol.json": "0a93de9e717f584d143b1d36fa34ab33a8c812fc5337ee37dfd11e019f23fc9f",
    "method.md": "dfbe9950d9ce41f79131354960367d5d3434fbca1261bf17b2279a9c251d4583",
}
NATIVE_PLAN_SHA256 = "c0e52eeac4ca792f2d41211d63780d9a67c53e7dee003b1b42d440cae8ef2e4d"


def read_capture(capture: Path) -> dict[str, dict[str, Any]]:
    """Accept only the exact retained successful source consumer and observer."""
    result: dict[str, dict[str, Any]] = {}
    for name, expected in CAPTURE_SHA256.items():
        path = capture / name
        if not path.is_file() or path.is_symlink():
            raise ValueError("Retained counting capture must be a regular file")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("Retained counting capture hash differs: " + name)
        if path.suffix == ".json":
            result[name] = json.loads(raw)
    terminal = result["terminal.json"]
    observer = result["independent-verification.json"]
    report = result["report.json"]
    if (
        terminal["native_exit"] != 0
        or terminal["plan_sha256"] != NATIVE_PLAN_SHA256
        or len(terminal["stages"]) != 5
        or any(stage["native_exit"] != 0 for stage in terminal["stages"])
        or observer["native_exit"] != 0
        or observer["report_sha256"] != CAPTURE_SHA256["report.json"]
        or report["family_native_sample_population"] != observer["all_native_samples"]
        or sum(row["admitted_samples"] for row in report["coverage"])
        != observer["actual_intervals_checked"]
    ):
        raise ValueError("Successful native counting and observer custody required")
    return result


def public_summary(report: dict[str, Any]) -> dict[str, Any]:
    """Publish only aggregate populations, bounds and directions, preserving values."""
    fields = (
        "source",
        "taxa",
        "family_native_sample_population",
        "family_exact_max_error",
        "binary64_confidence",
        "actual_union_bound_fraction",
        "coverage",
        "transitions",
        "joint_lake_relations",
        "scenario",
        "admissions",
    )
    result = {key: deepcopy(report[key]) for key in fields}
    result["schema_version"] = "literal-pair-count-trajectory-public.v1"
    bin_fields = (
        "dataset_id",
        "bin_id",
        "native_sample_count",
        "refused_sample_count",
        "available",
        "sample_count",
        "pair_total",
        "counts",
        "point",
        "lower",
        "upper",
    )
    result["bins"] = [
        {key: deepcopy(row[key]) for key in bin_fields if key in row}
        for row in report["bins"]
    ]
    result["contrast_direction"] = {
        "taxon": "Alnus",
        "axis": "increasing native calendar BP, younger to older",
        "formula": "older-bin pair probability minus younger-bin pair probability",
        "complement": "Plantago lanceolata is the complementary second axis, not an independent extra family",
    }
    result["private_detail_boundary"] = (
        "Native aliquot objects, sample identifiers, source pointers, request journal and per-aliquot interval/tail certificates remain private artifacts."
    )
    return result


def source_account(capture: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Expose actual finite execution and observer scope without private observations."""
    terminal = capture["terminal.json"]
    observer = capture["independent-verification.json"]
    return {
        "schema_version": "literal-pair-count-trajectory-source.v1",
        "capture_sha256": CAPTURE_SHA256,
        "native_plan_sha256": NATIVE_PLAN_SHA256,
        "source_candidate": terminal["candidate_baseline"],
        "source_overlay": terminal["source_overlay"],
        "controller_recorded_argv": terminal["actual_argv"],
        "native_exit": terminal["native_exit"],
        "stages": [
            {
                key: stage[key]
                for key in (
                    "id",
                    "actual_argv",
                    "native_exit",
                    "timeout",
                    "wall_seconds",
                    "stdout_sha256",
                    "stderr_sha256",
                )
            }
            for stage in terminal["stages"]
        ],
        "wall_seconds": terminal["wall_seconds"],
        "observed_child_peak_rss_bytes": terminal["observed_child_peak_rss_bytes"],
        "all_controlled_output_bytes": terminal["all_controlled_output_bytes"],
        "actual_source_guards": 44,
        "strict_source_and_test_files": 8,
        "independent_verification": observer,
        "original_source_and_runtime_unchanged": (
            not terminal["before"]["mismatches"]
            and not terminal["after"]["mismatches"]
            and terminal["before"]["runtime_entries_unchanged"]
            and terminal["after"]["runtime_entries_unchanged"]
            and terminal["before"]["plan_unchanged"]
            and terminal["after"]["plan_unchanged"]
        ),
        "verification_limits": (
            "All 121 native source objects, 80 actual intervals, 26 bins and 24 directions were independently reconstructed. Every nontrivial returned endpoint was checked by directed 110 digit positive combinatorial tail summation, separately from production recurrence. This finite-request verification reuses the maintained general API proof and establishes neither independent ecological accuracy nor nominal coverage conditional on observed source admission. Public projection performs zero new interval fits or source-count analyses."
        ),
        "scientific_admission": False,
        "rights_admission": False,
        "release_admission": False,
    }


def main() -> int:
    """Publish the authenticated retained aggregate under an owned artifact root."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--capture", type=Path)
    parser.add_argument("--source-descriptor", type=Path)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = require_absent_artifact_output(args.repository, args.output)
    if args.capture is not None:
        if args.source_descriptor is not None or args.source_root is not None:
            parser.error(
                "Choose direct retained capture or configured source descriptor"
            )
        directory = args.capture
    else:
        if args.source_descriptor is None or args.source_root is None:
            parser.error(
                "Configured capture requires --source-descriptor and --source-root"
            )
        directory = validated_pair_counting_capture(
            args.repository, args.source_root, args.source_descriptor
        ).directory
    capture = read_capture(directory)
    summary = public_summary(capture["report.json"])
    source = source_account(capture)
    source["public_summary_sha256"] = hashlib.sha256(
        (
            json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        ).encode()
    ).hexdigest()
    output.mkdir()
    for name, value in (
        ("pair-counting.json", summary),
        ("pair-counting-source.json", source),
    ):
        (output / name).write_text(
            json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
