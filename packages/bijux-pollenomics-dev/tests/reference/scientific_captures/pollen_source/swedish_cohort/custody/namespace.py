"""Authenticate the completed producer and failed observer without relabelling either."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from contracts import ROOT, exact, load, pin, require, sha, verify_frozen_pins
from runtime import absent_path, check_aliases, system_unchanged, tree_membership

RETAINED = ROOT / "artifacts/science/current-swedish-cohort-metadata-replay"
ORIGINAL_CANDIDATE = "c292dafa60f9d992f162c92dd327207d9aefd76b"
PLAN_SHA = "686e9b4c0a73735bfd5dac7e081832e5e94fc33c827be86c729a0519b2f3e652"
COMMON_SHA = "324e7e084d6a111608b84f2863f6536ee6d03ae69cb53adcc9936390107ac02a"
OUTER_SHA = "9baf18964647c6a0d2a66d9d6d546362f3da7daff2adb62aed6a982925b2113f"


def retained_contract(
    plan: dict[str, Any], common: dict[str, Any], outer: dict[str, Any]
) -> None:
    require(
        all(row["candidate"] == ORIGINAL_CANDIDATE for row in (plan, common, outer)),
        "Original candidate differs",
    )
    require(
        common["plan_sha256"] == outer["plan_sha256"] == PLAN_SHA,
        "Original plan links differ",
    )
    require(
        type(common["actual_exit"]) is int
        and common["actual_exit"] == 1
        and type(outer["actual_exit"]) is int
        and outer["actual_exit"] == 1,
        "Original whole failure was relabelled",
    )
    require(
        type(outer["common_actual_exit"]) is int
        and outer["common_actual_exit"] == 1
        and outer["outer_timed_out"] is False
        and exact(outer["actual_native_stage_exits"], [0, 1]),
        "Original source/observer outcome differs",
    )
    require(
        common["before_pin_mismatches"] == common["after_pin_mismatches"] == []
        and common["absent_input_paths_unchanged"] is True,
        "Original pin custody failed",
    )
    require(
        len(plan["input_pins"]) == len({p["path"] for p in plan["input_pins"]}) == 3537,
        "Complete original input count differs",
    )
    require(
        len(plan["stages"]) == len(common["stages"]) == 2,
        "Original stage membership differs",
    )
    for index, (actual, declared) in enumerate(
        zip(common["stages"], plan["stages"], strict=True)
    ):
        require(
            all(
                exact(actual[k], declared[k])
                for k in ("id", "argv", "timeout_seconds", "must_succeed")
            ),
            "Original native command differs",
        )
        require(
            type(actual["actual_exit"]) is int
            and actual["actual_exit"] == index
            and actual["timed_out"] is False,
            "Original source0/observer1 differs",
        )
    for key in (
        "completed_whole_wall_bound_pass",
        "framework_membership_unchanged",
        "absent_paths_unchanged",
        "memory_bound_pass",
        "storage_bound_pass",
    ):
        require(
            outer[key] is True, "Original completed custody/resource failed: " + key
        )
    require(
        outer["tracked_byte_checker_exit"] is None
        and outer["independent_review"] is None,
        "Original missing successful observer was invented",
    )


def validate_launch_log(
    raw: bytes,
    original: dict[str, Any],
    common: dict[str, Any],
    outer: dict[str, Any],
    status: str,
) -> None:
    """Admit only the recorded prefix and literal source-defined final JSON summary tail."""
    prefix = raw[: original["bytes"]]
    require(
        hashlib.sha256(prefix).hexdigest() == original["sha256"],
        "Original captured stdout prefix differs",
    )
    tail = (
        json.dumps(
            {"terminal": common["path"], "sha256": common["sha256"], "status": status}
        )
        + "\n"
        + json.dumps({"terminal": outer, "actual_exit": 1})
        + "\n"
    ).encode()
    require(
        raw[original["bytes"] :] == tail, "Final common/outer stdout summary differs"
    )


def retained_file_pins(common: dict[str, Any]) -> list[dict[str, Any]]:
    common_path = RETAINED / "terminal.json"
    outer_path = RETAINED / "swedish-cohort-terminal.json"
    members = common["products"]
    require(
        len(members) == len({p["path"] for p in members}), "Duplicate original product"
    )
    for row in members:
        path = Path(row["path"])
        require(
            path == path.resolve() and path.is_relative_to(RETAINED),
            "Original product escaped",
        )
        if path == RETAINED / "root-launch.log":
            validate_launch_log(
                path.read_bytes(),
                row,
                pin(common_path),
                pin(outer_path),
                common["status"],
            )
        else:
            require(
                exact(pin(path), row), "Original produced file differs: " + str(path)
            )
    expected = {row["path"] for row in members} | {str(common_path), str(outer_path)}
    actual = set()
    directories = set()
    for path in RETAINED.rglob("*"):
        require(
            not path.is_symlink() and (path.is_file() or path.is_dir()),
            "Retained output alias/special",
        )
        if path.is_file():
            actual.add(str(path))
        else:
            directories.add(path.relative_to(RETAINED).as_posix())
    require(
        actual == expected and directories == {"producer", "scratch"},
        "Retained output membership differs",
    )
    return [pin(Path(p)) for p in sorted(expected)]


def runtime_unchanged(plan: dict[str, Any]) -> None:
    runtime = plan["runtime_profile"]
    require(
        check_aliases(runtime["tree_aliases"] + runtime["native_aliases"]),
        "Original runtime aliases differ",
    )
    require(
        system_unchanged(runtime["system_authority"]), "Original OS authority differs"
    )
    require(
        tree_membership(Path(runtime["framework_root"]))
        == runtime["framework_membership"],
        "Original framework namespace differs",
    )
    require(
        all(absent_path(Path(p)) for p in plan["absent_input_paths"]),
        "Original runtime absence differs",
    )


def authenticate_retained() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    for name, expected in [
        ("plan.json", PLAN_SHA),
        ("terminal.json", COMMON_SHA),
        ("swedish-cohort-terminal.json", OUTER_SHA),
    ]:
        require(
            sha(RETAINED / name) == expected,
            "Original registered receipt differs: " + name,
        )
    plan, common, outer = [
        load(RETAINED / name)
        for name in ("plan.json", "terminal.json", "swedish-cohort-terminal.json")
    ]
    retained_contract(plan, common, outer)
    verify_frozen_pins(plan["input_pins"])
    runtime_unchanged(plan)
    records = retained_file_pins(common)
    return plan, records
