"""Independently admit observed namespaces and DLLs against the complete native input closure."""

from __future__ import annotations
import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import dump, pin, read, require, sha
from runtime_custody import aliases_unchanged


def validate_metadata(meta: dict[str, Any], plan: dict[str, Any]) -> dict[str, int]:
    require(
        meta["schema_version"] == "controlled-lra-R-process.v1"
        and meta["metadata_only"] is True
        and meta["original_script"] is None
        and meta["numerical_exit"] is None
        and meta["numerical_error"] is None
        and type(meta["metadata_exit"]) is int
        and meta["metadata_exit"] == 0
        and meta["metadata_error"] is None,
        "Metadata-only status differs; numerical execution not permitted",
    )
    require(
        meta["actual_trailing_arguments"] == [],
        "Runtime probe received numerical source arguments",
    )
    pins = {r["path"] for r in plan["input_pins"]}
    native = set(plan["native_dependency_files"])
    roots = [
        Path(plan["current_R_home"]),
        Path(plan["original_Darwin_native_installation"]["root"]),
    ]
    counts = {}
    for label in ("before", "after"):
        value = meta[label]
        require(
            value["version"] == "4.6.0"
            and value["R_arch"] == ""
            and value["dynlib_ext"] == ".so"
            and value["R_home"] == str(roots[0]),
            "Actual R platform/home/layout differs",
        )
        require(
            set(value["library_paths"]) == {str(roots[0] / "library"), str(roots[1])},
            "Actual library namespace search differs",
        )
        namespaces = value["namespaces"]
        by = {r["name"]: r for r in namespaces}
        require(len(by) == len(namespaces), "Duplicate namespace")
        for name, version in [
            ("base", "4.6.0"),
            ("disqover", "0.9.14"),
            ("RcppDE", "0.1.9"),
            ("jsonlite", "2.0.0"),
        ]:
            require(
                by[name]["version"] == version,
                "Actual required namespace version differs",
            )
        for row in namespaces:
            path = Path(row["path"])
            require(
                row["path_error"] is None
                and isinstance(row["raw_path"], str)
                and Path(row["raw_path"]).resolve() == path
                and path.resolve() == path
                and str(path / "DESCRIPTION") in pins
                and any(path.is_relative_to(root) for root in roots),
                "Namespace outside complete pinned physical trees",
            )
        for row in value["DLLs"]:
            require(type(row["built_in"]) is bool, "DLL built-in identity type differs")
            if row["built_in"]:
                require(
                    row["name"] == row["path"] == row["raw_path"] == "base"
                    and row["path_error"] is None,
                    "Unknown built-in DLL sentinel",
                )
            else:
                path = Path(row["path"])
                require(
                    row["path_error"] is None
                    and isinstance(row["raw_path"], str)
                    and Path(row["raw_path"]).resolve() == path
                    and row["path"] in native & pins
                    and path.resolve() == path
                    and any(path.is_relative_to(root) for root in roots),
                    f"Observed DLL outside exact declared closure: {row}",
                )
        require(bool(value["session_info"]), "Actual sessionInfo missing")
        counts[label + "_namespaces"] = len(namespaces)
        counts[label + "_DLLs"] = len(value["DLLs"])
    return counts


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--plan", type=Path, required=True)
    a = p.parse_args()
    plan = read(a.plan)
    out = Path(plan["output"])
    require(
        aliases_unchanged(
            plan["runtime_aliases"], link_text=plan["runtime_alias_links"]
        ),
        "Frozen lexical aliases differ",
    )
    for row in plan["input_pins"]:
        require(pin(Path(row["path"])) == row, "Original frozen input changed")
    progress = read(out / "stage-progress.json")
    require(
        len(progress) == 1
        and progress[0]["argv"] == plan["stages"][0]["argv"]
        and type(progress[0]["actual_exit"]) is int
        and progress[0]["actual_exit"] == 0
        and progress[0]["timed_out"] is False,
        "Actual metadata-only R stage not zero",
    )
    meta = read(out / "runtime-observation.json")
    counts = validate_metadata(meta, plan)
    dump(
        out / "independent-runtime-review.json",
        {
            "candidate": plan["candidate"],
            "plan_sha256": sha(a.plan),
            "actual_native_R_stage_exit": 0,
            "counts": counts,
            "metadata": pin(out / "runtime-observation.json"),
            "native_dependency_files": len(plan["native_dependency_files"]),
            "input_pin_count": len(plan["input_pins"]),
            "original_native_library_files": 913,
            "failed_original_replay": plan["failed_original_replay"],
            "R_numerical_source_ran": False,
            "Python_optimizer_ran": False,
            "actual_exit": 0,
        },
    )


if __name__ == "__main__":
    main()
