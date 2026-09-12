"""Deterministic site/block splits and fail-closed input lineage checks."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from .contracts import (
    Fold,
    SiteRecord,
    ValidationRefusal,
    identity_values,
    manifest_sha256,
    required_identity,
)


def _groups(records: Iterable[SiteRecord]) -> tuple[tuple[SiteRecord, ...], ...]:
    rows = tuple(sorted(records, key=lambda row: row.record_id))
    if not rows or len({row.record_id for row in rows}) != len(rows):
        raise ValidationRefusal(
            "invalid_records", "Records must be nonempty with unique record IDs"
        )
    parents = list(range(len(rows)))

    def root(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    owners: dict[tuple[str, str], int] = {}
    for index, row in enumerate(rows):
        keys = [("site", row.site_id), *(("alias", key) for key in row.identity_keys)]
        for key in keys:
            if key in owners:
                parents[root(index)] = root(owners[key])
            else:
                owners[key] = index
    grouped: dict[int, list[SiteRecord]] = {}
    for index, row in enumerate(rows):
        grouped.setdefault(root(index), []).append(row)
    return tuple(
        sorted(
            (tuple(group) for group in grouped.values()),
            key=lambda group: group[0].record_id,
        )
    )


def _group_id(group: tuple[SiteRecord, ...]) -> str:
    return "site-group:" + manifest_sha256([row.record_id for row in group])


def _folds(
    groups: tuple[tuple[SiteRecord, ...], ...], labels: tuple[str, ...]
) -> tuple[Fold, ...]:
    unique_labels = sorted(set(labels))
    if len(unique_labels) < 2:
        raise ValidationRefusal(
            "insufficient_groups", "At least two independent split groups are required"
        )
    folds = []
    for label in unique_labels:
        training = [
            group
            for group, assigned in zip(groups, labels, strict=True)
            if assigned != label
        ]
        testing = [
            group
            for group, assigned in zip(groups, labels, strict=True)
            if assigned == label
        ]
        folds.append(
            Fold(
                label,
                tuple(row.record_id for group in training for row in group),
                tuple(row.record_id for group in testing for row in group),
                tuple(_group_id(group) for group in training),
                tuple(_group_id(group) for group in testing),
            )
        )
    return tuple(folds)


def grouped_leave_one_out(records: Iterable[SiteRecord]) -> tuple[Fold, ...]:
    """Hold all records connected by physical-site or alias identity out together."""
    groups = _groups(records)
    return _folds(groups, tuple(_group_id(group) for group in groups))


def grouped_block_holdouts(records: Iterable[SiteRecord]) -> tuple[Fold, ...]:
    """Hold predefined spatial blocks out; refuse missing/conflicting assignments.

    Block geometry, buffers and training-only selection belong to the caller's
    frozen experiment, not this identity partitioner. Country is not a boundary.
    """
    groups = _groups(records)
    labels = []
    for group in groups:
        assigned = {row.block_id for row in group}
        if None in assigned or len(assigned) != 1:
            raise ValidationRefusal(
                "invalid_block_assignment",
                "Every alias of a site must have the same known block",
            )
        labels.append("block:" + str(next(iter(assigned))))
    return _folds(groups, tuple(labels))


def split_manifest(
    records: Iterable[SiteRecord], *, by_block: bool = False
) -> dict[str, object]:
    """Record identities and deterministic folds without any held-out outcomes."""
    rows = tuple(sorted(records, key=lambda row: row.record_id))
    folds = grouped_block_holdouts(rows) if by_block else grouped_leave_one_out(rows)
    return {
        "schema_version": "lra-site-splits.v1",
        "split_kind": "predefined_block" if by_block else "leave_one_site_group_out",
        "records": [
            {
                "record_id": row.record_id,
                "site_id": row.site_id,
                "identity_keys": row.identity_keys,
                "block_id": row.block_id,
            }
            for row in rows
        ],
        "folds": [fold.as_dict() for fold in folds],
    }


def assert_allowed_inputs(
    fold: Fold,
    input_ids: Iterable[str],
    dependency_graph: Mapping[str, Iterable[str]],
    *,
    admitted_external_ids: Iterable[str] = (),
) -> tuple[str, ...]:
    """Return validated fit-input closure; refuse test ancestry, gaps and cycles.

    Every visited node, including raw leaves, needs an explicit graph entry.
    Non-training nodes require explicit external admission. That admission never
    overrides withheld ancestry. Include every preprocessing, PPE-fit, regional
    estimate and published-grid dependency; renaming a product cannot cleanse it.
    Outcome-free p10 geometry must have a separate reviewed external identity.
    """
    inputs = tuple(sorted(set(identity_values(input_ids))))
    if not inputs:
        raise ValidationRefusal(
            "missing_fit_inputs", "Fit input identities cannot be empty"
        )
    allowed = set(fold.train_record_ids) | set(identity_values(admitted_external_ids))
    forbidden = set(fold.test_record_ids)
    return _input_closure(
        inputs, dependency_graph, allowed=allowed, forbidden=forbidden
    )


def _input_closure(
    inputs: tuple[str, ...],
    dependency_graph: Mapping[str, Iterable[str]],
    *,
    allowed: set[str],
    forbidden: set[str],
) -> tuple[str, ...]:
    """Walk original quantitative edges under an explicitly constructed admission."""
    graph = {
        required_identity(key): identity_values(values)
        for key, values in dependency_graph.items()
    }
    visited: set[str] = set()
    active: set[str] = set()

    stack = [(node, False) for node in reversed(inputs)]
    while stack:
        node, exiting = stack.pop()
        if exiting:
            active.remove(node)
            visited.add(node)
            continue
        if node in forbidden:
            raise ValidationRefusal(
                "withheld_input_leakage",
                f"Withheld record in fit-input closure: {node}",
            )
        if node not in allowed:
            raise ValidationRefusal(
                "unadmitted_input", f"No training/external admission for: {node}"
            )
        if node not in graph:
            raise ValidationRefusal(
                "unknown_input_lineage", f"No explicit lineage entry for: {node}"
            )
        if node in active:
            raise ValidationRefusal(
                "cyclic_input_lineage", f"Cycle in source dependencies at: {node}"
            )
        if node in visited:
            continue
        active.add(node)
        stack.append((node, True))
        stack.extend((parent, False) for parent in reversed(graph[node]))
    return tuple(sorted(visited))
