"""Bind a source-table export to independently replayed acquisition identities."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.collection.sources.sead.acquisition.governed import (
    governed_sead_expected_identity,
)
from bijux_pollenomics.collection.sources.sead.evidence.source_keys.validation import (
    validate_sead_source_key_ledger_against_acquisition,
)
from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_ADMISSION_SHA256,
    SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
    governed_sead_evidence_root,
    read_validated_sead_evidence_document,
)

_TABLE_FIELDS = (
    "table",
    "primary_key",
    "row_count",
    "distinct_primary_key_count",
    "duplicate_primary_key_count",
    "minimum_primary_key",
    "maximum_primary_key",
    "key_range_count",
    "payload_sha256",
    "receipt_sha256",
    "receipt_status",
)


def reconcile_source_relations(
    data_root: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Replay every source key, UUID binding and receipt from the pinned capture."""
    data_root = data_root.resolve()
    normalized = governed_sead_evidence_root(data_root)
    raw = data_root / "sead/raw/acquisitions" / SEAD_GOVERNED_EVIDENCE_RUN_ID
    admission_path = raw / "admission.json"
    if admission_path.is_symlink() or not admission_path.is_file():
        raise ValueError("Governed SEAD admission must be a regular file")
    admission_bytes = admission_path.read_bytes()
    if hashlib.sha256(admission_bytes).hexdigest() != SEAD_GOVERNED_ADMISSION_SHA256:
        raise ValueError("Governed SEAD admission identity changed")
    document = read_validated_sead_evidence_document(
        normalized,
        "source_key_ledger.json",
        expected_run_id=SEAD_GOVERNED_EVIDENCE_RUN_ID,
        expected_manifest_sha256=SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    )
    ledger = validate_sead_source_key_ledger_against_acquisition(
        document,
        raw,
        expected_identity=governed_sead_expected_identity(data_root),
    )
    return source_relation_export(ledger, json.loads(admission_bytes))


def source_relation_export(
    ledger: dict[str, Any],
    admission: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Summarize already validated source custody without promoting event eligibility."""
    if ledger["acquisition_bundle_sha256"] != admission["acquisition_bundle_sha256"]:
        raise ValueError("Source ledger and admission bundle identities diverge")
    tables = ledger["tables"]
    if len(tables) != ledger["table_count"]:
        raise ValueError("Source table count does not reconcile")
    if sum(row["row_count"] for row in tables) != ledger["source_row_count"]:
        raise ValueError("Source row count does not reconcile")
    rows = [
        {
            **{field: row[field] for field in _TABLE_FIELDS[:8]},
            "payload_sha256": row["payload"]["sha256"],
            "receipt_sha256": row["receipt"]["sha256"],
            "receipt_status": row["receipt"]["status"],
        }
        for row in sorted(tables, key=lambda row: row["table"])
    ]
    accountability = ledger["country_binding_accountability"]
    summary = {
        "schema_version": "sead-source-relations-export.v1",
        "source_run_id": ledger["source_run_id"],
        "build_id": ledger["build_id"],
        "scope_id": ledger["scope_id"],
        "acquisition_manifest_sha256": ledger["acquisition_manifest_sha256"],
        "acquisition_bundle_sha256": ledger["acquisition_bundle_sha256"],
        "admission_sha256": SEAD_GOVERNED_ADMISSION_SHA256,
        "normalized_manifest_sha256": SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
        "source_key_set_sha256": ledger["source_key_set_sha256"],
        "site_identity_sha256": ledger["site_identity_sha256"],
        "site_country_binding_sha256": ledger["site_country_binding_sha256"],
        "table_count": ledger["table_count"],
        "source_row_count": ledger["source_row_count"],
        "distinct_primary_key_count": ledger["distinct_primary_key_count"],
        "duplicate_primary_key_count": sum(
            row["duplicate_primary_key_count"] for row in tables
        ),
        "empty_table_count": ledger["empty_table_count"],
        "receipt_status_counts": dict(
            sorted(Counter(row["receipt_status"] for row in rows).items())
        ),
        "country_accountability": accountability,
        "admission_release_status": admission["release_status"],
        "downstream_statuses": admission["downstream_statuses"],
        "interpretation": "Source capture, receipts, source keys and country UUID bindings were replayed against the pinned acquisition. This does not approve cross-source taxonomy, propagation events or independent vegetation truth.",
    }
    return summary, rows


def write_source_relations(data_root: Path, output: Path) -> dict[str, Any]:
    """Retain the reconciled denominator export in an unoccupied destination."""
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise ValueError("Source relation export destination already exists")
    summary, rows = reconcile_source_relations(data_root)
    output.mkdir(parents=True)
    with (output / "tables.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=_TABLE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    summary["tables_csv_sha256"] = hashlib.sha256(
        (output / "tables.csv").read_bytes()
    ).hexdigest()
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    summary = write_source_relations(args.data_root, args.output)
    print(
        f"Reconciled {summary['table_count']} tables / {summary['source_row_count']} source rows; admission remains {summary['admission_release_status']}."
    )
    return 0
