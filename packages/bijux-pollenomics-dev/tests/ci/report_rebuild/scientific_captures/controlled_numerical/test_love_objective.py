"""Retained LOVE source admission preserves exact histories and physical capsule boundaries."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.controlled_numerical import (
    love_objective as capture,
)

R_ROLE = capture.R_ROLE
PYTHON_ROLE = capture.PYTHON_ROLE
OBSERVER_ROLE = capture.OBSERVER_ROLE
qualify_scope = capture.qualify_scope


def fixture() -> tuple[dict[str, Any], ...]:
    contract = {
        "candidate_rows": 32,
        "active_optimizer_calls": 8,
        "absolute_tolerance": 3e-10,
        "relative_tolerance": 1e-10,
    }

    def planned(role: str) -> dict[str, Any]:
        return {
            "id": role,
            "argv": ["synthetic", role],
            "timeout_seconds": 60,
            "must_succeed": True,
        }

    original = {
        "candidate": "synthetic-source",
        "canonical_identity": {"candidate": "synthetic-source"},
        "numerical_contract": contract,
        "stages": [planned(R_ROLE), planned(PYTHON_ROLE), planned(OBSERVER_ROLE)],
    }
    Python_plan = {**original, "stages": [planned(PYTHON_ROLE), planned(OBSERVER_ROLE)]}
    observer_plan = {**original, "stages": [planned(OBSERVER_ROLE)]}

    def common(plan: dict[str, Any], exits: list[int]) -> dict[str, Any]:
        return {
            "candidate": plan["candidate"],
            "actual_exit": exits[-1],
            "canonical_before": plan["canonical_identity"],
            "canonical_after": plan["canonical_identity"],
            "before_pin_mismatches": [],
            "after_pin_mismatches": [],
            "absent_input_paths_unchanged": True,
            "stages": [
                {**stage, "actual_exit": code, "timed_out": False}
                for stage, code in zip(plan["stages"], exits, strict=False)
            ],
        }

    observation = {
        "candidate": "synthetic-source",
        "actual_exit": 0,
        "numerical_contract": contract,
        "Python_objective_events": {
            "search_returns_compared_to_R": 256,
            "solver_certification_returns": 8,
            "all_Python_tf_returns": 264,
            "complete_actual_contexts": 264,
            "selected_first_finite_minimum_certified": True,
            "observer_objective_calls": 0,
        },
        "per_call_objectives": [
            {"call": i, "vectors_compared": 32, "selected_index_one_based": i}
            for i in range(1, 9)
        ],
        "products": {
            name: {
                "shape": shape,
                "finite_pairs": 0,
                "NaN_pairs": shape[0] * shape[1],
                "maximum_absolute_finite_error": None,
            }
            for name, shape in (
                ("cover", [10, 10]),
                ("pollen", [10, 10]),
                ("objective", [10, 2]),
                ("k", [36, 10]),
            )
        },
        "old56_source_gate_waived": False,
        "historical_performance_reproduced": False,
        "new_CPP_adopted": False,
        "optimizer_convergence_tested": False,
    }
    R_common = common(original, [0, 1])
    Python_common = common(Python_plan, [0, 1])
    observer_common = common(observer_plan, [0])
    saved_R = {
        "original_whole_actual_exit": 1,
        "original_candidate": "synthetic-source",
        "original_stage_actual_exits": [0, 1],
        "retained_completed_R_stage": R_common["stages"][0],
    }
    saved_Python = {
        "original_whole_actual_exit": 1,
        "original_candidate": "synthetic-source",
        "original_stage_actual_exits": [0, 1],
        "retained_completed_Python_stage": Python_common["stages"][0],
    }
    observer_plan = {
        **observer_plan,
        "retained_completed_R": saved_R,
        "retained_completed_Python": saved_Python,
    }
    observation.update(
        {
            "retained_completed_R": saved_R,
            "retained_completed_Python": saved_Python,
            "actual_R_command": R_common["stages"][0]["argv"],
            "actual_Python_command": Python_common["stages"][0]["argv"],
        }
    )
    return (
        original,
        R_common,
        Python_plan,
        Python_common,
        observer_plan,
        observer_common,
        observation,
    )


def test_three_execution_scopes() -> None:
    qualify_scope(*fixture())
    changes: list[tuple[int, list[str | int], Any]] = [
        (1, ["actual_exit"], 0),
        (1, ["stages", 0, "actual_exit"], 1),
        (3, ["actual_exit"], 0),
        (3, ["stages", 0, "actual_exit"], False),
        (3, ["stages", 0, "actual_exit"], 1),
        (3, ["stages", 1, "actual_exit"], 0),
        (3, ["stages", 0, "argv"], ["changed"]),
        (3, ["after_pin_mismatches"], ["drift"]),
        (5, ["actual_exit"], False),
        (5, ["actual_exit"], 1),
        (5, ["stages", 0, "actual_exit"], 1),
        (5, ["stages", 0, "timed_out"], True),
        (4, ["stages"], []),
        (4, ["stages"], fixture()[2]["stages"]),
        (6, ["actual_exit"], 1),
        (6, ["candidate"], "wrong-epoch"),
        (6, ["numerical_contract", "absolute_tolerance"], 1.0),
        (6, ["Python_objective_events", "solver_certification_returns"], 0),
        (6, ["Python_objective_events", "all_Python_tf_returns"], 256),
        (6, ["Python_objective_events", "observer_objective_calls"], 8),
        (6, ["Python_objective_events", "observer_objective_calls"], False),
        (6, ["per_call_objectives", 0, "selected_index_one_based"], 33),
        (6, ["products", "cover", "shape"], [9, 10]),
        (6, ["products", "k", "finite_pairs"], 361),
        (6, ["historical_performance_reproduced"], True),
        (6, ["new_CPP_adopted"], True),
        (6, ["optimizer_convergence_tested"], True),
        (6, ["old56_source_gate_waived"], True),
        (6, ["actual_Python_command"], ["observer-instead-of-model"]),
        (6, ["actual_R_command"], ["observer-instead-of-R"]),
        (4, ["retained_completed_R", "original_whole_actual_exit"], 0),
        (4, ["retained_completed_Python", "original_whole_actual_exit"], 0),
    ]
    for index, keys, value in changes:
        documents = deepcopy(fixture())
        parent: Any = documents[index]
        for key in keys[:-1]:
            parent = parent[key]
        parent[keys[-1]] = value
        try:
            qualify_scope(*documents)
        except ValueError:
            continue
        raise AssertionError("Unsafe synthetic scope accepted: " + str(keys))


def test_capsule_members_refuse_empty_directory_special_alias_and_changed_bytes(
    tmp_path: Path,
) -> None:
    root = tmp_path / "capsule"
    root.mkdir()
    (root / "payloads").mkdir()
    (root / "capture.json").write_text("{}")
    raw = b"independent retained source"
    digest = hashlib.sha256(raw).hexdigest()
    member = root / "payloads" / digest
    member.write_bytes(raw)
    members = {"payloads/" + digest: {"sha256": digest, "bytes": len(raw)}}
    capture._validate_members(root, members)
    (root / "empty").mkdir()
    with pytest.raises(ValueError):
        capture._validate_members(root, members)
    (root / "empty").rmdir()
    os.mkfifo(root / "special")
    with pytest.raises(ValueError):
        capture._validate_members(root, members)
    (root / "special").unlink()
    (root / "alias").symlink_to(member)
    with pytest.raises(ValueError):
        capture._validate_members(root, members)
    (root / "alias").unlink()
    member.write_bytes(raw + b"changed")
    with pytest.raises(ValueError):
        capture._validate_members(root, members)


def test_closed_member_paths_and_typed_report_missing_counts() -> None:
    for value in ("", ".", "../outside", "/outside", "a/../b", "a//b", "a\\b"):
        with pytest.raises(ValueError):
            capture._name(value)
    assert not capture._typed_equal(
        {"NaN_pairs": 60, "finite_pairs": 40}, {"NaN_pairs": 0, "finite_pairs": 40}
    )
    assert not capture._typed_equal({"actual_exit": 0}, {"actual_exit": False})
    documents = list(fixture())
    documents[-1]["products"]["cover"]["maximum_absolute_finite_error"] = float("inf")
    with pytest.raises(ValueError):
        capture.qualify_scope(*documents)
