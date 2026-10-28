"""Preserve native stages, tracked-byte status and completed resource accounting."""

from __future__ import annotations

import argparse
from contextlib import suppress
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Any

# Authenticate the physical helper namespace before Python can select local imports.
_entrypoint_path = Path(__file__).absolute()
_source_directory = _entrypoint_path.parent
if _entrypoint_path != _entrypoint_path.resolve() or any(
    _ancestor.is_symlink()
    for _ancestor in (_entrypoint_path, *_entrypoint_path.parents)
):
    raise ValueError("Controller entrypoint or ancestor is an alias")
_source_modules = {
    "observe.py",
    "common_runner.py",
    "prepare.py",
    "cache_contract.py",
    "runtime.py",
    "contracts.py",
    "run.py",
    "execute_source.py",
    "independent.py",
    "check_contracts.py",
}
for _entry in _source_directory.iterdir():
    if _entry.is_symlink() or (not _entry.is_file() and not _entry.is_dir()):
        raise ValueError("Controller namespace contains an alias/special entry")
    if _entry.is_dir() and _entry.name != "preflight":
        raise ValueError("Unexpected controller import directory")
    if _entry.suffix in {".py", ".pyc", ".so"} and _entry.name not in _source_modules:
        raise ValueError("Unexpected controller import member")
sys.path.insert(0, str(_source_directory))
from cache_contract import (  # noqa: E402 — authenticate local imports first.
    validate_cache,
)
from contracts import (  # noqa: E402 — authenticate local imports first.
    BASE,
    CACHE,
    SOURCE,
    dump,
    exact,
    load,
    output_products,
    pin,
    require,
    sha,
)
from runtime import (  # noqa: E402 — authenticate local imports first.
    absent_path,
    check_aliases,
    profile_guard,
    system_unchanged,
    tree_membership,
    wall_within_bound,
)


def main() -> None:
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--registered-plan-sha256", required=True)
    args = parser.parse_args()
    profile_guard()
    require(sha(args.plan) == args.registered_plan_sha256, "Registered plan differs")
    plan = load(args.plan)
    output = Path(plan["output"])
    aliases = (
        plan["runtime_profile"]["tree_aliases"]
        + plan["runtime_profile"]["native_aliases"]
    )
    require(check_aliases(aliases), "Prelaunch runtime aliases differ")
    require(
        system_unchanged(plan["runtime_profile"]["system_authority"]),
        "Prelaunch OS authority differs",
    )
    require(
        tree_membership(Path(plan["runtime_profile"]["framework_root"]))
        == plan["runtime_profile"]["framework_membership"],
        "Prelaunch framework membership differs",
    )
    validate_cache(CACHE, load(SOURCE / "xlrd-cache-contract.json"))
    require(
        all(absent_path(Path(value)) for value in plan["absent_input_paths"]),
        "Prelaunch absence differs",
    )
    terminal_path = output / "rootsi-replay-terminal.json"
    require(not terminal_path.exists(), "No terminal overwrite")
    child = subprocess.Popen(
        [
            str(BASE),
            "-I",
            "-S",
            "-B",
            plan["common_runner"],
            "--plan",
            str(args.plan),
            "--registered-plan-sha256",
            args.registered_plan_sha256,
        ],
        cwd=plan["repository"],
        start_new_session=True,
    )
    timed_out = False
    try:
        returncode = child.wait(timeout=plan["resources"]["outer_timeout_seconds"])
    except subprocess.TimeoutExpired:
        timed_out = True
        with suppress(ProcessLookupError):
            os.killpg(child.pid, signal.SIGKILL)
        child.wait()
        returncode = 124
        dump(
            output / "outer-timeout-observation.json",
            {
                "owned_common_launcher_pid": child.pid,
                "owned_common_launcher_pgid": child.pid,
                "native_wait_returncode": child.returncode,
                "reported_timeout_exit": 124,
                "actual_launch_argv": [
                    str(BASE),
                    "-I",
                    "-S",
                    "-B",
                    plan["common_runner"],
                    "--plan",
                    str(args.plan),
                    "--registered-plan-sha256",
                    args.registered_plan_sha256,
                ],
                "cleanup_scope": "Only the authenticated launcher process group was killed and waited. Common runner uses separate child sessions; complete descendant cleanup remains unconfirmed on this outer timeout.",
                "complete_descendant_cleanup_confirmed": False,
            },
        )
    common_path = output / "terminal.json"
    common: dict[str, Any] = (
        load(common_path)
        if common_path.is_file()
        else {"actual_exit": returncode, "stages": []}
    )
    require(
        timed_out or common["actual_exit"] == returncode, "Native common exit differs"
    )
    require(check_aliases(aliases), "Postexecution runtime aliases differ")
    require(
        system_unchanged(plan["runtime_profile"]["system_authority"]),
        "Postexecution OS authority differs",
    )
    for row in plan["input_pins"]:
        require(
            exact(pin(Path(row["path"])), row),
            "Postexecution input differs: " + row["path"],
        )
    validate_cache(CACHE, load(SOURCE / "xlrd-cache-contract.json"))
    membership_stable = (
        tree_membership(Path(plan["runtime_profile"]["framework_root"]))
        == plan["runtime_profile"]["framework_membership"]
    )
    absences_stable = all(
        absent_path(Path(value)) for value in plan["absent_input_paths"]
    )
    products = output_products(output)
    used = sum(row["bytes"] for row in products)
    rss = max(
        (
            r["observed_cumulative_completed_child_peak_rss_bytes_macos"]
            for r in common["stages"]
        ),
        default=0,
    )
    review = output / "independent-source-review.json"
    checker = load(review)["tracked_byte_checker_exit"] if review.exists() else None
    elapsed = time.monotonic() - started
    wall_pass = wall_within_bound(elapsed, plan["resources"]["overall_timeout_seconds"])
    passed = (
        returncode == 0
        and common_path.is_file()
        and len(common["stages"]) == len(plan["stages"])
        and all(
            type(row["actual_exit"]) is int and row["actual_exit"] == 0
            for row in common["stages"]
        )
        and not timed_out
        and membership_stable
        and absences_stable
        and wall_pass
        and rss <= plan["resources"]["declared_memory_bytes"]
        and used + 16384 <= plan["resources"]["declared_storage_bytes"]
    )
    dump(
        terminal_path,
        {
            "candidate": plan["candidate"],
            "plan_sha256": args.registered_plan_sha256,
            "common_terminal": pin(common_path) if common_path.is_file() else None,
            "common_actual_exit": returncode,
            "outer_timed_out": timed_out,
            "observed_elapsed_seconds": elapsed,
            "completed_whole_wall_bound_pass": wall_pass,
            "framework_membership_unchanged": membership_stable,
            "absent_paths_unchanged": absences_stable,
            "actual_native_stage_exits": [r["actual_exit"] for r in common["stages"]],
            "tracked_byte_checker_exit": checker,
            "independent_review": pin(review) if review.exists() else None,
            "completed_child_peak_rss_bytes_macos": rss,
            "output_bytes_before_receipt": used,
            "own_receipt_reserved_bytes": 16384,
            "memory_bound_pass": rss <= plan["resources"]["declared_memory_bytes"],
            "storage_bound_pass": used + 16384
            <= plan["resources"]["declared_storage_bytes"],
            "actual_exit": 0 if passed else 1,
            "scope": plan["scope"],
            "resource_limit": "Completed-child peak RSS and logical regular output accounting; no enforced memory/disk quota or complete descendant census.",
        },
    )
    require(terminal_path.stat().st_size <= 16384, "Own receipt reserve exceeded")
    print(
        __import__("json").dumps(
            {"terminal": pin(terminal_path), "actual_exit": 0 if passed else 1}
        )
    )
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
