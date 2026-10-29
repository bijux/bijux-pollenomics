"""Preserve native producer/refusal observer and tracked-byte checker statuses separately."""

from __future__ import annotations

import argparse
from contextlib import suppress
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time
from typing import Any

_entry_directory = Path(__file__).resolve().parent
_expected_python = {
    "contracts.py",
    "metadata.py",
    "execute_source.py",
    "observe.py",
    "prepare.py",
    "run.py",
    "check_contracts.py",
    "source_runtime.py",
    "runtime_contracts.py",
    "runtime_guarded_runner.py",
    "common_runner.py",
}
for _entry in _entry_directory.iterdir():
    if _entry.is_symlink() or not (_entry.is_dir() or _entry.is_file()):
        raise ValueError("Controller alias/special entry")
    if _entry.is_dir() and _entry.name != "preflight":
        raise ValueError("Unexpected controller directory")
    if _entry.suffix in {".py", ".pyc", ".so"} and _entry.name not in _expected_python:
        raise ValueError("Unexpected controller import")
sys.path.insert(0, str(_entry_directory))
from contracts import (  # noqa: E402 - authenticate the local import namespace first.
    REPORT,
    ROOT,
    load,
    pin,
    require,
    sha,
    verify_inputs,
)
from source_runtime import (  # noqa: E402 - guarded local helper.
    PYTHON,
)


def accounted_receipt(output: Path, value: dict[str, Any], bound: int) -> bytes:
    used = 0
    for path in output.rglob("*"):
        require(
            not path.is_symlink() and (path.is_file() or path.is_dir()),
            "Output alias/special entry",
        )
        if path.is_file():
            used += path.stat().st_size
    total = used
    for _ in range(32):
        import json

        raw = (
            json.dumps(
                {**value, "completed_output_bytes_including_receipt": total},
                indent=2,
                allow_nan=False,
            )
            + "\n"
        ).encode()
        size = used + len(raw)
        if size == total:
            require(size <= bound, "Inclusive logical output postcheck failed")
            return raw
        total = size
    raise ValueError("Receipt accounting did not converge")


def main() -> None:
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--registered-plan-sha256", required=True)
    args = parser.parse_args()
    require(
        sha(args.plan) == args.registered_plan_sha256, "Registered plan SHA differs"
    )
    plan = load(args.plan)
    verify_inputs(plan)
    output = Path(plan["output"])
    target = output / "pairing-terminal.json"
    require(
        not target.exists() and (not (output / "terminal.json").exists()),
        "Native job already launched",
    )
    child = subprocess.Popen(
        [
            str(PYTHON),
            "-I",
            "-B",
            plan["common_runner"],
            "--plan",
            str(args.plan),
            "--registered-plan-sha256",
            args.registered_plan_sha256,
        ],
        cwd=ROOT,
        start_new_session=True,
    )
    timeout = False
    try:
        remaining = plan["resources"]["overall_timeout_seconds"] - (
            time.monotonic() - started
        )
        if remaining <= 0:
            raise subprocess.TimeoutExpired(child.args, 0)
        code = child.wait(timeout=remaining)
    except subprocess.TimeoutExpired:
        timeout = True
        with suppress(ProcessLookupError):
            os.killpg(child.pid, signal.SIGKILL)
        child.wait()
        code = 124
    common: dict[str, Any] = (
        load(output / "terminal.json")
        if (output / "terminal.json").is_file()
        else {"actual_exit": code, "stages": []}
    )
    custody = None
    try:
        verify_inputs(plan)
    except Exception as error:
        custody = str(error)
    expected = plan["stages"]
    actual = common["stages"]
    stage_ok = len(actual) == len(expected) == 2 and all(
        (
            a["id"] == b["id"]
            and a["argv"] == b["argv"]
            and (type(a["actual_exit"]) is int)
            and (a["actual_exit"] == 0)
            and (a["timed_out"] is False)
            for a, b in zip(actual, expected, strict=True)
        )
    )
    comparisons = []
    for name in ("pairs.csv", "report.json"):
        produced = output / "producer" / name
        tracked = ROOT / REPORT / name
        comparisons.append(
            {
                "path": str(tracked),
                "generated": pin(produced) if produced.is_file() else None,
                "tracked": pin(tracked),
                "checker_actual_exit": 0
                if produced.is_file() and produced.read_bytes() == tracked.read_bytes()
                else 2,
            }
        )
    elapsed = time.monotonic() - started
    rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    passed = (
        code == 0
        and common["actual_exit"] == 0
        and stage_ok
        and (not timeout)
        and (custody is None)
        and (elapsed <= plan["resources"]["overall_timeout_seconds"])
        and (rss <= plan["resources"]["resident_memory_limit_bytes"])
    )
    value = {
        "schema_version": "outcome-blind-empd2-nfi-source-replay-terminal.v1",
        "actual_exit": 0 if passed else 1,
        "candidate": plan["candidate"],
        "plan_sha256": args.registered_plan_sha256,
        "common_actual_exit": code,
        "common_terminal": pin(output / "terminal.json")
        if (output / "terminal.json").is_file()
        else None,
        "native_stages": actual,
        "tracked_byte_comparisons": comparisons,
        "tracked_checker_changes_are_native_failure": False,
        "timed_out": timeout,
        "source_custody_error": custody,
        "completed_elapsed_seconds": elapsed,
        "completed_child_peak_RSS_bytes_macos": rss,
        "resources": plan["resources"],
        "scope": plan["scope"],
        "timeout_cleanup_scope": "Own launcher group killed/waited; independent child sessions mean detached descendants are not certified absent on outer timeout. Timeout never passes.",
        "scientific_acceptance_claimed": False,
    }
    try:
        raw = accounted_receipt(output, value, plan["resources"]["output_byte_limit"])
    except ValueError as error:
        value.update(actual_exit=1, output_error=str(error))
        raw = accounted_receipt(output, value, 2**63 - 1)
    if time.monotonic() - started > plan["resources"]["overall_timeout_seconds"]:
        value.update(
            actual_exit=1, completed_elapsed_seconds=time.monotonic() - started
        )
        raw = accounted_receipt(output, value, 2**63 - 1)
    with target.open("xb") as stream:
        stream.write(raw)
    raise SystemExit(value["actual_exit"])


if __name__ == "__main__":
    main()
