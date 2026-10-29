"""Freeze two exact Swedish source cohorts and current fixed-baseline execution."""

from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import shutil
import sys
from typing import Any

_entry_path = Path(__file__).absolute()
if _entry_path != _entry_path.resolve() or any(
    p.is_symlink() for p in (_entry_path, *_entry_path.parents)
):
    raise ValueError("Physical controller entrypoint before helper imports")
_entry_directory = _entry_path.parent
_expected_python = {
    "contracts.py",
    "independent.py",
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

from contracts import (  # noqa: E402
    FAMILIES,
    POLICY,
    PREPARED,
    PRIVATE,
    ROOT,
    SOURCE,
    dump,
    exact,
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
    namespace()
    output = output_root(args.output, absent=True)
    require(
        not output.is_relative_to(SOURCE) and not SOURCE.is_relative_to(output),
        "Source/output overlap",
    )
    canonical = identity()
    require(
        canonical["candidate"] == args.candidate and canonical["status"] == "",
        "Exact clean source candidate required",
    )
    manifest_pin = pin(SOURCE / "prepared-source-manifest.json")
    review_pin = pin(args.review)
    require(review_pin["sha256"] == args.review_sha256, "Exact review SHA differs")
    review, manifest = load(args.review), load(Path(manifest_pin["path"]))
    require(
        review["approved"] is True
        and review["source_manifest_sha256"] == manifest_pin["sha256"],
        "Exact independent source approval required",
    )
    original = union([manifest_pin, review_pin])
    for row in manifest["files"]:
        expected = {**row, "path": str(SOURCE / row["path"])}
        require(pin(Path(expected["path"])) == expected, "Held controller differs")
        original = union(original, [expected])
    declared = load(SOURCE / "declared-inputs.json")
    for expected in declared["files"]:
        require(
            pin(Path(expected["path"])) == expected,
            "Original declared source input changed",
        )
        original = union(original, [expected])
    policy_pin = pin(ROOT / POLICY)
    policy = load(ROOT / POLICY)
    owners = {}
    for family in FAMILIES:
        owner_id = "regions/nordic/" + family + "/report-products"
        selected = [x for x in policy["owners"] if x["owner_id"] == owner_id]
        require(
            len(selected) == 1
            and exact(selected[0], declared["studies"][family]["original_owner_row"]),
            "Original unresolved owner declaration changed",
        )
        require(
            selected[0]["role"] == "unresolved", "Future admission must be separate"
        )
        owners[family] = selected[0]
        require(
            declared["studies"][family]["actual_protocol_training"]["path"]
            not in [str(ROOT / p) for p in selected[0]["producer_inputs"]],
            "Training declaration defect must remain explicit until reviewed correction",
        )
    original = union(original, [policy_pin])
    trees, source_rows = first_party_snapshot()
    authority, runtime_rows = authenticate_runtime()
    inputs = union(original, source_rows, runtime_rows)
    original_runtime = load(Path(authority["plan"]["path"]))
    cache_namespaces = [
        *trees,
        *original_runtime["base_namespaces"],
        *original_runtime["protected_materialized_namespaces"],
    ]
    protected = {row["path"] for row in inputs}
    absent_caches = {}
    cache_census = {
        "protected_py_sources": 0,
        "cache_candidates_present": 0,
        "cache_candidates_absent": 0,
    }
    for tree in cache_namespaces:
        for relative, entry in tree["entries"].items():
            source = Path(tree["root"]) / relative
            if entry["kind"] != "file" or source.suffix != ".py":
                continue
            require(
                str(source) in protected, "Complete guarded cache source not protected"
            )
            candidate = Path(
                importlib.util.cache_from_source(str(source), optimization="")
            )
            cache_census["protected_py_sources"] += 1
            require(
                not candidate.is_symlink()
                and not any(p.is_symlink() for p in candidate.parents),
                "Import cache aliases are not admitted",
            )
            if candidate.exists():
                require(
                    str(candidate) in protected and candidate.is_file(),
                    "Existing import cache is not an exact protected file",
                )
                cache_census["cache_candidates_present"] += 1
            else:
                absent_caches[str(candidate)] = {
                    "source_path": str(source),
                    "cache_tag": sys.implementation.cache_tag,
                }
                cache_census["cache_candidates_absent"] += 1
    proj_data = (
        PYTHON.parent.parent / "lib/python3.11/site-packages/pyproj/proj_dir/share/proj"
    )
    require(
        pin(proj_data / "proj.db") in inputs,
        "Qualified complete PROJ database required",
    )
    plan: dict[str, Any] = {
        "schema_version": "swedish-direct-pollen-source-replay-plan.v1",
        "candidate": args.candidate,
        "repository": str(ROOT),
        "canonical_identity": canonical,
        "output": str(output),
        "studies": declared["studies"],
        "owner_rows": owners,
        "whole_ownership_policy": policy_pin,
        "first_party_namespaces": trees,
        "input_pins": inputs,
        "runtime_aliases": load(Path(authority["plan"]["path"]))["runtime_aliases"],
        "original_controller_and_source_expected_pins": original,
        "absent_input_paths": sorted(absent_caches),
        "absent_source_cache_candidates": absent_caches,
        "cache_source_namespaces": cache_namespaces,
        "protected_source_cache_census": cache_census,
        "common_runner": str(SOURCE / "common_runner.py"),
        "private_source_store": str(PRIVATE),
        "PROJ_data_directory": str(proj_data),
        "PROJ_user_directory": str(output / "proj-cache"),
        "source_metadata_defect": declared["source_metadata_defect"],
        "prepared_produced_output_names": list(PREPARED),
        "historical_protocol_freeze_reference_or_verification_files_reproduced": False,
        "resources": {
            "overall_timeout_seconds": 300,
            "resident_memory_limit_bytes": 2 * 1024**3,
            "output_byte_limit": 256 * 1024**2,
        },
        "scope": "New source-bound replay of two previously exposed direct observed-pollen cohorts. Maintained prepare/predict/score and independent source membership/count-mass/exclusion/score/whole-byte observer. Four preparation products per cohort are actually produced; authored protocol, earlier freeze/reference snapshot and verification manifest remain historical input roles. Fixed spatial baselines only; no LRA, independent confirmation, vegetation/field accuracy, acquisition, rights or human acceptance.",
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
        "Ambient PROJ override",
    )
    stages = []
    for family in FAMILIES:
        for stage in ("prepare", "predict", "score", "observe"):
            stages.append(
                {
                    "id": family + "-" + stage,
                    "argv": [
                        str(PYTHON),
                        "-I",
                        "-B",
                        str(
                            SOURCE
                            / (
                                "observe.py"
                                if stage == "observe"
                                else "execute_source.py"
                            )
                        ),
                        "--plan",
                        str(output / "plan.json"),
                        "--family",
                        family,
                        *([] if stage == "observe" else ["--stage", stage]),
                    ],
                    "timeout_seconds": 60 if stage in ("prepare", "observe") else 30,
                    "must_succeed": True,
                }
            )
    plan["stages"] = stages
    plan["actual_launch_argv"] = attach_runtime_launcher(
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
        wall=300,
        memory=2 * 1024**3,
        storage=256 * 1024**2,
    )
    # Every original expected declaration is frozen before expensive census and
    # revalidated with namespace/runtime authority immediately before any write.
    verify_inputs(plan)
    require(identity() == canonical, "Candidate changed during source preparation")
    parent = output.parent
    while not parent.exists():
        parent = parent.parent
    require(
        shutil.disk_usage(parent).free >= 1024**3,
        "At least1GiB physical free reserve required",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output_root(output, absent=True).mkdir()
    for name in ("temporary", "cache", "matplotlib", "proj-cache", "native-receipts"):
        (output / name).mkdir()
    dump(output / "plan.json", plan)
    dump(
        output / "preparation.json",
        {
            "actual_exit": 0,
            "candidate": args.candidate,
            "plan": pin(output / "plan.json"),
            "input_pins": len(plan["input_pins"]),
            "actual_stages_launched": 0,
            "qualified_source_runtime": authority,
            "scope": plan["scope"],
        },
    )
    print(output / "plan.json")


if __name__ == "__main__":
    main()
