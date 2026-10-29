"""Admit exact shared numerical requests while preserving every fold's ancestry."""

from __future__ import annotations

from collections import Counter
import math
from typing import Any

from .fixed_starts import STARTS
from .withheld_fold import _attempts, _canonical_sha
from .withheld_pollen import _close, _composition, _number, _require

COUNTS = {
    "folds": 15,
    "logical_requests": 195,
    "unique_requests": 27,
    "new_attempts": 896,
    "reused_attempts": 832,
    "unique_attempts": 1728,
    "logical_attempt_references": 12480,
    "prediction_slots": 45,
}


def _accepted(row: dict[str, Any]) -> bool:
    result = row.get("result")
    if type(result) is not dict:
        return False
    x = result.get("x")
    return bool(
        result.get("success") is True
        and _number(result.get("fun"))
        and type(x) is list
        and len(x) == 30
        and all(_number(value) and 0 <= value <= 1 for value in x)
        and abs(math.fsum(x) - 1) <= 1e-6
    )


def validate_pool(
    training: dict[str, Any],
    events: list[dict[str, Any]],
    previous: dict[str, Any],
    first: dict[str, Any],
    protocol: dict[str, Any],
    experiment: dict[str, Any],
) -> dict[str, Any]:
    """Recompute54 ring choices from1728 unique recorded optimization outcomes."""
    logical = training["logical_requests"]
    _require(
        training["counts"] == protocol["counts"] == COUNTS
        and logical == protocol["logical_requests"]
        and len(logical) == 195,
        "cohort accounting or195 logical requests differs",
    )
    _require(
        training["prior_evidence"] == protocol["prior_evidence"],
        "prior source identities differ",
    )
    expected: dict[str, dict[str, Any]] = {}
    folds: dict[str, list[dict[str, Any]]] = {}
    for row in logical:
        folds.setdefault(row["fold_id"], []).append(row)
        old = expected.setdefault(row["request_sha256"], row)
        _require(
            (old["local_record_id"], old["regional_anchor_record_id"])
            == (row["local_record_id"], row["regional_anchor_record_id"]),
            "equal numeric request has distinct source identity",
        )
    _require(
        len(expected) == 27
        and len(folds) == 15
        and Counter(Counter(row["request_sha256"] for row in logical).values())
        == {13: 14, 1: 13},
        "exact27 equivalence classes differ",
    )
    records = sorted(row["record_id"] for row in experiment["sites"])
    groups = {record: "site-group:" + _canonical_sha([record]) for record in records}
    outer_folds = {}
    for fold_id, rows in folds.items():
        targets = {row["target_record_id"] for row in rows}
        _require(
            len(targets) == 1 and len(rows) == 13,
            "one held site and13 local predictors required",
        )
        target = next(iter(targets))
        train = sorted(set(records) - {target})
        _require(
            target in groups and groups[target] == fold_id and len(train) == 14,
            "original whole-site grouping differs",
        )
        anchor = next(
            record for record in experiment["regional_priority"] if record in train
        )
        _require(
            {row["regional_anchor_record_id"] for row in rows} == {anchor}
            and sorted(row["local_record_id"] for row in rows)
            == sorted(set(train) - {anchor}),
            "original regional priority or local membership differs",
        )
        _require(
            all(
                {row["local_record_id"], anchor}.issubset(train)
                and target not in {row["local_record_id"], anchor}
                for row in rows
            ),
            "target entered its own training ancestry",
        )
        outer_folds[fold_id] = {
            "fold_id": fold_id,
            "train_record_ids": train,
            "test_record_ids": [target],
            "train_group_ids": sorted(groups[record] for record in train),
            "test_group_ids": [groups[target]],
        }
    _require(
        {row["test_record_ids"][0] for row in outer_folds.values()} == set(records),
        "every original target must appear exactly once",
    )
    pool = training["numerical_requests"]
    _require(set(pool) == set(expected), "unique numerical request population differs")
    new_items = [
        expected[key]["local_record_id"]
        for key in sorted(expected)
        if expected[key]["regional_anchor_record_id"] == "author:BECKHAM"
    ]
    _require(
        len(new_items) == 14 and len(training["new_attempts"]) == 896,
        "new unique attempt denominator differs",
    )
    _attempts(training["new_attempts"], events, new_items)
    previous_rows = first["attempts"] + previous["new_attempts"]
    _require(
        len(previous_rows) == 832
        and previous["total_attempts"] == 832
        and not previous["failures"],
        "complete admitted prior832 required",
    )
    attempts = previous_rows + training["new_attempts"]
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for row in attempts:
        _require(
            row["accepted"] is _accepted(row),
            "host feasibility or convergence overridden",
        )
        grouped.setdefault((row["request_sha256"], row["ring_index"]), []).append(row)
    _require(
        len(grouped) == 54 and sum(map(len, grouped.values())) == 1728,
        "unique54 ring objectives or1728 attempts differs",
    )
    accepted_total = 0
    refused_rings = []
    for checksum, row in pool.items():
        identity = expected[checksum]
        execution = (
            "reused"
            if identity["regional_anchor_record_id"] == "author:BROADOWN"
            else "new"
        )
        regional = row["regional_cover"]
        taxa = row["taxa"]
        _require(
            row["request_sha256"] == checksum
            and row["item_id"] == identity["local_record_id"]
            and row["execution"] == execution
            and len(row["selections"]) == 2,
            "pool source or execution identity differs",
        )
        _require(
            type(regional) is list
            and len(regional) == 30
            and all(_number(x) and x >= 0 for x in regional)
            and math.fsum(regional) > 0
            and _close(row["regional_fraction_sum"], math.fsum(regional))
            and row["regional_percent_precision_decimals"] == 3,
            "raw rounded regional handoff differs",
        )
        _require(
            type(taxa) is list
            and taxa == experiment["request_template"]["taxa"]
            and len(taxa) == len(set(taxa)) == 30
            and all(type(name) is str and name for name in taxa)
            and all(abs(x * 100000 - round(x * 100000)) <= 1e-8 for x in regional),
            "native percent precision or30-taxon axis differs",
        )
        for ring, chosen in enumerate(row["selections"]):
            candidates = grouped.get((checksum, ring), [])
            _require(
                len(candidates) == 32
                and [value["start_id"] for value in candidates] == list(STARTS)
                and all(value["item_id"] == row["item_id"] for value in candidates),
                "ordered32 starts or request/ring membership differs",
            )
            direction = candidates[1]["start"]
            _require(
                all(
                    _close(value, 0.5 / 30 + 0.5 * raw / math.fsum(regional))
                    for value, raw in zip(direction, regional, strict=True)
                ),
                "regional start changed raw background",
            )
            valid = [value for value in candidates if value["accepted"]]
            accepted_total += len(valid)
            if not valid:
                _require(chosen is None, "refused ring supplied a composition")
                refused_rings.append({"request_sha256": checksum, "ring_index": ring})
                continue
            _require(type(chosen) is dict, "accepted minimum missing")
            best = min(
                valid, key=lambda value: (value["result"]["fun"], value["start_id"])
            )
            _require(
                chosen["item_id"] == row["item_id"]
                and chosen["request_sha256"] == checksum
                and chosen["ring_index"] == ring
                and chosen["attempted"] == 32
                and chosen["accepted"] == len(valid)
                and chosen["refused"] == 32 - len(valid)
                and chosen["execution"] == execution,
                "ring acceptance/refusal accounting differs",
            )
            _require(
                chosen["selected_start_id"] == best["start_id"]
                and chosen["selected_objective"] == best["result"]["fun"]
                and chosen["selected_attempt_sha256"] == _canonical_sha(best),
                "selected candidate is not the certified minimum",
            )
            x = best["result"]["x"]
            composition = _composition(chosen["composition"])
            _require(
                chosen["raw_x"] == x
                and _close(chosen["raw_sum"], math.fsum(x))
                and set(composition) == set(taxa)
                and all(
                    _close(composition[taxon], raw / math.fsum(x))
                    for taxon, raw in zip(taxa, x, strict=True)
                )
                and _close(chosen["composition_sum"], math.fsum(composition.values())),
                "explicit unrounded diagnostic transform differs",
            )
            if execution == "reused":
                old = next(
                    value
                    for value in previous["training"]
                    if value["request_sha256"] == checksum
                )
                _require(
                    old["regional_cover"] == regional
                    and {
                        key: value
                        for key, value in chosen.items()
                        if key != "execution"
                    }
                    == {
                        key: value
                        for key, value in old["selections"][ring].items()
                        if key != "execution"
                    },
                    "prior832 selection or raw handoff changed",
                )
    return {
        "accepted": accepted_total,
        "refused": 1728 - accepted_total,
        "refused_rings": refused_rings,
        "folds": outer_folds,
        "groups": groups,
        "pool": pool,
        "logical": logical,
        "new_lifecycle_events": len(events),
    }
