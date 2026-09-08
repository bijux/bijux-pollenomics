"""Relational join reconciliation for scoped acquisitions."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence

from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    reconcile_sead_join,
)

from .codec import _row_identity
from .models import SeadJoinPlan


def _reconcile_join(
    plan: SeadJoinPlan,
    *,
    rows_by_table: Mapping[str, Sequence[Mapping[str, object]]],
    scope_id: str,
    run_id: str,
    parent_run_id: str,
    build_id: str,
) -> dict[str, object]:
    parent_rows = rows_by_table[plan.parent_table]
    all_child_rows = rows_by_table[plan.child_table]
    referenced_child_rows = tuple(
        row
        for row in all_child_rows
        if plan.reference_required or row.get(plan.child_foreign_key) is not None
    )
    reconciliation = reconcile_sead_join(
        edge=plan.edge,
        parent_rows=parent_rows,
        child_rows=referenced_child_rows,
        parent_key=plan.parent_key,
        child_key=plan.child_key,
        child_foreign_key=plan.child_foreign_key,
    )
    parent_ids = {
        str(row[plan.parent_key])
        for row in parent_rows
        if row.get(plan.parent_key) is not None
    }
    child_counts = Counter(
        str(row[plan.child_foreign_key])
        for row in referenced_child_rows
        if row.get(plan.child_foreign_key) is not None
    )
    matched_parent_ids = sorted(parent_ids & set(child_counts))
    unmatched_parent_ids = sorted(parent_ids - set(child_counts))
    null_reference_child_ids = sorted(
        _row_identity(row, index, plan.child_key)
        for index, row in enumerate(all_child_rows)
        if row.get(plan.child_foreign_key) is None
    )
    reconciliation.update(
        {
            "scope_id": scope_id,
            "run_id": run_id,
            "parent_run_id": parent_run_id,
            "build_id": build_id,
            "reference_required": plan.reference_required,
            "total_child_row_count": len(all_child_rows),
            "referenced_child_row_count": len(referenced_child_rows),
            "null_reference_child_count": len(null_reference_child_ids),
            "null_reference_child_ids": null_reference_child_ids,
            "matched_parent_count": len(matched_parent_ids),
            "matched_parent_ids": matched_parent_ids,
            "zero_child_parent_count": len(unmatched_parent_ids),
            "zero_child_parent_ids": unmatched_parent_ids,
            "one_child_parent_count": sum(
                child_counts[parent_id] == 1 for parent_id in parent_ids
            ),
            "many_child_parent_count": sum(
                child_counts[parent_id] > 1 for parent_id in parent_ids
            ),
        }
    )
    return reconciliation
