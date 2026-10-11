"""Plans are explicit, immutable and bounded before observation access."""

from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.observation_uncertainty import (
    ObservationUncertaintyPlan,
)

from .support import fixture


@pytest.mark.parametrize(
    "field,value",
    [
        ("effort", True),
        ("effort", 0),
        ("effort", 2.5),
        ("seed", -1),
        ("record_id", 1),
        ("taxa", "ab"),
        ("taxa", ("b", "a")),
        ("evidence_path", "../x"),
    ],
)
def test_entry_refuses_coercion(tmp_path: Path, field: str, value: Any) -> None:
    _, plan, _ = fixture(tmp_path)
    with pytest.raises(ValidationRefusal):
        replace(plan.entries[0], **{field: value})


def test_plan_roundtrip_and_original_list_not_shared(tmp_path: Path) -> None:
    _, plan, _ = fixture(tmp_path)
    payload = plan.as_dict()
    restored = ObservationUncertaintyPlan.from_dict(payload)
    assert restored == plan
    assert restored.sha256 == plan.sha256
    with pytest.raises(FrozenInstanceError):
        plan.__setattr__("repeats", 99)


@pytest.mark.parametrize(
    "field,value",
    [
        ("repeats", True),
        ("repeats", 1),
        ("coverage", True),
        ("coverage", 0.0),
        ("coverage", 1.0),
    ],
)
def test_invalid_plan_controls(tmp_path: Path, field: str, value: Any) -> None:
    _, plan, _ = fixture(tmp_path)
    with pytest.raises(ValidationRefusal):
        replace(plan, **{field: value})


def test_target_effort_consistency_and_global_storage(tmp_path: Path) -> None:
    _, plan, _ = fixture(tmp_path)
    entry = replace(plan.entries[0], effort=11)
    with pytest.raises(ValidationRefusal, match="p"):
        replace(plan, entries=(entry, *plan.entries[1:]))
    huge = tuple(
        replace(e, taxa=tuple(f"t{i:03}" for i in range(128))) for e in plan.entries
    )
    with pytest.raises(ValidationRefusal) as error:
        replace(plan, entries=huge, repeats=10000)
    assert error.value.reason_code == "observation_resource_budget_exceeded"
