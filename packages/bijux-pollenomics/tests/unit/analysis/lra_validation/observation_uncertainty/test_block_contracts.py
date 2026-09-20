"""Block uncertainty declarations preserve multi-target unit ownership."""

from dataclasses import replace

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.observation_uncertainty import (
    BlockEffortDeclaration,
    BlockObservationUncertaintyPlan,
    generate_block_pollen_observation_uncertainty,
)


def entry(record: str, method: str = "model") -> BlockEffortDeclaration:
    return BlockEffortDeclaration(
        "block:a",
        record,
        "bin",
        method,
        ("Alnus", "Betula"),
        100,
        len(record + method),
        record + ".json",
        "a" * 64,
    )


def test_same_fold_and_method_retain_distinct_target_records() -> None:
    assert callable(generate_block_pollen_observation_uncertainty)
    plan = BlockObservationUncertaintyPlan(
        "b" * 64,
        (entry("p1"), entry("p2")),
        10,
        0.9,
    )
    assert [value.key for value in plan.entries] == [
        ("block:a", "p1", "model"),
        ("block:a", "p2", "model"),
    ]
    assert BlockObservationUncertaintyPlan.from_dict(plan.as_dict()) == plan


def test_duplicate_exact_block_unit_refuses_without_collapsing_records() -> None:
    one = entry("p1")
    with pytest.raises(ValidationRefusal):
        BlockObservationUncertaintyPlan(
            "b" * 64,
            (one, replace(one, seed=one.seed + 1)),
            10,
            0.9,
        )


def test_one_record_cannot_claim_different_effort_across_methods() -> None:
    one = entry("p1", "model")
    two = replace(entry("p1", "baseline"), effort=101)
    with pytest.raises(ValidationRefusal, match="p1"):
        BlockObservationUncertaintyPlan("b" * 64, (one, two), 10, 0.9)
