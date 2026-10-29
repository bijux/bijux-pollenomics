"""Validate the retained qualified runtime metadata without loading that runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from contracts import PYTHON, require

PLAN_SHA = "5a34e885c17738c90e7fb65ac8d3780f3f57ebc39a8f5a0842bb811d409a16c4"


def validate_observation(
    plan: dict[str, Any],
    common: dict[str, Any],
    outer: dict[str, Any],
    review: dict[str, Any],
    checksum: str,
) -> None:
    require(
        checksum == PLAN_SHA
        and outer.get("plan_sha256") == checksum
        and (common.get("plan_sha256") == checksum),
        "Observed runtime plan binding differs",
    )
    for value in (common, outer, review):
        require(
            type(value.get("actual_exit")) is int and value["actual_exit"] == 0,
            "Runtime observation did not pass natively",
        )
        require(
            value.get("candidate") == plan.get("candidate"),
            "Runtime observation epochs differ",
        )
    require(
        type(outer.get("common_actual_exit")) is int
        and outer["common_actual_exit"] == 0
        and (outer.get("timed_out") is False)
        and (outer.get("input_after_failures") == [])
        and (outer.get("runtime_alias_after_failure") is None),
        "Runtime custody did not pass",
    )
    require(
        all(
            outer.get(key) is True
            for key in (
                "memory_bound_pass",
                "storage_bound_pass",
                "overall_wall_bound_pass",
            )
        ),
        "Runtime resource postchecks did not pass",
    )
    expected = plan["stages"]
    stages = common["stages"]
    require(
        len(expected) == len(stages) == 1
        and stages[0]["id"] == expected[0]["id"]
        and (stages[0]["argv"] == expected[0]["argv"])
        and (type(stages[0]["actual_exit"]) is int)
        and (stages[0]["actual_exit"] == 0)
        and (stages[0]["timed_out"] is False),
        "Runtime actual observer stage differs",
    )
    require(
        Path(plan["retained_environment"]) == PYTHON.parent.parent
        and Path(review["new_environment"]) == PYTHON.parent.parent,
        "Observed environment differs",
    )
    require(
        type(review.get("selected_distribution_count")) is int
        and review["selected_distribution_count"] == 147
        and (len(review.get("distributions", [])) == 147)
        and (review.get("new_observation_only") is True),
        "Complete147 distribution observation required",
    )
    require(
        review.get("first_party_editable_metadata_copied") is False
        and review.get("old_runtime_recovered_or_same_process_claimed") is False
        and (review.get("installed_first_party_interface_claimed") is False),
        "Runtime scope was relabelled",
    )
    retained = plan["retained_bootstrap"]
    require(
        type(retained.get("original_whole_actual_exit")) is int
        and retained["original_whole_actual_exit"] == 1
        and (retained.get("production_stage_actual_exits") == [0, 0, 0])
        and all(type(x) is int for x in retained["production_stage_actual_exits"])
        and (type(retained.get("original_observer_actual_exit")) is int)
        and (retained["original_observer_actual_exit"] == 1)
        and (type(outer.get("original_bootstrap_whole_actual_exit")) is int)
        and (outer["original_bootstrap_whole_actual_exit"] == 1)
        and (type(review.get("original_bootstrap_whole_actual_exit")) is int)
        and (review["original_bootstrap_whole_actual_exit"] == 1)
        and (outer.get("production_stages_repeated") is False),
        "Original failed whole epoch must remain explicit",
    )
