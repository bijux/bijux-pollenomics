"""Conflict and orphan accounting for relational projection."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
import copy
import json

from .identifiers import digest


def register_record(
    table: dict[str, dict[str, object]],
    record: dict[str, object],
    *,
    id_field: str,
    conflicts: list[dict[str, object]],
    conflict_kind: str,
    occurrence_counts: Counter[str] | None = None,
) -> None:
    if occurrence_counts is not None:
        occurrence_counts[id_field] += 1
    record_id = str(record[id_field])
    existing = table.get(record_id)
    if existing is None:
        table[record_id] = record
        return
    if existing == record:
        return
    variants = _merge_conflict_variants(
        conflicts,
        conflict_kind=conflict_kind,
        subject_id=record_id,
        records=(existing, record),
    )
    table[record_id] = variants[0]


def _merge_conflict_variants(
    conflicts: list[dict[str, object]],
    *,
    conflict_kind: str,
    subject_id: str,
    records: tuple[dict[str, object], dict[str, object]],
) -> list[dict[str, object]]:
    conflict_index: int | None = None
    variants = list(records)
    for index, conflict in enumerate(conflicts):
        if (
            conflict.get("conflict_kind") == conflict_kind
            and conflict.get("subject_id") == subject_id
        ):
            conflict_index = index
            detail = conflict.get("detail")
            if isinstance(detail, Mapping):
                recorded_variants = detail.get("variants")
                if isinstance(recorded_variants, list):
                    variants.extend(
                        dict(variant)
                        for variant in recorded_variants
                        if isinstance(variant, Mapping)
                    )
            break
    canonical_variants = {
        _canonical_record_key(variant): copy.deepcopy(variant) for variant in variants
    }
    ordered_variants = [canonical_variants[key] for key in sorted(canonical_variants)]
    merged = conflict_record(
        conflict_kind,
        subject_id,
        {
            "resolution": "canonical_minimum",
            "variants": ordered_variants,
        },
    )
    if conflict_index is None:
        conflicts.append(merged)
    else:
        conflicts[conflict_index] = merged
    return ordered_variants


def _canonical_record_key(record: Mapping[str, object]) -> str:
    return json.dumps(
        record,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def conflict_record(
    conflict_kind: str, subject_id: str, detail: Mapping[str, object]
) -> dict[str, object]:
    body = {
        "conflict_kind": conflict_kind,
        "subject_id": subject_id,
        "detail": copy.deepcopy(dict(detail)),
    }
    return {"conflict_id": f"neotoma:conflict:{digest(body)[:24]}", **body}


def add_conflict(
    conflicts: list[dict[str, object]],
    conflict_kind: str,
    subject_id: str,
    detail: Mapping[str, object],
) -> None:
    conflict = conflict_record(conflict_kind, subject_id, detail)
    if any(
        existing.get("conflict_id") == conflict["conflict_id"] for existing in conflicts
    ):
        return
    conflicts.append(conflict)


def add_orphan(
    orphans: list[dict[str, object]],
    entity_type: str,
    parent_id: str | None,
    reason: str,
    *,
    source_value: object = None,
    excluded_source_row_counts: Mapping[str, int] | None = None,
    source_field_present: bool | None = None,
) -> None:
    body: dict[str, object] = {
        "entity_type": entity_type,
        "parent_id": parent_id,
        "reason": reason,
        "source_value": copy.deepcopy(source_value),
    }
    if excluded_source_row_counts is not None:
        body["excluded_source_row_counts"] = dict(excluded_source_row_counts)
    if source_field_present is not None:
        body["source_field_present"] = source_field_present
    base_id = f"neotoma:orphan:{digest(body)[:24]}"
    occurrence = 1 + sum(
        orphan.get("orphan_id") == base_id
        or str(orphan.get("orphan_id", "")).startswith(f"{base_id}:")
        for orphan in orphans
    )
    orphan_id = base_id if occurrence == 1 else f"{base_id}:{occurrence}"
    orphans.append({"orphan_id": orphan_id, **body})
