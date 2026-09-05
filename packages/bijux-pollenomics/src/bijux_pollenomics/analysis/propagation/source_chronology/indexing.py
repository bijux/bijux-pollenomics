"""Relational indexes for source-native chronology nodes."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence

from .identity import canonical, optional_text


def source_default_chronologies(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, tuple[Mapping[str, object], ...]]:
    """Index only source-declared default chronology claims by sample identity."""
    selected: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    seen: dict[tuple[str, str], str] = {}
    for row in rows:
        if row.get("is_default_chronology") is not True:
            continue
        source_record_id = optional_text(row.get("source_record_id"))
        claim_id = optional_text(row.get("chronology_claim_id"))
        if source_record_id is None or claim_id is None:
            continue
        key = source_record_id, claim_id
        encoded = canonical(row)
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


__all__ = ["source_default_chronologies"]
