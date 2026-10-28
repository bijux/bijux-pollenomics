"""Synthetic geodesic reports checked by a separate rational metric certificate."""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import math
from typing import Any

from pyproj import Geod
import pytest

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.blocks.audit import (
    LOWER_METRIC,
    audit_block_screen,
    distance_bounds,
)


def packet(*, separated: bool = False) -> dict[str, Any]:
    sites: list[dict[str, Any]] = [
        {
            "record_id": f"site-{index:02d}",
            "group_id": f"group-{index:02d}",
            "block_id": "512" if index < 7 else "562",
            "latitude": (-60.0 if index < 7 else 60.0) if separated else 50.8,
            "longitude": 0.0 if separated else -3.8,
            "source_radius_m": 100000.0,
            "target_radius_m": 1000.0,
            "coordinate_uncertainty_m": 0.0,
            "geometry_reference": {"sha256": "a" * 64},
        }
        for index in range(15)
    ]
    ids = [row["record_id"] for row in sites]
    saved = [
        {
            "local_record_id": local,
            "regional_anchor_record_id": anchor,
            "request_sha256": hashlib.sha256(
                (local + ":" + anchor).encode()
            ).hexdigest(),
        }
        for local in ids
        for anchor in ids
        if local != anchor
    ]
    return {
        "sites": sites,
        "regional_priority": ids,
        "saved_pairs": saved,
        "policy": {"minimum_buffer_m": 20000.0},
    }


def reported(value: dict[str, Any]) -> dict[str, Any]:
    """Supply synthetic host-style observations; the oracle never calls Geod."""
    geod = Geod(ellps="WGS84")
    sites = {row["record_id"]: row for row in value["sites"]}
    saved = {
        (row["local_record_id"], row["regional_anchor_record_id"]): row[
            "request_sha256"
        ]
        for row in value["saved_pairs"]
    }
    priority = value["regional_priority"]
    minimum = value["policy"]["minimum_buffer_m"]
    blocks: list[dict[str, Any]] = []
    roles: list[dict[str, Any]] = []
    required: set[tuple[str, str]] = set()
    for label in ("512", "562"):
        targets = sorted(owner for owner in sites if sites[owner]["block_id"] == label)
        sources = sorted(set(sites) - set(targets))
        comparisons = []
        admitted = set(sources)
        for source in sources:
            for target in targets:
                first, second = sites[source], sites[target]
                distance = float(
                    geod.inv(
                        first["longitude"],
                        first["latitude"],
                        second["longitude"],
                        second["latitude"],
                    )[2]
                )
                clearance = max(
                    0.0,
                    distance
                    - second["target_radius_m"]
                    - first["source_radius_m"]
                    - second["coordinate_uncertainty_m"]
                    - first["coordinate_uncertainty_m"],
                )
                eligible = clearance >= minimum
                if not eligible:
                    admitted.discard(source)
                comparisons.append(
                    {
                        "source_record_id": source,
                        "target_record_id": target,
                        "source_group_id": first["group_id"],
                        "target_group_id": second["group_id"],
                        "distance": {
                            "centre_distance_m": distance,
                            "target_radius_m": second["target_radius_m"],
                            "training_radius_m": first["source_radius_m"],
                            "target_coordinate_uncertainty_m": second[
                                "coordinate_uncertainty_m"
                            ],
                            "training_coordinate_uncertainty_m": first[
                                "coordinate_uncertainty_m"
                            ],
                            "lower_bound_m": clearance,
                        },
                        "eligible": eligible,
                    }
                )
        blocks.append(
            {
                "block_id": label,
                "target_record_ids": targets,
                "candidate_training_record_ids": sources,
                "admitted_training_record_ids": sorted(admitted),
                "excluded_training_record_ids": sorted(set(sources) - admitted),
                "regional_anchor_record_id": next(
                    (owner for owner in priority if owner in admitted), None
                ),
                "comparisons": comparisons,
                "target_dispositions": [
                    {
                        "record_id": target,
                        "status": "support_admitted"
                        if admitted
                        else "refused_no_admitted_training",
                    }
                    for target in targets
                ],
            }
        )
        for inner in [None, *sources]:
            training = [owner for owner in sources if owner != inner]
            anchor = next(owner for owner in priority if owner in training)
            pairs = [(owner, anchor) for owner in training if owner != anchor]
            required.update(pairs)
            roles.append(
                {
                    "heldout_block_id": label,
                    "kind": "outer" if inner is None else "inner",
                    "inner_target": inner,
                    "training_record_ids": training,
                    "forbidden_record_ids": sorted(
                        [*targets, *([] if inner is None else [inner])]
                    ),
                    "regional_anchor_record_id": anchor,
                    "required_pairs": [
                        {
                            "local_record_id": owner,
                            "regional_anchor_record_id": region,
                            "request_sha256": saved.get((owner, region)),
                        }
                        for owner, region in pairs
                    ],
                    "status": "all_pairs_covered"
                    if all(pair in saved for pair in pairs)
                    else "missing_saved_pair",
                }
            )
    return {
        "schema_version": "author-lra-block-screen.v1",
        "minimum_buffer_m": minimum,
        "blocks": blocks,
        "unbuffered_pair_inventory": roles,
        "summary": {
            "sites": 15,
            "blocks": 2,
            "cross_block_comparisons": 112,
            "admitted_source_roles": sum(
                len(row["admitted_training_record_ids"]) for row in blocks
            ),
            "excluded_source_roles": sum(
                len(row["excluded_training_record_ids"]) for row in blocks
            ),
            "target_roles": 15,
            "admitted_target_roles": sum(
                len(row["target_dispositions"])
                for row in blocks
                if row["admitted_training_record_ids"]
            ),
            "unbuffered_roles": 17,
            "distinct_required_pairs": len(required),
            "distinct_covered_pairs": len(required.intersection(saved)),
            "distinct_missing_pairs": len(required.difference(saved)),
        },
        "scope": "geometry_and_request_inventory_only",
    }


def test_all_112_overlaps_certify_universal_nonnegative_uncertainty_failure() -> None:
    value = packet()
    result = reported(value)
    facts = audit_block_screen(value, result)
    assert facts["comparisons_verified"] == 112
    assert facts["pair_classifications"] == {"excluded": 112}
    assert facts["pair_failures_even_at_zero_uncertainty"] == 112
    assert facts["all_comparisons_fail_for_every_nonnegative_uncertainty"]
    assert result["summary"]["distinct_required_pairs"] == 24
    assert result["summary"]["unbuffered_roles"] == 17


def test_opposite_hemispheres_are_positively_certified_without_an_inverse_solver() -> (
    None
):
    value = packet(separated=True)
    facts = audit_block_screen(value, reported(value))
    assert facts["pair_classifications"] == {"admitted": 112}
    assert not facts["all_comparisons_fail_for_every_nonnegative_uncertainty"]


def test_extra_uncertainty_cannot_rescue_the_zero_allowance_failure() -> None:
    value = packet()
    value["sites"][0]["coordinate_uncertainty_m"] = 300.0
    facts = audit_block_screen(value, reported(value))
    assert not facts["zero_uncertainty_input"]
    assert facts["all_comparisons_fail_for_every_nonnegative_uncertainty"]


def test_any_target_failure_excludes_source_and_regional_anchor_group() -> None:
    value = packet(separated=True)
    value["sites"][0]["latitude"] = 60.0
    result = reported(value)
    audit_block_screen(value, result)
    assert result["blocks"][0]["admitted_training_record_ids"] == []
    assert result["blocks"][0]["regional_anchor_record_id"] is None
    assert result["blocks"][1]["admitted_training_record_ids"] == [
        f"site-{index:02d}" for index in range(1, 7)
    ]
    assert result["blocks"][1]["regional_anchor_record_id"] == "site-01"


def test_missing_pair_is_retained_without_changing_priority_or_training() -> None:
    value = packet()
    first = reported(value)["unbuffered_pair_inventory"][0]["required_pairs"][0]
    value["saved_pairs"] = [row for row in value["saved_pairs"] if row != first]
    result = reported(value)
    assert result["summary"]["distinct_missing_pairs"] == 1
    assert audit_block_screen(value, result)["unbuffered_roles_verified"] == 17


@pytest.mark.parametrize(
    "defect",
    [
        "pair_missing",
        "partial_block",
        "wrong_group",
        "favourable_admission",
        "anchor",
        "wrong_radius",
        "bad_clearance",
        "distance_outside_bounds",
        "eligibility",
        "old_ancestry",
        "training_leak",
        "covered_missing_pair",
        "summary",
        "buffer",
    ],
)
def test_comparison_role_and_reuse_tampering_refuses(defect: str) -> None:
    value = packet()
    result = reported(value)
    row = result["blocks"][0]
    comparison = row["comparisons"][0]
    role = result["unbuffered_pair_inventory"][0]
    if defect == "pair_missing":
        row["comparisons"].pop()
    elif defect == "partial_block":
        row["target_record_ids"].pop()
    elif defect == "wrong_group":
        comparison["source_group_id"] = "foreign"
    elif defect == "favourable_admission":
        row["admitted_training_record_ids"] = row["candidate_training_record_ids"]
    elif defect == "anchor":
        row["regional_anchor_record_id"] = value["regional_priority"][0]
    elif defect == "wrong_radius":
        comparison["distance"]["training_radius_m"] = 10.0
    elif defect == "bad_clearance":
        comparison["distance"]["lower_bound_m"] = 1.0
    elif defect == "distance_outside_bounds":
        comparison["distance"]["centre_distance_m"] = 2.0
    elif defect == "eligibility":
        comparison["eligible"] = True
    elif defect == "old_ancestry":
        role["old_whole_training_sha256"] = "a" * 64
    elif defect == "training_leak":
        role["training_record_ids"].append(row["target_record_ids"][0])
    elif defect == "covered_missing_pair":
        role["required_pairs"][0]["request_sha256"] = None
    elif defect == "summary":
        result["summary"]["distinct_required_pairs"] = 23
    else:
        result["minimum_buffer_m"] = 1.0
    with pytest.raises(ValueError):
        audit_block_screen(value, result)


@pytest.mark.parametrize(
    "field,bad",
    [
        ("latitude", 91.0),
        ("longitude", -181.0),
        ("latitude", True),
        ("longitude", float("nan")),
        ("source_radius_m", -1.0),
        ("target_radius_m", 0.0),
        ("coordinate_uncertainty_m", -1.0),
    ],
)
def test_invalid_coordinate_and_footprint_domains_refuse(
    field: str, bad: object
) -> None:
    value = packet()
    result = reported(value)
    value["sites"][0][field] = bad
    with pytest.raises(ValueError):
        audit_block_screen(value, result)


def test_duplicate_physical_group_and_duplicate_saved_pair_are_not_silently_deduplicated() -> (
    None
):
    value = packet()
    result = reported(value)
    duplicated = deepcopy(value)
    duplicated["sites"][1]["group_id"] = duplicated["sites"][0]["group_id"]
    with pytest.raises(ValueError):
        audit_block_screen(duplicated, result)
    value["saved_pairs"].append(value["saved_pairs"][0])
    with pytest.raises(ValueError):
        audit_block_screen(value, result)


def test_broad_metric_bound_must_refuse_an_undecidable_admission() -> None:
    value = packet(separated=True)
    for row in value["sites"]:
        row["latitude"] = 0.0
        row["longitude"] = 0.0 if row["block_id"] == "512" else 2.0
    lower, upper = distance_bounds(value["sites"][0], value["sites"][-1])
    assert lower < 121000 < upper
    with pytest.raises(ValueError, match="metric_bound_unresolved"):
        audit_block_screen(value, reported(value))


def test_bounds_handle_antimeridian_and_poles_with_exact_rational_outputs() -> None:
    lower, upper = distance_bounds(
        {"latitude": 0.0, "longitude": -180.0}, {"latitude": 0.0, "longitude": 180.0}
    )
    assert lower == upper == 0
    lower, upper = distance_bounds(
        {"latitude": -90.0, "longitude": 0.0}, {"latitude": 90.0, "longitude": 0.0}
    )
    assert isinstance(lower, Fraction) and isinstance(upper, Fraction)
    assert 19_000_000 < lower < upper < 20_200_000


def test_east_west_block_admission_is_certified_without_latitude_separation() -> None:
    value = packet()
    for row in value["sites"]:
        row["latitude"] = 55.5
        row["longitude"] = 0.0 if row["block_id"] == "512" else 8.0
    facts = audit_block_screen(value, reported(value))
    assert facts["pair_classifications"] == {"admitted": 112}


@pytest.mark.parametrize("swedish_longitude", [13.4, 13.8])
def test_supplied_nordic_coordinate_pair_has_a_positive_121km_certificate(
    swedish_longitude: float,
) -> None:
    first = {"latitude": 56.12843278, "longitude": 8.6145225}
    second = {"latitude": 55.5, "longitude": swedish_longitude}
    lower, upper = distance_bounds(first, second)
    observed = float(
        Geod(ellps="WGS84").inv(
            first["longitude"],
            first["latitude"],
            second["longitude"],
            second["latitude"],
        )[2]
    )
    assert lower > 121000
    assert float(lower) <= observed <= float(upper)


@pytest.mark.parametrize("latitude", [-60.0, 0.0, 60.0])
def test_longitude_lower_bound_includes_both_exact_60_degree_boundaries(
    latitude: float,
) -> None:
    lower, _ = distance_bounds(
        {"latitude": latitude, "longitude": 0.0},
        {"latitude": latitude, "longitude": 6.0},
    )
    assert lower == LOWER_METRIC * Fraction(6, 180)


@pytest.mark.parametrize(
    "latitude",
    [math.nextafter(60.0, math.inf), math.nextafter(-60.0, -math.inf), 89.0, -90.0],
)
def test_longitude_lower_bound_is_not_extended_beyond_its_latitude_proof(
    latitude: float,
) -> None:
    lower, _ = distance_bounds(
        {"latitude": latitude, "longitude": 0.0},
        {"latitude": latitude, "longitude": 180.0},
    )
    assert lower == 0
    if abs(latitude) == 89:
        observed = abs(
            float(Geod(ellps="WGS84").inv(0.0, latitude, 180.0, latitude)[2])
        )
        assert observed < LOWER_METRIC  # The unguarded proposed term would be false.


def test_shorter_antimeridian_arc_and_latitude_bound_remain_independent() -> None:
    lower, _ = distance_bounds(
        {"latitude": 55.0, "longitude": 179.0}, {"latitude": 55.0, "longitude": -179.0}
    )
    assert lower == LOWER_METRIC * Fraction(2, 180)
    lower, _ = distance_bounds(
        {"latitude": -60.0, "longitude": 0.0}, {"latitude": 60.0, "longitude": 6.0}
    )
    assert lower == 2 * LOWER_METRIC


def test_one_endpoint_outside_60_degrees_disables_only_the_longitude_term() -> None:
    first_latitude = math.nextafter(60.0, math.inf)
    lower, _ = distance_bounds(
        {"latitude": first_latitude, "longitude": 0.0},
        {"latitude": 59.0, "longitude": 180.0},
    )
    difference = Fraction.from_float(first_latitude) - 59
    assert lower == LOWER_METRIC * difference * 3 / 180
