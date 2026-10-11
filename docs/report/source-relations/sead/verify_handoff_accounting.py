"""Check governed SEAD handoff denominators across source, review, and map reports."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

REPORT = Path("docs/report/source-relations/sead")
COUNTRIES = {"DK": "Denmark", "FI": "Finland", "NO": "Norway", "SE": "Sweden"}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _document(root: Path, relative: str) -> dict[str, Any]:
    value = json.loads((root / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"SEAD handoff input is not an object: {relative}")
    return value


def _same(label: str, *values: object) -> None:
    if any(value != values[0] for value in values[1:]):
        raise ValueError(f"SEAD handoff {label} differs: {values!r}")


def _bound(root: Path, owner: dict[str, Any], relative: str, field: str) -> None:
    if _sha(root / relative) != owner[field][relative]:
        raise ValueError(f"SEAD handoff source digest differs: {relative}")


def _source_join_projection(source: dict[str, Any]) -> list[dict[str, Any]]:
    """Retain every relation identity and denominator from the captured join audit."""
    edges = source["edges"]
    if not isinstance(edges, list):
        raise ValueError("SEAD handoff source join audit is not a list")
    projected: list[dict[str, Any]] = []
    names: set[str] = set()
    for edge in edges:
        name = edge["edge"]
        if not isinstance(name, str) or name in names:
            raise ValueError("SEAD handoff source join identities differ")
        names.add(name)
        projected.append(
            {
                "edge": name,
                "child_row_count": edge["child_row_count"],
                "referenced_child_row_count": edge["referenced_child_row_count"],
                "matched_child_count": edge["matched_child_count"],
                "null_reference_child_count": edge["null_reference_child_count"],
                "orphan_child_count": len(edge["orphan_child_ids"]),
                "unexplained_loss_count": edge["unexplained_loss_count"],
            }
        )
    return sorted(projected, key=lambda row: row["edge"])


def _checked_country_rows(
    rows: object, codes: set[str], label: str
) -> dict[str, dict[str, Any]]:
    """Refuse duplicate or missing country records before reducing denominators."""
    if not isinstance(rows, list) or len(rows) != len(codes):
        raise ValueError(f"SEAD handoff {label} country population differs")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"SEAD handoff {label} country row is not an object")
        code = row.get("country_code")
        if not isinstance(code, str) or code not in codes or code in result:
            raise ValueError(f"SEAD handoff {label} country identities differ")
        result[code] = row
    return result


def _count(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"SEAD handoff {label} is not a nonnegative integer")
    return value


def verify(root: Path) -> dict[str, Any]:
    """Return local accounting only after the existing source-owned reports agree."""
    root = root.resolve()
    base = REPORT.as_posix()
    summary = _document(root, f"{base}/summary.json")
    public = _document(root, f"{base}/public-custody/report.json")
    review = _document(root, f"{base}/chronology-claim-review/report.json")
    chronology = _document(root, f"{base}/chronology-country-accounting/report.json")
    coverage = _document(root, f"{base}/country-coverage/report.json")
    map_report = _document(root, f"{base}/map-candidate/report.json")
    run = summary["source_run_id"]
    raw = f"data/sead/raw/acquisitions/{run}"
    normalized = f"data/sead/normalized/acquisitions/{run}"
    admission_path = f"{raw}/admission.json"
    manifest_path = f"{raw}/manifest.json"
    evidence_path = f"{normalized}/evidence_materialization_manifest.json"
    admission = _document(root, admission_path)
    manifest = _document(root, manifest_path)
    evidence = _document(root, evidence_path)

    _same(
        "source run",
        run,
        admission["run_id"],
        evidence["source_run_id"],
        public["source_run_id"],
        review["source_run_id"],
        chronology["source_run_id"],
        coverage["source_run_id"],
        map_report["source_run_id"],
    )
    _same(
        "build",
        summary["build_id"],
        admission["build_id"],
        evidence["build_id"],
        review["source_build_id"],
    )
    _same(
        "raw admission",
        summary["admission_sha256"],
        review["input_hashes"]["admission_sha256"],
        _sha(root / admission_path),
    )
    _same(
        "raw manifest",
        summary["acquisition_manifest_sha256"],
        admission["acquisition_manifest_sha256"],
        review["input_hashes"]["manifest_sha256"],
        _sha(root / manifest_path),
    )
    _same(
        "evidence manifest",
        summary["normalized_manifest_sha256"],
        _sha(root / evidence_path),
    )
    joins_path = f"{raw}/reconciliation/joins.json"
    for relative in (admission_path, manifest_path, joins_path):
        _bound(root, public, relative, "inputs_sha256")
    for relative in (
        f"{base}/chronology-claim-review/report.json",
        f"{base}/public-custody/report.json",
    ):
        _bound(root, chronology, relative, "input_sha256")
    for relative in (evidence_path, f"{normalized}/evidence_events.json"):
        _bound(root, coverage, relative, "input_sha256")
    for relative in (
        f"{base}/chronology-country-accounting/report.json",
        f"{base}/country-coverage/report.json",
    ):
        _bound(root, map_report, relative, "source_sha256")

    _same("capture status", manifest["status"], "complete")
    _same("incomplete tables", manifest["incomplete_required_tables"], [])
    _same("missing tables", manifest["missing_required_tables"], [])
    _same("failed joins", manifest["failed_join_edges"], [])
    _same(
        "source table count",
        summary["table_count"],
        evidence["source_table_count"],
        coverage["capture_retrieval"]["table_receipts"],
        61,
    )
    _same(
        "source key count",
        summary["source_row_count"],
        summary["distinct_primary_key_count"],
        evidence["source_key_count"],
        522270,
    )
    _same("duplicate source keys", summary["duplicate_primary_key_count"], 0)
    _same(
        "source key set",
        summary["source_key_set_sha256"],
        evidence["source_key_set_sha256"],
    )
    _same(
        "site-country bindings",
        summary["site_country_binding_sha256"],
        evidence["site_country_binding_sha256"],
    )
    _same("complete receipts", summary["receipt_status_counts"], {"complete": 61})
    _same("join edges", public["join_edge_count"], len(public["join_edges"]), 86)
    _same(
        "source join projection",
        public["join_edges"],
        _source_join_projection(_document(root, joins_path)),
    )
    _same(
        "join null references",
        _count(public["join_null_reference_count"], "join null references"),
        sum(
            _count(edge["null_reference_child_count"], "edge null references")
            for edge in public["join_edges"]
        ),
    )
    if any(
        edge["orphan_child_count"] or edge["unexplained_loss_count"]
        for edge in public["join_edges"]
    ):
        raise ValueError("SEAD handoff has unresolved join loss")
    _same(
        "claims",
        review["claim_count"],
        chronology["claim_count"],
        evidence["chronology_claim_count"],
        map_report["reviewed_claim_count"],
        25109,
    )
    _same("claim types", review["claim_type_counts"], chronology["claim_type_counts"])
    _same(
        "age bases",
        review["reviewed_age_basis_counts"],
        chronology["reviewed_age_basis_counts"],
    )
    _same(
        "claim eligibility",
        review["chronology_eligibility_counts"],
        chronology["chronology_eligibility_counts"],
    )
    if sum(review["claim_type_counts"].values()) != review["claim_count"]:
        raise ValueError("SEAD handoff claim types do not reconcile")

    assigned = summary["country_accountability"]["country_counts"]
    _same(
        "assigned sites",
        sum(assigned.values()),
        summary["country_accountability"]["assigned_site_count"],
        public["raw_and_public_site_count"],
        chronology["assigned_site_count"],
        map_report["site_count"],
        2069,
    )
    _same(
        "excluded sites",
        summary["country_accountability"]["excluded_site_count"],
        public["excluded_decision_count"],
        chronology["excluded_site_count"],
        126,
    )
    _same(
        "excluded decisions",
        public["excluded_status_counts"],
        chronology["excluded_site_status_counts"],
        {"review": 103, "unassigned": 23},
    )
    _same(
        "country decisions",
        sum(summary["country_accountability"]["decision_status_counts"].values()),
        summary["country_accountability"]["bbox_site_count"],
        2195,
    )
    _same(
        "public countries",
        {code: public["country_counts"][name] for code, name in COUNTRIES.items()},
        assigned,
    )
    _same(
        "map countries",
        {
            code: map_report["site_country_counts"][name]
            for code, name in COUNTRIES.items()
        },
        assigned,
    )
    country_rows = _checked_country_rows(
        coverage["country_rows"], set(COUNTRIES), "coverage"
    )
    for code, sites in assigned.items():
        _same(
            f"{code} site custody",
            country_rows[code]["governed_assigned_sites"],
            country_rows[code]["retrieved_sites"],
            country_rows[code]["normalized_sites"],
            sites,
        )
    _same(
        "country claims",
        sum(chronology["country_counts"].values()),
        review["claim_count"],
    )
    if set(chronology["country_counts"]) != set(COUNTRIES):
        raise ValueError("SEAD handoff chronology country set differs")
    chronology_rows = _checked_country_rows(
        chronology["country_site_denominators"], set(COUNTRIES), "chronology"
    )
    for code, row in chronology_rows.items():
        _same(f"{code} chronology country name", row["country"], COUNTRIES[code])
        _same(
            f"{code} chronology assigned sites",
            _count(row["assigned_site_count"], "assigned sites"),
            assigned[code],
        )
        _same(
            f"{code} chronology site split",
            _count(row["claim_site_count"], "claim sites")
            + _count(row["assigned_sites_without_claim_count"], "sites without claims"),
            assigned[code],
        )
        _same(
            f"{code} chronology claims",
            _count(row["claim_count"], "country claims"),
            chronology["country_counts"][code],
            chronology["propagation_refusal_counts_by_country"][code],
        )
    _same(
        "chronology claim sites",
        sum(row["claim_site_count"] for row in chronology_rows.values()),
        chronology["claim_site_count"],
    )
    _same(
        "source observations",
        sum(row["source_native_observations"] for row in country_rows.values()),
        coverage["source_native_observation_denominator"],
        evidence["observation_count"],
        177763,
    )
    _same(
        "refused observations",
        sum(row["refused_observation_dispositions"] for row in country_rows.values()),
        coverage["refused_observation_disposition_denominator"],
        evidence["refused_event_count"],
        177763,
    )
    _same(
        "eligible events",
        evidence["eligible_event_count"],
        coverage["eligible_evidence_event_count"],
        map_report["eligible_ecological_event_count"],
        map_report["built_accepted_edge_count"],
        0,
    )
    _same(
        "release posture",
        admission["release_status"],
        summary["admission_release_status"],
        map_report["source_release_status"],
        "refused",
    )
    if (
        review["review_posture"]["event_propagation_approved"]
        or review["review_posture"]["scientific_chronology_admission_approved"]
    ):
        raise ValueError("SEAD handoff scientific posture changed")

    return {
        "source_run_id": run,
        "local_accounting": "verified",
        "source_tables": 61,
        "source_rows": 522270,
        "join_edges": 86,
        "reviewed_claims": 25109,
        "assigned_sites": assigned,
        "refused_observations": 177763,
        "eligible_ecological_events": 0,
        "release_status": "refused",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(verify(args.repository), sort_keys=True))


if __name__ == "__main__":
    main()
