"""Independent validation for SEAD source-key ledger documents."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
from typing import cast

from ...acquisition.admission import (
    SeadAdmissionExpectedIdentity,
    read_materialized_sead_full_evidence_admission,
)

from .contract import (
    SOURCE_KEY_LEDGER_SCHEMA_VERSION,
    SOURCE_KEY_RANGE_ENCODING,
    SOURCE_KEY_TABLE_CONTRACT_SCHEMA_VERSION,
    sead_source_key_table_plans,
    source_key_table_contract_rows,
    source_key_table_contract_sha256,
    table_contract_fields,
)
from .derivation import build_sead_source_key_ledger
from .identities import canonical_site_uuid
from .ranges import (
    decode_positive_integer_ranges,
    positive_integer_key_set_sha256,
    positive_integer_ranges_sha256,
)
from .serialization import canonical_sha256

_COUNTRY_CODES = ["DK", "FI", "NO", "SE"]
_BINDING_FIELDS = [
    "site_id",
    "site_uuid",
    "country_code_index",
    "assignment_method_index",
]
_LEDGER_FIELDS = {
    "schema_version",
    "source_family",
    "source_run_id",
    "scope_id",
    "build_id",
    "acquisition_manifest_sha256",
    "acquisition_bundle_sha256",
    "parent_admission_sha256",
    "country_decisions_sha256",
    "table_contract_schema_version",
    "table_contract_sha256",
    "table_count",
    "source_row_count",
    "distinct_primary_key_count",
    "key_range_count",
    "empty_table_count",
    "payload_set_sha256",
    "receipt_set_sha256",
    "source_key_set_sha256",
    "site_identity_sha256",
    "site_country_binding_sha256",
    "site_country_bindings",
    "country_binding_accountability",
    "tables",
}
_TABLE_FIELDS = {
    "ordinal",
    "table",
    "primary_key",
    "projection_fields",
    "filter_field",
    "dependencies",
    "row_count",
    "distinct_primary_key_count",
    "duplicate_primary_key_count",
    "minimum_primary_key",
    "maximum_primary_key",
    "key_encoding",
    "key_ranges",
    "key_range_count",
    "key_set_sha256",
    "key_ranges_sha256",
    "payload",
    "receipt",
    "table_record_sha256",
}
_PAYLOAD_FIELDS = {"path", "byte_count", "sha256"}
_RECEIPT_FIELDS = {
    "path",
    "byte_count",
    "sha256",
    "receipt_id",
    "status",
    "row_count",
    "content_sha256",
}
_SITE_BINDING_FIELDS = {
    "fields",
    "country_codes",
    "assignment_methods",
    "rows",
}
_COUNTRY_ACCOUNTABILITY_FIELDS = {
    "country_decisions_sha256",
    "bbox_site_count",
    "assigned_site_count",
    "review_site_count",
    "unassigned_site_count",
    "excluded_site_count",
    "country_counts",
    "decision_status_counts",
}


def validate_sead_source_key_ledger(
    document: Mapping[str, object],
) -> dict[str, object]:
    """Validate ledger structure, ordering, ranges, and aggregate identities."""
    if set(document) != _LEDGER_FIELDS:
        raise ValueError("SEAD source-key ledger fields changed")
    if document.get("schema_version") != SOURCE_KEY_LEDGER_SCHEMA_VERSION:
        raise ValueError("SEAD source-key ledger schema version changed")
    if document.get("source_family") != "sead":
        raise ValueError("SEAD source-key ledger family changed")
    if (
        document.get("table_contract_schema_version")
        != SOURCE_KEY_TABLE_CONTRACT_SCHEMA_VERSION
    ):
        raise ValueError("SEAD source-key table contract schema changed")
    _required_text(document, "source_run_id")
    for field in ("scope_id", "build_id", "acquisition_bundle_sha256"):
        _required_prefixed_sha256(document, field)
    for field in (
        "acquisition_manifest_sha256",
        "parent_admission_sha256",
        "country_decisions_sha256",
        "table_contract_sha256",
        "payload_set_sha256",
        "receipt_set_sha256",
        "source_key_set_sha256",
        "site_identity_sha256",
        "site_country_binding_sha256",
    ):
        _required_sha256(document, field)

    expected_contract = source_key_table_contract_rows()
    if document.get("table_contract_sha256") != source_key_table_contract_sha256(
        expected_contract
    ):
        raise ValueError("SEAD source-key table contract digest changed")
    tables_value = document.get("tables")
    if not isinstance(tables_value, list) or any(
        not isinstance(row, Mapping) for row in tables_value
    ):
        raise TypeError("SEAD source-key tables must be an object list")
    tables = cast(list[Mapping[str, object]], tables_value)
    plans = sead_source_key_table_plans()
    if len(tables) != len(plans) or _non_negative_int(document, "table_count") != len(
        plans
    ):
        raise ValueError("SEAD source-key table denominator changed")

    payload_inventory: list[dict[str, object]] = []
    receipt_inventory: list[dict[str, object]] = []
    key_inventory: list[dict[str, object]] = []
    decoded_by_table: dict[str, list[int]] = {}
    source_row_count = 0
    key_range_count = 0
    empty_table_count = 0
    for ordinal, (plan, row) in enumerate(zip(plans, tables, strict=True)):
        if set(row) != _TABLE_FIELDS:
            raise ValueError(f"SEAD source-key table fields changed: {plan.table}")
        if _non_negative_int(row, "ordinal") != ordinal:
            raise ValueError(f"SEAD source-key table ordinal changed: {plan.table}")
        if table_contract_fields(row) != expected_contract[ordinal]:
            raise ValueError(f"SEAD source-key table contract changed: {plan.table}")
        if row.get("key_encoding") != SOURCE_KEY_RANGE_ENCODING:
            raise ValueError(f"SEAD source-key encoding changed: {plan.table}")
        ranges = row.get("key_ranges")
        keys = decode_positive_integer_ranges(ranges)
        row_count = _non_negative_int(row, "row_count")
        if (
            row_count != len(keys)
            or _non_negative_int(row, "distinct_primary_key_count") != row_count
            or _non_negative_int(row, "duplicate_primary_key_count") != 0
        ):
            raise ValueError(f"SEAD source-key row denominator changed: {plan.table}")
        if _non_negative_int(row, "key_range_count") != len(cast(list[object], ranges)):
            raise ValueError(f"SEAD source-key range denominator changed: {plan.table}")
        expected_minimum = keys[0] if keys else None
        expected_maximum = keys[-1] if keys else None
        observed_minimum = _optional_positive_int(row, "minimum_primary_key")
        observed_maximum = _optional_positive_int(row, "maximum_primary_key")
        if observed_minimum != expected_minimum or observed_maximum != expected_maximum:
            raise ValueError(f"SEAD source-key extrema changed: {plan.table}")
        if row.get("key_set_sha256") != positive_integer_key_set_sha256(keys):
            raise ValueError(f"SEAD source-key set digest changed: {plan.table}")
        if row.get("key_ranges_sha256") != positive_integer_ranges_sha256(
            cast(list[list[int]], ranges)
        ):
            raise ValueError(f"SEAD source-key range digest changed: {plan.table}")

        payload = _required_mapping(row, "payload")
        receipt = _required_mapping(row, "receipt")
        payload_identity = _validate_payload_identity(payload, plan.table)
        receipt_identity = _validate_receipt_identity(
            receipt,
            plan.table,
            row_count=row_count,
            payload_sha256=cast(str, payload_identity["sha256"]),
        )
        record_without_digest = dict(row)
        table_record_sha256 = record_without_digest.pop("table_record_sha256", None)
        if table_record_sha256 != canonical_sha256(record_without_digest):
            raise ValueError(f"SEAD source-key table digest changed: {plan.table}")
        payload_inventory.append({"table": plan.table, **payload_identity})
        payload_inventory[-1].pop("path")
        receipt_inventory.append({"table": plan.table, **receipt_identity})
        for field in ("path", "receipt_id", "status", "row_count", "content_sha256"):
            receipt_inventory[-1].pop(field)
        key_inventory.append(
            {
                "table": plan.table,
                "primary_key": plan.primary_key,
                "row_count": row_count,
                "key_set_sha256": row["key_set_sha256"],
            }
        )
        decoded_by_table[plan.table] = keys
        source_row_count += row_count
        key_range_count += len(cast(list[object], ranges))
        empty_table_count += not keys

    aggregate_expectations = {
        "source_row_count": source_row_count,
        "distinct_primary_key_count": source_row_count,
        "key_range_count": key_range_count,
        "empty_table_count": empty_table_count,
        "payload_set_sha256": canonical_sha256(payload_inventory),
        "receipt_set_sha256": canonical_sha256(receipt_inventory),
        "source_key_set_sha256": canonical_sha256(key_inventory),
    }
    for field, expected in aggregate_expectations.items():
        observed = (
            _non_negative_int(document, field)
            if isinstance(expected, int)
            else document.get(field)
        )
        if observed != expected:
            raise ValueError(f"SEAD source-key aggregate changed: {field}")

    site_binding = _required_mapping(document, "site_country_bindings")
    site_identities, country_counts = _validate_site_binding(
        site_binding, decoded_by_table["tbl_sites"]
    )
    if document.get("site_identity_sha256") != canonical_sha256(site_identities):
        raise ValueError("SEAD site identity digest changed")
    if document.get("site_country_binding_sha256") != canonical_sha256(site_binding):
        raise ValueError("SEAD site-country binding digest changed")
    _validate_country_accountability(
        _required_mapping(document, "country_binding_accountability"),
        document=document,
        country_counts=country_counts,
        admitted_site_count=len(site_identities),
    )
    return dict(document)


def validate_sead_source_key_ledger_against_acquisition(
    document: Mapping[str, object],
    acquisition_root: Path,
    *,
    expected_identity: SeadAdmissionExpectedIdentity,
) -> dict[str, object]:
    """Replay the ledger from independently admitted on-disk acquisition bytes."""
    validated = validate_sead_source_key_ledger(document)
    snapshot = read_materialized_sead_full_evidence_admission(
        acquisition_root,
        expected_identity=expected_identity,
    )
    tables, table_sha256 = _tables_from_admitted_bytes(snapshot.copied_files)
    expected = build_sead_source_key_ledger(
        acquisition_root,
        admission=snapshot.admission,
        tables=tables,
        table_sha256=table_sha256,
    )
    if validated != expected:
        raise ValueError("SEAD source-key ledger differs from admitted acquisition")
    return validated


def _tables_from_admitted_bytes(
    copied_files: Mapping[str, bytes],
) -> tuple[dict[str, list[Mapping[str, object]]], dict[str, str]]:
    tables: dict[str, list[Mapping[str, object]]] = {}
    digests: dict[str, str] = {}
    for plan in sead_source_key_table_plans():
        path = f"payloads/{plan.table}.json"
        try:
            content = copied_files[path]
        except KeyError as exc:
            raise ValueError(f"Admitted SEAD payload is missing: {path}") from exc
        try:
            payload = json.loads(content)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"Admitted SEAD payload is invalid: {path}") from exc
        if not isinstance(payload, Mapping) or payload.get("table") != plan.table:
            raise ValueError(f"Admitted SEAD payload identity changed: {path}")
        rows = payload.get("rows")
        if not isinstance(rows, list) or any(
            not isinstance(row, Mapping) for row in rows
        ):
            raise TypeError(f"Admitted SEAD payload rows are invalid: {path}")
        tables[plan.table] = cast(list[Mapping[str, object]], rows)
        digests[plan.table] = hashlib.sha256(content).hexdigest()
    return tables, digests


def _validate_payload_identity(
    value: Mapping[str, object], table: str
) -> dict[str, object]:
    if set(value) != _PAYLOAD_FIELDS:
        raise ValueError(f"SEAD source-key payload fields changed: {table}")
    if value.get("path") != f"payloads/{table}.json":
        raise ValueError(f"SEAD source-key payload path changed: {table}")
    return {
        "path": value["path"],
        "byte_count": _non_negative_int(value, "byte_count"),
        "sha256": _required_sha256(value, "sha256"),
    }


def _validate_receipt_identity(
    value: Mapping[str, object],
    table: str,
    *,
    row_count: int,
    payload_sha256: str,
) -> dict[str, object]:
    if set(value) != _RECEIPT_FIELDS:
        raise ValueError(f"SEAD source-key receipt fields changed: {table}")
    if value.get("path") != f"receipts/{table}.json":
        raise ValueError(f"SEAD source-key receipt path changed: {table}")
    if (
        value.get("status") != "complete"
        or _non_negative_int(value, "row_count") != row_count
    ):
        raise ValueError(f"SEAD source-key receipt status changed: {table}")
    if value.get("content_sha256") != payload_sha256:
        raise ValueError(f"SEAD source-key receipt content digest changed: {table}")
    return {
        "path": value["path"],
        "byte_count": _non_negative_int(value, "byte_count"),
        "sha256": _required_sha256(value, "sha256"),
        "receipt_id": _required_text(value, "receipt_id"),
        "status": "complete",
        "row_count": row_count,
        "content_sha256": payload_sha256,
    }


def _validate_site_binding(
    value: Mapping[str, object], expected_site_ids: list[int]
) -> tuple[list[dict[str, object]], Counter[str]]:
    if set(value) != _SITE_BINDING_FIELDS:
        raise ValueError("SEAD site-country binding fields changed")
    if value.get("fields") != _BINDING_FIELDS:
        raise ValueError("SEAD site-country binding fields changed")
    if value.get("country_codes") != _COUNTRY_CODES:
        raise ValueError("SEAD site-country binding countries changed")
    methods = value.get("assignment_methods")
    if (
        not isinstance(methods, list)
        or not methods
        or methods != sorted(set(methods))
        or any(not isinstance(method, str) or not method for method in methods)
    ):
        raise ValueError("SEAD site-country assignment methods are invalid")
    rows = value.get("rows")
    if not isinstance(rows, list):
        raise TypeError("SEAD site-country binding rows must be a list")
    identities: list[dict[str, object]] = []
    country_counts: Counter[str] = Counter()
    site_ids: list[int] = []
    site_uuids: set[str] = set()
    for row in rows:
        if not isinstance(row, list) or len(row) != len(_BINDING_FIELDS):
            raise TypeError("SEAD site-country binding row shape changed")
        site_id, site_uuid, country_index, method_index = row
        if isinstance(site_id, bool) or not isinstance(site_id, int) or site_id <= 0:
            raise ValueError("SEAD site-country binding ID is invalid")
        site_uuid = canonical_site_uuid(site_uuid)
        if site_uuid in site_uuids:
            raise ValueError("SEAD site-country binding UUIDs must be unique")
        if (
            isinstance(country_index, bool)
            or not isinstance(country_index, int)
            or country_index not in range(len(_COUNTRY_CODES))
        ):
            raise ValueError("SEAD site-country binding country index is invalid")
        if (
            isinstance(method_index, bool)
            or not isinstance(method_index, int)
            or method_index not in range(len(methods))
        ):
            raise ValueError("SEAD site-country binding method index is invalid")
        site_ids.append(site_id)
        site_uuids.add(site_uuid)
        identities.append({"site_id": site_id, "site_uuid": site_uuid})
        country_counts[_COUNTRY_CODES[country_index]] += 1
    if site_ids != expected_site_ids:
        raise ValueError("SEAD site-country bindings do not match tbl_sites keys")
    return identities, country_counts


def _validate_country_accountability(
    value: Mapping[str, object],
    *,
    document: Mapping[str, object],
    country_counts: Counter[str],
    admitted_site_count: int,
) -> None:
    if set(value) != _COUNTRY_ACCOUNTABILITY_FIELDS:
        raise ValueError("SEAD country-binding accountability fields changed")
    expected_counts = {code: country_counts.get(code, 0) for code in _COUNTRY_CODES}
    observed_counts = _non_negative_count_mapping(value, "country_counts")
    if observed_counts != expected_counts:
        raise ValueError("SEAD site-country counts changed")
    if _non_negative_int(value, "assigned_site_count") != admitted_site_count:
        raise ValueError("SEAD assigned-site denominator changed")
    review_count = _non_negative_int(value, "review_site_count")
    unassigned_count = _non_negative_int(value, "unassigned_site_count")
    excluded_count = _non_negative_int(value, "excluded_site_count")
    bbox_count = _non_negative_int(value, "bbox_site_count")
    if excluded_count != review_count + unassigned_count:
        raise ValueError("SEAD excluded-site denominator changed")
    if bbox_count != admitted_site_count + excluded_count:
        raise ValueError("SEAD bbox-site denominator changed")
    if value.get("country_decisions_sha256") != document.get(
        "country_decisions_sha256"
    ):
        raise ValueError("SEAD country-decision digest does not reconcile")
    statuses = value.get("decision_status_counts")
    if not isinstance(statuses, Mapping) or _validated_count_mapping(statuses) != {
        "assigned": admitted_site_count,
        **({"review": review_count} if review_count else {}),
        **({"unassigned": unassigned_count} if unassigned_count else {}),
    }:
        raise ValueError("SEAD country-decision status counts changed")


def _required_mapping(value: Mapping[str, object], field: str) -> Mapping[str, object]:
    result = value.get(field)
    if not isinstance(result, Mapping):
        raise TypeError(f"SEAD source-key {field} must be an object")
    return result


def _required_text(value: Mapping[str, object], field: str) -> str:
    result = value.get(field)
    if not isinstance(result, str) or not result.strip():
        raise ValueError(f"SEAD source-key {field} must be nonempty text")
    return result.strip()


def _required_sha256(value: Mapping[str, object], field: str) -> str:
    result = _required_text(value, field)
    if len(result) != 64 or any(
        character not in "0123456789abcdef" for character in result
    ):
        raise ValueError(f"SEAD source-key {field} must be a lowercase SHA-256")
    return result


def _required_prefixed_sha256(value: Mapping[str, object], field: str) -> str:
    result = _required_text(value, field)
    digest = result.removeprefix("sha256:")
    if (
        result == digest
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise ValueError(
            f"SEAD source-key {field} must be a prefixed lowercase SHA-256"
        )
    return result


def _non_negative_int(value: Mapping[str, object], field: str) -> int:
    result = value.get(field)
    if isinstance(result, bool) or not isinstance(result, int) or result < 0:
        raise ValueError(f"SEAD source-key {field} must be a non-negative integer")
    return result


def _optional_positive_int(value: Mapping[str, object], field: str) -> int | None:
    result = value.get(field)
    if result is None:
        return None
    if isinstance(result, bool) or not isinstance(result, int) or result <= 0:
        raise ValueError(f"SEAD source-key {field} must be null or a positive integer")
    return result


def _non_negative_count_mapping(
    value: Mapping[str, object], field: str
) -> dict[str, int]:
    result = value.get(field)
    if not isinstance(result, Mapping):
        raise TypeError(f"SEAD source-key {field} must be an object")
    return _validated_count_mapping(result)


def _validated_count_mapping(value: Mapping[object, object]) -> dict[str, int]:
    result: dict[str, int] = {}
    for key, count in value.items():
        if not isinstance(key, str) or not key:
            raise ValueError("SEAD source-key count labels must be nonempty text")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError("SEAD source-key counts must be non-negative integers")
        result[key] = count
    return result


__all__ = [
    "validate_sead_source_key_ledger",
    "validate_sead_source_key_ledger_against_acquisition",
]
