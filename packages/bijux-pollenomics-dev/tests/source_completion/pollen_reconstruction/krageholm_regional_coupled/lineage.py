"""Build complete identity components before assigning regional or target roles."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from hashlib import sha256
import json
from typing import Any

from .scalar import require


def digest(value: object) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(body.encode()).hexdigest()


def families(records: Sequence[Mapping[str, Any]]) -> list[list[str]]:
    require(bool(records), "nonempty source catalogue required")
    ids = [row["record_id"] for row in records]
    require(
        all(type(value) is str and value for value in ids)
        and len(set(ids)) == len(ids),
        "unique literal source records required",
    )
    sites: dict[str, list[str]] = {}
    aliases: dict[str, list[str]] = {}
    for row in records:
        record, site, keys = row["record_id"], row["site_id"], row["identity_keys"]
        require(
            type(site) is str
            and site
            and type(keys) in (list, tuple)
            and all(type(key) is str and key for key in keys),
            "complete source identity fields required",
        )
        sites.setdefault(site, []).append(record)
        for key in keys:
            aliases.setdefault(key, []).append(record)
    adjacency: dict[str, set[str]] = {record: set() for record in ids}
    for group in sites.values():
        for record in group:
            adjacency[record].update(group)
    for key, declarations in aliases.items():
        named = ([key] if key in adjacency else []) + sites.get(key, [])
        named_sites = {row["site_id"] for row in records if row["record_id"] in named}
        require(len(named_sites) <= 1, "ambiguous record/site alias target")
        members = set(declarations + named)
        for record in members:
            adjacency[record].update(members)
    unvisited = set(ids)
    result = []
    while unvisited:
        stack = [min(unvisited)]
        component: set[str] = set()
        while stack:
            record = stack.pop()
            if record in component:
                continue
            component.add(record)
            stack.extend(adjacency[record] - component)
        result.append(sorted(component))
        unvisited.difference_update(component)
    return sorted(result)


def expected_folds(
    records: Sequence[Mapping[str, Any]], targets: Sequence[str], regional: str
) -> list[dict[str, Any]]:
    components = families(records)
    catalogue = {row["record_id"] for row in records}
    target_set = set(targets)
    require(
        len(target_set) == len(targets) == 3
        and target_set <= catalogue
        and regional in catalogue - target_set,
        "three targets and distinct regional-only record required",
    )
    for component in components:
        overlap = set(component) & target_set
        require(
            not overlap or set(component) <= target_set,
            "transitive family crosses target/regional roles",
        )
    require(
        len(components) == 4 and all(len(component) == 1 for component in components),
        "four singleton physical families required for fixed experiment",
    )
    group = {
        member: "site-group:" + digest(component)
        for component in components
        for member in component
    }
    folds = []
    for target in targets:
        train = sorted(catalogue - {target})
        require(
            regional in train and len(set(train) & target_set) == 2,
            "exactly two local training predictors plus regional source required",
        )
        folds.append(
            {
                "fold_id": group[target],
                "train_record_ids": train,
                "test_record_ids": [target],
                "train_group_ids": sorted(group[record] for record in train),
                "test_group_ids": [group[target]],
            }
        )
    return sorted(folds, key=lambda row: row["fold_id"])


def allowed_closure(
    roots: Sequence[str],
    graph: Mapping[str, Sequence[str]],
    training: Sequence[str],
    heldout: Sequence[str],
    external: Sequence[str],
) -> list[str]:
    allowed, forbidden = set(training) | set(external), set(heldout)
    require(bool(roots), "nonempty quantitative lineage required")
    complete: set[str] = set()
    active: set[str] = set()

    def walk(node: str) -> None:
        require(node not in forbidden, "held-out source in quantitative ancestry")
        require(
            node in allowed and node in graph,
            "unadmitted or absent quantitative lineage",
        )
        require(node not in active, "cyclic quantitative lineage")
        if node in complete:
            return
        active.add(node)
        for parent in graph[node]:
            walk(parent)
        active.remove(node)
        complete.add(node)

    for root in roots:
        walk(root)
    return sorted(complete)
