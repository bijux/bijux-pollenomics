from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence

from .identity import _canonical, _optional_text, _source_record_id


def _deduplicate_memberships(
    rows: Sequence[Mapping[str, object]],
) -> tuple[dict[str, Mapping[str, object]], int, int, int, dict[str, str]]:
    result: dict[str, Mapping[str, object]] = {}
    conflicts: dict[str, str] = {}
    duplicate_count = 0
    identical_duplicate_count = 0
    conflicting_duplicate_count = 0
    for row in rows:
        observation_id = _optional_text(row.get("observation_id"))
        if observation_id is None:
            raise ValueError("observation membership requires observation_id")
        existing = result.get(observation_id)
        if existing is None:
            result[observation_id] = row
        elif _canonical(existing) == _canonical(row):
            duplicate_count += 1
            identical_duplicate_count += 1
        else:
            conflicts[observation_id] = "ambiguous_classification_membership"
            duplicate_count += 1
            conflicting_duplicate_count += 1
    return (
        result,
        duplicate_count,
        identical_duplicate_count,
        conflicting_duplicate_count,
        conflicts,
    )


def _unique_index(
    rows: Sequence[Mapping[str, object]], key_name: str
) -> tuple[dict[str, Mapping[str, object]], set[str]]:
    result: dict[str, Mapping[str, object]] = {}
    conflicts: set[str] = set()
    for row in rows:
        key = _optional_text(row.get(key_name))
        if key is None:
            continue
        existing = result.get(key)
        if existing is None:
            result[key] = row
        elif _canonical(existing) != _canonical(row):
            conflicts.add(key)
    return result, conflicts


def _source_observation_index(
    rows: Sequence[Mapping[str, object]],
) -> tuple[
    dict[str, Mapping[str, object]],
    set[str],
    set[str],
    int,
    int,
]:
    result: dict[str, Mapping[str, object]] = {}
    conflicts: set[str] = set()
    identical_duplicates: set[str] = set()
    duplicate_count = 0
    identical_duplicate_count = 0
    for row in rows:
        observation_id = _optional_text(row.get("observation_id"))
        if observation_id is None:
            raise ValueError("source observation requires observation_id")
        existing = result.get(observation_id)
        if existing is None:
            result[observation_id] = row
        elif _canonical(existing) == _canonical(row):
            identical_duplicates.add(observation_id)
            duplicate_count += 1
            identical_duplicate_count += 1
        else:
            conflicts.add(observation_id)
            duplicate_count += 1
    return (
        result,
        conflicts,
        identical_duplicates,
        duplicate_count,
        identical_duplicate_count,
    )


def _selected_chronologies(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, tuple[Mapping[str, object], ...]]:
    selected: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    seen: dict[tuple[str, str], str] = {}
    for row in rows:
        if (
            row.get("selected_for_event") is not True
            and row.get("is_default_chronology") is not True
        ):
            continue
        source_record_id = _source_record_id(row)
        claim_id = _optional_text(row.get("chronology_claim_id"))
        if source_record_id is None or claim_id is None:
            continue
        key = (source_record_id, claim_id)
        encoded = _canonical(row)
        existing = seen.get(key)
        if existing is None:
            seen[key] = encoded
            selected[source_record_id].append(row)
        elif existing != encoded:
            selected[source_record_id].append(row)
    return {
        key: tuple(sorted(values, key=lambda row: str(row["chronology_claim_id"])))
        for key, values in selected.items()
    }
