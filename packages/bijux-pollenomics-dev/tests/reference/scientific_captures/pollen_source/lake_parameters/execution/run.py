# ruff: noqa: E402
"""Execute the exact common plan with independent complete runtime/resource postchecks."""

from __future__ import annotations

import argparse
from contextlib import suppress
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

ENTRY_STARTED = time.monotonic()


def _verify_entry_namespace(root: Path) -> None:
    expected = {
        ".": [
            "check_controls.py",
            "check_tools.py",
            "common_runner.py",
            "contracts.py",
            "execute_projection.py",
            "execute_reader.py",
            "lake_review.py",
            "observe.py",
            "prepare.py",
            "projection_review.py",
            "run.py",
            "runtime_contracts.py",
            "source_admission.py",
            "source_entry.py",
            "source_inputs.py",
            "source_runtime.py",
        ]
    }
    for domain, names in expected.items():
        directory = root if domain == "." else root / domain
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError("Controller import domain is absent or linked")
        for entry in directory.iterdir():
            if entry.is_symlink() or not (entry.is_file() or entry.is_dir()):
                raise ValueError("Controller import namespace contains alias/special")
            if domain == ".":
                if entry.is_dir() and entry.name not in {
                    "preflight",
                    *set(expected) - {"."},
                }:
                    raise ValueError("Unexpected controller import directory")
                if (
                    entry.suffix in {".py", ".pyc", ".so", ".pyd", ".dylib"}
                    and entry.name not in names
                ):
                    raise ValueError("Unexpected controller import member")
            elif entry.is_dir() or entry.name not in names:
                raise ValueError("Unexpected nested controller import member")
        if domain != "." and {entry.name for entry in directory.iterdir()} != set(
            names
        ):
            raise ValueError("Nested controller import member is missing")


def _verify_reviewed_entry(root: Path) -> None:
    manifest = root / "prepared-source-manifest.json"
    review = root / "independent-source-review.json"
    for path in (manifest, review):
        if not path.is_file() or any(
            parent.is_symlink() for parent in (path, *path.parents)
        ):
            raise ValueError(
                "Reviewed controller entry requires regular source authority"
            )
    raw = manifest.read_bytes()
    document = json.loads(raw)
    admission = json.loads(review.read_bytes())
    if (
        document["source_only"] is not True
        or admission["approved"] is not True
        or admission["source_manifest_sha256"] != hashlib.sha256(raw).hexdigest()
    ):
        raise ValueError(
            "Exact independent source approval required before local imports"
        )
    names = [row["path"] for row in document["files"]]
    if names != sorted(set(names)):
        raise ValueError("Reviewed entry source paths must be sorted and unique")
    for row in document["files"]:
        path = Path(row["path"])
        if (
            not path.is_absolute()
            or ".." in path.parts
            or not path.is_relative_to(root)
            or any(parent.is_symlink() for parent in (path, *path.parents))
        ):
            raise ValueError("Reviewed controller entry leaves physical source")
        if (
            not path.is_file()
            or type(row["bytes"]) is not int
            or path.stat().st_size != row["bytes"]
        ):
            raise ValueError("Reviewed controller entry length changed")
        with path.open("rb") as stream:
            checksum = hashlib.file_digest(stream, "sha256").hexdigest()
        if checksum != row["sha256"]:
            raise ValueError("Reviewed controller source changed before local imports")
    required = {
        entry
        for names in {
            ".": [
                "check_controls.py",
                "check_tools.py",
                "common_runner.py",
                "contracts.py",
                "execute_projection.py",
                "execute_reader.py",
                "lake_review.py",
                "observe.py",
                "prepare.py",
                "projection_review.py",
                "run.py",
                "runtime_contracts.py",
                "source_admission.py",
                "source_entry.py",
                "source_inputs.py",
                "source_runtime.py",
            ]
        }.values()
        for entry in names
    }
    declared = {Path(name).relative_to(root).as_posix() for name in names}
    if not required.issubset(declared):
        raise ValueError("Reviewed controller manifest omits a local import member")


_verify_entry_namespace(Path(__file__).resolve().parent)
_verify_reviewed_entry(Path(__file__).resolve().parent)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import (
    PYTHON,
    ROOT,
    checkpoint,
    execution_scope,
    identity,
    load,
    require,
    write,
)
from source_inputs import pin
from source_runtime import clean_child_environment


def main() -> None:
    started = ENTRY_STARTED
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--registered-plan-sha256", required=True)
    args = parser.parse_args()
    require(
        pin(args.plan)["sha256"] == args.registered_plan_sha256,
        "Registered plan differs",
    )
    plan = load(args.plan)
    authority, scope = execution_scope(plan)
    require(
        identity() == plan["canonical_identity"], "Canonical candidate/index differs"
    )
    output = Path(plan["output"])
    terminal = output / "lakeparameter-terminal.json"
    require(
        not terminal.exists() and not (output / "terminal.json").exists(),
        "No execution receipt replacement",
    )
    environment = clean_child_environment(dict(os.environ))
    environment.update(plan["environment"])
    argv = [
        str(PYTHON),
        "-I",
        "-B",
        plan["common_runner"],
        "--plan",
        str(args.plan),
        "--registered-plan-sha256",
        args.registered_plan_sha256,
    ]
    process = subprocess.Popen(argv, cwd=ROOT, env=environment, start_new_session=True)
    timeout = False
    try:
        exit_code = process.wait(timeout=plan["resources"]["outer_timeout_seconds"])
    except subprocess.TimeoutExpired:
        timeout = True
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        exit_code = 124
    after_error = None
    try:
        checkpoint(authority, scope)
        require(
            identity() == plan["canonical_identity"],
            "Canonical candidate/index changed",
        )
        require(
            pin(args.plan)["sha256"] == args.registered_plan_sha256,
            "Registered plan changed",
        )
    except Exception as error:
        after_error = str(error)
    common_path = output / "terminal.json"
    common = load(common_path) if common_path.is_file() else None
    total = 0
    for path in output.rglob("*"):
        require(
            not path.is_symlink() and (path.is_file() or path.is_dir()),
            "Output alias/special refused",
        )
        if path.is_file():
            total += path.stat().st_size
    elapsed = time.monotonic() - started
    rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    resources = plan["resources"]
    memory_pass = rss <= resources["declared_memory_bytes"]
    storage_pass = total + 16384 <= resources["declared_storage_bytes"]
    wall_pass = elapsed <= resources["overall_timeout_seconds"]
    passed = (
        exit_code == 0
        and not timeout
        and after_error is None
        and common is not None
        and type(common["actual_exit"]) is int
        and common["actual_exit"] == 0
        and common["plan_sha256"] == args.registered_plan_sha256
        and len(common["stages"]) == len(plan["stages"])
        and memory_pass
        and storage_pass
        and wall_pass
    )
    write(
        terminal,
        {
            "candidate": plan["candidate"],
            "plan_sha256": args.registered_plan_sha256,
            "actual_exit": 0 if passed else 1,
            "actual_common_launch_argv": argv,
            "common_native_exit": exit_code,
            "common_terminal": pin(common_path) if common is not None else None,
            "outer_timed_out": timeout,
            "after_custody_error": after_error,
            "completed_elapsed_seconds": elapsed,
            "completed_child_peak_rss_bytes_macos": rss,
            "output_bytes_before_own_receipt": total,
            "own_receipt_reserve_bytes": 16384,
            "memory_bound_pass": memory_pass,
            "inclusive_storage_bound_pass": storage_pass,
            "completed_whole_wall_bound_pass": wall_pass,
            "complete_descendant_cleanup_or_RSS_claimed": False,
            "resources": resources,
            "scope": plan["scope"],
        },
    )
    require(terminal.stat().st_size <= 16384, "Receipt reserve exceeded")
    print(
        __import__("json").dumps(
            {"terminal": pin(terminal), "actual_exit": 0 if passed else 1}
        )
    )
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
