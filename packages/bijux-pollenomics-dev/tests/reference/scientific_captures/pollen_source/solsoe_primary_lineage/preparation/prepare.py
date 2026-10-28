"""Freeze the maintained pollen-lineage CLI and an independent raw-count observer."""

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
    FAMILY,
    MANIFEST,
    PRIMARY,
    PRODUCER,
    REPORT,
    SAMPLES,
    dump,
    exact,
    input_catalog,
    load,
    owner_contract,
    pin,
    require,
    sha,
)
from runtime import profile_guard, runtime_inputs

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


def data_input(path: Path) -> dict[str, object]:
    require(
        path == path.resolve()
        and not any(parent.is_symlink() for parent in (path, *path.parents)),
        "Source data must have physical nonsymlink ancestors",
    )
    return pin(path)


def output_root(path: Path) -> Path:
    output = path.absolute()
    require(
        output == output.resolve()
        and output.is_relative_to(R / "artifacts")
        and not output.exists()
        and not any(parent.is_symlink() for parent in (output, *output.parents))
        and not output.is_relative_to(A),
        "Fresh separate physical artifact output required",
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    profile_guard()
    before = identity()
    require(
        before["candidate"] == args.candidate and before["status"] == "",
        "Exact clean candidate required",
    )
    output = output_root(args.output)
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
    catalog = load(A / "declared-inputs.json")
    private = Path(catalog["private_source_root"])
    ownership = R / "configs/ci/report-ownership.json"
    owner = owner_contract(load(ownership))
    files.add(ownership)
    for row in input_catalog():
        path = (private if row["path"] == PRIMARY else R) / row["path"]
        require(
            exact(data_input(path), {**row, "path": str(path)}),
            "Declared source input differs: " + row["path"],
        )
        files.add(path)
    for row in (catalog["source_report"], catalog["canonical_sample_ledger"]):
        path = Path(row["path"]) if Path(row["path"]).is_absolute() else R / row["path"]
        require(
            exact(data_input(path), {**row, "path": str(path)}),
            "Canonical product authority differs",
        )
        files.add(path)
    require(
        sha(A / "common_runner.py") == COMMON_SHA, "Qualified common runner differs"
    )
    source_argv = [
        str(R / PRODUCER),
        "--repository",
        str(R),
        "--source-root",
        str(private),
        "--output",
        str(output / "producer"),
    ]
    plan_path = output / "plan.json"
    stages = [
        {
            "id": "maintained-solsoe-primary-pollen-lineage",
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
            "id": "independent-solsoe-pollen-source-count-and-name-vectors",
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
    pins = [pin(path) for path in sorted(files)]
    require(
        identity() == before
        and all(exact(pin(Path(row["path"])), row) for row in pins),
        "Canonical/input bytes changed during preparation",
    )
    output_root(output)
    output.mkdir()
    (output / "scratch").mkdir()
    plan = {
        "id": "solsoe-primary-pollen-lineage-"
        + args.candidate[:12]
        + "-"
        + hashlib.sha256(str(output).encode()).hexdigest()[:12],
        "candidate": args.candidate,
        "repository": str(R),
        "output": str(output),
        "canonical_identity": before,
        "qualified_python": str(BASE),
        "runtime_profile": runtime,
        "common_runner": str(A / "common_runner.py"),
        "declared_owner": owner,
        "ownership_policy": pin(ownership),
        "maintained_source": pin(R / PRODUCER),
        "maintained_source_argv": source_argv,
        "historical_report": pin(R / REPORT),
        "historical_samples": pin(R / SAMPLES),
        "private_primary": pin(private / PRIMARY),
        "relational_manifest": pin(R / MANIFEST),
        "input_pins": pins,
        "absent_input_paths": [runtime["absent_stdlib_zip"]],
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
        "scope": "Current maintained primary739834 source-count lineage only; exact66depths/147parameters/9702cells/2881positive/6821zero/128653counts and129literal+18unique numerical rename candidates must be independently derived. Complete JSON/66rowCSV bytes must match canonical authority. Primary raw CCBYNC remains external, no redistribution or recovered acquisition/copy chain. Numeric name-vector equality is not ecological taxonomy, original79 selection, chronology, basin, LRA, rights, human or official release acceptance. No numerical models, R, fitting or network.",
    }
    require(
        plan["declared_owner"]["paths"]
        == [FAMILY + "report.json", FAMILY + "samples.csv"],
        "Only two report products selected",
    )
    dump(plan_path, plan)
    print(
        __import__("json").dumps(
            {
                "plan": pin(plan_path),
                "inputs": len(pins),
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
