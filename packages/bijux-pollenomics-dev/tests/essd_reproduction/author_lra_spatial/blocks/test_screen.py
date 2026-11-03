"""Whole-source admission and prospective request roles precede block models."""

from __future__ import annotations

from copy import deepcopy
import hashlib
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.blocks.screen import (
    screen_blocks,
)


def packet(*, far: bool = False) -> dict[str, Any]:
    sites = [
        {
            "record_id": record,
            "group_id": "group:" + record,
            "block_id": "left" if record in {"a", "b"} else "right",
            "latitude": 0.0,
            "longitude": longitude,
            "source_radius_m": 100000.0,
            "target_radius_m": 1000.0,
            "coordinate_uncertainty_m": 0.0,
        }
        for record, longitude in [
            ("a", 0.0),
            ("b", 0.01),
            ("c", 10.0 if far else 0.1),
            ("d", 10.01 if far else 0.11),
        ]
    ]
    return {
        "schema_version": "author-lra-spatial-block-inputs.v1",
        "sites": sites,
        "regional_priority": ["c", "a", "b", "d"],
        "saved_pairs": [
            {
                "local_record_id": local,
                "regional_anchor_record_id": anchor,
                "request_sha256": hashlib.sha256(
                    (local + ":" + anchor).encode()
                ).hexdigest(),
            }
            for local in "abcd"
            for anchor in "abcd"
            if local != anchor
        ],
    }


def test_every_block_source_refuses_under_overlapping_integration_support() -> None:
    source = packet()
    original = deepcopy(source)
    result = screen_blocks(source, minimum_buffer_m=20000.0)
    assert source == original
    assert result["summary"]["cross_block_comparisons"] == 8
    assert result["summary"]["admitted_source_roles"] == 0
    assert result["summary"]["excluded_source_roles"] == 4
    assert result["summary"]["admitted_target_roles"] == 0
    assert all(block["regional_anchor_record_id"] is None for block in result["blocks"])
    assert all(
        row["status"] == "refused_no_admitted_training"
        for block in result["blocks"]
        for row in block["target_dispositions"]
    )
    assert all(
        row["distance"]["lower_bound_m"] == 0
        for block in result["blocks"]
        for row in block["comparisons"]
    )


def test_separated_source_groups_can_pass_without_fitting_or_outcomes() -> None:
    result = screen_blocks(packet(far=True), minimum_buffer_m=20000.0)
    assert result["summary"]["admitted_source_roles"] == 4
    assert result["summary"]["excluded_source_roles"] == 0
    assert result["summary"]["admitted_target_roles"] == 4
    assert {
        block["block_id"]: block["regional_anchor_record_id"]
        for block in result["blocks"]
    } == {"left": "c", "right": "a"}
    assert result["scope"] == "geometry_and_request_inventory_only"


def test_regional_anchor_faces_every_held_target_before_admission() -> None:
    source = packet(far=True)
    # Candidate c is close to a, while d clears both a and b.
    source["sites"][1]["longitude"] = 10.0
    source["sites"][2]["longitude"] = 0.1
    source["sites"][3]["longitude"] = 20.0
    left = screen_blocks(source, minimum_buffer_m=20000.0)["blocks"][0]
    assert left["candidate_training_record_ids"] == ["c", "d"]
    assert left["admitted_training_record_ids"] == ["d"]
    assert left["excluded_training_record_ids"] == ["c"]
    assert left["regional_anchor_record_id"] == "d"
    assert len(left["comparisons"]) == 4


def test_uncertainty_cannot_rescue_an_optimistic_support_refusal() -> None:
    source = packet()
    zero = screen_blocks(source, minimum_buffer_m=20000.0)
    for row in source["sites"]:
        row["coordinate_uncertainty_m"] = 1000000.0
    larger = screen_blocks(source, minimum_buffer_m=20000.0)
    assert larger["summary"] == zero["summary"]
    assert all(
        not row["eligible"]
        for block in larger["blocks"]
        for row in block["comparisons"]
    )


def test_unbuffered_inventory_never_changes_anchor_to_force_fit_reuse() -> None:
    source = packet()
    for record, block, longitude in [("e", "left", 0.02), ("f", "right", 0.12)]:
        source["sites"].append(
            {
                **source["sites"][0],
                "record_id": record,
                "group_id": "group:" + record,
                "block_id": block,
                "longitude": longitude,
            }
        )
    source["regional_priority"].extend(["e", "f"])
    source["saved_pairs"] = [
        {
            "local_record_id": local,
            "regional_anchor_record_id": anchor,
            "request_sha256": hashlib.sha256(
                (local + ":" + anchor).encode()
            ).hexdigest(),
        }
        for local in "abcdef"
        for anchor in "abcef"
        if local != anchor
    ]
    result = screen_blocks(source, minimum_buffer_m=20000.0)
    role = next(
        row
        for row in result["unbuffered_pair_inventory"]
        if row["heldout_block_id"] == "left" and row["inner_target"] == "c"
    )
    assert role["regional_anchor_record_id"] == "d"
    assert role["required_pairs"] == [
        {
            "local_record_id": "f",
            "regional_anchor_record_id": "d",
            "request_sha256": None,
        }
    ]
    assert role["status"] == "missing_saved_pair"
    assert role["training_record_ids"] == ["d", "f"]
    assert role["forbidden_record_ids"] == ["a", "b", "c", "e"]
    assert result["summary"]["admitted_target_roles"] == 0


@pytest.mark.parametrize("value", [0, -1, True, float("nan"), float("inf")])
def test_invalid_separation_buffer_refuses(value: Any) -> None:
    with pytest.raises(ValueError):
        screen_blocks(packet(), minimum_buffer_m=value)


def test_duplicate_physical_identity_cannot_inflate_independent_groups() -> None:
    source = packet()
    source["sites"][2]["group_id"] = source["sites"][0]["group_id"]
    with pytest.raises(ValueError, match="Distinct source physical"):
        screen_blocks(source, minimum_buffer_m=20000.0)


def test_foreign_and_duplicate_pair_sources_refuse() -> None:
    source = packet()
    source["saved_pairs"].append(deepcopy(source["saved_pairs"][0]))
    with pytest.raises(ValueError, match="Unique saved"):
        screen_blocks(source, minimum_buffer_m=20000.0)
    source = packet()
    source["saved_pairs"][0]["local_record_id"] = "foreign"
    with pytest.raises(ValueError, match="Foreign"):
        screen_blocks(source, minimum_buffer_m=20000.0)
