"""Exact outer/inner physical-site ancestry with only thirty-nine numeric pairs."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def contexts(
    original: dict[str, Any], spec: Any
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    sites = {site.record.record_id: site for site in spec.sites}
    folds = original["grouped_leave_one_out"]([site.record for site in spec.sites])
    if len(folds) != 15 or any(
        len(f.train_record_ids) != 14 or len(f.test_record_ids) != 1 for f in folds
    ):
        raise ValueError("Exact fifteen whole-site outer groups required")
    groups = {
        record: fold.test_group_ids[0]
        for fold in folds
        for record in fold.test_record_ids
    }
    rows = []
    for outer in folds:
        rows.append(
            {
                "outer": outer,
                "fold": outer,
                "kind": "outer",
                "target": outer.test_record_ids[0],
            }
        )
        inner = original["grouped_leave_one_out"](
            [sites[x].record for x in outer.train_record_ids]
        )
        if len(inner) != 14:
            raise ValueError("Complete fourteen inner groups required")
        for fold in inner:
            if len(fold.train_record_ids) != 13 or set(outer.test_record_ids) & {
                *fold.train_record_ids,
                *fold.test_record_ids,
            }:
                raise ValueError("Outer physical target leaked into inner partition")
            rows.append(
                {
                    "outer": outer,
                    "fold": fold,
                    "kind": "inner",
                    "target": fold.test_record_ids[0],
                }
            )
    for row in rows:
        fold = row["fold"]
        anchor = next(x for x in spec.regional_priority if x in fold.train_record_ids)
        row.update(
            anchor=anchor,
            predictors=tuple(
                x for x in fold.train_record_ids if groups[x] != groups[anchor]
            ),
        )
        if len(row["predictors"]) != (13 if row["kind"] == "outer" else 12):
            raise ValueError("Local predictor denominator differs")
    return rows, groups


def weighted_experiment(experiment: dict[str, Any], method: str) -> dict[str, Any]:
    result = deepcopy(experiment)
    for role in ("reveals", "love"):
        result["request_template"]["configuration"][role]["distance_weighting"] = method
    return result


def requests(
    original: dict[str, Any], spec: Any, prepared: Any, rows: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    sites = {site.record.record_id: site for site in spec.sites}
    pairs = {}
    logical = []
    consumed_pollen: set[str] = set()
    consumed_geometry: set[str] = set()
    for row in rows:
        fold = row["fold"]
        target = row["outer"].test_record_ids[0]
        for local in row["predictors"]:
            key = (local, row["anchor"])
            if not set(key).issubset(fold.train_record_ids) or (
                row["kind"] == "inner" and target in fold.train_record_ids
            ):
                raise ValueError("Numeric pair violates original outer/inner ancestry")
            if key not in pairs:
                payload = original["make_request"](
                    spec,
                    sites[local],
                    sites[row["anchor"]],
                    fold,
                    prepared,
                    consumed_pollen=consumed_pollen,
                    consumed_geometry=consumed_geometry,
                )
                pairs[key] = original["LRABatchItem"](local, payload)
            item = pairs[key]
            logical.append(
                {
                    "kind": row["kind"],
                    "outer_target": target,
                    "target": row["target"],
                    "fold": fold.as_dict(),
                    "local_record_id": local,
                    "regional_anchor_record_id": row["anchor"],
                    "request_sha256": item.request_sha256,
                }
            )
    numeric = {item.request_sha256: item for item in pairs.values()}
    if len(pairs) != 39 or len(numeric) != 39 or len(logical) != 2715:
        raise ValueError(
            "Exact39 numeric/195outer/2520inner request population required"
        )
    if len([row for row in logical if row["kind"] == "outer"]) != 195:
        raise ValueError("Original outer request denominator differs")
    # make_request reads only the immutable local/anchor pair after training admission.
    # Every logical reference independently retains its complete original Fold.
    return numeric, logical
