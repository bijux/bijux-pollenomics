"""Source-row admission, identity indexing, and duplicate accounting."""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def _mapping_rows(value: object) -> list[Mapping[str, object]]:
    from . import Mapping as RuntimeMapping
    from . import Sequence as RuntimeSequence

    if not isinstance(value, RuntimeSequence) or isinstance(value, (str, bytes)):
        return []
    return [row for row in value if isinstance(row, RuntimeMapping)]


def _index_rows(
    rows: Sequence[Mapping[str, object]], id_field: str
) -> dict[str, Mapping[str, object]]:
    from . import _canonical_json

    indexed: dict[str, Mapping[str, object]] = {}
    for row in rows:
        value = row.get(id_field)
        if value is None:
            continue
        row_id = str(value)
        existing = indexed.get(row_id)
        if existing is not None and _canonical_json(existing) != _canonical_json(row):
            raise ValueError(f"conflicting duplicate {id_field}: {row_id}")
        indexed[row_id] = row
    return indexed


def _deduplicate_observations(
    rows: Sequence[Mapping[str, object]],
) -> tuple[list[Mapping[str, object]], list[dict[str, object]]]:
    from . import Counter, _canonical_json, _required_text

    unique: dict[str, Mapping[str, object]] = {}
    duplicate_counts: Counter[str] = Counter()
    for row in rows:
        observation_id = _required_text(row, "observation_id")
        existing = unique.get(observation_id)
        if existing is None:
            unique[observation_id] = row
            continue
        if _canonical_json(existing) != _canonical_json(row):
            raise ValueError(f"conflicting duplicate observation_id: {observation_id}")
        duplicate_counts[observation_id] += 1
    blockers: list[dict[str, object]] = [
        {
            "reason_code": "duplicate_observation_id",
            "subject_id": observation_id,
            "detail": str(count),
        }
        for observation_id, count in sorted(duplicate_counts.items())
    ]
    return list(unique.values()), blockers


def _integer_count(row: Mapping[str, object], field: str) -> int:
    value = row.get(field)
    if not isinstance(value, int):
        raise TypeError(f"{field} must be an integer")
    return value


def _required_text(row: Mapping[str, object], field: str) -> str:
    value = row.get(field)
    text = "" if value is None else str(value).strip()
    if not text:
        raise ValueError(f"observation requires {field}")
    return text


def _canonical_json(value: object) -> str:
    from . import json

    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
