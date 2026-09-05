from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping

from .model import NORDIC_COUNTRY_CODES


def reconcile_sead_countries(
    rows: Iterable[Mapping[str, object]],
    *,
    country_by_site_id: Mapping[str, str],
) -> dict[str, object]:
    """Account for every site in the four-country scope or as unassigned."""
    counts: Counter[str] = Counter(dict.fromkeys(NORDIC_COUNTRY_CODES, 0))
    row_count = 0
    duplicate_site_ids: list[str] = []
    seen: set[str] = set()
    for row in rows:
        row_count += 1
        site_id = str(row.get("site_id", "")).strip()
        if not site_id or site_id in seen:
            duplicate_site_ids.append(site_id)
        seen.add(site_id)
        code = country_by_site_id.get(site_id, "UNASSIGNED").strip().upper()
        counts[code if code in NORDIC_COUNTRY_CODES else "UNASSIGNED"] += 1
    assigned_count = sum(counts[code] for code in NORDIC_COUNTRY_CODES[:-1])
    return {
        "schema_version": "sead-country-reconciliation.v1",
        "row_count": row_count,
        "counts": {code: counts[code] for code in NORDIC_COUNTRY_CODES},
        "assigned_count": assigned_count,
        "unassigned_count": counts["UNASSIGNED"],
        "duplicate_site_ids": sorted(duplicate_site_ids),
        "reconciles": assigned_count + counts["UNASSIGNED"] == row_count
        and not duplicate_site_ids,
    }


def reconcile_sead_join(
    *,
    edge: str,
    parent_rows: Iterable[Mapping[str, object]],
    child_rows: Iterable[Mapping[str, object]],
    parent_key: str,
    child_key: str,
    child_foreign_key: str,
) -> dict[str, object]:
    """Build a loss ledger for one declared parent-to-child relation edge."""
    parent_values = [row.get(parent_key) for row in parent_rows]
    null_parent_keys = _null_positions(parent_values)
    parent_ids = {str(value) for value in parent_values if value is not None}
    duplicate_parent_ids = _duplicate_values(parent_values)
    (
        child_key_values,
        null_child_ids,
        orphan_child_ids,
        matched_count,
    ) = _classify_children(
        child_rows,
        child_key=child_key,
        child_foreign_key=child_foreign_key,
        parent_ids=parent_ids,
    )
    null_child_keys = _null_positions(child_key_values)
    duplicate_child_ids = _duplicate_values(child_key_values)
    unexplained_loss_count = sum(
        len(values)
        for values in (
            null_parent_keys,
            duplicate_parent_ids,
            null_child_keys,
            duplicate_child_ids,
            null_child_ids,
            orphan_child_ids,
        )
    )
    return {
        "schema_version": "sead-join-reconciliation.v1",
        "edge": edge,
        "parent_key": parent_key,
        "child_key": child_key,
        "child_foreign_key": child_foreign_key,
        "parent_row_count": len(parent_values),
        "unique_parent_count": len(parent_ids),
        "null_parent_keys": null_parent_keys,
        "child_row_count": len(child_key_values),
        "matched_child_count": matched_count,
        "duplicate_parent_ids": duplicate_parent_ids,
        "null_child_keys": null_child_keys,
        "duplicate_child_ids": duplicate_child_ids,
        "null_foreign_key_child_ids": sorted(null_child_ids),
        "orphan_child_ids": sorted(orphan_child_ids),
        "unexplained_loss_count": unexplained_loss_count,
        "status": "complete" if unexplained_loss_count == 0 else "failed",
    }


def assert_sead_join_complete(reconciliation: Mapping[str, object]) -> None:
    """Fail closed when a join reconciliation contains unexplained loss."""
    if reconciliation.get("status") != "complete":
        raise ValueError(
            f"SEAD join reconciliation failed: {reconciliation.get('edge', 'unknown')}"
        )


def child_identity_for(row: Mapping[str, object], index: int) -> str:
    for key in sorted(row):
        if key.endswith("_id") and row.get(key) is not None:
            return f"{key}:{row[key]}"
    return f"row:{index}"


def _null_positions(values: list[object]) -> list[str]:
    return [f"row:{index}" for index, value in enumerate(values) if value is None]


def _duplicate_values(values: list[object]) -> list[str]:
    return sorted(
        value
        for value, count in Counter(
            str(value) for value in values if value is not None
        ).items()
        if count > 1
    )


def _classify_children(
    rows: Iterable[Mapping[str, object]],
    *,
    child_key: str,
    child_foreign_key: str,
    parent_ids: set[str],
) -> tuple[list[object], list[str], list[str], int]:
    key_values: list[object] = []
    null_foreign_keys: list[str] = []
    orphan_foreign_keys: list[str] = []
    matched_count = 0
    for index, row in enumerate(rows):
        key_values.append(row.get(child_key))
        foreign_key = row.get(child_foreign_key)
        identity = child_identity_for(row, index)
        if foreign_key is None:
            null_foreign_keys.append(identity)
        elif str(foreign_key) not in parent_ids:
            orphan_foreign_keys.append(identity)
        else:
            matched_count += 1
    return key_values, null_foreign_keys, orphan_foreign_keys, matched_count
