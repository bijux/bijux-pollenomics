"""The complete SEAD table contract used by source-key evidence."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from ...acquisition.scoped.models import SeadScopedTablePlan
from ...acquisition.scoped.plans import (
    SEAD_FULL_EVIDENCE_TABLE_PLANS,
    SEAD_SITE_TABLE_PLAN,
)
from .serialization import canonical_sha256

SOURCE_KEY_LEDGER_SCHEMA_VERSION: Final = "sead-source-key-ledger.v1"
SOURCE_KEY_TABLE_CONTRACT_SCHEMA_VERSION: Final = "sead-source-key-table-contract.v1"
SOURCE_KEY_RANGE_ENCODING: Final = "positive_integer_inclusive_ranges.v1"


def sead_source_key_table_plans() -> tuple[SeadScopedTablePlan, ...]:
    """Return the site plan followed by all dependency-ordered evidence plans."""
    return (SEAD_SITE_TABLE_PLAN, *SEAD_FULL_EVIDENCE_TABLE_PLANS)


def source_key_table_contract_rows() -> list[dict[str, object]]:
    """Render the complete source-key table contract in dependency order."""
    return [
        {
            "ordinal": ordinal,
            "table": plan.table,
            "primary_key": plan.primary_key,
            "projection_fields": plan.projection.split(","),
            "filter_field": plan.filter_field,
            "dependencies": [
                {"table": dependency.table, "field": dependency.field}
                for dependency in plan.dependencies
            ],
        }
        for ordinal, plan in enumerate(sead_source_key_table_plans())
    ]


def source_key_table_contract_sha256(
    rows: list[dict[str, object]] | None = None,
) -> str:
    """Digest the exact ordered source-key table contract."""
    return canonical_sha256(source_key_table_contract_rows() if rows is None else rows)


def table_contract_fields(row: Mapping[str, object]) -> dict[str, object]:
    """Select contract-owned fields from one ledger table record."""
    return {
        "ordinal": row.get("ordinal"),
        "table": row.get("table"),
        "primary_key": row.get("primary_key"),
        "projection_fields": row.get("projection_fields"),
        "filter_field": row.get("filter_field"),
        "dependencies": row.get("dependencies"),
    }


__all__ = [
    "SOURCE_KEY_LEDGER_SCHEMA_VERSION",
    "SOURCE_KEY_RANGE_ENCODING",
    "SOURCE_KEY_TABLE_CONTRACT_SCHEMA_VERSION",
    "sead_source_key_table_plans",
    "source_key_table_contract_rows",
    "source_key_table_contract_sha256",
    "table_contract_fields",
]
