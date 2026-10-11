"""Account for governed SEAD source units by assigned site country."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256,
    SEAD_GOVERNED_ADMISSION_SHA256,
    SEAD_GOVERNED_BUILD_ID,
    SEAD_GOVERNED_COUNTRY_AUTHORITY_ID,
    SEAD_GOVERNED_COUNTRY_DECISIONS_SHA256,
    SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
    SEAD_GOVERNED_EVIDENCE_SCOPE_ID,
    governed_sead_evidence_root,
    read_validated_sead_evidence_documents,
)

COUNTRIES = {"SE": "Sweden", "DK": "Denmark", "NO": "Norway", "FI": "Finland"}
TABLE_KEYS = {
    "tbl_sites": "site_id",
    "tbl_sample_groups": "sample_group_id",
    "tbl_physical_samples": "physical_sample_id",
    "tbl_analysis_entities": "analysis_entity_id",
    "tbl_datasets": "dataset_id",
    "tbl_analysis_values": "analysis_value_id",
}
FIELDS = (
    "country_code",
    "country",
    "decision_status",
    "discovered_sites",
    "retrieved_sites",
    "sites_with_sample_groups",
    "sample_groups",
    "physical_samples",
    "analysis_entities",
    "datasets",
    "analysis_values",
    "dataset_membership_posture",
    "source_unit_posture",
)


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _read_json(path: Path, expected: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"SEAD source input is missing or linked: {path}")
    content = path.read_bytes()
    if _sha(content) != expected:
        raise ValueError(f"SEAD source identity changed: {path}")
    document = json.loads(content)
    if not isinstance(document, dict):
        raise ValueError(f"SEAD source input is not an object: {path}")
    return document


def _indexed(
    rows: list[dict[str, Any]], field: str, table: str
) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for row in rows:
        key = row.get(field)
        if (
            isinstance(key, bool)
            or not isinstance(key, int)
            or key <= 0
            or key in result
        ):
            raise ValueError(
                f"SEAD {table} has an invalid or duplicate {field}: {key!r}"
            )
        result[key] = row
    return result


def _required_parent(row: dict[str, Any], field: str, parents: dict[int, Any]) -> int:
    key = row.get(field)
    if isinstance(key, bool) or not isinstance(key, int) or key not in parents:
        raise ValueError(f"SEAD {field} has an unexplained missing parent: {key!r}")
    return key


def account(
    tables: dict[str, list[dict[str, Any]]],
    decisions: list[dict[str, Any]],
    bindings: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Traverse source keys without treating datasets as physical samples."""
    indexed = {
        table: _indexed(tables[table], key, table) for table, key in TABLE_KEYS.items()
    }
    sites = indexed["tbl_sites"]
    groups = indexed["tbl_sample_groups"]
    samples = indexed["tbl_physical_samples"]
    entities = indexed["tbl_analysis_entities"]
    datasets = indexed["tbl_datasets"]
    values = indexed["tbl_analysis_values"]
    if bindings["fields"] != [
        "site_id",
        "site_uuid",
        "country_code_index",
        "assignment_method_index",
    ] or bindings["assignment_methods"] != ["strict_boundary_containment"]:
        raise ValueError("SEAD normalized country binding contract changed")
    codes = bindings["country_codes"]
    bound = {
        site_id: (site_uuid, codes[code_index])
        for site_id, site_uuid, code_index, method_index in bindings["rows"]
        if method_index == 0
    }
    if len(bound) != len(bindings["rows"]) or set(bound) != set(sites):
        raise ValueError("SEAD normalized site country bindings do not close")
    decisions_by_id = _indexed(decisions, "site_id", "country-decisions")
    if len(decisions_by_id) != 2195 or len(sites) != 2069:
        raise ValueError("SEAD discovery/retrieval denominator changed")
    statuses: Counter[str] = Counter()
    site_country: dict[int, str] = {}
    for site_id, decision in decisions_by_id.items():
        detail = decision["decision"]
        status = detail["decision_status"]
        code = decision["governed_country_code"]
        statuses[status] += 1
        if status == "assigned":
            site = sites.get(site_id)
            if (
                site is None
                or code not in COUNTRIES
                or detail["decision_method"] != "strict_boundary_containment"
                or detail["derived_country"] != COUNTRIES[code]
                or (site["site_uuid"], code) != bound[site_id]
                or decision["site_uuid"] != site["site_uuid"]
            ):
                raise ValueError(
                    f"SEAD assigned site country identity changed: {site_id}"
                )
            site_country[site_id] = code
        elif status in {"review", "unassigned"}:
            if (
                site_id in sites
                or code != "UNASSIGNED"
                or detail["derived_country"] is not None
            ):
                raise ValueError(
                    f"SEAD unresolved site entered assigned capture: {site_id}"
                )
        else:
            raise ValueError(f"SEAD country decision status changed: {site_id}")
    if statuses != {"assigned": 2069, "review": 103, "unassigned": 23}:
        raise ValueError("SEAD country decision totals changed")
    country_sites = Counter(site_country.values())
    if country_sites != {"SE": 1925, "DK": 59, "NO": 45, "FI": 40}:
        raise ValueError("SEAD assigned country denominators changed")

    group_site = {
        group_id: _required_parent(row, "site_id", sites)
        for group_id, row in groups.items()
    }
    sample_site = {
        sample_id: group_site[_required_parent(row, "sample_group_id", groups)]
        for sample_id, row in samples.items()
    }
    entity_site = {
        entity_id: sample_site[_required_parent(row, "physical_sample_id", samples)]
        for entity_id, row in entities.items()
    }
    value_site = {
        value_id: entity_site[_required_parent(row, "analysis_entity_id", entities)]
        for value_id, row in values.items()
    }
    dataset_countries: dict[int, set[str]] = defaultdict(set)
    missing_dataset_entities: Counter[str] = Counter()
    for entity_id, entity in entities.items():
        code = site_country[entity_site[entity_id]]
        dataset_id = entity["dataset_id"]
        if dataset_id is None:
            missing_dataset_entities[code] += 1
            continue
        _required_parent(entity, "dataset_id", datasets)
        dataset_countries[dataset_id].add(code)
    if set(dataset_countries) != set(datasets):
        raise ValueError("SEAD dataset capture includes unlinked dataset keys")
    memberships = Counter(
        code for countries in dataset_countries.values() for code in countries
    )
    rows: list[dict[str, Any]] = []
    for code, name in COUNTRIES.items():
        linked_sites = {
            group_site[group_id]
            for group_id in groups
            if site_country[group_site[group_id]] == code
        }
        rows.append(
            {
                "country_code": code,
                "country": name,
                "decision_status": "assigned",
                "discovered_sites": country_sites[code],
                "retrieved_sites": country_sites[code],
                "sites_with_sample_groups": len(linked_sites),
                "sample_groups": sum(
                    site_country[site_id] == code for site_id in group_site.values()
                ),
                "physical_samples": sum(
                    site_country[site_id] == code for site_id in sample_site.values()
                ),
                "analysis_entities": sum(
                    site_country[site_id] == code for site_id in entity_site.values()
                ),
                "datasets": memberships[code],
                "analysis_values": sum(
                    site_country[site_id] == code for site_id in value_site.values()
                ),
                "dataset_membership_posture": "distinct_source_dataset_ids_linked_by_analysis_entities",
                "source_unit_posture": "captured_source_relations_only_no_event_admission",
            }
        )
    for status in ("review", "unassigned"):
        rows.append(
            {
                "country_code": status.upper(),
                "country": "",
                "decision_status": status,
                "discovered_sites": statuses[status],
                "retrieved_sites": 0,
                "sites_with_sample_groups": "",
                "sample_groups": "",
                "physical_samples": "",
                "analysis_entities": "",
                "datasets": "",
                "analysis_values": "",
                "dataset_membership_posture": "source_units_not_retrieved",
                "source_unit_posture": "excluded_pending_country_review",
            }
        )
    totals = {
        "retrieved_site_count": len(sites),
        "sites_with_sample_groups": len(set(group_site.values())),
        "sample_group_count": len(groups),
        "physical_sample_count": len(samples),
        "analysis_entity_count": len(entities),
        "dataset_distinct_count": len(datasets),
        "dataset_country_membership_count": sum(memberships.values()),
        "datasets_in_multiple_countries": sum(
            len(x) > 1 for x in dataset_countries.values()
        ),
        "analysis_entities_without_dataset_id_by_country": dict(
            sorted(missing_dataset_entities.items())
        ),
        "analysis_value_count": len(values),
        "decision_status_counts": dict(sorted(statuses.items())),
    }
    for field, expected in (
        ("retrieved_sites", totals["retrieved_site_count"]),
        ("sites_with_sample_groups", totals["sites_with_sample_groups"]),
        ("sample_groups", totals["sample_group_count"]),
        ("physical_samples", totals["physical_sample_count"]),
        ("analysis_entities", totals["analysis_entity_count"]),
        ("datasets", totals["dataset_country_membership_count"]),
        ("analysis_values", totals["analysis_value_count"]),
    ):
        if sum(int(row[field]) for row in rows[:4]) != expected:
            raise ValueError(f"SEAD country {field} totals do not reconcile")
    return rows, totals


def build(repository: Path, output: Path) -> dict[str, Any]:
    """Replay pinned raw and normalized identities to an absent destination."""
    repository, output = repository.resolve(), output.resolve()
    if (
        output.exists()
        or output.is_symlink()
        or not output.is_relative_to(repository / "artifacts")
    ):
        raise ValueError("Absent repository artifact destination required")
    data_root = repository / "data"
    raw = data_root / "sead/raw/acquisitions" / SEAD_GOVERNED_EVIDENCE_RUN_ID
    admission = _read_json(raw / "admission.json", SEAD_GOVERNED_ADMISSION_SHA256)
    _read_json(raw / "manifest.json", SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256)
    decisions = _read_json(
        raw / "country-decisions.json", SEAD_GOVERNED_COUNTRY_DECISIONS_SHA256
    )
    if (
        admission["run_id"] != SEAD_GOVERNED_EVIDENCE_RUN_ID
        or admission["build_id"] != SEAD_GOVERNED_BUILD_ID
        or admission["scope_id"] != SEAD_GOVERNED_EVIDENCE_SCOPE_ID
        or admission["release_status"] != "refused"
        or admission["country_accounting"]["boundary_authority_id"]
        != SEAD_GOVERNED_COUNTRY_AUTHORITY_ID
        or admission["country_accounting"]["country_counts"]
        != {"SE": 1925, "DK": 59, "NO": 45, "FI": 40}
        or decisions["boundary_authority"]["authority_id"]
        != SEAD_GOVERNED_COUNTRY_AUTHORITY_ID
    ):
        raise ValueError("SEAD governed admission or country authority changed")
    normalized = read_validated_sead_evidence_documents(
        governed_sead_evidence_root(data_root),
        ("source_key_ledger.json", "observation_relation_index.json"),
        expected_run_id=SEAD_GOVERNED_EVIDENCE_RUN_ID,
        expected_manifest_sha256=SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    )
    ledger = cast(dict[str, Any], normalized["source_key_ledger.json"])
    relation = cast(dict[str, Any], normalized["observation_relation_index.json"])
    if (
        ledger["acquisition_bundle_sha256"] != admission["acquisition_bundle_sha256"]
        or ledger["country_decisions_sha256"] != SEAD_GOVERNED_COUNTRY_DECISIONS_SHA256
        or ledger["table_count"] != 61
        or ledger["source_row_count"] != 522270
        or relation["source_run_id"] != SEAD_GOVERNED_EVIDENCE_RUN_ID
        or relation["build_id"] != SEAD_GOVERNED_BUILD_ID
        or relation["acquisition_manifest_sha256"]
        != SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256
    ):
        raise ValueError("SEAD raw/normalized relation identity changed")
    ledger_tables = {record["table"]: record for record in ledger["tables"]}
    copied = {record["path"]: record for record in admission["copied_files"]}
    tables: dict[str, list[dict[str, Any]]] = {}
    inputs: list[dict[str, Any]] = []
    for table, key in TABLE_KEYS.items():
        record = ledger_tables[table]
        payload_path = f"payloads/{table}.json"
        receipt_path = f"receipts/{table}.json"
        expected = record["payload"]["sha256"]
        payload = _read_json(raw / payload_path, expected)
        receipt = _read_json(raw / receipt_path, record["receipt"]["sha256"])
        rows = payload["rows"]
        if (
            expected != copied[payload_path]["sha256"]
            or expected != relation["source_table_sha256"][table]
            or expected != receipt["content_sha256"]
            or record["receipt"]["sha256"] != copied[receipt_path]["sha256"]
            or record["primary_key"] != key
            or len(rows) != record["row_count"]
            or len(rows) != receipt["row_count"]
            or len(rows) != relation["source_table_counts"][table]
            or receipt["status"] != "complete"
            or receipt["run_id"] != SEAD_GOVERNED_EVIDENCE_RUN_ID
            or receipt["build_id"] != SEAD_GOVERNED_BUILD_ID
            or receipt["scope_id"] != SEAD_GOVERNED_EVIDENCE_SCOPE_ID
        ):
            raise ValueError(f"SEAD source relation changed: {table}")
        tables[table] = rows
        inputs.append(
            {
                "table": table,
                "primary_key": key,
                "row_count": len(rows),
                "payload_sha256": expected,
                "receipt_sha256": record["receipt"]["sha256"],
            }
        )
    rows, totals = account(
        tables, decisions["decisions"], ledger["site_country_bindings"]
    )
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    csv_bytes = stream.getvalue().encode()
    report = {
        "schema_version": "sead-country-source-units.v1",
        "source_run_id": SEAD_GOVERNED_EVIDENCE_RUN_ID,
        "build_id": SEAD_GOVERNED_BUILD_ID,
        "scope_id": SEAD_GOVERNED_EVIDENCE_SCOPE_ID,
        "acquisition_manifest_sha256": SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256,
        "acquisition_bundle_sha256": admission["acquisition_bundle_sha256"],
        "admission_sha256": SEAD_GOVERNED_ADMISSION_SHA256,
        "country_decisions_sha256": SEAD_GOVERNED_COUNTRY_DECISIONS_SHA256,
        "country_authority_id": SEAD_GOVERNED_COUNTRY_AUTHORITY_ID,
        "normalized_manifest_sha256": SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
        "normalized_source_key_set_sha256": ledger["source_key_set_sha256"],
        "normalized_site_country_binding_sha256": ledger["site_country_binding_sha256"],
        "source_tables": inputs,
        "totals": totals,
        "country_rows": rows,
        "release_status": admission["release_status"],
        "scientific_admission": "none; source-unit accounting only",
        "rows_csv_sha256": _sha(csv_bytes),
    }
    output.mkdir(parents=True)
    (output / "rows.csv").write_bytes(csv_bytes)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    """Publish country-assigned source units with explicit review exclusions."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    build(args.repository, args.output)


if __name__ == "__main__":
    main()
