"""Independently verify source claims and zero ranking without importing the producer."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import (
    ROOT,
    SOURCE,
    dump,
    exact,
    load,
    pin,
    require,
    source_namespace,
    validate_scope,
)
from runtime import profile_guard, qualify_process_snapshot, raw_process_snapshot


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--plan", type=Path, required=True)
    a = p.parse_args()
    source_namespace()
    profile_guard()
    plan = load(a.plan)
    output = Path(plan["output"])
    before = raw_process_snapshot()
    qualify_process_snapshot(before, plan["input_pins"], SOURCE)
    declared = load(SOURCE / "declared-inputs.json")
    private = Path(declared["private_root"]) / "svar/normalized-export-2026-09-08"
    summary = load(private / "svar_summary.json")
    manifest = load(private / "svar_lake_registry_manifest.json")
    review = load(ROOT / "data/svar/review/lake_candidate_registry_review.json")
    subset = load(ROOT / "data/svar/review/sweden_lake_candidate_registry.geojson")
    rank = load(
        ROOT / "docs/report/countries/sweden/sweden_lake_evidence_richness_v66.json"
    )
    require(
        type(summary["lake_count"]) is int
        and summary["lake_count"]
        == manifest["normalized_lake_count"]
        == manifest["matched_lake_count"]
        == 40565,
        "Normalized source claims differ",
    )
    require(
        summary["generated_on"] == manifest["generated_on"] == "2026-09-08",
        "Source epoch differs",
    )
    require(
        review["source_lake_count"] == 40523
        and len(subset["features"]) == 99
        and rank["candidate_count"] == 0
        and rank["methodology"]["refusal_reason"] == "governing_svar_registry_missing",
        "Public refusal differs",
    )
    generated = output / "producer/report.json"
    report = load(generated)
    validate_scope(report)
    inputs = []
    for name in [
        "sweden_lake_registry.geojson",
        "svar_summary.json",
        "svar_lake_registry_manifest.json",
    ]:
        item = pin(private / name)
        inputs.append(
            {
                "source_root_role": "external_svar_source_store",
                "path": "svar/normalized-export-2026-09-08/" + name,
                **{k: item[k] for k in ("bytes", "sha256")},
            }
        )
    for name in [
        "data/svar/review/lake_candidate_registry_review.json",
        "data/svar/review/sweden_lake_candidate_registry.geojson",
        "docs/report/countries/sweden/sweden_lake_evidence_richness_v66.json",
    ]:
        item = pin(ROOT / name)
        inputs.append({"path": name, **{k: item[k] for k in ("bytes", "sha256")}})
    require(exact(report["inputs"], inputs), "Complete source identity ledger differs")
    original = Path(plan["historical_report"]["path"])
    require(exact(report, load(original)), "Complete typed current report differs")
    require(
        generated.read_bytes() == original.read_bytes(), "Tracked byte checker refused"
    )
    runtime = load(output / "source-runtime-observation.json")
    require(
        runtime["source_exit"] == runtime["metadata_exit"] == 0
        and type(runtime["source_exit"]) is int
        and type(runtime["metadata_exit"]) is int,
        "Producer/runtime observation failed",
    )
    require(
        runtime["candidate"] == plan["candidate"]
        and runtime["plan"] == pin(a.plan)
        and runtime["source"] == plan["maintained_source"]
        and runtime["executed_source_argv"] == plan["maintained_source_argv"],
        "Producer source/plan binding differs",
    )
    qualify_process_snapshot(runtime["before"], plan["input_pins"], SOURCE)
    qualify_process_snapshot(runtime["after"], plan["input_pins"], SOURCE)
    after = raw_process_snapshot()
    qualify_process_snapshot(after, plan["input_pins"], SOURCE)
    dump(
        output / "independent-source-review.json",
        {
            "actual_exit": 0,
            "candidate": plan["candidate"],
            "plan": pin(a.plan),
            "generated": pin(generated),
            "canonical": pin(original),
            "tracked_byte_checker_exit": 0,
            "complete_typed_report_and_bytes_exact": True,
            "independently_authenticated_input_members": 6,
            "source_population_difference": 40565 - 40523,
            "source_lake_count_is_metadata_claim_not_new_GeoJSON_feature_census": True,
            "ranking_admitted": False,
            "source_runtime": pin(output / "source-runtime-observation.json"),
            "observer_before": before,
            "observer_after": after,
            "scope": "Independent source identity/metadata claims and refusal only. Full privateGeoJSON hashed, not parsed or promoted to operational authority. WFS/export linkage,42 difference and qualified review remain unresolved.",
        },
    )


if __name__ == "__main__":
    main()
