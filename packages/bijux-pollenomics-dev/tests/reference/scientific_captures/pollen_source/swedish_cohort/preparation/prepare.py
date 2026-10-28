"""Freeze one corrected observer over an unchanged completed Swedish source replay."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys

_entry_directory = Path(__file__).resolve().parent
_expected_python = {
    "execute_source.py",
    "observe.py",
    "metadata.py",
    "common_runner.py",
    "runtime.py",
    "prepare.py",
    "contracts.py",
    "run.py",
    "check_contracts.py",
    "custody.py",
}
for _entry in _entry_directory.iterdir():
    if _entry.is_symlink() or (not _entry.is_file() and not _entry.is_dir()):
        raise ValueError("Controller alias/special entry")
    if _entry.is_dir() and _entry.name != "preflight":
        raise ValueError("Unexpected controller import directory")
    if _entry.suffix in {".py", ".pyc", ".so"} and _entry.name not in _expected_python:
        raise ValueError("Unexpected controller module before helper import")
sys.path.insert(0, str(_entry_directory))
from contracts import (  # noqa: E402
    BASE,
    ROOT,
    SOURCE,
    confined_output,
    dump,
    exact,
    frozen_pin_union,
    load,
    pin,
    require,
    sha,
    source_namespace,
    verify_frozen_pins,
)
from custody import ORIGINAL_CANDIDATE, RETAINED, authenticate_retained  # noqa: E402
from runtime import profile_guard  # noqa: E402


def identity() -> dict[str, str]:
    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", *args], cwd=ROOT, timeout=30)

    require(git("branch", "--show-current").strip() == b"main", "Local main required")
    return {
        "candidate": git("rev-parse", "HEAD").decode().strip(),
        "status": git("status", "--porcelain").decode(),
        "tracked_inventory_sha256": hashlib.sha256(
            git("ls-files", "-s", "-z")
        ).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review-sha256", required=True)
    args = parser.parse_args()
    source_namespace()
    profile_guard()
    canonical = identity()
    require(
        canonical["candidate"] == args.candidate == ORIGINAL_CANDIDATE
        and canonical["status"] == "",
        "Exact original clean candidate required; no unreviewed Git bridge",
    )
    output = confined_output(args.output, absent=True)
    for protected in (SOURCE, RETAINED):
        require(
            not output.is_relative_to(protected)
            and not protected.is_relative_to(output),
            "Output overlaps protected root",
        )
    manifest = SOURCE / "prepared-source-manifest.json"
    peer = SOURCE / "independent-source-review.json"
    require(
        sha(peer) == args.review_sha256
        and load(peer)["approved"] is True
        and load(peer)["source_manifest_sha256"] == sha(manifest),
        "Exact source approval required",
    )
    expected = [pin(manifest), pin(peer)]
    for row in load(manifest)["files"]:
        path = SOURCE / row["path"]
        require(exact(pin(path), {**row, "path": str(path)}), "Held source differs")
        expected.append({**row, "path": str(path)})
    original, products = authenticate_retained()
    inputs = frozen_pin_union([*expected, *original["input_pins"], *products])
    plan = {
        "schema_version": "swedish-cohort-observer-only-plan.v1",
        "candidate": args.candidate,
        "repository": str(ROOT),
        "canonical_identity": canonical,
        "output": str(output),
        "input_pins": inputs,
        "absent_input_paths": original["absent_input_paths"],
        "runtime_profile": original["runtime_profile"],
        "original_plan": pin(RETAINED / "plan.json"),
        "original_common": pin(RETAINED / "terminal.json"),
        "original_outer": pin(RETAINED / "swedish-cohort-terminal.json"),
        "retained_output_members": products,
        "retained_producer_native_exit": 0,
        "original_whole_actual_exit": 1,
        "common_runner": str(SOURCE / "common_runner.py"),
        "resources": {
            "overall_timeout_seconds": 110,
            "resident_memory_limit_bytes": 1024**3,
            "output_byte_limit": 128 * 1024**2,
            "outer_timeout_seconds": 100,
            "declared_memory_bytes": 1024**3,
            "declared_storage_bytes": 128 * 1024**2,
        },
        "environment": {
            "PYTHONDONTWRITEBYTECODE": "1",
            "TMPDIR": str(output / "scratch"),
        },
        "scope": "One corrected independent full metadata source join over genuine unchanged source0/observer1. No producer rerun, new acquisition/count table/selected age/physical fresh cohort/rights/ecology/LRA/human acceptance.",
    }
    plan_path = output / "plan.json"
    plan["stages"] = [
        {
            "id": "independent-nested-swedish-metadata-observer",
            "argv": [
                str(BASE),
                "-I",
                "-S",
                "-B",
                str(SOURCE / "observe.py"),
                "--plan",
                str(plan_path),
            ],
            "timeout_seconds": 45,
            "must_succeed": True,
        }
    ]
    parent = output.parent
    while not parent.exists():
        parent = parent.parent
    require(
        shutil.disk_usage(parent).free >= 1024**3,
        "Need128MiB output budget plus physical reserve",
    )
    source_namespace()
    verify_frozen_pins(inputs)
    checked, retained = authenticate_retained()
    require(
        exact(checked, original) and exact(retained, products),
        "Retained source changed during preparation",
    )
    require(identity() == canonical, "Git changed during census")
    confined_output(output, absent=True)
    output.mkdir()
    (output / "scratch").mkdir()
    dump(plan_path, plan)
    dump(
        output / "preparation.json",
        {
            "actual_exit": 0,
            "plan": pin(plan_path),
            "original_whole_exit": 1,
            "producer_rerun": False,
            "launch_argv": [
                str(BASE),
                "-I",
                "-S",
                "-B",
                str(SOURCE / "run.py"),
                "--plan",
                str(plan_path),
                "--registered-plan-sha256",
                sha(plan_path),
            ],
        },
    )
    print(plan_path)


if __name__ == "__main__":
    main()
