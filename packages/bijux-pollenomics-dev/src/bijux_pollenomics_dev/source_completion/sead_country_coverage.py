"""Account for SEAD country retrieval and source-native evidence dispositions."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

RUN = "sead-full-evidence-39bfff6a-ce80714e"
RAW = Path("data/sead/raw/acquisitions") / RUN
NORMALIZED = Path("data/sead/normalized/acquisitions") / RUN
RETRIEVAL = Path("docs/report/source-relations/sead-country-retrieval")
PINNED = {
    RAW
    / "manifest.json": "6fc2428046d148f9ce6c158f982afbbbbaea39de2132850a4fb8f41acf8a4c14",
    NORMALIZED
    / "evidence_materialization_manifest.json": "383151443d04da5a6e127ea2e4344b4b10bb210137dd1d13b77e50dbfae93508",
    NORMALIZED
    / "source_native_observations.json": "f059815108ce02e7cb28c49bf2f3d90455a6fbb4d0996a34fe563e0ca7da7d29",
    NORMALIZED
    / "evidence_events.json": "aacba06cd6d037151d64dcacaf14c24fb5748dc7b80f2507055343584812357e",
    RETRIEVAL
    / "report.json": "32321c08a249d2042a6a5d68315492a229b05336dace46a2507ff279c4269be5",
    RETRIEVAL
    / "countries.csv": "ee39d12eff900b8aaf3a15c571f182c3e15957d3cfe3d797c2f31f9c70221c9f",
}
COUNTRIES = ("SE", "DK", "NO", "FI")
FIELDS = (
    "country_code",
    "governed_discovered_sites",
    "governed_assigned_sites",
    "retrieved_sites",
    "normalized_sites",
    "terminal_site_retrieval_losses",
    "source_native_observations",
    "refused_observation_dispositions",
    "propagation_eligible_sites",
    "eligible_evidence_events",
    "source_country_posture",
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_pinned(repository: Path, relative: Path) -> bytes:
    path = repository / relative
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Pinned SEAD input missing or linked: {relative}")
    content = path.read_bytes()
    if _sha(content) != PINNED[relative]:
        raise ValueError(f"Pinned SEAD input changed: {relative}")
    return content


def _receipt_accounting(repository: Path, manifest: dict[str, Any]) -> dict[str, int]:
    entries = {
        entry["path"]: entry
        for entry in manifest["files"]
        if entry["path"].startswith("receipts/")
    }
    if (
        manifest["status"] != "complete"
        or len(manifest["required_tables"]) != 61
        or len(entries) != 61
        or manifest["missing_required_tables"]
        or manifest["incomplete_required_tables"]
    ):
        raise ValueError("SEAD required relation capture incomplete")
    counts = {
        "table_receipts": 0,
        "query_receipts": 0,
        "query_failures": 0,
        "query_retries": 0,
        "terminal_table_failures": 0,
    }
    for table in manifest["required_tables"]:
        relative = f"receipts/{table}.json"
        entry = entries.get(relative)
        if entry is None:
            raise ValueError(f"Missing SEAD table receipt: {table}")
        path = repository / RAW / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Missing or linked SEAD table receipt: {table}")
        content = path.read_bytes()
        if len(content) != entry["byte_count"] or _sha(content) != entry["sha256"]:
            raise ValueError(f"SEAD table receipt identity changed: {table}")
        receipt = json.loads(content)
        if receipt["run_id"] != RUN or receipt["table"] != table:
            raise ValueError(f"SEAD table receipt lineage changed: {table}")
        counts["table_receipts"] += 1
        counts["terminal_table_failures"] += receipt["status"] != "complete"
        queries = receipt["query_receipts"]
        if len(queries) != receipt["query_count"]:
            raise ValueError(f"SEAD query receipt count changed: {table}")
        for query in queries:
            counts["query_receipts"] += 1
            counts["query_failures"] += query["result"]["failure_count"]
            counts["query_retries"] += query["result"]["retry_count"]
            if query["status"] != "complete" or query["failure_reason"] is not None:
                counts["terminal_table_failures"] += 1
    if counts["terminal_table_failures"]:
        raise ValueError("SEAD retrieval contains terminal failures")
    return counts


def run(repository: Path, output: Path) -> dict[str, Any]:
    """Replay exact country denominators into a fresh repository artifact path."""
    repository, output = repository.resolve(), output.resolve()
    if (
        output.exists()
        or output.is_symlink()
        or not output.is_relative_to(repository / "artifacts")
    ):
        raise ValueError("Absent repository artifact destination required")
    contents = {path: _read_pinned(repository, path) for path in PINNED}
    raw_manifest = json.loads(contents[RAW / "manifest.json"])
    materialization = json.loads(
        contents[NORMALIZED / "evidence_materialization_manifest.json"]
    )
    observations = json.loads(contents[NORMALIZED / "source_native_observations.json"])
    events = json.loads(contents[NORMALIZED / "evidence_events.json"])
    retrieval = json.loads(contents[RETRIEVAL / "report.json"])
    country_rows = list(
        csv.DictReader(io.StringIO(contents[RETRIEVAL / "countries.csv"].decode()))
    )
    indexed = {row["group"]: row for row in country_rows}
    files = {entry["path"]: entry["sha256"] for entry in materialization["files"]}
    if (
        len(indexed) != 6
        or set(indexed) != {*COUNTRIES, "REVIEW", "UNASSIGNED"}
        or retrieval["run_id"] != RUN
        or retrieval["outputs"]["countries.csv"]["sha256"]
        != PINNED[RETRIEVAL / "countries.csv"]
        or retrieval["inventory"]
        != {
            "discovered_bbox": 2195,
            "governed_assigned": 2069,
            "normalized_site_consumer": 2069,
            "retrieved_tbl_sites": 2069,
            "review_excluded": 103,
            "unassigned_excluded": 23,
        }
        or materialization["source_run_id"] != RUN
        or observations["source_run_id"] != RUN
        or events["source_run_id"] != RUN
        or materialization["acquisition_manifest_sha256"]
        != PINNED[RAW / "manifest.json"]
        or observations["acquisition_manifest_sha256"] != PINNED[RAW / "manifest.json"]
        or events["acquisition_manifest_sha256"] != PINNED[RAW / "manifest.json"]
        or files["source_native_observations.json"]
        != PINNED[NORMALIZED / "source_native_observations.json"]
        or files["evidence_events.json"] != PINNED[NORMALIZED / "evidence_events.json"]
        or len(
            {observations["build_id"], events["build_id"], materialization["build_id"]}
        )
        != 1
        or observations["observation_count"] != events["observation_denominator"]
        or observations["observation_count"] != materialization["observation_count"]
        or events["refused_event_count"] != observations["observation_count"]
        or events["eligible_event_count"] != materialization["eligible_event_count"]
        or events["refused_event_count"] != materialization["refused_event_count"]
        or events["events"] != []
        or set(observations["country_counts"]) != set(COUNTRIES)
        or events["country_observation_counts"] != observations["country_counts"]
        or set(events["country_eligible_event_counts"]) != set(COUNTRIES)
        or sum(observations["country_counts"].values())
        != observations["observation_count"]
        or sum(events["country_eligible_event_counts"].values())
        != events["eligible_event_count"]
        or events["eligible_event_count"] != 0
        or retrieval["source_country_field_posture"]
        != "not_supplied_on_all_discovered_sites"
        or retrieval["admission"]["qualified_review_of_126_coordinates"] != "pending"
    ):
        raise ValueError("SEAD country retrieval or evidence lineage changed")
    receipts = _receipt_accounting(repository, raw_manifest)
    rows = []
    for code in COUNTRIES:
        source = indexed[code]
        counts = [
            int(source[key])
            for key in (
                "discovered_with_governed_country",
                "governed_assigned",
                "retrieved_payload",
                "normalized_consumer",
            )
        ]
        if (
            len(set(counts)) != 1
            or source["source_reported_country_count"] != "not_supplied"
        ):
            raise ValueError(f"SEAD country site retrieval changed: {code}")
        observation_count = observations["country_counts"][code]
        rows.append(
            {
                "country_code": code,
                "governed_discovered_sites": counts[0],
                "governed_assigned_sites": counts[1],
                "retrieved_sites": counts[2],
                "normalized_sites": counts[3],
                "terminal_site_retrieval_losses": counts[1] - counts[2],
                "source_native_observations": observation_count,
                "refused_observation_dispositions": observation_count,
                "propagation_eligible_sites": 0,
                "eligible_evidence_events": events["country_eligible_event_counts"][
                    code
                ],
                "source_country_posture": "not_supplied;governed_boundary_assignment",
            }
        )
    for status, expected in (("REVIEW", 103), ("UNASSIGNED", 23)):
        source = indexed[status]
        if int(source["discovered_with_governed_country"]) != expected or any(
            int(source[key])
            for key in ("governed_assigned", "retrieved_payload", "normalized_consumer")
        ):
            raise ValueError(f"SEAD excluded country decisions changed: {status}")
    output.mkdir(parents=True)
    with (output / "rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "schema_version": "sead-country-coverage.v1",
        "source_run_id": RUN,
        "source_scope": "governed_four_country_bbox_and_61_declared_relations",
        "country_assignment": "versioned_boundary_decision;source_country_not_supplied",
        "country_rows": rows,
        "excluded_country_decisions": {
            "review_pending": 103,
            "unassigned": 23,
            "retrieval_posture": "excluded_from_assigned_scope_not_retrieval_failures",
            "coordinate_validation": "not_independently_verified",
        },
        "capture_retrieval": receipts,
        "source_native_observation_denominator": observations["observation_count"],
        "refused_observation_disposition_denominator": events["refused_event_count"],
        "refused_country_allocation_basis": "all_source_native_observations_have_refused_event_dispositions;country_counts_follow_observation_country",
        "eligible_evidence_event_count": events["eligible_event_count"],
        "propagation_eligible_site_count": 0,
        "site_eligibility_basis": "no_eligible_observation_event_has_a_source_site",
        "scientific_posture": "source_native_observations_retained;all_event_dispositions_refused",
        "wp01_section6_posture": "partial_country_coverage_account;not_a_closure_claim",
        "wp01_section6_units_outside_this_replay": [
            "sites_linked_to_sample_groups_by_country",
            "physical_samples_by_country",
            "analysis_entities_by_country",
            "datasets_by_country",
            "analysis_values_by_country",
            "chronology_claims_by_type_age_system_and_refusal_reason_by_country",
            "propagation_eligible_sites_by_country",
        ],
        "coverage_caveats": [
            "source_country_field_not_supplied",
            "126_boundary_decisions_pending_or_unassigned",
            "excluded_preflight_coordinates_not_independently_verified",
            "provider_schema_version_not_reported",
            "capture_complete_only_for_declared_snapshot_and_scope",
            "no_scientifically_eligible_propagation_events",
        ],
        "input_sha256": {path.as_posix(): digest for path, digest in PINNED.items()},
        "rows_csv": {
            "path": "rows.csv",
            "sha256": _sha((output / "rows.csv").read_bytes()),
            "row_count": len(rows),
        },
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    return report


def main() -> int:
    """Publish complete country coverage and source retrieval accounting."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
