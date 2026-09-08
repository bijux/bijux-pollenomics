"""Mutable build state owned by one relational snapshot construction."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .contracts import COUNTRY_CODES, TABLE_NAMES


@dataclass
class RelationalBuildState:
    source_snapshot_id: str
    build_id: str
    tables: dict[str, dict[str, dict[str, object]]]
    conflicts: list[dict[str, object]]
    orphans: list[dict[str, object]]
    source_counts: Counter[str]
    age_postures: Counter[str]
    age_reasons: Counter[str]
    unit_counts: Counter[str]
    country_counts: dict[str, Counter[str]]

    @classmethod
    def create(cls, *, source_snapshot_id: str, build_id: str) -> RelationalBuildState:
        return cls(
            source_snapshot_id=source_snapshot_id,
            build_id=build_id,
            tables={table_name: {} for table_name in TABLE_NAMES},
            conflicts=[],
            orphans=[],
            source_counts=Counter(),
            age_postures=Counter(),
            age_reasons=Counter(),
            unit_counts=Counter(),
            country_counts={code: Counter() for code in COUNTRY_CODES},
        )
