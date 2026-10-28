"""Freeze only authenticated SVAR source bytes and an isolated standard-library runtime."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import (
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
from runtime import absent_path, check_aliases, runtime_inputs, tree_membership


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
    p = argparse.ArgumentParser()
    p.add_argument("--candidate", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--review-sha256", required=True)
    a = p.parse_args()
    source_namespace()
    before = identity()
    require(
        before["candidate"] == a.candidate and before["status"] == "",
        "Exact clean candidate required",
    )
    output = confined_output(a.output, absent=True)
    manifest = SOURCE / "prepared-source-manifest.json"
    peer = SOURCE / "independent-source-review.json"
    require(sha(peer) == a.review_sha256, "Peer reference differs")
    review = load(peer)
    require(
        review["approved"] is True
        and review["source_manifest_sha256"] == sha(manifest),
        "Held independent source approval required",
    )
    expected = []
    for row in load(manifest)["files"]:
        file = SOURCE / row["path"]
        require(exact(pin(file), {**row, "path": str(file)}), "Held controller differs")
        expected.append({**row, "path": str(file)})
    expected.extend((pin(manifest), pin(peer)))
    declared = load(SOURCE / "declared-inputs.json")
    for row in declared["inputs"]:
        require(exact(pin(Path(row["path"])), row), "Science/source input differs")
        expected.append(dict(row))
    policy = ROOT / "configs/ci/report-ownership.json"
    policy_pin = pin(policy)
    owners = [x for x in load(policy)["owners"] if x["owner_id"] == declared["owner"]]
    require(
        len(owners) == 1
        and owners[0]["role"] == "unresolved"
        and owners[0]["paths"] == [declared["report"]],
        "Expected unresolved owner differs",
    )
    expected.append(policy_pin)
    runtime_files, runtime = runtime_inputs()
    expected.extend(pin(file) for file in sorted(runtime_files))
    frozen_inputs = frozen_pin_union(expected)
    frozen_by_path = {row["path"]: row for row in frozen_inputs}
    source = ROOT / declared["maintained_source"]
    report = ROOT / declared["report"]
    output_parent = output.parent
    while not output_parent.exists():
        output_parent = output_parent.parent
    require(
        shutil.disk_usage(output_parent).free >= 1024**3,
        "Need128MiB outputs and available reserve",
    )
    source_namespace()
    verify_frozen_pins(frozen_inputs)
    require(
        tree_membership(Path(runtime["framework_root"]))
        == runtime["framework_membership"],
        "Runtime namespace changed during preparation",
    )
    require(
        check_aliases(runtime["tree_aliases"] + runtime["native_aliases"])
        and absent_path(Path(runtime["absent_stdlib_zip"])),
        "Runtime alias or absence changed during preparation",
    )
    framework_files = {
        str(Path(runtime["framework_root"]) / row["path"])
        for row in runtime["framework_membership"]
        if row["kind"] == "file"
    }
    require(
        framework_files.issubset({row["path"] for row in frozen_inputs}),
        "Unpinned framework namespace entry",
    )
    require(identity() == before, "Candidate changed during preparation")
    confined_output(output, absent=True)
    verify_frozen_pins(frozen_inputs)
    output.mkdir()
    (output / "scratch").mkdir()
    plan_path = output / "plan.json"
    plan = {
        "id": "svar-normalized-source-" + a.candidate[:12],
        "schema_version": "svar-normalized-source-replay-plan.v1",
        "candidate": a.candidate,
        "repository": str(ROOT),
        "canonical_identity": before,
        "output": str(output),
        "input_pins": frozen_inputs,
        "absent_input_paths": [runtime["absent_stdlib_zip"]],
        "runtime_profile": runtime,
        "maintained_source": frozen_by_path[str(source)],
        "maintained_source_argv": [
            str(source),
            "--repository",
            str(ROOT),
            "--source-root",
            declared["private_root"],
            "--output",
            str(output / "producer"),
        ],
        "historical_report": frozen_by_path[str(report)],
        "declared_owner": owners[0],
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
        "scope": "Exact normalized privateSVAR source identity and current public refusal only.40565claimed vs40523review/99subset/zero ranks remain unreconciled. No WFS acquisition, new basin/geometry/ranking, rights/qualifiedhuman or scientific acceptance.",
    }
    plan["stages"] = [
        {
            "id": name,
            "argv": [
                str(BASE),
                "-I",
                "-S",
                "-B",
                str(SOURCE / script),
                "--plan",
                str(plan_path),
            ],
            "timeout_seconds": 45,
            "must_succeed": True,
        }
        for name, script in [
            ("maintained-svar-normalized-source", "execute_source.py"),
            ("independent-svar-source-refusal-observer", "observe.py"),
        ]
    ]
    dump(plan_path, plan)
    dump(
        output / "preparation.json",
        {
            "actual_exit": 0,
            "candidate": a.candidate,
            "plan": pin(plan_path),
            "protected_input_count": len(plan["input_pins"]),
            "native_consumers_launched": 0,
        },
    )
    print(plan_path)


if __name__ == "__main__":
    main()
