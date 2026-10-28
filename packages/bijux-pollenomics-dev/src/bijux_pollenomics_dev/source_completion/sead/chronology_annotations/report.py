"""Publish aggregate/native-witness custody without approving chronology use."""

from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path
from typing import Any

from .comparison import canonical
from .custody import audit_claim, reference_links
from .source import INDEX_SHA256, RUN, SOURCES, TABLE_KEYS, _read, index_rows


def build(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Consume the fixed source index and exact native payloads; never reacquire."""
    base = root / "data/sead/normalized/acquisitions" / RUN
    raw = root / "data/sead/raw/acquisitions" / RUN
    inputs: dict[str, str] = {}
    index = _read(base / "chronology_claims.json", INDEX_SHA256, inputs, root)
    manifest = _read(
        raw / "manifest.json", index["acquisition_manifest_sha256"], inputs, root
    )
    if index["source_run_id"] != RUN or index["claim_count"] != 25109:
        raise ValueError("Native chronology capture scope differs")
    payloads = {row["path"]: row["sha256"] for row in manifest["files"]}
    tables: dict[str, dict[int, dict[str, Any]]] = {}
    for name, key in TABLE_KEYS.items():
        document = _read(
            raw / "payloads" / (name + ".json"),
            payloads["payloads/" + name + ".json"],
            inputs,
            root,
        )
        if document.get("table") != name:
            raise ValueError("Native payload table differs")
        tables[name] = index_rows(document["rows"], key)
    references = reference_links(tables)
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for part in index["partitioned_fields"]["claims"]["parts"]:
        document = _read(base / part["path"], part["sha256"], inputs, root)
        if len(document["claims"]) != part["row_count"]:
            raise ValueError("Claim part row count differs")
        for claim in document["claims"]:
            identity = (claim["source_table"], claim["source_record_id"])
            if identity in seen:
                raise ValueError("Native source chronology row reused")
            seen.add(identity)
            records.append(audit_claim(claim, tables, references))
    expected = {
        (table, str(identifier))
        for table, _ in SOURCES.values()
        for identifier in tables[table]
    }
    if seen != expected or len(records) != 25109:
        raise ValueError("Native age population omission or addition")
    witness = hashlib.sha256(b"\n".join(canonical(row) for row in records)).hexdigest()
    report = {
        "schema_version": "sead-native-age-annotation-custody.v1",
        "source_run_id": RUN,
        "claim_count": len(records),
        "selected_native_table_count": len(tables),
        "source_native_table_row_counts": {
            name: len(rows) for name, rows in tables.items()
        },
        "all_captured_date_rows_accounted": True,
        "chronology_eligibility_counts": dict(
            sorted(
                Counter(str(row["chronology_eligibility"]) for row in records).items()
            )
        ),
        "native_field_cells_compared": sum(
            row["native_field_count"] for row in records
        ),
        "all_raw_annotations_preserved_in_sidecar": True,
        "native_field_comparison_counts": dict(
            sorted(
                Counter(
                    item["category"]
                    for row in records
                    for item in row["field_comparisons"]
                ).items()
            )
        ),
        "native_lookup_comparison_counts": dict(
            sorted(
                Counter(
                    item["category"]
                    for row in records
                    for item in row["lookup_comparisons"]
                ).items()
            )
        ),
        "raw_unknown_flag_count": sum(
            item["native_unknown_flag"]
            for row in records
            for item in row["field_comparisons"]
        ),
        "stored_unknown_flags_changed_to_nonnull_count": sum(
            item["native_unknown_flag"]
            and item["stored_present"]
            and item["stored_type"] != "null"
            for row in records
            for item in row["field_comparisons"]
        ),
        "stored_unknown_flags_omitted_count": sum(
            item["native_unknown_flag"] and not item["stored_present"]
            for row in records
            for item in row["field_comparisons"]
        ),
        "claims_with_stored_native_differences": sum(
            not row["all_stored_native_fields_exact"] for row in records
        ),
        "native_source_null_field_cells": sum(
            row["native_null_fields"] for row in records
        ),
        "claim_type_counts": dict(
            sorted(Counter(row["claim_type"] for row in records).items())
        ),
        "uncertainty_label_counts": dict(
            sorted(Counter(str(row["uncertainty_label"]) for row in records).items())
        ),
        "dataset_method_counts": dict(
            sorted(Counter(str(row["dataset_method_id"]) for row in records).items())
        ),
        "bibliography_status_counts": dict(
            sorted(Counter(row["bibliography_status"] for row in records).items())
        ),
        "calibration_status_counts": dict(
            sorted(Counter(row["calibration_status"] for row in records).items())
        ),
        "claim_witness_sha256": witness,
        "reference_link_occurrences_by_role": {
            role: sum(len(row["reference_ids"][role]) for row in records)
            for role in ["dataset", "site", "sample_group", "relative_age"]
        },
        "null_reference_occurrences_by_role": {
            role: sum(
                value is None for row in records for value in row["reference_ids"][role]
            )
            for role in ["dataset", "site", "sample_group", "relative_age"]
        },
        "source_inputs_sha256": inputs,
        "eligible_event_count": 0,
        "scientific_admission": False,
        "limits": "Original raw typed annotations are preserved in the private sidecar; every difference or omission in stored normalized fields is explicit and is not approved as harmless. Native field/owner/lookup comparison only. Null methods or references stay null, model chronology IDs remain unresolved when no source authority is captured, calibration and unknown bases are unchanged. No qualified age/event/rights approval, date conversion, model or ecological inference.",
    }
    return report, records
