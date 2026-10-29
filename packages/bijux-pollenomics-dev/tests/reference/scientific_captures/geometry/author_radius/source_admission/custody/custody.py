"""Authenticate the completed radius run and every original protected input."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

JsonObject = dict[str, Any]
A = Path(__file__).absolute().parent
R = A.parents[2]
B = R / "artifacts/science/current-author-radius-source-comparison"
CANDIDATE = "2784d4eae839e4a4e43f80ec77fd26bd0172aff0"
PLAN_SHA = "0442ab3ec6a44b2ed57a4e4078a3aa2bcb690c51b79a1d08e7bdeb074ea7065e"
OUTER_SHA = "3c4b7c6ffc7bb3242894fdf9f06ad3e88d5dd55022da4643858320a654289957"
OBSERVER_SHA = "262e6e4b49e6f0779349509ad15ead6a5277ab3964d2ea8952eef149f1b63792"
NONMATH = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild/maintained_sources.py"


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def regular(path: Path) -> JsonObject:
    assert path.is_absolute() and ".." not in path.parts
    assert path.is_file() and not any(p.is_symlink() for p in (path, *path.parents))
    return {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}


def identity() -> JsonObject:
    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", *args], cwd=R, timeout=60)

    assert git("branch", "--show-current").strip() == b"main"
    return {
        "candidate": git("rev-parse", "HEAD").decode().strip(),
        "status": git("status", "--porcelain").decode(),
        "tracked_inventory_sha256": hashlib.sha256(
            git("ls-files", "-s", "-z")
        ).hexdigest(),
    }


def blob(candidate: str, name: str) -> bytes:
    assert name and not Path(name).is_absolute() and ".." not in Path(name).parts
    return subprocess.check_output(
        ["git", "show", f"{candidate}:{name}"], cwd=R, timeout=60
    )


def output_path(path: Path) -> Path:
    path = path.absolute()
    assert ".." not in path.parts and path.resolve() == path
    assert not path.exists() and not path.is_symlink()
    assert path.is_relative_to(R / "artifacts") and path != R / "artifacts"
    assert path.parent.is_dir()
    assert not any(p.is_symlink() for p in (path, *path.parents))
    return path


def validate_terminal(plan: JsonObject, common: JsonObject, outer: JsonObject) -> None:
    assert plan["candidate"] == common["candidate"] == outer["candidate"] == CANDIDATE
    assert common["plan_sha256"] == outer["plan_sha256"] == PLAN_SHA
    assert common["status"] == "passed"
    assert all(
        type(v) is int and v == 0
        for v in [
            common["actual_exit"],
            outer["actual_exit"],
            outer["common_actual_exit"],
        ]
    )
    assert outer["memory_bound_pass"] is True and outer["storage_bound_pass"] is True
    assert (
        common["canonical_before"]
        == common["canonical_after"]
        == plan["canonical_identity"]
    )
    assert common["canonical_before"]["status"] == ""
    assert common["before_pin_mismatches"] == common["after_pin_mismatches"] == []
    assert common["absent_input_paths_unchanged"] is True
    assert len(common["stages"]) == len(plan["stages"]) == 3
    for actual, intended in zip(common["stages"], plan["stages"], strict=True):
        assert actual["id"] == intended["id"] and actual["argv"] == intended["argv"]
        assert type(actual["actual_exit"]) is int and actual["actual_exit"] == 0
        assert actual["timed_out"] is False
    assert common["actual_launch_argv"] == [
        plan["qualified_python"],
        plan["common_runner"],
        "--plan",
        str(B / "plan.json"),
        "--registered-plan-sha256",
        PLAN_SHA,
    ]


def authenticate() -> JsonObject:
    pp, tp, op, rp = [
        B / n
        for n in [
            "plan.json",
            "terminal.json",
            "radius-terminal.json",
            "independent-radius-comparison-review.json",
        ]
    ]
    assert sha(pp) == PLAN_SHA and sha(op) == OUTER_SHA and sha(rp) == OBSERVER_SHA
    plan, common, outer, review = [json.loads(p.read_bytes()) for p in (pp, tp, op, rp)]
    validate_terminal(plan, common, outer)
    assert outer["common_terminal"] == {"path": str(tp), "sha256": sha(tp)}
    assert review["candidate"] == CANDIDATE
    assert review["all_historical_scientific_values_types_and_orders_exact"] is True
    assert review["scores_CSV_byte_exact"] is True
    assert review["original_33336_inputs_reauthenticated"] is True
    assert review["complete_900_file_work_reauthenticated"] is True
    assert [
        review[k]
        for k in ["training_attempts", "training_completed", "training_refused"]
    ] == [195, 192, 3]
    original = plan["input_pins"]
    assert len(original) == len({r["path"] for r in original}) == 34271
    aliases = plan["runtime_entry_targets"]
    pins: dict[str, JsonObject] = {}
    transitions = []
    current_candidate = identity()["candidate"]
    for row in original:
        path = Path(row["path"])
        if path.is_symlink():
            assert str(path) in aliases and str(path.resolve()) == aliases[str(path)]
            current = regular(path.resolve())
            assert (
                current["sha256"] == row["sha256"] and current["bytes"] == row["bytes"]
            )
        else:
            current = regular(path)
            if current != row:
                assert path.is_relative_to(R) and not path.is_relative_to(
                    R / "artifacts"
                )
                name = path.relative_to(R).as_posix()
                old = blob(CANDIDATE, name)
                assert (
                    hashlib.sha256(old).hexdigest() == row["sha256"]
                    and len(old) == row["bytes"]
                )
                raw = blob("HEAD", name)
                assert (
                    hashlib.sha256(raw).hexdigest() == current["sha256"]
                    and len(raw) == current["bytes"]
                )
                assert name in {
                    NONMATH,
                    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/report_portal/scientific_accounts.json",
                }, f"Unreviewed original protected input changed: {name}"
                transitions.append(
                    {
                        "original": row,
                        "current": current,
                        "original_git_candidate": CANDIDATE,
                        "current_git_candidate": current_candidate,
                    }
                )
        pins[current["path"]] = current
    for entry, target in aliases.items():
        assert Path(entry).is_symlink() and Path(entry).resolve() == Path(target)
    assert all(
        not Path(n).exists() and not Path(n).is_symlink()
        for n in plan["absent_input_paths"]
    )
    work = Path(plan["inputs"]).parent
    expected_work = {
        row["path"]: row for row in original if Path(row["path"]).is_relative_to(work)
    }
    assert len(expected_work) == 900
    physical_work = {}
    for path in work.rglob("*"):
        assert not path.is_symlink()
        if path.is_file():
            physical_work[str(path)] = regular(path)
    assert physical_work == expected_work
    for item in plan["qualified_original_source_projection"]:
        physical = regular(R / item["path"])
        assert (
            physical["sha256"] == item["sha256"] and physical["bytes"] == item["bytes"]
        )
    proofs = {p["path"]: p for p in common["products"]}
    for row in review["products"]:
        assert regular(Path(row["path"])) == row == proofs[row["path"]]
        pins[row["path"]] = row
    for p in [pp, tp, op, rp]:
        pins[str(p)] = regular(p)
    for actual in common["stages"]:
        for kind in ["stdout", "stderr"]:
            p = Path(actual[kind])
            assert sha(p) == actual[kind + "_sha256"]
            pins[str(p)] = regular(p)
    return {
        "pins": sorted(pins.values(), key=lambda r: r["path"]),
        "original_input_count": len(original),
        "original_input_transitions": transitions,
        "runtime_entry_targets": aliases,
        "original_source_candidate": CANDIDATE,
        "original_plan_sha256": PLAN_SHA,
        "original_outer_sha256": OUTER_SHA,
        "original_observer_sha256": OBSERVER_SHA,
        "raw_products": review["products"],
        "original_numerical_source_projection": plan[
            "qualified_original_source_projection"
        ],
    }
