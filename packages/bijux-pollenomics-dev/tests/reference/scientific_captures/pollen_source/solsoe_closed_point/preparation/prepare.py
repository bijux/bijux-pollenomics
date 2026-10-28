"""Freeze a clean-candidate, isolated-stdlib Solsø relational replay."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import (
    BASE,
    COMMON_SHA,
    IDENTITIES,
    PAPER,
    PAPER_ID,
    REPLAY,
    dump,
    exact,
    load,
    owner_contract,
    pin,
    require,
    sha,
)
from runtime import runtime_inputs

A = Path(__file__).resolve().parent
R = A.parents[2]


def identity() -> dict[str, str]:
    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", *args], cwd=R, timeout=30)

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
    args = parser.parse_args()
    before = identity()
    require(
        before["candidate"] == args.candidate and before["status"] == "",
        "Exact clean candidate required",
    )
    files, runtime = runtime_inputs()
    manifest = A / "prepared-source-manifest.json"
    peer = A / "independent-source-review.json"
    for row in load(manifest)["files"]:
        require(
            exact(pin(A / row["path"]), {**row, "path": str(A / row["path"])}),
            "Held source bytes changed",
        )
        files.add(A / row["path"])
    require(
        load(peer)["approved"] is True
        and load(peer)["source_manifest_sha256"] == sha(manifest),
        "Independent source approval required",
    )
    files.update((manifest, peer))
    ownership = R / "configs/ci/report-ownership.json"
    owner = owner_contract(load(ownership))
    files.add(ownership)
    for relative, (digest, size) in IDENTITIES.items():
        require(
            exact(
                pin(R / relative),
                {"path": str(R / relative), "sha256": digest, "bytes": size},
            ),
            "Maintained source/data identity differs: " + relative,
        )
        files.add(R / relative)
    require(
        sha(PAPER) == PAPER_ID[0] and PAPER.stat().st_size == PAPER_ID[1],
        "Retained private paper differs",
    )
    files.add(PAPER)
    common = A / "common_runner.py"
    require(sha(common) == COMMON_SHA, "Recovered common runner differs")
    forensic = (
        R
        / "artifacts/science/solsoe-original-source-feasibility/source-feasibility.json"
    )
    require(
        sha(forensic)
        == "ab40cfa412e4a6e722409aba41da60167e17b6be3f0508ed3135badf2aa81d48",
        "Source forensic evidence changed",
    )
    files.add(forensic)
    output = args.output.absolute()
    require(
        output == output.resolve()
        and output.is_relative_to(R / "artifacts")
        and not output.exists()
        and not any(p.is_symlink() for p in (output, *output.parents)),
        "Fresh physical artifact output required",
    )
    plan_path = output / "plan.json"
    stages = [
        {
            "id": "solsoe-maintained-closed-central-point-replay",
            "argv": [
                str(BASE),
                "-I",
                "-S",
                "-B",
                str(A / "execute_source.py"),
                "--plan",
                str(plan_path),
            ],
            "timeout_seconds": 45,
            "must_succeed": True,
        },
        {
            "id": "independent-solsoe-controls-and-native-sample-joins",
            "argv": [
                str(BASE),
                "-I",
                "-S",
                "-B",
                str(A / "observe.py"),
                "--plan",
                str(plan_path),
            ],
            "timeout_seconds": 45,
            "must_succeed": True,
        },
    ]
    output.mkdir()
    (output / "scratch").mkdir()
    plan = {
        "id": "solsoe-original-controls-"
        + args.candidate[:12]
        + "-"
        + hashlib.sha256(str(output).encode()).hexdigest()[:12],
        "candidate": args.candidate,
        "repository": str(R),
        "output": str(output),
        "canonical_identity": before,
        "qualified_python": str(BASE),
        "runtime_profile": runtime,
        "common_runner": str(common),
        "declared_owner": owner,
        "ownership_policy": pin(ownership),
        "maintained_source": pin(R / REPLAY),
        "maintained_source_argv": [
            str(R / REPLAY),
            "--repository",
            str(R),
            "--paper",
            str(PAPER),
            "--output",
            str(output / "producer"),
        ],
        "historical_report": pin(
            R
            / "docs/report/countries/denmark/solsoe-source-lineage/original-core-selection/report.json"
        ),
        "input_pins": [pin(p) for p in sorted(files)],
        "absent_input_paths": [str(output / "producer"), runtime["absent_stdlib_zip"]],
        "environment": {
            "PYTHONPATH": "",
            "PYTHONDONTWRITEBYTECODE": "1",
            "TMPDIR": str(output / "scratch"),
        },
        "stages": stages,
        "resources": {
            "overall_timeout_seconds": 110,
            "outer_timeout_seconds": 130,
            "declared_memory_bytes": 1073741824,
            "declared_storage_bytes": 134217728,
        },
        "scope": "Genuine current standalone stdlib closed central-point replay against exact retained Neotoma relations. Complete92-row raw ledger/refusals and14 native relation IDs/seven underlying controls; no corrected total asserted before execution. Canonical source executes under truthful runpy launcher with actual namespace/native before-after records and separate source/metadata exits. Original8456 v1 half-unbounded report remains historical. PDF identity only, no fresh table extraction, original provider/process recovery,79 membership, uncertainty-support/analytical admission, basin chronology, ecological or human acceptance. Distinct isolated base profile; no dependency-equipped scientific runtime substitution.",
    }
    # Common absent-input checks are for paths remaining absent throughout execution.
    plan["absent_input_paths"] = [runtime["absent_stdlib_zip"]]
    require(identity() == before, "Canonical source changed during preparation")
    dump(plan_path, plan)
    print(
        __import__("json").dumps(
            {
                "plan": pin(plan_path),
                "inputs": len(plan["input_pins"]),
                "launch_argv": [
                    str(BASE),
                    "-I",
                    "-S",
                    "-B",
                    str(A / "run.py"),
                    "--plan",
                    str(plan_path),
                    "--registered-plan-sha256",
                    sha(plan_path),
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
