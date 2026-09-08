"""Compact atlas detail record encoding helpers."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, MutableMapping, Sequence
from typing import cast

from .io import _identifier_text, _mapping, _required_text


def _features(layer: Mapping[str, object]) -> list[MutableMapping[str, object]]:
    raw = layer.get("features")
    if not isinstance(raw, list) or any(
        not isinstance(row, MutableMapping) for row in raw
    ):
        raise ValueError("governed atlas point layer features must be mutable objects")
    return cast(list[MutableMapping[str, object]], raw)


def _set_feature_record_id(
    feature: MutableMapping[str, object], record_id: str
) -> None:
    current = feature.get("record_id")
    if current is not None and current != record_id:
        raise ValueError(
            "atlas feature record_id conflicts with governed source identity"
        )
    feature["record_id"] = record_id


def _unique_rows(
    rows: Sequence[Mapping[str, object]], key: str, label: str
) -> dict[str, Mapping[str, object]]:
    result: dict[str, Mapping[str, object]] = {}
    for row in rows:
        row_id = _identifier_text(row.get(key), f"{label} {key}")
        if row_id in result:
            raise ValueError(f"{label} contain duplicate {key}: {row_id}")
        result[row_id] = row
    return result


def _compact_rows_by_site(
    rows: Sequence[Mapping[str, object]],
    *,
    fields: Sequence[str],
    label: str,
) -> dict[str, list[list[object]]]:
    grouped: dict[str, list[list[object]]] = defaultdict(list)
    for row in rows:
        site_id = _required_text(row.get("site_id"), f"{label} site_id")
        grouped[site_id].append([row.get(field) for field in fields])
    return grouped


def _row_table(
    fields: Sequence[str],
    rows: Sequence[Sequence[object]],
    *,
    identifier_prefixes: Mapping[str, str] | None = None,
) -> dict[str, object]:
    prefixes = dict(identifier_prefixes or {})
    field_indexes = {field: index for index, field in enumerate(fields)}
    unknown_prefix_fields = sorted(set(prefixes) - set(field_indexes))
    if unknown_prefix_fields:
        raise ValueError(
            f"identifier prefixes name unknown fields: {unknown_prefix_fields}"
        )
    encoded_rows = [list(row) for row in rows]
    for field, prefix in prefixes.items():
        field_index = field_indexes[field]
        for row in encoded_rows:
            value = row[field_index]
            if value is None:
                continue
            if not isinstance(value, str) or not value.startswith(prefix):
                raise ValueError(
                    f"{field} does not match its declared identifier prefix"
                )
            row[field_index] = value.removeprefix(prefix)
    table: dict[str, object] = {
        "record_count": len(rows),
        "fields": list(fields),
        "records": encoded_rows,
    }
    if prefixes:
        table["identifier_prefixes"] = prefixes
    return table


def _non_null_unique(rows: Sequence[Mapping[str, object]], field: str) -> list[object]:
    values = {row.get(field) for row in rows if row.get(field) is not None}
    return sorted(values, key=lambda value: (type(value).__name__, str(value)))


def _tabs(record: Mapping[str, object]) -> Mapping[str, object]:
    return _mapping(record.get("tabs"), "atlas detail tabs")


def _is_unavailable(value: object) -> bool:
    return isinstance(value, Mapping) and value.get("status") == "unavailable"


def _unavailable(reason_code: str) -> dict[str, object]:
    return {"status": "unavailable", "reason_code": reason_code}
