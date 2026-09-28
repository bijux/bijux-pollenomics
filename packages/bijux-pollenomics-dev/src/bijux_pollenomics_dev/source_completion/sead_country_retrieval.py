"""Reconcile SEAD country discovery, retained retrieval and public site rows."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

RUN = "sead-full-evidence-39bfff6a-ce80714e"
RAW = Path("data/sead/raw/acquisitions") / RUN
BOUNDARY = Path("data/boundaries/review/country-decisions/sead.json")
PUBLIC = Path("data/sead/normalized/nordic_environmental_sites.csv")
PINNED = {
    RAW
    / "admission.json": "69f93b6bd34e457bedc4047077024de1beefc900142f45051fab60dce03751ea",
    RAW
    / "manifest.json": "6fc2428046d148f9ce6c158f982afbbbbaea39de2132850a4fb8f41acf8a4c14",
    RAW
    / "country-decisions.json": "e08c2fa2f70d9a3491b95a87b81c992ec3902051aa6e30c35dbcb0f86e214528",
    RAW
    / "payloads/tbl_sites.json": "b5cb28e935fdd2293999ffce7fe72c064571d4f7fc9e98b5e8bc4681a2b93479",
    RAW
    / "receipts/tbl_sites.json": "2cc201892afd57a148c4a9359228c06e3f3265af6daff6b2669fdac3352361b4",
    RAW
    / "reconciliation/countries.json": "1b321a672d4eb8f02875068973e6e24e4ee17d3af2a3619ab6dee2484f2e24a8",
    BOUNDARY: "5f74c5b8eeb02e28e0ff0b5abdb96a8fb0dc7fa32427055dce0c1967e07ad643",
    PUBLIC: "dbf4df63e8da625637f3ddb19ed7f5e7ddc7d884da9a45a85cebd286f0dbf158",
}
COUNTRIES = {"SE": "Sweden", "DK": "Denmark", "NO": "Norway", "FI": "Finland"}
COUNTRY_FIELDS = (
    "group",
    "discovered_with_governed_country",
    "source_reported_country_count",
    "governed_assigned",
    "retrieved_payload",
    "normalized_consumer",
    "source_country_posture",
    "admission_posture",
)
SITE_FIELDS = (
    "site_id",
    "site_uuid",
    "source_country",
    "candidate_countries",
    "governed_country_code",
    "country_decision_status",
    "decision_method",
    "retrieved_payload",
    "normalized_consumer",
    "normalized_country",
    "qualified_review_status",
    "admission_posture",
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _distinct(items: list[int], meaning: str) -> set[int]:
    result = set(items)
    if len(result) != len(items):
        raise ValueError(f"Duplicate {meaning} site ID")
    return result


def reconcile(
    decisions: dict[str, Any],
    boundary: dict[str, Any],
    receipt: dict[str, Any],
    payload: dict[str, Any],
    normalized: list[dict[str, str]],
    country_reconciliation: dict[str, Any],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Keep source country, governed country, and retrieval as separate claims."""
    discovered = decisions["decisions"]
    reviewed = boundary["decisions"]
    retrieved = payload["rows"]
    if (
        len(discovered) != 2195
        or len(reviewed) != 2195
        or len(retrieved) != 2069
        or len(normalized) != 2069
        or receipt["status"] != "complete"
        or receipt["requested_identity_count"] != 2195
        or receipt["row_count"] != 2069
        or receipt["governed_row_count"] != 2069
        or receipt["bbox_row_count"] != 2195
        or receipt["query_count"] != 1
        or receipt["query_receipts"][0]["row_count"] != 2195
        or receipt["query_receipts"][0]["status"] != "complete"
        or receipt["scope_exclusion_reason"] != "country_assignment_unassigned"
        or country_reconciliation["row_count"] != 2069
        or country_reconciliation["scope_excluded_count"] != 126
        or country_reconciliation["reconciles"] is not True
        or country_reconciliation["run_id"] != RUN
        or receipt["run_id"] != RUN
        or country_reconciliation["build_id"] != receipt["build_id"]
        or country_reconciliation["scope_id"] != receipt["scope_id"]
        or country_reconciliation["parent_run_id"] != decisions["run_id"]
        or country_reconciliation["country_assignment_id"]
        != decisions["boundary_authority"]["authority_id"]
    ):
        raise ValueError("SEAD discovery or retrieval denominators changed")
    by_decision = {int(row["site_id"]): row for row in discovered}
    by_boundary = {
        int(row["source_record_id"].removeprefix("sead:site:")): row for row in reviewed
    }
    by_payload = {int(row["site_id"]): row for row in retrieved}
    by_public = {int(row["record_id"]): row for row in normalized}
    discovered_ids = _distinct([int(row["site_id"]) for row in discovered], "discovery")
    if (
        len(by_boundary) != 2195
        or len(by_payload) != 2069
        or len(by_public) != 2069
        or set(by_boundary) != discovered_ids
        or _distinct(receipt["requested_identities"], "requested") != discovered_ids
        or len({row["site_uuid"] for row in discovered}) != 2195
        or len({row["site_uuid"] for row in retrieved}) != 2069
        or len({row["site_uuid"] for row in normalized}) != 2069
    ):
        raise ValueError("SEAD site identities changed")
    assignment = {
        int(row["site_id"]): row["country_code"]
        for row in receipt["governed_country_assignments"]
    }
    if len(assignment) != 2195 or set(assignment) != discovered_ids:
        raise ValueError("Receipt country assignments changed")
    excluded = {
        site_id for site_id in discovered_ids if assignment[site_id] == "UNASSIGNED"
    }
    if (
        excluded != _distinct(receipt["scope_excluded_site_ids"], "excluded")
        or excluded
        != _distinct(
            country_reconciliation["scope_excluded_site_ids"], "reconciled excluded"
        )
        or set(by_payload) != discovered_ids - excluded
        or set(by_public) != set(by_payload)
    ):
        raise ValueError("Excluded coordinates entered retrieval or public consumer")
    rows: list[dict[str, object]] = []
    for site_id in sorted(discovered_ids):
        source = by_decision[site_id]
        decision = source["decision"]
        review = by_boundary[site_id]
        status = decision["decision_status"]
        code = source["governed_country_code"]
        admitted = status == "assigned"
        if (
            status not in {"assigned", "review", "unassigned"}
            or decision["raw_country"] is not None
            or review["raw_country"] is not None
            or decision["raw_country_comparison"] != "not_supplied"
            or review["raw_country_comparison"] != "not_supplied"
            or review["prior_country_decision_comparison"] != "agrees"
            or review["country_decision_status"] != status
            or review["boundary_decision_status"] != status
            or review["decision_method"] != decision["decision_method"]
            or review["candidate_countries"] != decision["candidate_countries"]
            or review["boundary_artifact_digest"]
            != decision["boundary_artifact_digest"]
            or review["longitude"] != source["longitude_dd"]
            or review["latitude"] != source["latitude_dd"]
            or code != assignment[site_id]
            or (
                admitted
                and (
                    code not in COUNTRIES
                    or decision["derived_country"] != COUNTRIES[code]
                    or review["published_country"] != code
                    or review["derived_country_code"] != code
                    or review["review_requirement"] != "no_point_review_required"
                )
            )
            or (
                not admitted
                and (
                    code != "UNASSIGNED"
                    or decision["derived_country"] is not None
                    or review["published_country"] is not None
                    or review["derived_country_code"] is not None
                    or review["review_requirement"] != "qualified_review_required"
                    or review["qualified_review_status"] != "pending"
                )
            )
        ):
            raise ValueError(
                f"SEAD source/governed country divergence at site {site_id}"
            )
        if admitted:
            record = by_payload[site_id]
            consumer = by_public[site_id]
            if (
                record["site_uuid"] != source["site_uuid"]
                or consumer["site_uuid"] != source["site_uuid"]
                or consumer["country"] != COUNTRIES[code]
                or consumer["source"] != "SEAD"
                or consumer["source_url"] != f"https://browser.sead.se/site/{site_id}"
            ):
                raise ValueError(
                    f"SEAD retrieved/public identity diverged at site {site_id}"
                )
        rows.append(
            {
                "site_id": site_id,
                "site_uuid": source["site_uuid"],
                "source_country": "not_supplied",
                "candidate_countries": ";".join(decision["candidate_countries"]),
                "governed_country_code": code if admitted else "",
                "country_decision_status": status,
                "decision_method": decision["decision_method"],
                "retrieved_payload": str(admitted).lower(),
                "normalized_consumer": str(admitted).lower(),
                "normalized_country": COUNTRIES[code] if admitted else "",
                "qualified_review_status": "not_required" if admitted else "pending",
                "admission_posture": "governed_site_context"
                if admitted
                else "excluded_pending_review",
            }
        )
    statuses = Counter(str(row["country_decision_status"]) for row in rows)
    codes = Counter(
        str(row["governed_country_code"])
        for row in rows
        if row["governed_country_code"]
    )
    if (
        statuses != {"assigned": 2069, "review": 103, "unassigned": 23}
        or codes != {"SE": 1925, "DK": 59, "NO": 45, "FI": 40}
        or country_reconciliation["counts"] != {**dict(codes), "UNASSIGNED": 0}
    ):
        raise ValueError("SEAD country counts changed")
    countries: list[dict[str, object]] = []
    for code in ("SE", "DK", "NO", "FI"):
        countries.append(
            {
                "group": code,
                "discovered_with_governed_country": codes[code],
                "source_reported_country_count": "not_supplied",
                "governed_assigned": codes[code],
                "retrieved_payload": codes[code],
                "normalized_consumer": codes[code],
                "source_country_posture": "not_supplied",
                "admission_posture": "governed_site_context",
            }
        )
    for status in ("review", "unassigned"):
        countries.append(
            {
                "group": status.upper(),
                "discovered_with_governed_country": statuses[status],
                "source_reported_country_count": "not_supplied",
                "governed_assigned": 0,
                "retrieved_payload": 0,
                "normalized_consumer": 0,
                "source_country_posture": "not_supplied",
                "admission_posture": "excluded_pending_review",
            }
        )
    return countries, rows


def build(repository: Path, output: Path) -> dict[str, Any]:
    """Write a source-bound row and country ledger in an absent destination."""
    repository = repository.resolve()
    output = output.resolve()
    if output.exists() or output.is_symlink():
        raise ValueError("Absent output destination required")
    inputs: list[dict[str, object]] = []
    for relative, expected in PINNED.items():
        path = repository / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Pinned SEAD input is missing or linked: {relative}")
        content = path.read_bytes()
        if _sha(content) != expected:
            raise ValueError(f"Pinned SEAD input changed: {relative}")
        inputs.append(
            {"path": relative.as_posix(), "bytes": len(content), "sha256": expected}
        )
    raw = repository / RAW
    admission = json.loads((raw / "admission.json").read_text())
    manifest = json.loads((raw / "manifest.json").read_text())
    copied = {row["path"]: row["sha256"] for row in admission["copied_files"]}
    if (
        admission["run_id"] != RUN
        or admission["release_status"] != "refused"
        or len(admission["table_counts"]) != 61
        or len(manifest["required_tables"]) != 61
        or manifest["status"] != "complete"
        or admission["acquisition_manifest_sha256"] != PINNED[RAW / "manifest.json"]
        or any(
            copied[relative.relative_to(RAW).as_posix()] != digest
            for relative, digest in PINNED.items()
            if relative.is_relative_to(RAW) and relative.name != "admission.json"
        )
    ):
        raise ValueError("Governed SEAD source receipt changed")
    with (repository / PUBLIC).open(encoding="utf-8", newline="") as handle:
        normalized = list(csv.DictReader(handle))
    countries, sites = reconcile(
        json.loads((raw / "country-decisions.json").read_text()),
        json.loads((repository / BOUNDARY).read_text()),
        json.loads((raw / "receipts/tbl_sites.json").read_text()),
        json.loads((raw / "payloads/tbl_sites.json").read_text()),
        normalized,
        json.loads((raw / "reconciliation/countries.json").read_text()),
    )
    output.mkdir(parents=True)
    for name, fields, records in (
        ("countries.csv", COUNTRY_FIELDS, countries),
        ("sites.csv", SITE_FIELDS, sites),
    ):
        with (output / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(records)
    report: dict[str, Any] = {
        "schema_version": "sead-country-retrieval.v1",
        "run_id": RUN,
        "source_table_count": 61,
        "source_country_field_posture": "not_supplied_on_all_discovered_sites",
        "inventory": {
            "discovered_bbox": 2195,
            "governed_assigned": 2069,
            "review_excluded": 103,
            "unassigned_excluded": 23,
            "retrieved_tbl_sites": 2069,
            "normalized_site_consumer": 2069,
        },
        "admission": {
            "qualified_review_of_126_coordinates": "pending",
            "source_release_status": "refused",
            "site_context": "admitted_for_2069_governed_country_assignments_only",
        },
        "inputs": inputs,
        "outputs": {
            name: {
                "bytes": (output / name).stat().st_size,
                "sha256": _sha((output / name).read_bytes()),
            }
            for name in ("countries.csv", "sites.csv")
        },
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    build(args.repository, args.output)


if __name__ == "__main__":
    main()
