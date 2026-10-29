"""Guard the qualified dependency runtime around current publication source stages."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time
from typing import Any

_entry_path = Path(__file__).absolute()
if _entry_path != _entry_path.resolve(strict=True) or any(
    p.is_symlink() for p in (_entry_path, *_entry_path.parents)
):
    raise ValueError("Physical absolute controller entry and ancestors required")
_entry_directory = _entry_path.parent
_expected_python = {
    "common_runner.py",
    "prepare.py",
    "run.py",
    "runtime_contracts.py",
    "check_contracts.py",
    "runtime_guarded_runner.py",
    "source_runtime.py",
    "observe.py",
    "execute_source.py",
    "contracts.py",
    "metadata.py",
}
_present_python = set()
for _entry in _entry_directory.iterdir():
    if _entry.is_symlink() or not (_entry.is_dir() or _entry.is_file()):
        raise ValueError("Controller alias/special entry before helper import")
    if _entry.is_dir() and _entry.name != "preflight":
        raise ValueError("Unexpected controller directory before helper import")
    if _entry.suffix in {".py", ".pyc", ".so", ".dylib", ".pyd"}:
        if _entry.name not in _expected_python:
            raise ValueError("Unexpected controller import before helper import")
        _present_python.add(_entry.name)
if _present_python != _expected_python:
    raise ValueError("Incomplete exact controller import namespace")
sys.path.insert(0, str(_entry_directory))
from source_runtime import (  # noqa: E402 - guarded local namespace.
    authenticate_runtime,
    clean_child_environment,
)


def completed_bytes(
    roots: list[Path], aliases: list[dict[str, str]] | None = None
) -> int:
    unique: list[Path] = []
    for root in sorted(set(roots), key=lambda path: len(path.parts)):
        if any(root.is_relative_to(parent) for parent in unique):
            continue
        unique.append(root)
    declared = {row["path"]: row["target"] for row in aliases or []}
    if len(declared) != len(aliases or []):
        raise ValueError("Duplicate output alias")
    seen = set()
    total = 0
    for root in unique:
        if not root.is_dir() or root.is_symlink():
            raise ValueError("Measured output root is missing or linked")
        for path in root.rglob("*"):
            if path.is_symlink():
                if (
                    str(path) not in declared
                    or os.readlink(path) != declared[str(path)]
                    or not path.resolve().is_relative_to(root)
                    or not path.resolve().exists()
                ):
                    raise ValueError(
                        "Output alias differs from the registered exact source alias"
                    )
                seen.add(str(path))
                total += len(os.fsencode(os.readlink(path)))
                continue
            if not (path.is_file() or path.is_dir()):
                raise ValueError("Output special entry is not admitted")
            if path.is_file():
                total += path.stat().st_size
    if seen != set(declared):
        raise ValueError("A registered output alias is missing")
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--registered-plan-sha256", required=True)
    args = parser.parse_args()
    import hashlib

    raw = args.plan.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.registered_plan_sha256:
        raise ValueError("Registered runtime-guarded plan differs")
    plan: dict[str, Any] = json.loads(raw)
    output = Path(plan["qualified_runtime_output_root"])
    terminal = output / "runtime-custody-terminal.json"
    if terminal.exists() or terminal.is_symlink():
        raise ValueError("Runtime custody receipt already exists")
    resources = plan["qualified_runtime_resource_bounds"]
    started = time.monotonic()
    authority = None
    before_error = None
    after_error = None
    code = None
    timed_out = False
    try:
        authority, _ = authenticate_runtime()
        if authority != plan["qualified_source_runtime"]:
            raise ValueError(
                "Current runtime observation differs from registered source epoch"
            )
    except (ValueError, OSError) as error:
        before_error = str(error)
    if before_error is None:
        delegate = [
            args.registered_plan_sha256
            if value in {"PLAN_SHA256", "<registered-plan-sha256>"}
            else value
            for value in plan["qualified_runtime_delegate_argv"]
        ]
        env = clean_child_environment(dict(os.environ))
        private = output / "runtime-temporary"
        private.mkdir()
        for name in ("cache", "matplotlib"):
            (private / name).mkdir()
        env.update(
            TMPDIR=str(private),
            XDG_CACHE_HOME=str(private / "cache"),
            MPLCONFIGDIR=str(private / "matplotlib"),
            PYTHONDONTWRITEBYTECODE="1",
            PATH="/Library/Developer/CommandLineTools/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
        )
        with (
            (output / "runtime-delegate.stdout").open("xb") as out,
            (output / "runtime-delegate.stderr").open("xb") as err,
        ):
            child = subprocess.Popen(
                delegate,
                cwd=plan["qualified_runtime_repository"],
                env=env,
                stdout=out,
                stderr=err,
                start_new_session=True,
            )
            try:
                remaining = resources["overall_seconds"] - (time.monotonic() - started)
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(delegate, 0)
                code = child.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                timed_out = True
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(child.pid, signal.SIGKILL)
                child.wait()
                code = 124
    try:
        after, _ = authenticate_runtime()
        if after != plan["qualified_source_runtime"]:
            raise ValueError("Runtime observation changed after delegated execution")
    except (ValueError, OSError) as error:
        after_error = str(error)
    peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    roots = [output, *[Path(name) for name in plan.get("measured_output_roots", [])]]
    output_error = None
    used = 0
    try:
        used = completed_bytes(roots, plan.get("qualified_runtime_output_aliases", []))
    except (ValueError, OSError) as error:
        output_error = str(error)
    elapsed = time.monotonic() - started
    passed = (
        output_error is None
        and before_error is None
        and after_error is None
        and type(code) is int
        and code == 0
        and not timed_out
        and elapsed <= resources["overall_seconds"]
        and peak <= resources["completed_child_peak_rss_bytes"]
        and used + 16384 <= resources["logical_output_bytes"]
    )
    receipt = {
        "schema_version": "atlas-qualified-source-runtime-custody.v1",
        "plan_sha256": args.registered_plan_sha256,
        "source_candidate": plan["candidate"],
        "qualified_source_runtime": plan["qualified_source_runtime"],
        "delegate_actual_exit": code,
        "actual_exit": 0 if passed else 1,
        "timed_out": timed_out,
        "before_runtime_error": before_error,
        "after_runtime_error": after_error,
        "completed_elapsed_seconds": elapsed,
        "completed_child_peak_rss_bytes_macos": peak,
        "output_logical_bytes_before_receipt": used,
        "output_measurement_error": output_error,
        "own_receipt_reserved_bytes": 16384,
        "resource_bounds_met": passed,
        "scope": "New147 dependency runtime before/after pin/namespace/alias/absence custody around unchanged native stages. Original129 bootstrap whole1 and production3zero remain historical; actual current Neotoma publication source epoch is separate. Completed-child RSS/logical storage postchecks are not OS quotas or aggregate descendants; outer-timeout cleanup does not establish detached descendant termination.",
    }
    encoded = (json.dumps(receipt, indent=2) + "\n").encode()
    if len(encoded) > 16384:
        raise ValueError("Runtime custody receipt exceeded reserved bytes")
    with terminal.open("xb") as stream:
        stream.write(encoded)
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
