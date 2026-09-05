"""Conflict and orphan accounting for relational projection."""

from __future__ import annotations

from collections.abc import Mapping
import copy

from .identifiers import digest, optional_source_id


def register_record(
    table: dict[str, dict[str, object]],
    record: dict[str, object],
    *,
    id_field: str,
    conflicts: list[dict[str, object]],
    conflict_kind: str,
) -> None:
    record_id = str(record[id_field])
    existing = table.get(record_id)
    if existing is None:
        table[record_id] = record
        return
    if existing != record:
        conflicts.append(
            conflict_record(
                conflict_kind,
                record_id,
                {"existing": existing, "incoming": record},
            )
        )


def required_source_id(
    value: object,
    entity_type: str,
    orphans: list[dict[str, object]],
    *,
    parent_id: str | None,
) -> str | None:
    source_id = optional_source_id(value)
    if source_id is None:
        add_orphan(
            orphans,
            entity_type,
            parent_id,
            "missing_source_identifier",
            source_value=value,
        )
    return source_id


def conflict_record(
    conflict_kind: str, subject_id: str, detail: Mapping[str, object]
) -> dict[str, object]:
    body = {
        "conflict_kind": conflict_kind,
        "subject_id": subject_id,
        "detail": copy.deepcopy(dict(detail)),
    }
    return {"conflict_id": f"neotoma:conflict:{digest(body)[:24]}", **body}


def add_orphan(
    orphans: list[dict[str, object]],
    entity_type: str,
    parent_id: str | None,
    reason: str,
    *,
    source_value: object = None,
) -> None:
    body = {
        "entity_type": entity_type,
        "parent_id": parent_id,
        "reason": reason,
        "source_value": copy.deepcopy(source_value),
    }
    orphans.append({"orphan_id": f"neotoma:orphan:{digest(body)[:24]}", **body})
