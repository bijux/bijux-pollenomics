"""Freeze two canonical source CLIs, exact private identities and a distinct pure-xlrd profile."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys

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
    LANES,
    PRIVATE,
    ROOT,
    SOURCE,
    confined_output,
    dump,
    exact,
    frozen_pin_union,
    load,
    physical_pin,
    pin,
    require,
    sha,
    source_namespace,
    verify_frozen_pins,
)
from runtime import (  # noqa: E402 — authenticate local imports first.
    absent_path,
    check_aliases,
    runtime_inputs,
    tree_membership,
)


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
    before = identity()
    require(
        before["candidate"] == args.candidate and before["status"] == "",
        "Exact clean candidate required",
    )
    output = confined_output(args.output, absent=True)
    require(
        not output.is_relative_to(SOURCE) and not SOURCE.is_relative_to(output),
        "Output/source overlap refused",
    )
    manifest = SOURCE / "prepared-source-manifest.json"
    peer = SOURCE / "independent-source-review.json"
    require(
        sha(peer) == args.review_sha256
        and load(peer)["approved"] is True
        and load(peer)["source_manifest_sha256"] == sha(manifest),
        "Exact approved held-source review required",
    )
    expected = [pin(manifest), pin(peer)]
    for row in load(manifest)["files"]:
        p = SOURCE / row["path"]
        require(exact(pin(p), {**row, "path": str(p)}), "Held source changed")
        expected.append({**row, "path": str(p)})
    declared = load(SOURCE / "declared-inputs.json")
    for row in declared["inputs"]:
        require(
            exact(physical_pin(Path(row["path"])), row), "Declared source/data differs"
        )
        expected.append(dict(row))
    expected.extend(validate_cache(CACHE, load(SOURCE / "xlrd-cache-contract.json")))
    policy = ROOT / "configs/ci/report-ownership.json"
    policy_pin = pin(policy)
    owners = {}
    for name, spec in LANES.items():
        selected = [
            row for row in load(policy)["owners"] if row["owner_id"] == spec["owner_id"]
        ]
        require(
            len(selected) == 1
            and selected[0]["role"] == "unresolved"
            and selected[0]["paths"] == [spec["report"]]
            and selected[0]["producer_paths"] == [spec["source"]],
            "Exact unresolved selected owner/recipe required",
        )
        owners[name] = selected[0]
    expected.append(policy_pin)
    runtime_files, runtime = runtime_inputs()
    expected.extend(pin(p) for p in sorted(runtime_files))
    pins = frozen_pin_union(expected)
    by_path = {row["path"]: row for row in pins}
    parent = output.parent
    while not parent.exists():
        parent = parent.parent
    require(
        shutil.disk_usage(parent).free >= 1024**3,
        "At least1GiB free capacity required for128MiB output budget",
    )
    source_namespace()
    verify_frozen_pins(pins)
    validate_cache(CACHE, load(SOURCE / "xlrd-cache-contract.json"))
    require(
        tree_membership(Path(runtime["framework_root"]))
        == runtime["framework_membership"]
        and tree_membership(CACHE) == runtime["xlrd_cache_membership"],
        "Base/cache namespace changed during census",
    )
    require(
        check_aliases(runtime["tree_aliases"] + runtime["native_aliases"])
        and absent_path(Path(runtime["absent_stdlib_zip"])),
        "Alias/absence changed during census",
    )
    framework_files = {
        str(Path(runtime["framework_root"]) / row["path"])
        for row in runtime["framework_membership"]
        if row["kind"] == "file"
    }
    require(framework_files.issubset(by_path), "Unpinned base namespace file")
    require(identity() == before, "Candidate changed during census")
    confined_output(output, absent=True)
    verify_frozen_pins(pins)
    output.mkdir()
    (output / "scratch").mkdir()
    plan_path = output / "plan.json"
    lanes = {
        name: {
            "source": by_path[str(ROOT / spec["source"])],
            "historical_report": by_path[str(ROOT / spec["report"])],
            "owner": owners[name],
            "source_argv": [
                str(ROOT / spec["source"]),
                "--source-root",
                str(PRIVATE),
                "--output",
                str(output / "producer" / name / "report.json"),
            ],
        }
        for name, spec in LANES.items()
    }
    stages = []
    for lane in LANES:
        for kind, script in [
            ("maintained", "execute_source.py"),
            ("independent", "observe.py"),
        ]:
            stages.append(
                {
                    "id": kind + "-rootsi-" + lane,
                    "argv": [
                        str(BASE),
                        "-I",
                        "-S",
                        "-B",
                        str(SOURCE / script),
                        "--plan",
                        str(plan_path),
                        "--lane",
                        lane,
                    ],
                    "timeout_seconds": 45,
                    "must_succeed": True,
                }
            )
    plan = {
        "schema_version": "rootsi-source-chronology-replay-plan.v1",
        "id": "rootsi-source-chronology-"
        + args.candidate[:12]
        + "-"
        + hashlib.sha256(str(output).encode()).hexdigest()[:12],
        "candidate": args.candidate,
        "repository": str(ROOT),
        "output": str(output),
        "canonical_identity": before,
        "common_runner": str(SOURCE / "common_runner.py"),
        "input_pins": pins,
        "absent_input_paths": [runtime["absent_stdlib_zip"]],
        "runtime_profile": runtime,
        "ownership_policy": policy_pin,
        "lanes": lanes,
        "stages": stages,
        "environment": {
            "PYTHONDONTWRITEBYTECODE": "1",
            "TMPDIR": str(output / "scratch"),
        },
        "resources": {
            "overall_timeout_seconds": 220,
            "outer_timeout_seconds": 240,
            "declared_memory_bytes": 1024**3,
            "declared_storage_bytes": 128 * 1024**2,
        },
        "scope": "Two current canonical private Rootsi workbook source replays and independent raw-workbook/Neotoma observers. Declared1950-minus-age and0.0500001 comparison are retained arithmetic diagnostics, not a calendar/no-year-zero conversion or source correction. Literal pollen-name/count/depth agreement establishes shared source lineage, not independent chronology, ecological taxonomy, historical LandClim input identity, uncertainty, dated basin, rights/human or LRA acceptance. STAV/RANV absent workbook ages and FLINK sign discrepancy remain; no raw workbook redistribution, source acquisition, interpolation, model or R. A distinct source-bound pure-xlrd cache is used, not observed147/SOURCE3331 runtime authority.",
    }
    dump(plan_path, plan)
    print(
        __import__("json").dumps(
            {
                "plan": pin(plan_path),
                "protected_inputs": len(pins),
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
            }
        )
    )


if __name__ == "__main__":
    main()
