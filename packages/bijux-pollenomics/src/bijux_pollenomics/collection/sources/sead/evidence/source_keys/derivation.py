"""Derive compact source-key accountability from an admitted SEAD acquisition."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
import hashlib
import json
from pathlib import Path
from typing import cast

from ...acquisition.scoped.models import SeadScopedTablePlan

from .contract import (
    SOURCE_KEY_LEDGER_SCHEMA_VERSION,
    SOURCE_KEY_RANGE_ENCODING,
    SOURCE_KEY_TABLE_CONTRACT_SCHEMA_VERSION,
    sead_source_key_table_plans,
    source_key_table_contract_rows,
    source_key_table_contract_sha256,
)
from .ranges import (
    encode_positive_integer_ranges,
    positive_integer_key_set_sha256,
    positive_integer_ranges_sha256,
)
from .identities import canonical_site_uuid
from .serialization import canonical_sha256

_COUNTRY_CODES = ("DK", "FI", "NO", "SE")


def build_sead_source_key_ledger(
    acquisition_root: Path,
    *,
    admission: Mapping[str, object],
    tables: Mapping[str, Sequence[Mapping[str, object]]],
    table_sha256: Mapping[str, str],
) -> dict[str, object]:
    """Build the exact primary-key ledger for all admitted SEAD source tables."""
    root = Path(acquisition_root)
    plans = sead_source_key_table_plans()
    expected_tables = tuple(plan.table for plan in plans)
    if set(tables) != set(expected_tables) or set(table_sha256) != set(expected_tables):
        raise ValueError("SEAD source-key inputs must cover the exact planned tables")

    copied_records = _copied_file_records(admission)
    contract_rows = source_key_table_contract_rows()
    table_records: list[dict[str, object]] = []
    payload_inventory: list[dict[str, object]] = []
    receipt_inventory: list[dict[str, object]] = []
    key_inventory: list[dict[str, object]] = []

    for ordinal, plan in enumerate(plans):
        rows = tables[plan.table]
        keys = [row.get(plan.primary_key) for row in rows]
        ranges = encode_positive_integer_ranges(keys)
        ordered_keys = sorted(cast(list[int], keys))
        key_set_sha256 = positive_integer_key_set_sha256(ordered_keys)
        key_ranges_sha256 = positive_integer_ranges_sha256(ranges)
        payload_path = f"payloads/{plan.table}.json"
        receipt_path = f"receipts/{plan.table}.json"
        payload_record = _required_file_record(copied_records, payload_path)
        receipt_record = _required_file_record(copied_records, receipt_path)
        payload_digest = _required_sha256(payload_record, "sha256")
        if payload_digest != table_sha256[plan.table]:
            raise ValueError(f"SEAD payload digest changed for {plan.table}")
        receipt = _read_bound_object(root, receipt_path, receipt_record)
        _validate_receipt(receipt, plan=plan, admission=admission, rows=rows)
        if receipt.get("content_sha256") != payload_digest:
            raise ValueError(f"SEAD receipt content digest changed for {plan.table}")

        payload_identity = {
            "path": payload_path,
            "byte_count": _non_negative_int(payload_record, "byte_count"),
            "sha256": payload_digest,
        }
        receipt_identity = {
            "path": receipt_path,
            "byte_count": _non_negative_int(receipt_record, "byte_count"),
            "sha256": _required_sha256(receipt_record, "sha256"),
            "receipt_id": _required_text(receipt, "receipt_id"),
            "status": "complete",
            "row_count": len(rows),
            "content_sha256": payload_digest,
        }
        table_record: dict[str, object] = {
            **contract_rows[ordinal],
            "row_count": len(rows),
            "distinct_primary_key_count": len(ordered_keys),
            "duplicate_primary_key_count": 0,
            "minimum_primary_key": ordered_keys[0] if ordered_keys else None,
            "maximum_primary_key": ordered_keys[-1] if ordered_keys else None,
            "key_encoding": SOURCE_KEY_RANGE_ENCODING,
            "key_ranges": ranges,
            "key_range_count": len(ranges),
            "key_set_sha256": key_set_sha256,
            "key_ranges_sha256": key_ranges_sha256,
            "payload": payload_identity,
            "receipt": receipt_identity,
        }
        table_record["table_record_sha256"] = canonical_sha256(table_record)
        table_records.append(table_record)
        payload_inventory.append(
            {
                "table": plan.table,
                "byte_count": payload_identity["byte_count"],
                "sha256": payload_identity["sha256"],
            }
        )
        receipt_inventory.append(
            {
                "table": plan.table,
                "byte_count": receipt_identity["byte_count"],
                "sha256": receipt_identity["sha256"],
            }
        )
        key_inventory.append(
            {
                "table": plan.table,
                "primary_key": plan.primary_key,
                "row_count": len(rows),
                "key_set_sha256": key_set_sha256,
            }
        )

    country_decisions_sha256 = _copied_file_sha256(
        copied_records, "country-decisions.json"
    )
    country_document = _read_bound_object(
        root,
        "country-decisions.json",
        _required_file_record(copied_records, "country-decisions.json"),
    )
    site_binding, country_accountability, site_identity_sha256 = (
        _build_site_country_binding(
            tables["tbl_sites"],
            country_document,
            country_decisions_sha256=country_decisions_sha256,
        )
    )

    row_count = sum(cast(int, row["row_count"]) for row in table_records)
    range_count = sum(cast(int, row["key_range_count"]) for row in table_records)
    return {
        "schema_version": SOURCE_KEY_LEDGER_SCHEMA_VERSION,
        "source_family": "sead",
        "source_run_id": _required_text(admission, "run_id"),
        "scope_id": _required_prefixed_sha256(admission, "scope_id"),
        "build_id": _required_prefixed_sha256(admission, "build_id"),
        "acquisition_manifest_sha256": _required_sha256(
            admission, "acquisition_manifest_sha256"
        ),
        "acquisition_bundle_sha256": _required_prefixed_sha256(
            admission, "acquisition_bundle_sha256"
        ),
        "parent_admission_sha256": _required_sha256(
            admission, "parent_admission_sha256"
        ),
        "country_decisions_sha256": country_decisions_sha256,
        "table_contract_schema_version": SOURCE_KEY_TABLE_CONTRACT_SCHEMA_VERSION,
        "table_contract_sha256": source_key_table_contract_sha256(contract_rows),
        "table_count": len(table_records),
        "source_row_count": row_count,
        "distinct_primary_key_count": row_count,
        "key_range_count": range_count,
        "empty_table_count": sum(not row["row_count"] for row in table_records),
        "payload_set_sha256": canonical_sha256(payload_inventory),
        "receipt_set_sha256": canonical_sha256(receipt_inventory),
        "source_key_set_sha256": canonical_sha256(key_inventory),
        "site_identity_sha256": site_identity_sha256,
        "site_country_binding_sha256": canonical_sha256(site_binding),
        "site_country_bindings": site_binding,
        "country_binding_accountability": country_accountability,
        "tables": table_records,
    }


def _build_site_country_binding(
    site_rows: Sequence[Mapping[str, object]],
    country_document: Mapping[str, object],
    *,
    country_decisions_sha256: str,
) -> tuple[dict[str, object], dict[str, object], str]:
    decisions_value = country_document.get("decisions")
    if not isinstance(decisions_value, list):
        raise TypeError("SEAD country decisions must be a list")
    decisions: dict[int, Mapping[str, object]] = {}
    decision_status_counts: Counter[str] = Counter()
    for value in decisions_value:
        if not isinstance(value, Mapping):
            raise TypeError("SEAD country decision must be an object")
        site_id = _positive_int(value, "site_id")
        if site_id in decisions:
            raise ValueError(f"Duplicate SEAD country decision for site {site_id}")
        decision = _required_mapping(value, "decision")
        status = _required_text(decision, "decision_status")
        if status not in {"assigned", "review", "unassigned"}:
            raise ValueError(f"SEAD country decision status is invalid: {status}")
        decision_status_counts[status] += 1
        decisions[site_id] = value

    site_identity_rows: list[dict[str, object]] = []
    expanded_bindings: list[dict[str, object]] = []
    country_counts: Counter[str] = Counter()
    methods: set[str] = set()
    site_ids: set[int] = set()
    site_uuids: set[str] = set()
    for site in sorted(site_rows, key=lambda row: _positive_int(row, "site_id")):
        site_id = _positive_int(site, "site_id")
        site_uuid = canonical_site_uuid(site.get("site_uuid"))
        if site_id in site_ids or site_uuid in site_uuids:
            raise ValueError("SEAD site IDs and UUIDs must form a bijection")
        site_ids.add(site_id)
        site_uuids.add(site_uuid)
        row = decisions.get(site_id)
        if row is None:
            raise ValueError(f"SEAD country decision is missing for site {site_id}")
        decision = _required_mapping(row, "decision")
        if _required_text(decision, "decision_status") != "assigned":
            raise ValueError(f"Admitted SEAD site is not assigned: {site_id}")
        if canonical_site_uuid(row.get("site_uuid")) != site_uuid:
            raise ValueError(f"SEAD site UUID differs from country decision: {site_id}")
        country_code = _required_text(row, "governed_country_code")
        if country_code not in _COUNTRY_CODES:
            raise ValueError(f"SEAD admitted site has invalid country: {site_id}")
        method = _required_text(decision, "decision_method")
        country_counts[country_code] += 1
        methods.add(method)
        site_identity_rows.append({"site_id": site_id, "site_uuid": site_uuid})
        expanded_bindings.append(
            {
                "site_id": site_id,
                "site_uuid": site_uuid,
                "country_code": country_code,
                "assignment_method": method,
            }
        )

    assigned_decision_ids = {
        site_id
        for site_id, row in decisions.items()
        if _required_text(_required_mapping(row, "decision"), "decision_status")
        == "assigned"
    }
    if assigned_decision_ids != site_ids:
        raise ValueError("Assigned SEAD decisions must exactly match admitted sites")
    method_values = sorted(methods)
    compact_rows = [
        [
            cast(int, row["site_id"]),
            cast(str, row["site_uuid"]),
            _COUNTRY_CODES.index(cast(str, row["country_code"])),
            method_values.index(cast(str, row["assignment_method"])),
        ]
        for row in expanded_bindings
    ]
    compact_binding: dict[str, object] = {
        "fields": [
            "site_id",
            "site_uuid",
            "country_code_index",
            "assignment_method_index",
        ],
        "country_codes": list(_COUNTRY_CODES),
        "assignment_methods": method_values,
        "rows": compact_rows,
    }
    review_count = decision_status_counts.get("review", 0)
    unassigned_count = decision_status_counts.get("unassigned", 0)
    accountability: dict[str, object] = {
        "country_decisions_sha256": country_decisions_sha256,
        "bbox_site_count": len(decisions),
        "assigned_site_count": len(site_rows),
        "review_site_count": review_count,
        "unassigned_site_count": unassigned_count,
        "excluded_site_count": review_count + unassigned_count,
        "country_counts": {
            code: country_counts.get(code, 0) for code in _COUNTRY_CODES
        },
        "decision_status_counts": dict(sorted(decision_status_counts.items())),
    }
    _match_declared_mapping(
        country_document.get("decision_status_counts"),
        accountability["decision_status_counts"],
        "decision status counts",
    )
    _match_declared_mapping(
        country_document.get("country_counts"),
        {
            **cast(dict[str, int], accountability["country_counts"]),
            "UNASSIGNED": review_count + unassigned_count,
        },
        "country counts",
    )
    return compact_binding, accountability, canonical_sha256(site_identity_rows)


def _validate_receipt(
    receipt: Mapping[str, object],
    *,
    plan: SeadScopedTablePlan,
    admission: Mapping[str, object],
    rows: Sequence[Mapping[str, object]],
) -> None:
    expected = {
        "table": plan.table,
        "primary_key": plan.primary_key,
        "projection": plan.projection,
        "filter_field": plan.filter_field,
        "status": "complete",
        "row_count": len(rows),
        "run_id": _required_text(admission, "run_id"),
        "scope_id": _required_prefixed_sha256(admission, "scope_id"),
        "build_id": _required_prefixed_sha256(admission, "build_id"),
    }
    for field, value in expected.items():
        if receipt.get(field) != value:
            raise ValueError(f"SEAD receipt {field} changed for {plan.table}")


def _read_bound_object(
    root: Path, relative_path: str, record: Mapping[str, object]
) -> dict[str, object]:
    content = (root / relative_path).read_bytes()
    if len(content) != _non_negative_int(record, "byte_count"):
        raise ValueError(f"SEAD admitted byte count changed: {relative_path}")
    if hashlib.sha256(content).hexdigest() != _required_sha256(record, "sha256"):
        raise ValueError(f"SEAD admitted digest changed: {relative_path}")
    try:
        value = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"SEAD JSON is invalid: {relative_path}") from exc
    if not isinstance(value, dict):
        raise TypeError(f"SEAD JSON object is required: {relative_path}")
    return value


def _copied_file_records(
    admission: Mapping[str, object],
) -> dict[str, Mapping[str, object]]:
    value = admission.get("copied_files")
    if not isinstance(value, list):
        raise TypeError("SEAD admission copied_files must be a list")
    result: dict[str, Mapping[str, object]] = {}
    for row in value:
        if not isinstance(row, Mapping):
            raise TypeError("SEAD copied-file record must be an object")
        path = _required_text(row, "path")
        if path in result:
            raise ValueError(f"Duplicate SEAD copied-file path: {path}")
        result[path] = row
    return result


def _required_file_record(
    records: Mapping[str, Mapping[str, object]], path: str
) -> Mapping[str, object]:
    try:
        return records[path]
    except KeyError as exc:
        raise ValueError(f"SEAD admission does not bind {path}") from exc


def _copied_file_sha256(records: Mapping[str, Mapping[str, object]], path: str) -> str:
    return _required_sha256(_required_file_record(records, path), "sha256")


def _required_mapping(value: Mapping[str, object], field: str) -> Mapping[str, object]:
    result = value.get(field)
    if not isinstance(result, Mapping):
        raise TypeError(f"SEAD {field} must be an object")
    return result


def _required_text(value: Mapping[str, object], field: str) -> str:
    result = value.get(field)
    if not isinstance(result, str) or not result.strip():
        raise ValueError(f"SEAD {field} must be nonempty text")
    return result.strip()


def _required_sha256(value: Mapping[str, object], field: str) -> str:
    result = _required_text(value, field)
    if len(result) != 64 or any(
        character not in "0123456789abcdef" for character in result
    ):
        raise ValueError(f"SEAD {field} must be a lowercase SHA-256")
    return result


def _required_prefixed_sha256(value: Mapping[str, object], field: str) -> str:
    result = _required_text(value, field)
    digest = result.removeprefix("sha256:")
    if (
        result == digest
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise ValueError(f"SEAD {field} must be a prefixed lowercase SHA-256")
    return result


def _positive_int(value: Mapping[str, object], field: str) -> int:
    result = value.get(field)
    if isinstance(result, bool) or not isinstance(result, int) or result <= 0:
        raise ValueError(f"SEAD {field} must be a positive integer")
    return result


def _non_negative_int(value: Mapping[str, object], field: str) -> int:
    result = value.get(field)
    if isinstance(result, bool) or not isinstance(result, int) or result < 0:
        raise ValueError(f"SEAD {field} must be a non-negative integer")
    return result


def _match_declared_mapping(actual: object, expected: object, label: str) -> None:
    if actual is not None and actual != expected:
        raise ValueError(f"SEAD declared {label} do not reconcile")


__all__ = ["build_sead_source_key_ledger"]
