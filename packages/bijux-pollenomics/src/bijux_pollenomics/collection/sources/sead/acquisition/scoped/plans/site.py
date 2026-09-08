"""Canonical acquisition plan for the SEAD site table."""

from __future__ import annotations

from ..models import _SITE_PROJECTION, SeadScopedTablePlan

SEAD_SITE_TABLE_PLAN = SeadScopedTablePlan(
    table="tbl_sites",
    primary_key="site_id",
    projection=_SITE_PROJECTION,
    filter_field="site_id",
    dependencies=(),
)

__all__ = ["SEAD_SITE_TABLE_PLAN"]
