"""Verify and summarize the source-bound empty Nordic propagation ledger."""

from __future__ import annotations

from collections import Counter
import csv
from hashlib import sha256
import io
import json
from pathlib import Path
from typing import Any


DIRECTORY = Path(__file__).resolve().parent
REPOSITORY = DIRECTORY.parents[3]
EVIDENCE = DIRECTORY / "evidence"
CLASSIFICATION = DIRECTORY / "classification-evidence"
COUNTRIES = ("DK", "FI", "NO", "SE")
SOURCE_REPORT = REPOSITORY / "docs/report/propagation/source-first-observed/report.json"
CONCEPTS = REPOSITORY / "data/neotoma/review/source_taxon_concepts.json"
FIELDS = ("source_country", "target_country", "input_events", "evaluated_pairs", "directed_candidates", "status")


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def checked_json(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError(f"Expected object: {path}")
    return result


def summarize() -> tuple[list[dict[str, object]], dict[str, object]]:
    manifest = checked_json(EVIDENCE / "manifest.json")
    if manifest["payload_file_count"] != len(manifest["files"]):
        raise ValueError("Evidence file count changed")
    for item in manifest["files"]:
        path = EVIDENCE / item["path"]
        if path.parent != EVIDENCE or digest(path) != item["sha256"]:
            raise ValueError(f"Evidence identity changed: {item['path']}")

    source = checked_json(SOURCE_REPORT)
    concepts = checked_json(CONCEPTS)
    release = checked_json(EVIDENCE / "release_metadata.json")
    classification = checked_json(CLASSIFICATION / "manifest.json")
    if digest(CLASSIFICATION / "manifest.json") != release["classification_review_digest"]:
        raise ValueError("Classification receipt identity changed")
    classification_files = {item["path"]: item for item in classification["files"]}
    for name in ("accepted_mapping_queue.json", "release_metadata.json", "observation_denominators.json"):
        if digest(CLASSIFICATION / name) != classification_files[name]["sha256"]:
            raise ValueError(f"Classification decision identity changed: {name}")
    accepted = checked_json(CLASSIFICATION / "accepted_mapping_queue.json")
    classification_release = checked_json(CLASSIFICATION / "release_metadata.json")
    observation_denominators = checked_json(CLASSIFICATION / "observation_denominators.json")
    primary = checked_json(EVIDENCE / "primary_scenario_reconciliation.json")
    sensitivity = checked_json(EVIDENCE / "sensitivity_summary.json")
    if source["source_identity"]["build_id"] != release["build_id"]:
        raise ValueError("Source build and release build differ")
    if concepts["source_summaries"]["neotoma"]["source_snapshot_id"] != source["source_identity"]["source_snapshot_id"]:
        raise ValueError("Classification and observed-source snapshots differ")
    if classification["source_snapshot_id"] != source["source_identity"]["source_snapshot_id"] or classification["build_id"] != release["build_id"]:
        raise ValueError("Classification audit and source identities differ")
    if accepted["record_count"] != 0 or accepted["records"] or classification_release["reviewed_accepted_mapping_count"] != 0:
        raise ValueError("Accepted classification queue changed")
    if classification_release["public_release_allowed"] is not False or observation_denominators["total_observation_count"] != 370936:
        raise ValueError("Classification release or source denominator changed")
    statuses = Counter(row["current_mapping_status"] for row in concepts["rows"])
    if sum(statuses.values()) != concepts["row_count"] or set(statuses) != {"unmapped", "not_applicable"}:
        raise ValueError("Classification admission changed")
    if source["denominators"]["events"] != 0 or source["denominators"]["refused"] != source["denominators"]["attempts"]:
        raise ValueError("Observed-source refusal changed")
    if release["accepted_classification_mapping_count"] != 0 or release["input_event_count"] != 0 or release["public_release_allowed"] is not False:
        raise ValueError("Release admission changed")
    if primary["event_manifest_digest"] != manifest["event_manifest_digest"]:
        raise ValueError("Primary event identity changed")

    pairs = primary["reconciliation"]["ordered_country_pair_counts"]
    expected = {f"{source_country}-{target_country}" for source_country in COUNTRIES for target_country in COUNTRIES}
    if set(pairs) != expected or primary["reconciliation"]["evaluated_pair_count"] != 0:
        raise ValueError("Primary country-pair support changed")
    if any(any(value != 0 for value in counts.values()) for counts in pairs.values()):
        raise ValueError("A primary country pair has a nonzero outcome")
    scenarios = sensitivity["scenarios"]
    if len(scenarios) != 16 or len({item["scenario_id"] for item in scenarios}) != 16:
        raise ValueError("Sensitivity scenario support changed")
    for scenario in scenarios:
        counts = scenario["country_pair_counts"]
        if set(counts) != expected or any(any(value != 0 for value in row.values()) for row in counts.values()):
            raise ValueError("A sensitivity country pair has a nonzero outcome")

    rows = [
        {
            "source_country": source_country,
            "target_country": target_country,
            "input_events": 0,
            "evaluated_pairs": 0,
            "directed_candidates": 0,
            "status": "unobserved_no_admitted_events",
        }
        for source_country in COUNTRIES
        for target_country in COUNTRIES
    ]
    report: dict[str, object] = {
        "schema_version": "nordic-governed-edge-ledger.v1",
        "source_report_sha256": digest(SOURCE_REPORT),
        "source_snapshot_id": source["source_identity"]["source_snapshot_id"],
        "source_build_id": release["build_id"],
        "source_screen_sites": source["denominators"]["sites"],
        "source_screen_attempts": source["denominators"]["attempts"],
        "source_screen_events": source["denominators"]["events"],
        "concepts_sha256": digest(CONCEPTS),
        "concept_rows": concepts["row_count"],
        "concept_status_counts": dict(sorted(statuses.items())),
        "original_evidence_manifest_sha256": digest(EVIDENCE / "manifest.json"),
        "classification_review_digest": release["classification_review_digest"],
        "accepted_mapping_queue_sha256": digest(CLASSIFICATION / "accepted_mapping_queue.json"),
        "classification_source_observations": observation_denominators["total_observation_count"],
        "scenario_count": len(scenarios),
        "ordered_country_pair_bins_per_scenario": len(pairs),
        "admitted_event_count": 0,
        "evaluated_pair_count": 0,
        "directed_candidate_count": 0,
        "public_release_allowed": False,
        "interpretation": "Empty reporting bins after source and classification refusal; no ecological edge or four-country event coverage is inferred.",
    }
    return rows, report


def main() -> None:
    rows, report = summarize()
    ledger = DIRECTORY / "edge-ledger.csv"
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    expected_ledger = stream.getvalue().encode("utf-8")
    report["edge_ledger_sha256"] = sha256(expected_ledger).hexdigest()
    expected_report = (json.dumps(report, indent=2) + "\n").encode("utf-8")
    if ledger.read_bytes() != expected_ledger or (DIRECTORY / "report.json").read_bytes() != expected_report:
        raise ValueError("Retained edge ledger or report differs from source-bound replay")
    print("Verified 16 Nordic country-pair bins and 16 sensitivity scenarios; zero admitted events.")


if __name__ == "__main__":
    main()
