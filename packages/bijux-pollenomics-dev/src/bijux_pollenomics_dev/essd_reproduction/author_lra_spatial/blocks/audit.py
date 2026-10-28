"""Exact rational bounds audit of block footprints and request inventories.

WGS84's metric is bounded by L=b²/a and U=a²/b times the unit-sphere
metric. Every path must cover the latitude difference; a meridian/parallel
path covers at most the latitude-plus-shortest-longitude difference.
Using 3 < pi < 22/7 gives conservative, trigonometry-free distance bounds.
When both endpoint latitudes have magnitude at most 60 degrees, haversine
also gives central angle >= shortest longitude difference in degrees / 180.
These certify admission only when the entire clearance interval agrees.
"""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
import json
import math
import re
from typing import Any

from bijux_pollenomics_dev.lra_validation.spatial_reference.geodesic import (
    distance_bounds,
)

FLOAT_TOLERANCE_M = Fraction.from_float(1e-6)


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError("Independent block audit: " + message)


def _number(value: Any) -> Fraction:
    _require(type(value) in (int, float), "native numeric scalar required")
    native = float(value)
    _require(math.isfinite(native), "finite geometry scalar required")
    return Fraction.from_float(native)


def _exact(actual: Any, expected: Any) -> None:
    _require(
        json.dumps(actual, sort_keys=True, separators=(",", ":"), allow_nan=False)
        == json.dumps(expected, sort_keys=True, separators=(",", ":"), allow_nan=False),
        "complete literal inventory mismatch",
    )


def _pair(
    source: dict[str, Any],
    target: dict[str, Any],
    actual: dict[str, Any],
    minimum: Fraction,
) -> tuple[bool, bool]:
    _require(
        set(actual)
        == {
            "source_record_id",
            "target_record_id",
            "source_group_id",
            "target_group_id",
            "distance",
            "eligible",
        },
        "comparison fields",
    )
    _exact(
        {
            key: actual[key]
            for key in (
                "source_record_id",
                "target_record_id",
                "source_group_id",
                "target_group_id",
            )
        },
        {
            "source_record_id": source["record_id"],
            "target_record_id": target["record_id"],
            "source_group_id": source["group_id"],
            "target_group_id": target["group_id"],
        },
    )
    distance = actual["distance"]
    _require(
        set(distance)
        == {
            "centre_distance_m",
            "target_radius_m",
            "training_radius_m",
            "target_coordinate_uncertainty_m",
            "training_coordinate_uncertainty_m",
            "lower_bound_m",
        },
        "all conservative distance components",
    )
    for field, expected in {
        "target_radius_m": target["target_radius_m"],
        "training_radius_m": source["source_radius_m"],
        "target_coordinate_uncertainty_m": target["coordinate_uncertainty_m"],
        "training_coordinate_uncertainty_m": source["coordinate_uncertainty_m"],
    }.items():
        _require(
            _number(distance[field]) == _number(expected),
            "source radius/uncertainty identity",
        )
    lower, upper = distance_bounds(source, target)
    centre = _number(distance["centre_distance_m"])
    _require(
        centre >= 0
        and lower - FLOAT_TOLERANCE_M <= centre <= upper + FLOAT_TOLERANCE_M,
        "host distance outside independent metric bounds",
    )
    radii = _number(source["source_radius_m"]) + _number(target["target_radius_m"])
    allowances = _number(source["coordinate_uncertainty_m"]) + _number(
        target["coordinate_uncertainty_m"]
    )
    reported = _number(distance["lower_bound_m"])
    _require(
        abs(reported - max(Fraction(), centre - radii - allowances))
        <= FLOAT_TOLERANCE_M,
        "reported clearance arithmetic",
    )
    lower_clearance, upper_clearance = (
        max(Fraction(), lower - radii - allowances),
        max(Fraction(), upper - radii - allowances),
    )
    if upper_clearance < minimum:
        admitted = False
    elif lower_clearance >= minimum:
        admitted = True
    else:
        raise ValueError("Independent block audit: metric_bound_unresolved")
    _require(
        type(actual["eligible"]) is bool
        and actual["eligible"] == admitted
        and actual["eligible"] == (reported >= minimum),
        "independent admission classification",
    )
    # Dropping all nonnegative error allowances maximizes conservative clearance.
    failure_even_at_zero = max(Fraction(), upper - radii) < minimum
    return admitted, failure_even_at_zero


def audit_block_screen(
    packet: dict[str, Any], result: dict[str, Any]
) -> dict[str, Any]:
    """Audit supplied metadata only; refuse a geometrically undecidable interval."""
    _require(
        set(result)
        == {
            "schema_version",
            "minimum_buffer_m",
            "blocks",
            "unbuffered_pair_inventory",
            "summary",
            "scope",
        }
        and result["schema_version"] == "author-lra-block-screen.v1"
        and result["scope"] == "geometry_and_request_inventory_only",
        "screen schema and scope",
    )
    minimum = _number(result["minimum_buffer_m"])
    _require(minimum > 0, "positive minimum buffer")
    _require(
        minimum == _number(packet["policy"]["minimum_buffer_m"]),
        "declared separation buffer",
    )
    sites = packet["sites"]
    _require(type(sites) is list and len(sites) >= 4, "complete site population")
    index = {row["record_id"]: row for row in sites}
    _require(
        len(index) == len(sites) == len({row["group_id"] for row in sites}),
        "unique physical source groups",
    )
    for row in sites:
        _require(
            all(
                type(row[field]) is str and row[field]
                for field in ("record_id", "group_id", "block_id")
            ),
            "source identities",
        )
        distance_bounds(row, row)
        _require(
            _number(row["source_radius_m"]) > 0
            and _number(row["target_radius_m"]) > 0
            and _number(row["coordinate_uncertainty_m"]) >= 0,
            "positive radii and nonnegative uncertainty",
        )
    blocks = sorted({row["block_id"] for row in sites})
    _require(len(blocks) == len(result["blocks"]) == 2, "two geographic blocks")
    priority = packet["regional_priority"]
    _require(
        len(priority) == len(set(priority)) == len(index)
        and set(priority) == set(index),
        "complete unchanged regional priority",
    )
    saved: dict[tuple[str, str], str] = {}
    for row in packet["saved_pairs"]:
        _require(
            set(row)
            == {"local_record_id", "regional_anchor_record_id", "request_sha256"},
            "saved pair fields",
        )
        key = row["local_record_id"], row["regional_anchor_record_id"]
        _require(
            key not in saved
            and all(owner in index for owner in key)
            and key[0] != key[1],
            "unique source pair owners",
        )
        _require(
            type(row["request_sha256"]) is str
            and re.fullmatch(r"[a-f0-9]{64}", row["request_sha256"]) is not None,
            "saved request SHA256",
        )
        saved[key] = row["request_sha256"]
    _require(len(set(saved.values())) == len(saved), "unique saved request identities")
    expected_blocks: list[dict[str, Any]] = []
    roles: list[dict[str, Any]] = []
    required: set[tuple[str, str]] = set()
    failures_at_zero = 0
    statuses: Counter[str] = Counter()
    for block_id, observed in zip(blocks, result["blocks"], strict=True):
        targets = sorted(
            owner for owner, row in index.items() if row["block_id"] == block_id
        )
        training = sorted(set(index) - set(targets))
        _require(
            len(targets) >= 2 and len(training) >= 2, "populated outer and inner blocks"
        )
        pairs = [(source, target) for source in training for target in targets]
        _require(
            len(observed["comparisons"]) == len(pairs),
            "complete cross-block pair population",
        )
        excluded_groups = set()
        for (source, target), comparison in zip(
            pairs, observed["comparisons"], strict=True
        ):
            admitted, best_case_fails = _pair(
                index[source], index[target], comparison, minimum
            )
            failures_at_zero += best_case_fails
            statuses["admitted" if admitted else "excluded"] += 1
            if not admitted:
                excluded_groups.add(index[source]["group_id"])
        admitted_sources = [
            owner
            for owner in training
            if index[owner]["group_id"] not in excluded_groups
        ]
        expected_blocks.append(
            {
                "block_id": block_id,
                "target_record_ids": targets,
                "candidate_training_record_ids": training,
                "admitted_training_record_ids": admitted_sources,
                "excluded_training_record_ids": sorted(
                    set(training) - set(admitted_sources)
                ),
                "regional_anchor_record_id": next(
                    (owner for owner in priority if owner in admitted_sources), None
                ),
                "comparisons": observed["comparisons"],
                "target_dispositions": [
                    {
                        "record_id": target,
                        "status": "support_admitted"
                        if admitted_sources
                        else "refused_no_admitted_training",
                    }
                    for target in targets
                ],
            }
        )
        for inner in [None, *training]:
            allowed = [owner for owner in training if owner != inner]
            anchor = next(owner for owner in priority if owner in allowed)
            requests = [(owner, anchor) for owner in allowed if owner != anchor]
            required.update(requests)
            roles.append(
                {
                    "heldout_block_id": block_id,
                    "kind": "outer" if inner is None else "inner",
                    "inner_target": inner,
                    "training_record_ids": allowed,
                    "forbidden_record_ids": sorted(
                        [*targets, *([] if inner is None else [inner])]
                    ),
                    "regional_anchor_record_id": anchor,
                    "required_pairs": [
                        {
                            "local_record_id": owner,
                            "regional_anchor_record_id": regional,
                            "request_sha256": saved.get((owner, regional)),
                        }
                        for owner, regional in requests
                    ],
                    "status": "all_pairs_covered"
                    if all(key in saved for key in requests)
                    else "missing_saved_pair",
                }
            )
    _exact(result["blocks"], expected_blocks)
    _exact(result["unbuffered_pair_inventory"], roles)
    summary = {
        "sites": len(sites),
        "blocks": len(blocks),
        "cross_block_comparisons": sum(
            len(row["comparisons"]) for row in expected_blocks
        ),
        "admitted_source_roles": sum(
            len(row["admitted_training_record_ids"]) for row in expected_blocks
        ),
        "excluded_source_roles": sum(
            len(row["excluded_training_record_ids"]) for row in expected_blocks
        ),
        "target_roles": len(sites),
        "admitted_target_roles": sum(
            len(row["target_dispositions"])
            for row in expected_blocks
            if row["admitted_training_record_ids"]
        ),
        "unbuffered_roles": len(roles),
        "distinct_required_pairs": len(required),
        "distinct_covered_pairs": len(required.intersection(saved)),
        "distinct_missing_pairs": len(required.difference(saved)),
    }
    _exact(result["summary"], summary)
    return {
        "status": "passed",
        "comparisons_verified": summary["cross_block_comparisons"],
        "pair_classifications": dict(statuses),
        "pair_failures_even_at_zero_uncertainty": failures_at_zero,
        "all_comparisons_fail_for_every_nonnegative_uncertainty": failures_at_zero
        == summary["cross_block_comparisons"],
        "zero_uncertainty_input": all(
            _number(row["coordinate_uncertainty_m"]) == 0 for row in sites
        ),
        "unbuffered_roles_verified": len(roles),
        "distance_oracle": "Exact rational WGS84 global metric and meridian/parallel path bounds; not micrometre inverse-geodesic agreement",
        "scope": "Declared finite footprints and centres only; no empirical support, error calibration, outcomes, new fits or transferred old training ancestry",
    }
