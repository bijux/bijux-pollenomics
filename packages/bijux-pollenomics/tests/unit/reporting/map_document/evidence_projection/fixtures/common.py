"""Shared atlas evidence-projection fixture encoding."""

from __future__ import annotations

from __future__ import annotations
import json
from pathlib import Path
from typing import cast


def _write_json(path: Path, value: object) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    path.write_bytes(payload)
    return payload


def _decode_sead_claim_table(table: dict[str, object]) -> list[dict[str, object]]:
    fields = cast(list[str], table["fields"])
    dictionaries = cast(dict[str, list[object]], table["column_dictionaries"])
    list_fields = set(cast(list[str], table["list_dictionary_fields"]))
    list_dictionary = cast(list[str], table["list_value_dictionary"])
    age_columns = cast(
        dict[str, list[str]], table["source_age_value_columns_by_claim_type"]
    )
    inherited = cast(
        dict[str, dict[str, str]],
        table["source_age_value_inherited_fields_by_claim_type"],
    )
    age_dictionaries = cast(
        dict[str, dict[str, list[object]]],
        table["source_age_value_dictionaries_by_claim_type"],
    )
    relation_dictionary = cast(
        list[list[list[str]]], table["source_relation_path_dictionary"]
    )
    common = cast(dict[str, object], table["common_fields"])
    decoded: list[dict[str, object]] = []
    for encoded in cast(list[list[object]], table["records"]):
        row = dict(zip(fields, encoded, strict=True))
        for field, dictionary in dictionaries.items():
            row[field] = dictionary[cast(int, row[field])]
        for field in list_fields:
            row[field] = [
                list_dictionary[index] for index in cast(list[int], row[field])
            ]
        claim_type = cast(str, row["claim_type"])
        source_age_value: dict[str, object] = {}
        for field, encoded_value in zip(
            age_columns[claim_type],
            cast(list[object], row["source_age_value"]),
            strict=True,
        ):
            age_dictionary = age_dictionaries[claim_type].get(field)
            source_age_value[field] = (
                age_dictionary[cast(int, encoded_value)]
                if age_dictionary is not None
                else encoded_value
            )
        for source_field, claim_field in inherited[claim_type].items():
            source_age_value[source_field] = row[claim_field]
        row["source_age_value"] = source_age_value
        relation_shape = relation_dictionary[cast(int, row["source_relation_path"])]
        row["source_relation_path"] = [
            {
                "table": table_name,
                "key": key,
                "value": (
                    common["source_site_id"]
                    if value_field == "common_fields.source_site_id"
                    else row[value_field]
                ),
            }
            for table_name, key, value_field in relation_shape
        ]
        decoded.append({**common, **row})
    return decoded


def _decode_dictionary_table(table: dict[str, object]) -> list[dict[str, object]]:
    fields = cast(list[str], table["fields"])
    dictionaries = cast(dict[str, list[object]], table["column_dictionaries"])
    list_fields = set(cast(list[str], table["list_dictionary_fields"]))
    list_dictionary = cast(list[str], table["list_value_dictionary"])
    decoded: list[dict[str, object]] = []
    for encoded in cast(list[list[object]], table["records"]):
        row = dict(zip(fields, encoded, strict=True))
        for field, dictionary in dictionaries.items():
            row[field] = dictionary[cast(int, row[field])]
        for field in list_fields:
            row[field] = [
                list_dictionary[index] for index in cast(list[int], row[field])
            ]
        decoded.append(row)
    return decoded
