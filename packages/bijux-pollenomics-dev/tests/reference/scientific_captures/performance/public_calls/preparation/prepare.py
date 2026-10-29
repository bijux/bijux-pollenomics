"""Freeze bounded metadata assembly over an already completed performance run."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from assemble import PACKAGES, retained_source_bytes
from contracts import EXECUTION_CANDIDATE, pin, qualified_execution, require, write_json

A = Path(__file__).absolute().parent
R = A.parents[2]
PY = R / "artifacts/science/runtime/environment/bin/python"
B = R / "artifacts/science/representative-public-call-profile"


def identity() -> dict:
    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", *args], cwd=R, timeout=60)

    require(
        git("branch", "--show-current").strip() == b"main",
        "canonical branch is not main",
    )
    return {
        "candidate": git("rev-parse", "HEAD").decode().strip(),
        "status": git("status", "--porcelain").decode(),
        "tracked_inventory_sha256": hashlib.sha256(
            git("ls-files", "-s", "-z")
        ).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(
        Path(sys.executable).absolute() == PY
        and Path(sys.prefix).absolute() == PY.parent.parent
        and sys.version_info[:2] == (3, 11),
        "qualified lexical Python3.11 required",
    )
    before = identity()
    require(
        before["candidate"] == args.candidate and before["status"] == "",
        "current clean candidate differs",
    )
    output = args.output.absolute()
    require(
        not output.exists()
        and output.resolve() == output
        and output.is_relative_to(R / "artifacts")
        and ".." not in output.parts
        and not any(p.is_symlink() for p in (output, *output.parents)),
        "new confined output required",
    )
    manifest_path, peer_path = (
        A / "prepared-source-manifest.json",
        A / "independent-source-review.json",
    )
    manifest, peer = (
        json.loads(manifest_path.read_bytes()),
        json.loads(peer_path.read_bytes()),
    )
    require(
        peer["approved"] is True
        and peer["source_manifest_sha256"] == pin(manifest_path)["sha256"],
        "exact independent source approval required",
    )
    for row in manifest["files"]:
        require(pin(Path(row["path"])) == row, "held metadata source changed")
    original, _review = qualified_execution(B)
    pins = {row["path"]: row for row in original["input_pins"]}
    historical = []
    for path, row in list(pins.items()):
        member = Path(path)
        if any(
            member.is_relative_to(R / "packages" / name / "src") for name in PACKAGES
        ):
            _raw, authority = retained_source_bytes(R, row)
            if authority == "original_pin_equal_historical_git_blob":
                historical.append(row)
                del pins[path]
                pins[path] = pin(member)
        else:
            require(
                pin(member) == row, "original external/runtime/control input changed"
            )
    for entry, target in original["runtime_entry_targets"].items():
        require(str(Path(entry).resolve()) == target, "qualified runtime alias changed")
    for path in [
        manifest_path,
        peer_path,
        *[Path(row["path"]) for row in manifest["files"]],
        *[p for p in B.rglob("*") if p.is_file()],
    ]:
        row = pin(path)
        if row["path"] in pins:
            require(
                pins[row["path"]] == row,
                "new current pin cannot silently rebaseline an original input",
            )
        pins[row["path"]] = row
    plan = {
        "id": "representative-performance-publication-"
        + args.candidate[:12]
        + "-"
        + hashlib.sha256(str(output).encode()).hexdigest()[:12],
        "candidate": args.candidate,
        "source_candidate": args.candidate,
        "repository": str(R),
        "output": str(output),
        "execution_root": str(B),
        "original_execution_candidate": EXECUTION_CANDIDATE,
        "original_source_not_live_equivalence": historical,
        "metadata_source_pins": [
            pin(path)
            for path in sorted(
                [*A.glob("*.py"), A / "report-template.md", *A.glob("proposal/**/*.py")]
            )
        ],
        "qualified_python": str(PY),
        "common_runner": original["common_runner"],
        "canonical_identity": before,
        "runtime_entry_targets": original["runtime_entry_targets"],
        "input_pins": sorted(pins.values(), key=lambda row: row["path"]),
        "absent_input_paths": [],
        "environment": {
            "PYTHONDONTWRITEBYTECODE": "1",
            "TMPDIR": str(output / "scratch"),
            "PYTHONPYCACHEPREFIX": str(output / "scratch/bytecode"),
            "PROJ_NETWORK": "OFF",
        },
        "stages": [
            {
                "id": "retained-performance-metadata-assembly",
                "argv": [
                    str(PY),
                    "-B",
                    str(A / "assemble.py"),
                    "--plan",
                    str(output / "plan.json"),
                ],
                "timeout_seconds": 180,
                "must_succeed": True,
            },
            {
                "id": "independent-retained-source-and-measurement-review",
                "argv": [
                    str(PY),
                    "-B",
                    str(A / "observe.py"),
                    "--plan",
                    str(output / "plan.json"),
                ],
                "timeout_seconds": 180,
                "must_succeed": True,
            },
        ],
        "resources": {
            "overall_timeout_seconds": 420,
            "declared_memory_bytes": 536870912,
            "declared_storage_bytes": 268435456,
        },
        "scope": "Metadata-only retention and independent exact source/output/timing joins of completed116 performance. No model, benchmark, timing, profiling, compiler, R or source acquisition is executed. Private193 and runtime files remain original hash references, not redistributed. Historical first-party source blobs remain116; current clean assembly candidate is separate.",
        "actual_launch_argv": [
            str(PY),
            "-B",
            str(A / "run.py"),
            "--plan",
            str(output / "plan.json"),
            "--registered-plan-sha256",
            "PLAN_SHA256",
        ],
    }
    require(
        identity() == before, "canonical identity changed during metadata preparation"
    )
    output.mkdir()
    (output / "scratch").mkdir()
    write_json(output / "plan.json", plan)
    print(
        json.dumps(
            {
                "plan": pin(output / "plan.json"),
                "stages": 2,
                "actual_launch_argv": plan["actual_launch_argv"],
                "new_model_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
