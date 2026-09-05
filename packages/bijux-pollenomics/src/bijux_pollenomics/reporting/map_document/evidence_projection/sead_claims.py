"""Compact and validate SEAD chronology claims."""

from __future__ import annotations

from __future__ import annotations
from collections.abc import Mapping, Sequence
import hashlib
from pathlib import Path
from typing import cast
from .constants import (
    _SEAD_CLAIM_COMMON_FIELDS,
    _SEAD_CLAIM_FIELDS,
    _SEAD_DICTIONARY_FIELDS,
    _SEAD_LIST_DICTIONARY_FIELDS,
    _SEAD_RELATION_VALUE_FIELDS,
    _SEAD_SOURCE_AGE_INHERITED_FIELDS,
)
from .io import (
    _identifier_text,
    _mapping,
    _read_json_object,
    _read_regular_bytes,
    _regular_absolute_directory,
    _required_text,
    _safe_relative_path,
)


def _sead_claim_table(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """Encode complete SEAD claims without repeating shared source vocabulary."""
    if not rows:
        raise ValueError("SEAD chronology claim table cannot be empty")
    ordered = sorted(
        rows,
        key=lambda row: _required_text(
            row.get("chronology_claim_id"), "SEAD chronology claim ID"
        ),
    )
    required_fields = {*_SEAD_CLAIM_FIELDS, *_SEAD_CLAIM_COMMON_FIELDS}
    for row in ordered:
        missing = sorted(required_fields - set(row))
        if missing:
            raise ValueError(f"SEAD chronology claim fields are missing: {missing}")
        for field in (
            "chronology_claim_id",
            "source_family",
            "source_table",
            "site_uuid",
            "source_site_id",
            "country_code",
            "country_assignment_method",
            "subject_type",
            "claim_type",
            "source_age_type",
            "source_age_unit",
            "original_interval_orientation",
            "calibration_status",
            "comparability_status",
            "chronology_eligibility",
            "propagation_eligibility",
            "publication_role",
            "selection_status",
            "selection_rule_version",
            "provenance_record_id",
            "build_id",
            "schema_version",
            "source_payload_sha256",
            "acquisition_manifest_sha256",
        ):
            _required_text(row.get(field), f"SEAD chronology claim {field}")
        for field in ("source_record_id", "source_native_record_id", "subject_id"):
            _identifier_text(row.get(field), f"SEAD chronology claim {field}")

    common_fields: dict[str, object] = {}
    for field in _SEAD_CLAIM_COMMON_FIELDS:
        value = ordered[0].get(field)
        if any(row.get(field) != value for row in ordered[1:]):
            raise ValueError(f"SEAD site claims disagree on shared field: {field}")
        common_fields[field] = value
    if common_fields["source_family"] != "sead":
        raise ValueError("SEAD chronology claim source family changed")

    column_dictionaries: dict[str, list[object]] = {}
    column_dictionary_indexes: dict[str, dict[object, int]] = {}
    for field in sorted(_SEAD_DICTIONARY_FIELDS):
        raw_dictionary_values = [row.get(field) for row in ordered]
        if any(
            value is not None and not isinstance(value, str)
            for value in raw_dictionary_values
        ):
            raise ValueError(f"SEAD chronology claim {field} must be text or null")
        dictionary_values = sorted(
            set(raw_dictionary_values),
            key=lambda value: (value is not None, str(value)),
        )
        column_dictionaries[field] = dictionary_values
        column_dictionary_indexes[field] = {
            value: index for index, value in enumerate(dictionary_values)
        }

    list_values: set[str] = set()
    for field in _SEAD_LIST_DICTIONARY_FIELDS:
        for row in ordered:
            raw_values = row.get(field)
            if not isinstance(raw_values, list) or any(
                not isinstance(value, str) or not value for value in raw_values
            ):
                raise ValueError(f"SEAD chronology claim {field} must be text rows")
            list_values.update(cast(list[str], raw_values))
    list_value_dictionary = sorted(list_values)
    list_value_indexes = {
        value: index for index, value in enumerate(list_value_dictionary)
    }

    source_age_columns: dict[str, list[str]] = {}
    source_age_inherited: dict[str, dict[str, str]] = {}
    source_age_dictionaries: dict[str, dict[str, list[object]]] = {}
    source_age_dictionary_indexes: dict[str, dict[str, dict[object, int]]] = {}
    claim_types = sorted(
        {
            _required_text(row.get("claim_type"), "SEAD chronology claim type")
            for row in ordered
        }
    )
    for claim_type in claim_types:
        type_rows = [row for row in ordered if row.get("claim_type") == claim_type]
        age_values = [
            _mapping(row.get("source_age_value"), "SEAD source age value")
            for row in type_rows
        ]
        source_keys = set(age_values[0])
        if any(set(value) != source_keys for value in age_values[1:]):
            raise ValueError(
                f"SEAD {claim_type} source age value fields are inconsistent"
            )
        inherited: dict[str, str] = {}
        for source_field, claim_field in _SEAD_SOURCE_AGE_INHERITED_FIELDS.items():
            if source_field not in source_keys:
                continue
            if any(
                value.get(source_field) != row.get(claim_field)
                for row, value in zip(type_rows, age_values, strict=True)
            ):
                raise ValueError(
                    f"SEAD {claim_type} source age {source_field} disagrees with claim"
                )
            inherited[source_field] = claim_field
        columns = sorted(source_keys - set(inherited))
        source_age_columns[claim_type] = columns
        source_age_inherited[claim_type] = inherited
        dictionaries: dict[str, list[object]] = {}
        dictionary_indexes: dict[str, dict[object, int]] = {}
        for field in columns:
            values = [value.get(field) for value in age_values]
            if all(value is None or isinstance(value, str) for value in values):
                dictionary = sorted(
                    set(values), key=lambda value: (value is not None, str(value))
                )
                dictionaries[field] = dictionary
                dictionary_indexes[field] = {
                    value: index for index, value in enumerate(dictionary)
                }
        source_age_dictionaries[claim_type] = dictionaries
        source_age_dictionary_indexes[claim_type] = dictionary_indexes

    relation_shapes: list[list[list[str]]] = []
    encoded_rows: list[list[object]] = []
    for row in ordered:
        claim_type = _required_text(row.get("claim_type"), "SEAD chronology claim type")
        relation_path = row.get("source_relation_path")
        if not isinstance(relation_path, list) or not relation_path:
            raise ValueError("SEAD chronology claim relation path is missing")
        relation_shape: list[list[str]] = []
        for raw_entry in relation_path:
            entry = _mapping(raw_entry, "SEAD chronology relation entry")
            if set(entry) != {"table", "key", "value"}:
                raise ValueError("SEAD chronology relation entry fields changed")
            table = _required_text(entry.get("table"), "SEAD relation table")
            key = _required_text(entry.get("key"), "SEAD relation key")
            value_field = _SEAD_RELATION_VALUE_FIELDS.get(key)
            if value_field is None:
                raise ValueError(f"SEAD chronology relation key is unsupported: {key}")
            expected = (
                common_fields["source_site_id"]
                if value_field == "common_fields.source_site_id"
                else row.get(value_field)
            )
            if _identifier_text(entry.get("value"), "SEAD relation value") != (
                _identifier_text(expected, f"SEAD claim {value_field}")
            ):
                raise ValueError(
                    f"SEAD chronology relation {key} disagrees with its claim"
                )
            relation_shape.append([table, key, value_field])
        if relation_shape not in relation_shapes:
            relation_shapes.append(relation_shape)
        relation_index = relation_shapes.index(relation_shape)

        encoded: list[object] = []
        for field in _SEAD_CLAIM_FIELDS:
            value = row.get(field)
            if field in column_dictionary_indexes:
                value = column_dictionary_indexes[field][value]
            elif field in _SEAD_LIST_DICTIONARY_FIELDS:
                value = [list_value_indexes[item] for item in cast(list[str], value)]
            elif field == "source_age_value":
                source_age_value = _mapping(value, "SEAD source age value")
                value = [
                    source_age_dictionary_indexes[claim_type]
                    .get(source_field, {})
                    .get(
                        source_age_value.get(source_field),
                        source_age_value.get(source_field),
                    )
                    for source_field in source_age_columns[claim_type]
                ]
            elif field == "source_relation_path":
                value = relation_index
            encoded.append(value)
        encoded_rows.append(encoded)

    return {
        "record_count": len(encoded_rows),
        "fields": list(_SEAD_CLAIM_FIELDS),
        "records": encoded_rows,
        "encoding": "sead-chronology-claim-table.v1",
        "common_fields": common_fields,
        "column_dictionaries": column_dictionaries,
        "list_dictionary_fields": sorted(_SEAD_LIST_DICTIONARY_FIELDS),
        "list_value_dictionary": list_value_dictionary,
        "source_age_value_columns_by_claim_type": source_age_columns,
        "source_age_value_inherited_fields_by_claim_type": source_age_inherited,
        "source_age_value_dictionaries_by_claim_type": source_age_dictionaries,
        "source_relation_path_dictionary": relation_shapes,
        "source_relation_path_value_semantics": (
            "Each relation tuple is [table, key, claim/common field containing value]."
        ),
    }


def _validate_sead_claim_parents(
    acquisition_root: Path, claims_bundle: Mapping[str, object]
) -> Mapping[str, object]:
    root = _regular_absolute_directory(acquisition_root, "SEAD acquisition root")
    admission = _read_json_object(root / "admission.json", "SEAD admission")
    if admission.get("schema_version") != "sead-acquisition-admission.v1":
        raise ValueError("SEAD admission schema is unsupported")
    for field, claim_field in (
        ("run_id", "source_run_id"),
        ("build_id", "source_build_id"),
        ("acquisition_manifest_sha256", "acquisition_manifest_sha256"),
        ("acquisition_bundle_sha256", "acquisition_bundle_sha256"),
    ):
        if admission.get(field) != claims_bundle.get(claim_field):
            raise ValueError(f"SEAD admission and claim bundle {field} differ")
    copied_rows = admission.get("copied_files")
    if not isinstance(copied_rows, list) or any(
        not isinstance(row, Mapping) for row in copied_rows
    ):
        raise ValueError("SEAD admission copied-file inventory is invalid")
    copied = {
        _safe_relative_path(row.get("path")): row
        for row in cast(list[Mapping[str, object]], copied_rows)
    }
    if len(copied) != len(copied_rows):
        raise ValueError("SEAD admission copied-file paths are duplicated")
    required: dict[str, str] = {
        "manifest.json": _required_text(
            admission.get("acquisition_manifest_sha256"),
            "SEAD acquisition manifest SHA-256",
        ),
        "country-decisions.json": _required_text(
            claims_bundle.get("country_decisions_sha256"),
            "SEAD country decisions SHA-256",
        ),
    }
    table_digests = _mapping(
        claims_bundle.get("table_payload_sha256"), "SEAD table payload digests"
    )
    for table, digest in table_digests.items():
        required[f"payloads/{table}.json"] = _required_text(
            digest, f"SEAD {table} payload SHA-256"
        )
    for relative_path, expected_digest in required.items():
        copied_row = copied.get(relative_path)
        if copied_row is None or copied_row.get("sha256") != expected_digest:
            raise ValueError(f"SEAD admitted parent is not declared: {relative_path}")
        payload = _read_regular_bytes(root / relative_path, relative_path)
        if copied_row.get("byte_count") != len(payload):
            raise ValueError(f"SEAD admitted byte count changed: {relative_path}")
        if hashlib.sha256(payload).hexdigest() != expected_digest:
            raise ValueError(f"SEAD admitted digest changed: {relative_path}")
    return admission
