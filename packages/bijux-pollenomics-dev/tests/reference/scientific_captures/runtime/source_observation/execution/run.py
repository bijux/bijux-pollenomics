"""Run registered offline bootstrap stages and account completed children and all owned bytes."""

from __future__ import annotations

import argparse
from contextlib import suppress
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import (
    BASE,
    BASE_SHA,
    SOURCE,
    confined_output,
    digest,
    json_value,
    require,
    require_runtime_environment,
    runtime_override_key,
    verify_absences,
    verify_aliases,
    verify_base_namespaces,
    verify_cache_membership,
    verify_pin,
    verify_unused_namespaces,
)


def completed_receipt(
    output: Path, value: dict[str, Any], bound: int
) -> tuple[bytes, int]:
    count = 0
    for path in output.rglob("*"):
        require(
            not path.is_symlink() and (path.is_file() or path.is_dir()),
            "Unexpected output alias/special file",
        )
        if path.is_file():
            count += path.stat().st_size
    total = count
    for _ in range(20):
        raw = (
            json.dumps(
                {**value, "completed_output_bytes_including_receipt": total}, indent=2
            )
            + "\n"
        ).encode()
        next_total = count + len(raw)
        if next_total == total:
            require(total <= bound, "Completed output exceeded logical bound")
            return raw, total
        total = next_total
    raise ValueError("Completed receipt accounting did not converge")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--registered-plan-sha256", required=True)
    args = parser.parse_args()
    environment_admission = require_runtime_environment(dict(os.environ))
    require(
        digest(args.plan) == args.registered_plan_sha256 and digest(BASE) == BASE_SHA,
        "Registered plan/base differs",
    )
    plan = json_value(args.plan)
    output = confined_output(Path(plan["output"]))
    terminal = output / "runtime-observation-terminal.json"
    require(
        not terminal.exists() and not (output / "terminal.json").exists(),
        "Bootstrap already ran",
    )
    started = time.monotonic()
    verify_aliases(plan["runtime_aliases"])
    verify_cache_membership(plan["selected_payloads"])
    verify_unused_namespaces(plan["unused_no_site_namespaces"])
    verify_base_namespaces(plan["base_namespaces"])
    verify_base_namespaces(plan["protected_materialized_namespaces"])
    verify_absences(plan["absent_input_paths"])
    for row in plan["input_pins"]:
        verify_pin(row)
    env = dict(os.environ)
    for key in list(env):
        if (
            runtime_override_key(key)
            or key.startswith(("PYTHON", "PIP_", "UV_"))
            or key
            in {
                "VIRTUAL_ENV",
                "__PYVENV_LAUNCHER__",
                "PYTEST_ADDOPTS",
            }
        ):
            env.pop(key, None)
    env.update(plan["environment"])
    argv = [
        str(BASE),
        "-I",
        "-S",
        "-B",
        str(SOURCE / "run_account_qualification.py"),
        "--plan",
        str(args.plan),
        "--registered-plan-sha256",
        args.registered_plan_sha256,
    ]
    remaining = plan["resources"]["overall_timeout_seconds"] - (
        time.monotonic() - started
    )
    require(remaining > 0, "Overall bootstrap budget expired before launch")
    with (
        (output / "common-runner.stdout").open("xb") as out,
        (output / "common-runner.stderr").open("xb") as err,
    ):
        child = subprocess.Popen(
            argv,
            cwd=plan["repository"],
            env=env,
            stdout=out,
            stderr=err,
            start_new_session=True,
        )
        timed_out = False
        try:
            exit_code = child.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            timed_out = True
            with suppress(ProcessLookupError):
                os.killpg(child.pid, signal.SIGKILL)
            child.wait()
            exit_code = 124
    alias_failure = None
    try:
        verify_aliases(plan["runtime_aliases"])
        verify_cache_membership(plan["selected_payloads"])
        verify_unused_namespaces(plan["unused_no_site_namespaces"])
        verify_base_namespaces(plan["base_namespaces"])
        verify_base_namespaces(plan["protected_materialized_namespaces"])
        verify_absences(plan["absent_input_paths"])
    except (ValueError, OSError) as error:
        alias_failure = str(error)
    input_failures = []
    for row in plan["input_pins"]:
        try:
            verify_pin(row)
        except (ValueError, OSError) as error:
            input_failures.append({"path": row["path"], "error": str(error)})
    common_path = output / "terminal.json"
    common = json_value(common_path) if common_path.is_file() else None
    peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    common_peak = max(
        (
            s["observed_cumulative_completed_child_peak_rss_bytes_macos"]
            for s in (common or {}).get("stages", [])
        ),
        default=0,
    )
    memory_pass = (
        max(peak, common_peak) <= plan["resources"]["resident_memory_limit_bytes"]
    )
    child_pass = (
        type(exit_code) is int
        and exit_code == 0
        and common is not None
        and type(common.get("actual_exit")) is int
        and common.get("actual_exit") == 0
    )
    passed = (
        child_pass
        and not timed_out
        and alias_failure is None
        and not input_failures
        and memory_pass
        and time.monotonic() - started <= plan["resources"]["overall_timeout_seconds"]
    )
    receipt = {
        "schema_version": "offline-source-runtime-observation-terminal.v1",
        "candidate": plan["candidate"],
        "retained_bootstrap": plan["retained_bootstrap"],
        "original_bootstrap_whole_actual_exit": 1,
        "production_stages_repeated": False,
        "environment_override_admission": environment_admission,
        "plan_sha256": args.registered_plan_sha256,
        "actual_exit": 0 if passed else 1,
        "common_actual_exit": exit_code,
        "timed_out": timed_out,
        "elapsed_seconds": time.monotonic() - started,
        "common_terminal": {"path": str(common_path), "sha256": digest(common_path)}
        if common_path.is_file()
        else None,
        "runtime_alias_after_failure": alias_failure,
        "input_after_failures": input_failures,
        "observed_completed_child_peak_rss_bytes_macos": max(peak, common_peak),
        "memory_bound_pass": memory_pass,
        "storage_bound_pass": True,
        "resources": plan["resources"],
        "old_environment_identity_recovered": False,
        "installed_first_party_interface_claimed": False,
        "limits": [
            "New offline source qualification only; original lost runtime identities and old native epochs are not requalified.",
            "Logical all-output and cumulative completed-child RSS are postchecks, not OS quotas or full descendant memory measurements.",
        ],
    }
    # Reserve room for a truthful failure receipt even when outputs reach the bound.
    try:
        raw, _ = completed_receipt(
            output, receipt, plan["resources"]["output_byte_limit"]
        )
    except ValueError:
        receipt.update(actual_exit=1, storage_bound_pass=False)
        raw, _ = completed_receipt(output, receipt, 2**63 - 1)
        # Failure is retained; exceeding a logical limit is not hidden or retried.
    completed_elapsed = time.monotonic() - started
    receipt["elapsed_seconds_through_completed_output_postcheck"] = completed_elapsed
    receipt["overall_wall_bound_pass"] = (
        completed_elapsed <= plan["resources"]["overall_timeout_seconds"]
    )
    if not receipt["overall_wall_bound_pass"]:
        receipt["actual_exit"] = 1
    # Account the final wall-scope fields too; failed bounds never become a success.
    try:
        raw, _ = completed_receipt(
            output, receipt, plan["resources"]["output_byte_limit"]
        )
    except ValueError:
        receipt.update(actual_exit=1, storage_bound_pass=False)
        raw, _ = completed_receipt(output, receipt, 2**63 - 1)
    if time.monotonic() - started > plan["resources"]["overall_timeout_seconds"]:
        receipt.update(actual_exit=1, overall_wall_bound_pass=False)
        raw, _ = completed_receipt(output, receipt, 2**63 - 1)
    with terminal.open("xb") as stream:
        stream.write(raw)
    print(str(terminal))
    sys.exit(receipt["actual_exit"])


if __name__ == "__main__":
    main()
