"""Freeze a fresh observer over the unchanged offline environment and production receipts."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import (
    BASE,
    BASE_SHA,
    ROOT,
    SOURCE,
    confined_output,
    create_root,
    digest,
    json_value,
    namespace_snapshot,
    pin,
    require,
    require_runtime_environment,
    validate_probe_dependencies,
    verify_absences,
    verify_aliases,
    verify_base_namespaces,
    verify_cache_membership,
    verify_pin,
    verify_unused_namespaces,
    write_json,
)

RETAINED = ROOT / "artifacts/science/current-offline-isolated-source-runtime-bootstrap"
PLAN_SHA = "fb49f9b395f92cf7ca9c84c5ff2e9e1bf39cbd58e259b8017a029ec1a96e9057"
OUTER_SHA = "745a5f2d922ef96dea812ec92b01ca033a8133486ce557689e29136ae0a9d69d"
OLD_CANDIDATE = "7513efa1224b22d5de7748140bdd8fce34dca886"


def observation_output(path: Path) -> Path:
    output = confined_output(path, absent=True)
    for protected in (RETAINED, SOURCE):
        require(
            not output.is_relative_to(protected)
            and not protected.is_relative_to(output),
            "Observation output overlaps protected source/runtime",
        )
    return output


def identity() -> dict[str, str]:
    import hashlib

    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", *args], cwd=ROOT)

    return {
        "candidate": git("rev-parse", "HEAD").decode().strip(),
        "status": git("status", "--porcelain").decode(),
        "tracked_inventory_sha256": hashlib.sha256(
            git("ls-files", "-s", "-z")
        ).hexdigest(),
    }


def bootstrap_contract(
    plan: dict[str, Any], common: dict[str, Any], outer: dict[str, Any]
) -> None:
    require(
        all(row["candidate"] == OLD_CANDIDATE for row in (plan, common, outer)),
        "Original bootstrap candidate differs",
    )
    require(
        common["plan_sha256"] == outer["plan_sha256"] == PLAN_SHA,
        "Original plan link differs",
    )
    require(
        all(
            type(row["actual_exit"]) is int and row["actual_exit"] == 1
            for row in (common, outer)
        ),
        "Original whole1 was relabelled",
    )
    require(
        type(outer["common_actual_exit"]) is int
        and outer["common_actual_exit"] == 1
        and outer["timed_out"] is False,
        "Original common failure differs",
    )
    require(
        common["before_pin_mismatches"] == common["after_pin_mismatches"] == []
        and common["absent_input_paths_unchanged"] is True,
        "Original input custody failed",
    )
    require(
        outer["runtime_alias_after_failure"] is None
        and outer["input_after_failures"] == []
        and all(
            outer[key] is True
            for key in (
                "memory_bound_pass",
                "storage_bound_pass",
                "overall_wall_bound_pass",
            )
        ),
        "Original custody/resource postcheck failed",
    )
    stages = common["stages"]
    require(len(stages) == len(plan["stages"]) == 4, "Original stage count differs")
    for index, (actual, declared) in enumerate(
        zip(stages, plan["stages"], strict=True)
    ):
        require(
            all(
                actual[key] == declared[key]
                for key in ("id", "argv", "timeout_seconds", "must_succeed")
            ),
            "Original stage contract differs",
        )
        require(
            type(actual["actual_exit"]) is int
            and actual["actual_exit"] == (0 if index < 3 else 1)
            and actual["timed_out"] is False,
            "Original production/observer role differs",
        )


def materialized_pins(root: Path) -> list[dict[str, Any]]:
    require(root.is_dir() and not root.is_symlink(), "Retained output root differs")
    result = []
    for path in root.rglob("*"):
        require(
            not path.is_symlink() and (path.is_file() or path.is_dir()),
            "Retained runtime has aliases/specials",
        )
        if path.is_file():
            result.append(pin(path))
    return result


def production_pins(
    root: Path, common: dict[str, Any], common_path: Path, outer_path: Path
) -> list[dict[str, Any]]:
    import hashlib
    import json

    rows = common["products"]
    require(
        len(rows) == len({row["path"] for row in rows}),
        "Duplicate original produced path",
    )
    for row in rows:
        path = Path(row["path"])
        require(
            type(row["bytes"]) is int and row["bytes"] >= 0,
            "Original produced size differs",
        )
        require(
            path.is_absolute()
            and path.resolve(strict=True).is_relative_to(root.resolve(strict=True))
            and path == path.resolve(strict=True),
            "Original produced path escaped",
        )
        if path == root / "common-runner.stdout":
            raw = path.read_bytes()
            prefix = raw[: row["bytes"]]
            final = (
                json.dumps(
                    {
                        "terminal": str(common_path),
                        "sha256": digest(common_path),
                        "status": common["status"],
                    }
                )
                + "\n"
            ).encode()
            require(
                hashlib.sha256(prefix).hexdigest() == row["sha256"]
                and raw[row["bytes"] :] == final,
                "Common final stdout correspondence differs",
            )
        else:
            verify_pin(row)
    physical = materialized_pins(root)
    require(
        {row["path"] for row in physical}
        == {row["path"] for row in rows} | {str(common_path), str(outer_path)},
        "Original produced membership differs",
    )
    return physical


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--review-sha256", required=True)
    args = parser.parse_args()
    admission = require_runtime_environment(dict(os.environ))
    require(
        sys.flags.isolated == 1
        and sys.flags.no_site == 1
        and sys.dont_write_bytecode
        and digest(BASE) == BASE_SHA
        and Path(sys.executable).resolve(strict=True) == BASE,
        "Observer preparation base differs",
    )
    observation_output(args.output)
    canonical = identity()
    require(
        canonical["candidate"] == args.candidate and canonical["status"] == "",
        "Current clean candidate differs",
    )
    manifest_path = SOURCE / "prepared-source-manifest.json"
    require(
        digest(args.review) == args.review_sha256, "Independent review bytes differ"
    )
    review = json_value(args.review)
    require(
        review["approved"] is True
        and review["source_manifest_sha256"] == digest(manifest_path),
        "Independent approval differs",
    )
    source_files = []
    for row in json_value(manifest_path)["files"]:
        path = SOURCE / row["path"]
        require(
            path.is_file()
            and not path.is_symlink()
            and digest(path) == row["sha256"]
            and path.stat().st_size == row["bytes"],
            "Held observer source differs",
        )
        source_files.append(path)
    original_plan = RETAINED / "plan.json"
    original_outer = RETAINED / "runtime-bootstrap-terminal.json"
    original_common = RETAINED / "terminal.json"
    require(
        digest(original_plan) == PLAN_SHA and digest(original_outer) == OUTER_SHA,
        "Original bootstrap references differ",
    )
    old = json_value(original_plan)
    outer = json_value(original_outer)
    common = json_value(original_common)
    require(
        outer["common_terminal"]
        == {"path": str(original_common), "sha256": digest(original_common)},
        "Original common bytes differ",
    )
    bootstrap_contract(old, common, outer)
    validate_probe_dependencies(old["selected_payloads"])
    inputs: dict[str, Any] = {}
    produced = production_pins(RETAINED, common, original_common, original_outer)
    for row in [
        *old["input_pins"],
        *produced,
        *[pin(path) for path in [*source_files, manifest_path, args.review]],
    ]:
        require(
            row["path"] not in inputs or inputs[row["path"]] == row,
            "Protected input custody conflict",
        )
        verify_pin(row)
        inputs[row["path"]] = row
    verify_aliases(old["runtime_aliases"])
    verify_cache_membership(old["selected_payloads"])
    verify_base_namespaces(old["base_namespaces"])
    verify_unused_namespaces(old["unused_no_site_namespaces"])
    verify_absences(old["absent_input_paths"])
    materialized = namespace_snapshot(RETAINED, [])
    require(
        {
            str(RETAINED / name)
            for name, entry in materialized["entries"].items()
            if entry["kind"] == "file"
        }
        == {row["path"] for row in produced},
        "Materialized file membership changed during census",
    )
    for row in inputs.values():
        verify_pin(row)
    verify_base_namespaces([materialized])
    require(identity() == canonical, "Current candidate changed during readonly census")
    create_root(args.output)
    for name in ("temporary", "cache", "matplotlib"):
        (args.output / name).mkdir()
    plan_path = args.output / "plan.json"
    environment = RETAINED / "environment"
    reference = {
        "plan": pin(original_plan),
        "common": pin(original_common),
        "outer": pin(original_outer),
        "original_candidate": OLD_CANDIDATE,
        "original_whole_actual_exit": 1,
        "production_stage_actual_exits": [0, 0, 0],
        "original_observer_actual_exit": 1,
    }
    plan = {
        "schema_version": "saved-offline-source-runtime-observation-plan.v1",
        "candidate": args.candidate,
        "repository": str(ROOT),
        "canonical_identity": canonical,
        "output": str(args.output),
        "retained_environment": str(environment),
        "retained_wheels": str(RETAINED / "wheels"),
        "retained_bootstrap": reference,
        "base_interpreter": old["base_interpreter"],
        "base_prefix": old["base_prefix"],
        "runtime_aliases": old["runtime_aliases"],
        "base_namespaces": old["base_namespaces"],
        "protected_materialized_namespaces": [materialized],
        "unused_no_site_namespaces": old["unused_no_site_namespaces"],
        "absent_input_paths": old["absent_input_paths"],
        "selected_payloads": old["selected_payloads"],
        "input_pins": [inputs[k] for k in sorted(inputs)],
        "environment_override_admission": admission,
        "resources": {
            "overall_timeout_seconds": 180,
            "resident_memory_limit_bytes": 3 * 1024**3,
            "output_byte_limit": 256 * 1024**2,
        },
        "environment": {
            **old["environment"],
            "TMPDIR": str(args.output / "temporary"),
            "XDG_CACHE_HOME": str(args.output / "cache"),
            "MPLCONFIGDIR": str(args.output / "matplotlib"),
        },
        "stages": [
            {
                "id": "independent-source-runtime-observation",
                "argv": [
                    str(environment / "bin/python"),
                    "-I",
                    "-B",
                    str(SOURCE / "observe.py"),
                    "--plan",
                    str(plan_path),
                ],
                "timeout_seconds": 90,
                "must_succeed": True,
            }
        ],
        "scope": "Observer only over unchanged environment and transport from original129 three production0/whole1. Current candidate may differ; no first-party source is executed. Complete original input plus materialized root bytes/namespaces protected before/after. No install/ZIP/environment/model/network repeat, old runtime recovery or first-party installed interface claimed; completed-child RSS and logical bytes are postchecks.",
    }
    write_json(plan_path, plan)
    write_json(
        args.output / "preparation.json",
        {
            "actual_exit": 0,
            "plan": pin(plan_path),
            "candidate": args.candidate,
            "original_candidate": OLD_CANDIDATE,
            "input_pins": len(inputs),
            "old_output_regular_files": len(materialized_pins(RETAINED)),
            "native_stages_launched": 0,
        },
    )
    print(str(plan_path))


if __name__ == "__main__":
    main()
