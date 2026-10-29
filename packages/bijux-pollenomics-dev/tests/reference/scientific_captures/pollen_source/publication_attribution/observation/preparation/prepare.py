"""Prepare current publication source custody; native consumers require registration."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import sys
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
    "observation_custody.py",
    "check_observation.py",
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
import contracts as c  # noqa: E402
import observation_custody as o  # noqa: E402
from runtime_contracts import namespace_snapshot  # noqa: E402
from source_runtime import (  # noqa: E402
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
    c.namespace()
    output = c.output_root(args.output, absent=True)
    c.require(
        not output.is_relative_to(c.SOURCE) and not c.SOURCE.is_relative_to(output),
        "Source/output overlap",
    )
    canonical = c.identity()
    c.require(
        canonical["candidate"] == args.candidate and canonical["status"] == "",
        "Exact clean candidate required",
    )
    manifest_path = c.SOURCE / "prepared-source-manifest.json"
    manifest_record = c.pin(manifest_path)
    review_record = c.pin(args.review)
    review = c.load(args.review)
    c.require(
        review_record["sha256"] == args.review_sha256
        and review["approved"] is True
        and review["source_manifest_sha256"] == manifest_record["sha256"],
        "Exact reviewed source required",
    )
    frozen = c.union([manifest_record, review_record])
    for row in c.load(manifest_path)["files"]:
        name = Path(row["path"])
        c.require(
            not name.is_absolute() and ".." not in name.parts,
            "Held source path escaped",
        )
        expected = {**row, "path": str(c.SOURCE / name)}
        c.require(
            c.pin(Path(expected["path"])) == expected, "Held source bytes changed"
        )
        frozen = c.union(frozen, [expected])
    context_path = c.SOURCE / "saved-execution-context.json"
    context = c.load(context_path)
    original, mapped, original_pins = o.retained_inputs(context)
    frozen = c.union(frozen, original_pins)
    for label in (
        "historical_policy_review",
        "historical_policy_custody",
        "current_policy_review",
    ):
        row = context[label]
        c.require(c.pin(Path(row["path"])) == row, "Policy provenance bytes changed")
        frozen = c.union(frozen, [row])
    c.require(
        context["historical_policy_review"]["sha256"]
        == context["old_governed_policy_review_sha256"]
        and context["current_policy_review"]["sha256"]
        == context["current_governed_policy_review_sha256"],
        "Exact old/current policy epochs differ",
    )
    expected_origins = {}
    for kind in ("publication", "doi"):
        receipt = c.load(Path(original["output"]) / (kind + "-source-execution.json"))
        raw = Path(mapped[receipt["source"]["path"]]).read_bytes()
        o.source_role(
            kind, raw, receipt["first_party_origins"], receipt["first_party_origins"]
        )
        expected_origins[kind] = receipt["first_party_origins"]
    trees, source_rows = c.first_party_snapshot()
    runtime_authority, runtime_rows = authenticate_runtime()
    retention_root = Path(context["source_retention"]["path"]).parent
    retention_tree = namespace_snapshot(retention_root, [])
    c.require(
        all(v["kind"] != "symlink" for v in retention_tree["entries"].values()),
        "Retention alias",
    )
    retention_rows = [
        c.pin(retention_root / name)
        for name, v in retention_tree["entries"].items()
        if v["kind"] == "file"
    ]
    plan: dict[str, Any] = {
        "schema_version": "neotoma-publication-observer-plan.v1",
        "id": "neotoma-publication-observer-"
        + hashlib.sha256(
            (args.candidate + str(output) + manifest_record["sha256"]).encode()
        ).hexdigest()[:16],
        "candidate": args.candidate,
        "repository": str(c.ROOT),
        "canonical_identity": canonical,
        "output": str(output),
        "original_output": original["output"],
        "saved_execution_context": c.pin(context_path),
        "retained_original_paths": mapped,
        "expected_package_origins": expected_origins,
        "first_party_namespaces": trees,
        "capture_namespaces": [*original["capture_namespaces"], retention_tree],
        "input_pins": c.union(frozen, source_rows, runtime_rows, retention_rows),
        "absent_input_paths": original["absent_input_paths"],
        "original_controller_and_source_expected_pins": frozen,
        "common_runner": str(c.SOURCE / "common_runner.py"),
        "resources": {
            "overall_timeout_seconds": 120,
            "resident_memory_limit_bytes": 2 * 1024**3,
            "output_byte_limit": 64 * 1024**2,
        },
        "scope": "Observer-only replay over the original source native2zero/observer1/whole1 and tracked-checker2/2. Exact DOI standalone stdlib origin role differs from publication package imports. Independent85/13 reconstruction unchanged; only two authenticated provenance leaves bridge governed historical reports. No producer, acquisition, rights, human or LRA admission.",
        "environment": {
            "PYTHONDONTWRITEBYTECODE": "1",
            "TMPDIR": str(output / "temporary"),
            "XDG_CACHE_HOME": str(output / "cache"),
            "MPLCONFIGDIR": str(output / "matplotlib"),
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
        },
        "stages": [
            {
                "id": "independent-saved-publication-source-observer",
                "argv": [
                    str(PYTHON),
                    "-I",
                    "-B",
                    str(c.SOURCE / "observe.py"),
                    "--plan",
                    str(output / "plan.json"),
                ],
                "timeout_seconds": 90,
                "must_succeed": True,
            }
        ],
    }
    plan["actual_launch_argv"] = attach_runtime_launcher(
        plan,
        runtime_authority,
        runtime_rows,
        output,
        output / "plan.json",
        [
            str(PYTHON),
            "-I",
            "-B",
            str(c.SOURCE / "run.py"),
            "--plan",
            str(output / "plan.json"),
            "--registered-plan-sha256",
            "PLAN_SHA256",
        ],
        wall=120,
        memory=2 * 1024**3,
        storage=64 * 1024**2,
    )
    c.verify_inputs(plan)
    _, final_map, final_pins = o.retained_inputs(context)
    c.require(
        c.exact(final_map, mapped) and c.exact(final_pins, original_pins),
        "Original expected source changed during census",
    )
    c.require(c.identity() == canonical, "Candidate changed during preparation")
    parent = output.parent
    while not parent.exists():
        parent = parent.parent
    c.require(
        shutil.disk_usage(parent).free >= 256 * 1024**2, "Insufficient256MiB reserve"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    c.output_root(output, absent=True).mkdir()
    for directory_name in ("temporary", "cache", "matplotlib"):
        (output / directory_name).mkdir()
    c.dump(output / "plan.json", plan)
    c.dump(
        output / "preparation.json",
        {
            "actual_exit": 0,
            "candidate": args.candidate,
            "plan": c.pin(output / "plan.json"),
            "protected_inputs": len(plan["input_pins"]),
            "producer_stages_repeated": 0,
            "original_producer_exits": [0, 0],
            "original_observer_and_whole_exit": 1,
            "original_tracked_checker_exits": [2, 2],
        },
    )
    print(output / "plan.json")


if __name__ == "__main__":
    main()
