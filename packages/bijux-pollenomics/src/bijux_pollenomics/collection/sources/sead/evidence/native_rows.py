"""Join admitted native chronology rows without projecting their original fields."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy

from .normalization.chronology_claims import CHRONOLOGY_CLAIM_SPECS
from .normalization.models import SeadChronologyClaim


def attach_sead_native_source_rows(
    claims: Sequence[SeadChronologyClaim],
    tables: Mapping[str, Sequence[Mapping[str, object]]],
) -> None:
    """Attach each complete source row after a strict one-to-one ownership check.

    Values retain the admitted JSON decoder's types, including null and unknown
    flags. This is not wire-format preservation or a scientific equivalence
    judgment about the separate projected source_age_value field.
    """
    indexes: dict[str, dict[str, Mapping[str, object]]] = {}
    kinds: dict[str, str] = {}
    for _, kind, primary_key, table in CHRONOLOGY_CLAIM_SPECS:
        if table not in tables:
            raise ValueError(f"SEAD native chronology table is missing: {table}")
        index: dict[str, Mapping[str, object]] = {}
        for row in tables[table]:
            value = row.get(primary_key)
            if type(value) is not int or value < 0:
                raise ValueError(f"SEAD native primary key is invalid: {table}")
            key = str(value)
            if key in index:
                raise ValueError(f"SEAD native primary key is duplicated: {table}")
            index[key] = row
        indexes[table] = index
        kinds[table] = kind

    owned: set[tuple[str, str]] = set()
    matched: list[tuple[SeadChronologyClaim, Mapping[str, object]]] = []
    for claim in claims:
        table = claim["source_table"]
        key = claim["source_record_id"]
        if table not in indexes or claim["claim_type"] != kinds[table]:
            raise ValueError("SEAD claim native table or date kind is inconsistent")
        if claim["source_native_record_id"] != key or key not in indexes[table]:
            raise ValueError("SEAD claim has no exact native primary-key match")
        identity = (table, key)
        if identity in owned or "source_native_row" in claim:
            raise ValueError("SEAD native chronology row has duplicate claim ownership")
        owned.add(identity)
        matched.append((claim, indexes[table][key]))
    if owned != {(table, key) for table, index in indexes.items() for key in index}:
        raise ValueError("SEAD native chronology row has no claim owner")
    for claim, source_row in matched:
        claim["source_native_row"] = deepcopy(dict(source_row))
