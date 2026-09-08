"""Declared SEAD table projections and bounded spatial query parameters."""

from __future__ import annotations

from collections.abc import Sequence

from bijux_pollenomics.collection.sources.sead.acquisition.scoped import (
    SeadScopedTablePlan,
)

from ..models import _SITE_PRIMARY_KEY, _SITE_PROJECTION


def _declared_table_contract(
    table: str, *, plans: Sequence[SeadScopedTablePlan]
) -> tuple[str, str, str]:
    if table == "tbl_sites":
        return _SITE_PRIMARY_KEY, _SITE_PROJECTION, _SITE_PRIMARY_KEY
    for plan in plans:
        if plan.table == table:
            return plan.primary_key, plan.projection, plan.filter_field
    raise ValueError(f"Missing declared SEAD table plan: {table}")


def _bbox_query_parameters(
    bbox: tuple[float, float, float, float], projection: str
) -> list[list[str]]:
    return [
        ["select", projection],
        ["latitude_dd", f"gte.{bbox[1]}"],
        ["latitude_dd", f"lte.{bbox[3]}"],
        ["longitude_dd", f"gte.{bbox[0]}"],
        ["longitude_dd", f"lte.{bbox[2]}"],
        ["order", _SITE_PRIMARY_KEY],
    ]
