"""Relational join reconciliation and integrity validation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence

from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    reconcile_sead_join,
)
from bijux_pollenomics.collection.sources.sead.acquisition.scoped import (
    SeadJoinPlan,
)

from ..codec import _expect_equal, _required_text, _row_identity
from ..models import _JOIN_RECONCILIATIONS_SCHEMA_VERSION


def _validate_joins(
    payload: Mapping[str, object],
    *,
    rows_by_table: Mapping[str, Sequence[Mapping[str, object]]],
    identities: Mapping[str, str],
    join_plans: Sequence[SeadJoinPlan],
) -> None:
    _expect_equal(
        payload.get("schema_version"),
        _JOIN_RECONCILIATIONS_SCHEMA_VERSION,
        "join reconciliations schema_version",
    )
    edges = payload.get("edges")
    if not isinstance(edges, list) or any(
        not isinstance(edge, Mapping) for edge in edges
    ):
        raise ValueError("SEAD join reconciliations must be object rows")
    by_name: dict[str, Mapping[str, object]] = {}
    for edge in edges:
        if not isinstance(edge, Mapping):
            raise TypeError("SEAD join reconciliation must be an object")
        name = _required_text(edge.get("edge"), "join edge")
        if name in by_name:
            raise ValueError(f"Duplicate SEAD join reconciliation: {name}")
        by_name[name] = edge
    expected_specs = {
        plan.edge: (
            plan.parent_table,
            plan.child_table,
            plan.parent_key,
            plan.child_key,
            plan.child_foreign_key,
            plan.reference_required,
        )
        for plan in join_plans
    }
    if set(by_name) != set(expected_specs) or len(by_name) != len(expected_specs):
        raise ValueError(
            f"SEAD admission requires exactly the {len(expected_specs)} declared joins"
        )
    for name, spec in expected_specs.items():
        edge = by_name[name]
        expected = _recompute_join(
            name,
            spec=spec,
            rows_by_table=rows_by_table,
            identities=identities,
        )
        _expect_equal(dict(edge), expected, f"{name} independently recomputed ledger")


def _recompute_join(
    name: str,
    *,
    spec: tuple[str, str, str, str, str, bool],
    rows_by_table: Mapping[str, Sequence[Mapping[str, object]]],
    identities: Mapping[str, str],
) -> dict[str, object]:
    (
        parent_table,
        child_table,
        parent_key,
        child_key,
        child_foreign_key,
        reference_required,
    ) = spec
    parent_rows = rows_by_table[parent_table]
    all_child_rows = rows_by_table[child_table]
    referenced_child_rows = tuple(
        row
        for row in all_child_rows
        if reference_required or row.get(child_foreign_key) is not None
    )
    result = reconcile_sead_join(
        edge=name,
        parent_rows=parent_rows,
        child_rows=referenced_child_rows,
        parent_key=parent_key,
        child_key=child_key,
        child_foreign_key=child_foreign_key,
    )
    parent_ids = {
        str(row[parent_key]) for row in parent_rows if row.get(parent_key) is not None
    }
    child_counts = Counter(
        str(row[child_foreign_key])
        for row in referenced_child_rows
        if row.get(child_foreign_key) is not None
    )
    matched_parent_ids = sorted(parent_ids & set(child_counts))
    zero_child_parent_ids = sorted(parent_ids - set(child_counts))
    null_reference_child_ids = sorted(
        _row_identity(row, index, child_key)
        for index, row in enumerate(all_child_rows)
        if row.get(child_foreign_key) is None
    )
    result.update(
        {
            **identities,
            "reference_required": reference_required,
            "total_child_row_count": len(all_child_rows),
            "referenced_child_row_count": len(referenced_child_rows),
            "null_reference_child_count": len(null_reference_child_ids),
            "null_reference_child_ids": null_reference_child_ids,
            "matched_parent_count": len(matched_parent_ids),
            "matched_parent_ids": matched_parent_ids,
            "zero_child_parent_count": len(zero_child_parent_ids),
            "zero_child_parent_ids": zero_child_parent_ids,
            "one_child_parent_count": sum(
                child_counts[parent_id] == 1 for parent_id in parent_ids
            ),
            "many_child_parent_count": sum(
                child_counts[parent_id] > 1 for parent_id in parent_ids
            ),
        }
    )
    return result
