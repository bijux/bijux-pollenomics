"""Admit only the observed offline source runtime, retaining its failed production epoch."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any

from runtime_contracts import (
    digest,
    pin,
    require,
    require_runtime_environment,
    verify_absences,
    verify_aliases,
    verify_base_namespaces,
    verify_cache_membership,
    verify_pin,
    verify_unused_namespaces,
)

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[2]
RUNTIME_ROOT = ROOT / "artifacts/science/current-source-runtime-native-observation"
PYTHON = (
    ROOT
    / "artifacts/science/current-offline-isolated-source-runtime-bootstrap/environment/bin/python"
)
PLAN_SHA = "5a34e885c17738c90e7fb65ac8d3780f3f57ebc39a8f5a0842bb811d409a16c4"
OUTER_SHA = "1fcb3926925c5e186b3885e19f0325890f9bd8a536a243793e12e2ee178a7fec"
REVIEW_SHA = "9d71bfabd836242b5ec9dcf96e5d2a124200a77dea4975bdf8b19529d04ba059"


def _object(path: Path, expected: str) -> dict[str, Any]:
    require(
        path.is_file() and not path.is_symlink() and digest(path) == expected,
        "Runtime reference differs: " + str(path),
    )
    value = json.loads(path.read_bytes())
    require(isinstance(value, dict), "Runtime reference must be an object")
    assert isinstance(value, dict)
    return value


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
        and common.get("plan_sha256") == checksum,
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
        and outer.get("timed_out") is False
        and outer.get("input_after_failures") == []
        and outer.get("runtime_alias_after_failure") is None,
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
        and stages[0]["argv"] == expected[0]["argv"]
        and type(stages[0]["actual_exit"]) is int
        and stages[0]["actual_exit"] == 0
        and stages[0]["timed_out"] is False,
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
        and len(review.get("distributions", [])) == 147
        and review.get("new_observation_only") is True,
        "Complete147 distribution observation required",
    )
    require(
        review.get("first_party_editable_metadata_copied") is False
        and review.get("old_runtime_recovered_or_same_process_claimed") is False
        and review.get("installed_first_party_interface_claimed") is False,
        "Runtime scope was relabelled",
    )
    retained = plan["retained_bootstrap"]
    require(
        type(retained.get("original_whole_actual_exit")) is int
        and retained["original_whole_actual_exit"] == 1
        and retained.get("production_stage_actual_exits") == [0, 0, 0]
        and all(type(x) is int for x in retained["production_stage_actual_exits"])
        and type(retained.get("original_observer_actual_exit")) is int
        and retained["original_observer_actual_exit"] == 1
        and type(outer.get("original_bootstrap_whole_actual_exit")) is int
        and outer["original_bootstrap_whole_actual_exit"] == 1
        and type(review.get("original_bootstrap_whole_actual_exit")) is int
        and review["original_bootstrap_whole_actual_exit"] == 1
        and outer.get("production_stages_repeated") is False,
        "Original failed whole epoch must remain explicit",
    )


def verify_runtime_state(plan: dict[str, Any]) -> None:
    verify_aliases(plan["runtime_aliases"])
    verify_cache_membership(plan["selected_payloads"])
    verify_unused_namespaces(plan["unused_no_site_namespaces"])
    verify_base_namespaces(plan["base_namespaces"])
    verify_base_namespaces(plan["protected_materialized_namespaces"])
    verify_absences(plan["absent_input_paths"])
    names = [row["path"] for row in plan["input_pins"]]
    require(len(names) == len(set(names)), "Duplicate observed runtime pin")
    for row in plan["input_pins"]:
        verify_pin(row)


def authenticate_runtime(
    *, current_interpreter: bool = True
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    require_runtime_environment(dict(os.environ))
    if current_interpreter:
        require(
            sys.flags.isolated == 1 and sys.flags.dont_write_bytecode == 1,
            "Isolated no-bytecode source entry required",
        )
        require(
            Path(sys.executable).absolute() == PYTHON
            and Path(sys.prefix).absolute() == PYTHON.parent.parent
            and sys.version_info[:3] == (3, 11, 13),
            "Qualified lexical source interpreter required",
        )
    plan_path = RUNTIME_ROOT / "plan.json"
    outer_path = RUNTIME_ROOT / "runtime-observation-terminal.json"
    review_path = RUNTIME_ROOT / "independent-runtime-review.json"
    plan = _object(plan_path, PLAN_SHA)
    outer = _object(outer_path, OUTER_SHA)
    review = _object(review_path, REVIEW_SHA)
    common_path = Path(outer["common_terminal"]["path"])
    require(
        common_path == RUNTIME_ROOT / "terminal.json",
        "Observed runtime common path differs",
    )
    common = _object(common_path, outer["common_terminal"]["sha256"])
    validate_observation(plan, common, outer, review, PLAN_SHA)
    verify_runtime_state(plan)
    rows = list(plan["input_pins"])
    rows.extend(pin(path) for path in (plan_path, outer_path, common_path, review_path))
    unique: dict[str, dict[str, Any]] = {}
    for row in rows:
        name = str(row["path"])
        require(
            name not in unique or unique[name] == row,
            "Conflicting observed runtime pin",
        )
        unique[name] = row
    authority = {
        "plan": pin(plan_path),
        "outer": pin(outer_path),
        "common": pin(common_path),
        "independent_review": pin(review_path),
        "lexical_python": str(PYTHON),
        "observed_runtime_candidate": plan["candidate"],
        "current_source_candidate_is_separate": True,
        "original_bootstrap_whole_actual_exit": 1,
        "production_stage_actual_exits": [0, 0, 0],
        "new_observer_actual_exit": 0,
        "selected_distributions": 147,
    }
    return authority, [unique[key] for key in sorted(unique)]


def clean_child_environment(environment: dict[str, str]) -> dict[str, str]:
    require_runtime_environment(environment)
    return {
        key: value
        for key, value in environment.items()
        if not key.startswith(("DYLD_", "PIP_", "UV_"))
        and key
        not in {
            "LD_PRELOAD",
            "LD_LIBRARY_PATH",
            "_PYTHON_HOST_PLATFORM",
            "__PYVENV_LAUNCHER__",
            "PYTHONHOME",
            "PYTHONSTARTUP",
            "PYTHONUSERBASE",
            "VIRTUAL_ENV",
        }
    }


def add_runtime_to_plan(
    plan: dict[str, Any],
    authority: dict[str, Any],
    rows: list[dict[str, Any]],
    input_key: str = "input_pins",
) -> None:
    unique = {row["path"]: row for row in plan.get(input_key, [])}
    require(
        len(unique) == len(plan.get(input_key, [])),
        "Duplicate declared input before runtime union",
    )
    controlled = [
        *rows,
        *[
            pin(SOURCE / name)
            for name in (
                "source_runtime.py",
                "runtime_contracts.py",
                "runtime_guarded_runner.py",
            )
        ],
    ]
    for row in controlled:
        require(
            row["path"] not in unique or unique[row["path"]] == row,
            "Conflicting source/runtime custody pin",
        )
        unique[row["path"]] = row
    plan[input_key] = [unique[key] for key in sorted(unique)]
    plan["qualified_source_runtime"] = authority


def attach_runtime_launcher(
    plan: dict[str, Any],
    authority: dict[str, Any],
    rows: list[dict[str, Any]],
    output: Path,
    plan_path: Path,
    delegate: list[str],
    *,
    input_key: str = "input_pins",
    wall: int,
    memory: int,
    storage: int,
) -> list[str]:
    add_runtime_to_plan(plan, authority, rows, input_key)
    plan["qualified_runtime_delegate_argv"] = delegate
    plan["qualified_runtime_output_root"] = str(output)
    plan["qualified_runtime_repository"] = str(ROOT)
    plan["qualified_runtime_resource_bounds"] = {
        "overall_seconds": wall + 60,
        "completed_child_peak_rss_bytes": memory,
        "logical_output_bytes": storage,
        "native_runner_original_seconds": wall,
        "scope": "Existing native/stage budget unchanged;60seconds additional outer allowance is only complete runtime before/after custody. Completed-child RSS and logical all-owned output are postchecks, not aggregate descendants or OS quotas.",
    }
    current, _ = authenticate_runtime()
    require(current == authority, "Runtime observation changed during preparation")
    return [
        str(PYTHON),
        "-I",
        "-B",
        str(SOURCE / "runtime_guarded_runner.py"),
        "--plan",
        str(plan_path),
        "--registered-plan-sha256",
        "PLAN_SHA256",
    ]


def qualify_runtime_receipt(root: Path, checksum: str) -> Path:
    path = root / "runtime-custody-terminal.json"
    require(
        path.is_file() and not path.is_symlink(),
        "Actual runtime custody receipt is absent",
    )
    record = json.loads(path.read_bytes())
    require(
        record.get("plan_sha256") == checksum
        and type(record.get("actual_exit")) is int
        and record["actual_exit"] == 0
        and type(record.get("delegate_actual_exit")) is int
        and record["delegate_actual_exit"] == 0
        and record.get("timed_out") is False
        and record.get("before_runtime_error") is None
        and record.get("after_runtime_error") is None
        and record.get("resource_bounds_met") is True
        and record["qualified_source_runtime"]["plan"]["sha256"] == PLAN_SHA,
        "Current native runtime custody did not pass",
    )
    return path
