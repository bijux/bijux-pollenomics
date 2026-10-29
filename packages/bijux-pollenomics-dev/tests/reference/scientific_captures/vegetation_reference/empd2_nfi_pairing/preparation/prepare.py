"""Freeze exact private metadata, maintained source and qualified dependency runtime."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import sys
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
    INPUTS,
    OWNER,
    POLICY,
    PRIVATE,
    PRODUCER,
    REPORT,
    ROOT,
    SOURCE,
    dump,
    first_party_snapshot,
    identity,
    load,
    namespace,
    output_root,
    pin,
    require,
    union,
    verify_inputs,
)
from source_runtime import (  # noqa: E402 - authenticate the local import namespace first.
    PYTHON,
    attach_runtime_launcher,
    authenticate_runtime,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--review-sha256", required=True)
    args = parser.parse_args()
    namespace()
    output = output_root(args.output, absent=True)
    require(
        not output.is_relative_to(SOURCE) and (not SOURCE.is_relative_to(output)),
        "Source/output overlap",
    )
    canonical = identity()
    require(
        canonical["candidate"] == args.candidate and canonical["status"] == "",
        "Exact clean candidate required",
    )
    manifest_record = pin(SOURCE / "prepared-source-manifest.json")
    review_record = pin(args.review)
    require(review_record["sha256"] == args.review_sha256, "Review SHA differs")
    review = load(args.review)
    manifest = load(Path(manifest_record["path"]))
    require(
        review["approved"] is True
        and review["source_manifest_sha256"] == manifest_record["sha256"],
        "Exact independent source approval missing",
    )
    original = union([manifest_record, review_record])
    for row in manifest["files"]:
        expected = {**row, "path": str(SOURCE / row["path"])}
        require(pin(Path(expected["path"])) == expected, "Held controller differs")
        original = union(original, [expected])
    source_records = {}
    for role, (path, checksum, size) in INPUTS.items():
        expected = {"path": str(path), "sha256": checksum, "bytes": size}
        require(pin(path) == expected, "Declared source bytes differ: " + role)
        source_records[role] = expected
        original = union(original, [expected])
    policy_record = pin(ROOT / POLICY)
    policy = load(ROOT / POLICY)
    owners = [r for r in policy["owners"] if r["owner_id"] == OWNER]
    require(
        len(owners) == 1
        and owners[0]["paths"] == [REPORT + "/pairs.csv", REPORT + "/report.json"],
        "Exact owner output partition differs",
    )
    owner = owners[0]
    for name in [
        POLICY,
        *owner["producer_paths"],
        *owner["producer_inputs"],
        *owner["paths"],
    ]:
        original = union(original, [pin(ROOT / name)])
    trees, source_rows = first_party_snapshot()
    authority, runtime_rows = authenticate_runtime()
    inputs = union(original, source_rows, runtime_rows)
    site = PYTHON.parent.parent / "lib/python3.11/site-packages"
    proj_data = site / "pyproj/proj_dir/share/proj"
    require(
        pin(proj_data / "proj.db") in inputs, "Qualified PROJ database is not pinned"
    )
    plan: dict[str, Any] = {
        "schema_version": "outcome-blind-empd2-nfi-source-replay-plan.v1",
        "candidate": args.candidate,
        "repository": str(ROOT),
        "canonical_identity": canonical,
        "output": str(output),
        "owner_id": OWNER,
        "owner_row": owner,
        "whole_ownership_policy": policy_record,
        "maintained_source": pin(ROOT / PRODUCER),
        "private_source_store": str(PRIVATE),
        "source_input_records": source_records,
        "first_party_namespaces": trees,
        "input_pins": inputs,
        "original_controller_and_source_expected_pins": original,
        "absent_input_paths": [],
        "PROJ_data_directory": str(proj_data),
        "PROJ_user_directory": str(output / "proj-cache"),
        "common_runner": str(SOURCE / "common_runner.py"),
        "resources": {
            "overall_timeout_seconds": 240,
            "resident_memory_limit_bytes": 2 * 1024**3,
            "output_byte_limit": 128 * 1024**2,
        },
        "scope": "Fresh maintained metadata-only refusal replay. Native geometry rechecks sixteen selected source pairs under unchanged1e-5m agreement; the retained53 full-screen combinations are not a new132x43892 sweep. No measured vegetation/outcome selection, LRA estimator, model, R, source acquisition, rights, leakage or human review admission.",
    }
    plan["environment"] = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "TMPDIR": str(output / "temporary"),
        "XDG_CACHE_HOME": str(output / "cache"),
        "MPLCONFIGDIR": str(output / "matplotlib"),
        "PROJ_NETWORK": "OFF",
        "PROJ_USER_WRITABLE_DIRECTORY": str(output / "proj-cache"),
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
    }
    require(
        not any(
            k in os.environ
            for k in (
                "PROJ_DATA",
                "PROJ_LIB",
                "PROJ_AUX_DB",
                "PROJ_USER_WRITABLE_DIRECTORY",
            )
        ),
        "Ambient PROJ data/cache override present",
    )
    plan["stages"] = [
        {
            "id": "maintained-outcome-blind-pairing",
            "argv": [
                str(PYTHON),
                "-I",
                "-B",
                str(SOURCE / "execute_source.py"),
                "--plan",
                str(output / "plan.json"),
            ],
            "timeout_seconds": 120,
            "must_succeed": True,
        },
        {
            "id": "independent-source-pairing-observer",
            "argv": [
                str(PYTHON),
                "-I",
                "-B",
                str(SOURCE / "observe.py"),
                "--plan",
                str(output / "plan.json"),
            ],
            "timeout_seconds": 90,
            "must_succeed": True,
        },
    ]
    launch = attach_runtime_launcher(
        plan,
        authority,
        runtime_rows,
        output,
        output / "plan.json",
        [
            str(PYTHON),
            "-I",
            "-B",
            str(SOURCE / "run.py"),
            "--plan",
            str(output / "plan.json"),
            "--registered-plan-sha256",
            "PLAN_SHA256",
        ],
        wall=240,
        memory=2 * 1024**3,
        storage=128 * 1024**2,
    )
    plan["actual_launch_argv"] = launch
    verify_inputs(plan)
    require(identity() == canonical, "Candidate changed during preparation")
    parent = output.parent
    while not parent.exists():
        parent = parent.parent
    require(
        shutil.disk_usage(parent).free >= 512 * 1024**2,
        "Insufficient512MiB physical reserve",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output_root(output, absent=True).mkdir()
    for name in ("temporary", "cache", "matplotlib", "proj-cache"):
        (output / name).mkdir()
    dump(output / "plan.json", plan)
    dump(
        output / "preparation.json",
        {
            "actual_exit": 0,
            "candidate": args.candidate,
            "plan": pin(output / "plan.json"),
            "protected_inputs": len(plan["input_pins"]),
            "private_metadata_sources": source_records,
            "actual_native_stages_launched": 0,
            "runtime_authority": authority,
        },
    )
    print(output / "plan.json")


if __name__ == "__main__":
    main()
